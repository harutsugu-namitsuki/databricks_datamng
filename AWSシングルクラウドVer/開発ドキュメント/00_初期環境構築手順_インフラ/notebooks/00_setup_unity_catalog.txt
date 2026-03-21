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
# MAGIC - **Notebook上部の入力欄に S3 バケット名を入力**
# MAGIC
# MAGIC **クラスター**: 「専用（Single User）」モードで作成してください。

# COMMAND ----------

# 設定値（Notebook上部の入力欄から設定）
dbutils.widgets.text("s3_bucket_name", "", "S3 Bucket Name")
dbutils.widgets.text("storage_credential", "aws_s3_credential", "Storage Credential Name")
dbutils.widgets.text("catalog_name", "northwind_catalog", "Catalog Name")

S3_BUCKET_NAME = dbutils.widgets.get("s3_bucket_name")
STORAGE_CREDENTIAL_NAME = dbutils.widgets.get("storage_credential")
CATALOG_NAME = dbutils.widgets.get("catalog_name")

if not S3_BUCKET_NAME or "<" in S3_BUCKET_NAME:
    raise ValueError(
        "❌ S3_BUCKET_NAME が未設定です。\n"
        "Notebook上部の入力欄にバケット名を入力してください。\n"
        "確認: aws cloudformation describe-stacks "
        "--stack-name northwind-lakehouse "
        "--query \"Stacks[0].Outputs[?OutputKey=='S3BucketName'].OutputValue\""
    )

print(f"✅ 設定値")
print(f"   S3 Bucket: {S3_BUCKET_NAME}")
print(f"   Storage Credential: {STORAGE_CREDENTIAL_NAME}")
print(f"   Catalog: {CATALOG_NAME}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: 前提条件チェック

# COMMAND ----------

# Storage Credential 確認
creds = spark.sql("SHOW STORAGE CREDENTIALS").collect()
cred_names = [row["name"] for row in creds]
assert STORAGE_CREDENTIAL_NAME in cred_names, \
    f"❌ Storage Credential '{STORAGE_CREDENTIAL_NAME}' が見つかりません"
print(f"✅ Storage Credential '{STORAGE_CREDENTIAL_NAME}' 確認済み")

# COMMAND ----------

# カタログ確認
catalogs = spark.sql("SHOW CATALOGS").collect()
catalog_names = [row["catalog"] for row in catalogs]
assert CATALOG_NAME in catalog_names, \
    f"❌ カタログ '{CATALOG_NAME}' が見つかりません"
print(f"✅ カタログ '{CATALOG_NAME}' 確認済み")

# COMMAND ----------

# カタログ切り替え（Python セルで実行することで spark.sql() と共有される）
spark.sql(f"USE CATALOG {CATALOG_NAME}")

current = spark.sql("SELECT current_catalog()").collect()[0][0]
assert current == CATALOG_NAME, f"❌ カタログ切り替え失敗: {current}"
print(f"✅ current_catalog() = {current}")

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

# External Location 確認
spark.sql("SHOW EXTERNAL LOCATIONS").show(truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Schema 作成
# MAGIC
# MAGIC 各レイヤーの管理場所（MANAGED LOCATION）をそれぞれのパス（S3）に明示的に指定してスキーマを作成します。

# COMMAND ----------

schemas = [
    ("bronze", "Raw data from source systems"),
    ("silver", "Cleansed and standardized data"),
    ("gold",   "Aggregated business-ready data"),
    ("ops",    "Operational logs, DQ results"),
]

for schema_name, comment in schemas:
    spark.sql(f"""
    CREATE SCHEMA IF NOT EXISTS {CATALOG_NAME}.{schema_name}
    MANAGED LOCATION 's3://{S3_BUCKET_NAME}/{schema_name}/'
    COMMENT '{comment}'
    """)
    print(f"✅ {CATALOG_NAME}.{schema_name} 作成完了")

# COMMAND ----------

# 最終確認
spark.sql(f"SHOW SCHEMAS IN {CATALOG_NAME}").show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ セットアップ完了
# MAGIC
# MAGIC | 項目 | 確認方法 | 状態 |
# MAGIC |------|---------|------|
# MAGIC | Storage Credential | Step 1 で確認済み | ✅ |
# MAGIC | カタログ | Step 1 で確認済み | ✅ |
# MAGIC | External Locations | Step 2 で `ext_bronze`, `ext_silver`, `ext_gold`, `ext_ops` が表示 | ✅ |
# MAGIC | Schemas | Step 3 で `bronze`, `silver`, `gold`, `ops` が表示 | ✅ |
# MAGIC
# MAGIC **次のステップ**: `01_load_northwind_to_rds.py` → `02_etl_bronze_ingest.py`
