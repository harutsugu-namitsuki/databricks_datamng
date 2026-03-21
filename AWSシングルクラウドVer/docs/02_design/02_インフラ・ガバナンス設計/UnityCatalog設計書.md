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

### 5.1 ロール設計

| ロール | 権限 |
|--------|------|
| data_engineer | Bronze/Silver/Gold/Ops の読み書き |
| data_analyst | Gold の読み取りのみ |
| admin | 全権限 |

### 5.2 権限付与例

```sql
-- Analystにgoldスキーマの読み取り権限を付与
GRANT SELECT ON SCHEMA northwind_catalog.gold TO analyst_group;

-- DataEngineerに全スキーマの権限を付与
GRANT ALL PRIVILEGES ON SCHEMA northwind_catalog.bronze TO engineer_group;
GRANT ALL PRIVILEGES ON SCHEMA northwind_catalog.silver TO engineer_group;
GRANT ALL PRIVILEGES ON SCHEMA northwind_catalog.gold TO engineer_group;
GRANT ALL PRIVILEGES ON SCHEMA northwind_catalog.ops TO engineer_group;
```

### 5.3 方針

| スキーマ | Analyst | DataEngineer | Admin |
|---------|---------|-------------|-------|
| bronze | ❌ アクセス不可 | ✅ 読み書き | ✅ 全権限 |
| silver | ❌ アクセス不可 | ✅ 読み書き | ✅ 全権限 |
| gold | ✅ 読み取りのみ | ✅ 読み書き | ✅ 全権限 |
| ops | ✅ 読み取りのみ | ✅ 読み書き | ✅ 全権限 |

> Bronze/Silverは原則Analystに見せない（誤解・個人情報混入対策）。必要に応じてGoldにマスキングView経由で公開。

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
