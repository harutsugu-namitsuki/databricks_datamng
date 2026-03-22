# Unity Catalog 設計書（AWSシングルクラウド版）

## 1. 概要

Unity Catalog を使用してデータガバナンスを実現します。
AWS Databricks 上で動作し、S3をストレージとして使用します。

> 参照: [AWSを使用したDatabricksの環境構築 (Flect)](https://cloud.flect.co.jp/entry/2024/10/07/103341)

---

## 2. 名前空間構造

```
Unity Catalog
└── northwind_catalog (カタログ)
    ├── bronze (スキーマ) ← 全14テーブル
    │   ├── categories
    │   ├── customers
    │   ├── employees
    │   ├── suppliers
    │   ├── shippers
    │   ├── products
    │   ├── orders
    │   ├── order_details
    │   ├── region
    │   ├── territories
    │   ├── us_states
    │   ├── employee_territories
    │   ├── customer_demographics
    │   └── customer_customer_demo
    ├── silver (スキーマ)
    │   ├── customers
    │   ├── orders
    │   ├── order_details
    │   └── products
    ├── gold (スキーマ)
    │   ├── sales_by_product
    │   ├── sales_by_customer
    │   ├── sales_by_category
    │   └── order_summary
    └── ops (スキーマ)
        ├── job_runs
        ├── ingestion_log
        └── dq_results
```

---

## 3. Storage Credential

| 項目 | 値 |
|------|-----|
| 名前 | `aws_s3_credential` |
| タイプ | AWS IAM Role |
| IAM Role ARN | CloudFormation Output: `CatalogRoleArn` |
| 信頼ポリシー | UCMasterRole (`414351767826`) + self-assume |

> ⚠️ **カタログロール**のARNを使用。ワークスペースロールではない。

### IAM Role ポリシー（カタログロール）

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket",
        "s3:GetBucketLocation",
        "s3:GetLifecycleConfiguration",
        "s3:PutLifecycleConfiguration"
      ],
      "Resource": [
        "arn:aws:s3:::lake-northwind-<account-id>",
        "arn:aws:s3:::lake-northwind-<account-id>/*"
      ]
    }
  ]
}
```

---

## 4. External Location

| 名前 | URL | Credential | 作成方法 |
|------|-----|------------|---------|
| `ext_northwind_catalog` | `s3://lake-northwind-<account-id>/catalog/` | aws_s3_credential | UIから作成（実装手順書 Step 2-5） |
| `ext_bronze` | `s3://lake-northwind-<account-id>/bronze/` | aws_s3_credential | Notebook `00_setup_unity_catalog.py` |
| `ext_silver` | `s3://lake-northwind-<account-id>/silver/` | aws_s3_credential | Notebook `00_setup_unity_catalog.py` |
| `ext_gold` | `s3://lake-northwind-<account-id>/gold/` | aws_s3_credential | Notebook `00_setup_unity_catalog.py` |
| `ext_ops` | `s3://lake-northwind-<account-id>/ops/` | aws_s3_credential | Notebook `00_setup_unity_catalog.py` |

### 作成SQL例

```sql
-- External Location の作成
CREATE EXTERNAL LOCATION ext_bronze
  URL 's3://lake-northwind-<account-id>/bronze/'
  WITH (STORAGE CREDENTIAL aws_s3_credential);
```

---

## 5. アクセス制御

### 5.1 グループ設計

Databricks Unity Catalog ではグループ単位で権限を管理する。グループの作成・メンバー追加は **Databricks UI で行う**（SQL 不可）。

| グループ | 想定ユーザー | アクセス範囲 | 実装スプリント |
|---------|------------|------------|--------------|
| `analyst_group` | データアナリスト | Gold 層のみ（SELECT） | Sprint 1 ✅ |
| `marketing_group` | マーケティング担当 | 特定ビューのみ（動的マスキング経由） | Sprint 5 |
| `engineer_group` | データエンジニア | 全層フルアクセス | Sprint 5（現在は admin が相当） |

### 5.2 権限付与（analyst_group / Sprint 1 実装済み）

Unity Catalog ではスキーマのデータにアクセスするために **3段階の権限**が必要。

```sql
-- ① カタログへの入口（これがないと配下スキーマにも辿り着けない）
GRANT USE CATALOG ON CATALOG northwind_catalog TO analyst_group;

-- ② Gold スキーマへの入口
GRANT USE SCHEMA ON SCHEMA northwind_catalog.gold TO analyst_group;

-- ③ Gold スキーマのデータを読む権限
GRANT SELECT ON SCHEMA northwind_catalog.gold TO analyst_group;

-- ※ bronze / silver / ops は付与しない（Unity Catalog はデフォルト拒否）
```

**engineer_group 権限付与例（Sprint 5 で実施予定）:**

```sql
GRANT ALL PRIVILEGES ON SCHEMA northwind_catalog.bronze TO engineer_group;
GRANT ALL PRIVILEGES ON SCHEMA northwind_catalog.silver TO engineer_group;
GRANT ALL PRIVILEGES ON SCHEMA northwind_catalog.gold TO engineer_group;
GRANT ALL PRIVILEGES ON SCHEMA northwind_catalog.ops TO engineer_group;
```

### 5.3 方針

| スキーマ | analyst_group | engineer_group | Admin |
|---------|--------------|----------------|-------|
| bronze | ❌ アクセス不可 | ✅ 読み書き（Sprint 5） | ✅ 全権限 |
| silver | ❌ アクセス不可 | ✅ 読み書き（Sprint 5） | ✅ 全権限 |
| gold | ✅ 読み取りのみ（Sprint 1） | ✅ 読み書き（Sprint 5） | ✅ 全権限 |
| ops | ❌ アクセス不可 | ✅ 読み書き（Sprint 5） | ✅ 全権限 |

> Bronze/Silver は原則 Analyst に見せない（個人情報混入対策）。必要に応じて Gold に動的マスキング View 経由で公開（Sprint 5 / Story 2-3）。

---

## 6. AWS Databricks での注意点

| 項目 | 内容 |
|------|------|
| クラスターモード | **専用（Single User）** を使用 |
| Storage Credential作成 | **Databricks UIから作成**（SQLでは環境依存エラーあり） |
| Storage CredentialのIAMロール | **カタログロール**を指定（ワークスペースロールではない） |
| カタログ作成 | UIまたはSQLで作成（環境に応じて選択） |
| External Location | **SQLで作成可能** |
| スキーマ作成 | **SQLで作成可能** |

---

## 変更履歴

| 日付 | 変更内容 |
|------|----------|
| 2026-03-08 | シングルクラウド版として作成 |
| 2026-03-09 | カタログロール指定を明記、バケット名テンプレート修正 |
| 2026-03-22 | Notebook実装と同期: Bronzeスキーマを全14テーブルに拡大、ext_northwind_catalog (catalog/) を追加 |
| 2026-03-22 | アクセス制御を Sprint 1 実装内容に合わせて更新: グループ名を analyst_group に統一、USE CATALOG/USE SCHEMA の3段階 GRANT を明記、ops を Analyst アクセス不可に修正、Sprint 実装状況を追記 |
