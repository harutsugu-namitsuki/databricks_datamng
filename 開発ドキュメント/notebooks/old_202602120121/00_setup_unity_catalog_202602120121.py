# Databricks notebook source
# MAGIC %md
# MAGIC # 00. Unity Catalog セットアップ (Azure ADLS Gen2)
# MAGIC 
# MAGIC このノートブックでは以下を設定します：
# MAGIC 1. Storage Credential → **既存の `dbx_northwind_ws` を使用**（UI作成済み）
# MAGIC 2. External Location（ADLS Gen2 コンテナ）
# MAGIC 3. Catalog / Schema 作成（メタストアデフォルトストレージ使用）
# MAGIC 
# MAGIC **前提条件**:
# MAGIC - Azure ADLS Gen2 ストレージアカウント作成済み
# MAGIC - Access Connector 作成済み（Managed Identity）
# MAGIC - Storage Credential `dbx_northwind_ws` がUI上で作成済み

# COMMAND ----------

# 設定値
STORAGE_ACCOUNT_NAME = "lakenorthwindharu"
STORAGE_CREDENTIAL_NAME = "dbx_northwind_ws"  # 既存の資格情報を使用
CATALOG_NAME = "northwind_catalog"

print(f"✅ 設定値")
print(f"   Storage Account: {STORAGE_ACCOUNT_NAME}")
print(f"   Storage Credential: {STORAGE_CREDENTIAL_NAME}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Storage Credential 確認
# MAGIC 
# MAGIC **※ 既にUIで `dbx_northwind_ws` が作成済みのため、作成は不要です。**

# COMMAND ----------

# MAGIC %sql
# MAGIC SHOW STORAGE CREDENTIALS;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: External Location 作成
# MAGIC 
# MAGIC 各コンテナ（bronze, silver, gold）に対してExternal Locationを作成します。

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE EXTERNAL LOCATION IF NOT EXISTS ext_bronze
# MAGIC URL 'abfss://bronze@lakenorthwindharu.dfs.core.windows.net/'
# MAGIC WITH (STORAGE CREDENTIAL dbx_northwind_ws)
# MAGIC COMMENT 'Bronze Layer - Raw Data';

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE EXTERNAL LOCATION IF NOT EXISTS ext_silver
# MAGIC URL 'abfss://silver@lakenorthwindharu.dfs.core.windows.net/'
# MAGIC WITH (STORAGE CREDENTIAL dbx_northwind_ws)
# MAGIC COMMENT 'Silver Layer - Cleaned Data';

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE EXTERNAL LOCATION IF NOT EXISTS ext_gold
# MAGIC URL 'abfss://gold@lakenorthwindharu.dfs.core.windows.net/'
# MAGIC WITH (STORAGE CREDENTIAL dbx_northwind_ws)
# MAGIC COMMENT 'Gold Layer - Aggregated Data';

# COMMAND ----------

# MAGIC %sql
# MAGIC -- 確認
# MAGIC SHOW EXTERNAL LOCATIONS;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Catalog 作成
# MAGIC 
# MAGIC **注意**: MANAGED LOCATION は指定しません。
# MAGIC マネージドテーブルはメタストアのデフォルトストレージに保存されます。
# MAGIC 外部データへのアクセスは External Location 経由で行います。

# COMMAND ----------

# MAGIC %sql
# MAGIC DROP CATALOG IF EXISTS northwind_catalog CASCADE;

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE CATALOG IF NOT EXISTS northwind_catalog
# MAGIC COMMENT 'Northwind Data Lake Catalog';

# COMMAND ----------

# MAGIC %sql
# MAGIC USE CATALOG northwind_catalog;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Schema 作成

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
# MAGIC -- 確認
# MAGIC SHOW SCHEMAS IN northwind_catalog;

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ セットアップ完了チェック
# MAGIC 
# MAGIC 1. Storage Credential: `dbx_northwind_ws`（既存・UI作成済み）
# MAGIC 2. External Locations: `ext_bronze`, `ext_silver`, `ext_gold`
# MAGIC 3. Catalog: `northwind_catalog`（メタストアデフォルトストレージ使用）
# MAGIC 4. Schemas: `bronze`, `silver`, `gold`
# MAGIC 
# MAGIC 次のステップ: `01_load_northwind_to_rds.py` → `02_etl_bronze_ingest.py`