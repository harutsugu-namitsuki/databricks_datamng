# Unity Catalog 設計書（AWSシングルクラウド版）

## 1. 概要

Unity Catalog を使用してデータガバナンスを実現します。
AWS Databricks 上で動作し、S3をストレージとして使用します。

---

## 2. 名前空間構造

```
Unity Catalog
└── northwind_catalog (カタログ)
    ├── bronze (スキーマ)
    │   ├── customers
    │   ├── orders
    │   ├── order_details
    │   ├── products
    │   ├── categories
    │   ├── suppliers
    │   ├── employees
    │   └── shippers
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
| IAM Role ARN | `arn:aws:iam::<account-id>:role/databricks-unity-catalog-role` |
| 信頼ポリシー | Databricks の AWS Account ID を許可 |

### IAM Role ポリシー（最小権限）

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
        "s3:GetBucketLocation"
      ],
      "Resource": [
        "arn:aws:s3:::lake-northwind",
        "arn:aws:s3:::lake-northwind/*"
      ]
    }
  ]
}
```

---

## 4. External Location

| 名前 | URL | Credential |
|------|-----|------------|
| `ext_bronze` | `s3://lake-northwind/bronze/` | aws_s3_credential |
| `ext_silver` | `s3://lake-northwind/silver/` | aws_s3_credential |
| `ext_gold` | `s3://lake-northwind/gold/` | aws_s3_credential |
| `ext_ops` | `s3://lake-northwind/ops/` | aws_s3_credential |

### 作成SQL例

```sql
-- External Location の作成
CREATE EXTERNAL LOCATION ext_bronze
  URL 's3://lake-northwind/bronze/'
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
| カタログ作成 | UIまたはSQLで作成（環境に応じて選択） |
| External Location | **SQLで作成可能** |
| スキーマ作成 | **SQLで作成可能** |

---

## 変更履歴

| 日付 | 変更内容 |
|------|----------|
| 2026-03-08 | シングルクラウド版として作成（Azure Managed Identity → AWS IAM Role、ADLS → S3） |
