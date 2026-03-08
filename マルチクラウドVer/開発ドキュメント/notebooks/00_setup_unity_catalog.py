# Databricks notebook source
# MAGIC %md
# MAGIC # 00. Unity Catalog セットアップ確認 + External Location / Schema 作成
# MAGIC 
# MAGIC このノートブックでは以下を行います：
# MAGIC 1. **前提条件の確認**（Storage Credential、カタログの存在チェック）
# MAGIC 2. **External Location 作成**（ADLS Gen2 コンテナへのアクセスパス）
# MAGIC 3. **Schema 作成**（bronze / silver / gold）
# MAGIC 
# MAGIC ## ⚠️ 事前にUI操作が必要です
# MAGIC 
# MAGIC このNotebookを実行する**前**に、`azure-adls-setup-guide.md` の **Phase 1〜3** を完了してください：
# MAGIC - Phase 1: Azure リソース構築（ストレージアカウント、コンテナ）
# MAGIC - Phase 2: IAM 権限設定（Access Connector へのロール割り当て）
# MAGIC - Phase 3: Databricks UI 操作（カタログ作成）
# MAGIC 
# MAGIC **クラスター**: 「専用（旧: シングルユーザー）」モードで作成してください。

# COMMAND ----------

# 設定値（環境に合わせて変更してください）
STORAGE_ACCOUNT_NAME = "lakenorthwindharu"
STORAGE_CREDENTIAL_NAME = "dbx_northwind_ws"
CATALOG_NAME = "northwind_catalog"

print(f"✅ 設定値")
print(f"   Storage Account: {STORAGE_ACCOUNT_NAME}")
print(f"   Storage Credential: {STORAGE_CREDENTIAL_NAME}")
print(f"   Catalog: {CATALOG_NAME}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: 前提条件チェック
# MAGIC 
# MAGIC Storage Credential とカタログが存在するか確認します。
# MAGIC エラーが出る場合は `azure-adls-setup-guide.md` を確認してください。

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Storage Credential の一覧を確認
# MAGIC -- dbx_northwind_ws が表示されればOK
# MAGIC SHOW STORAGE CREDENTIALS;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- カタログの一覧を確認
# MAGIC -- northwind_catalog が表示されればOK（UIで作成済みのはず）
# MAGIC SHOW CATALOGS;

# COMMAND ----------

# MAGIC %sql
# MAGIC USE CATALOG northwind_catalog;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: External Location 作成
# MAGIC 
# MAGIC ADLS Gen2 の各コンテナに対してアクセスパスを登録します。
# MAGIC これにより、External Table として ADLS のデータを参照できるようになります。

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
# MAGIC -- External Location 確認
# MAGIC SHOW EXTERNAL LOCATIONS;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Schema 作成
# MAGIC 
# MAGIC カタログ内に bronze / silver / gold の3つのスキーマを作成します。

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
# MAGIC -- Schema 確認
# MAGIC SHOW SCHEMAS IN northwind_catalog;

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ セットアップ完了
# MAGIC 
# MAGIC 以下がすべて確認できれば成功です：
# MAGIC 
# MAGIC | 項目 | 確認方法 | 状態 |
# MAGIC |------|---------|------|
# MAGIC | Storage Credential | Step 1 で `dbx_northwind_ws` が表示 | ✅ |
# MAGIC | カタログ | Step 1 で `northwind_catalog` が表示 | ✅ |
# MAGIC | External Locations | Step 2 で `ext_bronze`, `ext_silver`, `ext_gold` が表示 | ✅ |
# MAGIC | Schemas | Step 3 で `bronze`, `silver`, `gold` が表示 | ✅ |
# MAGIC 
# MAGIC **次のステップ**: `01_load_northwind_to_rds.py` → `02_etl_bronze_ingest.py`