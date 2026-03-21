# Databricks notebook source
# MAGIC %md
# MAGIC # 00. Unity Catalog セットアップ（AWSシングルクラウド版）
# MAGIC
# MAGIC このノートブックでは以下を行います：
# MAGIC 1. **前提条件の確認**（Storage Credential、カタログの存在チェック）
# MAGIC 2. **External Location 作成**（S3 バケットへのアクセスパス）
# MAGIC 3. **Schema 作成**（bronze / silver / gold / ops）
# MAGIC
# MAGIC ## ⚠️ 事前にUI操作が必要です
# MAGIC
# MAGIC このNotebookを実行する**前**に、以下を完了してください：
# MAGIC - `環境構築手順書.md` の Step 1〜2（CloudFormation デプロイ、Databricks設定）
# MAGIC - Storage Credential を **Databricks UIから作成**
# MAGIC - カタログ `northwind_catalog` を作成
# MAGIC
# MAGIC **クラスター**: 「専用（Single User）」モードで作成してください。

# COMMAND ----------

# 設定値（環境に合わせて変更してください）
S3_BUCKET_NAME = "lake-northwind-<account-id>"  # CloudFormation Output: S3BucketName
STORAGE_CREDENTIAL_NAME = "aws_s3_credential"
CATALOG_NAME = "northwind_catalog"

print(f"✅ 設定値")
print(f"   S3 Bucket: {S3_BUCKET_NAME}")
print(f"   Storage Credential: {STORAGE_CREDENTIAL_NAME}")
print(f"   Catalog: {CATALOG_NAME}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: 前提条件チェック

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Storage Credential の一覧を確認
# MAGIC -- aws_s3_credential が表示されればOK
# MAGIC SHOW STORAGE CREDENTIALS;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- カタログの一覧を確認
# MAGIC -- northwind_catalog が表示されればOK
# MAGIC SHOW CATALOGS;

# COMMAND ----------

# MAGIC %sql
# MAGIC USE CATALOG northwind_catalog;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: External Location 作成
# MAGIC
# MAGIC S3 バケットの各レイヤーに対してアクセスパスを登録します。

# COMMAND ----------

spark.sql(f"""
CREATE EXTERNAL LOCATION IF NOT EXISTS ext_bronze
  URL 's3://{S3_BUCKET_NAME}/bronze/'
  WITH (STORAGE CREDENTIAL {STORAGE_CREDENTIAL_NAME})
  COMMENT 'Bronze Layer - Raw Data'
""")
print("✅ ext_bronze 作成完了")

# COMMAND ----------

spark.sql(f"""
CREATE EXTERNAL LOCATION IF NOT EXISTS ext_silver
  URL 's3://{S3_BUCKET_NAME}/silver/'
  WITH (STORAGE CREDENTIAL {STORAGE_CREDENTIAL_NAME})
  COMMENT 'Silver Layer - Cleaned Data'
""")
print("✅ ext_silver 作成完了")

# COMMAND ----------

spark.sql(f"""
CREATE EXTERNAL LOCATION IF NOT EXISTS ext_gold
  URL 's3://{S3_BUCKET_NAME}/gold/'
  WITH (STORAGE CREDENTIAL {STORAGE_CREDENTIAL_NAME})
  COMMENT 'Gold Layer - Aggregated Data'
""")
print("✅ ext_gold 作成完了")

# COMMAND ----------

spark.sql(f"""
CREATE EXTERNAL LOCATION IF NOT EXISTS ext_ops
  URL 's3://{S3_BUCKET_NAME}/ops/'
  WITH (STORAGE CREDENTIAL {STORAGE_CREDENTIAL_NAME})
  COMMENT 'Ops Layer - Logs and Quality'
""")
print("✅ ext_ops 作成完了")

# COMMAND ----------

# MAGIC %sql
# MAGIC -- External Location 確認
# MAGIC SHOW EXTERNAL LOCATIONS;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Schema 作成

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE SCHEMA IF NOT EXISTS bronze
# MAGIC COMMENT 'Raw data from source systems';

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE SCHEMA IF NOT EXISTS silver
# MAGIC COMMENT 'Cleansed and standardized data';

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE SCHEMA IF NOT EXISTS gold
# MAGIC COMMENT 'Aggregated business-ready data';

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE SCHEMA IF NOT EXISTS ops
# MAGIC COMMENT 'Operational logs, DQ results';

# COMMAND ----------

# MAGIC %sql
# MAGIC SHOW SCHEMAS IN northwind_catalog;

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ セットアップ完了
# MAGIC
# MAGIC | 項目 | 確認方法 | 状態 |
# MAGIC |------|---------|------|
# MAGIC | Storage Credential | Step 1 で `aws_s3_credential` が表示 | ✅ |
# MAGIC | カタログ | Step 1 で `northwind_catalog` が表示 | ✅ |
# MAGIC | External Locations | Step 2 で `ext_bronze`, `ext_silver`, `ext_gold`, `ext_ops` が表示 | ✅ |
# MAGIC | Schemas | Step 3 で `bronze`, `silver`, `gold`, `ops` が表示 | ✅ |
# MAGIC
# MAGIC **次のステップ**: `01_load_northwind_to_rds.py` → `02_etl_bronze_ingest.py`
