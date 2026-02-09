# Databricks notebook source
# MAGIC %md
# MAGIC # 00. Unity Catalog セットアップ (Azure ADLS Gen2)
# MAGIC 
# MAGIC このノートブックでは以下を設定します：
# MAGIC 1. Storage Credential（Access Connector経由でADLSアクセス）
# MAGIC 2. External Location（ADLS Gen2 コンテナ）
# MAGIC 3. Catalog / Schema 作成
# MAGIC 
# MAGIC **前提条件**:
# MAGIC - Azure ADLS Gen2 ストレージアカウント作成済み
# MAGIC - Access Connector 作成済み
# MAGIC - Access Connector (Managed Identity) に `Storage Blob Data Contributor` 権限付与済み

# COMMAND ----------

# 設定値（Azureリソース構築結果を入力）
STORAGE_ACCOUNT_NAME = "lakenorthwindharu"  # 作成したストレージアカウント名
ACCESS_CONNECTOR_ID = "/subscriptions/5b579d74-3de4-469b-8f70-b2acb7b2f369/resourceGroups/rg-northwind-datalake/providers/Microsoft.Databricks/accessConnectors/adb-access-connector-northwind" # Access ConnectorのリソースID

# 固定値
STORAGE_CREDENTIAL_NAME = "azure_adls_credential"
CATALOG_NAME = "northwind_catalog"

# ADLSパス (abfss形式)
ADLS_ROOT_PATH = f"abfss://bronze@{STORAGE_ACCOUNT_NAME}.dfs.core.windows.net/"

print(f"✅ 設定値")
print(f"   Storage Account: {STORAGE_ACCOUNT_NAME}")
print(f"   Access Connector ID: {ACCESS_CONNECTOR_ID}")
print(f"   Root Path: {ADLS_ROOT_PATH}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Storage Credential 作成
# MAGIC 
# MAGIC **重要**: 以下のSQLを実行する前に、**Databricks UI** でStorage Credentialを作成するか、以下のSQLを実行してください。
# MAGIC ※Databricks on AzureではSQLで作成可能です。

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Storage Credentialを作成
# MAGIC -- 注意: 既存の場合は一度削除するか、SKIPしてください
# MAGIC -- DROP STORAGE CREDENTIAL IF EXISTS azure_adls_credential;
# MAGIC 
# MAGIC CREATE STORAGE CREDENTIAL IF NOT EXISTS azure_adls_credential
# MAGIC WITH (
# MAGIC   AZURE_MANAGED_IDENTITY_ACCESS_CONNECTOR_ID = '/subscriptions/5b579d74-3de4-469b-8f70-b2acb7b2f369/resourceGroups/rg-northwind-datalake/providers/Microsoft.Databricks/accessConnectors/adb-access-connector-northwind'
# MAGIC );

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: External Location 作成
# MAGIC 
# MAGIC 各コンテナ（bronze, silver, gold）に対してExternal Locationを作成します。
# MAGIC ※ここではルートとして `bronze` コンテナを例に作成しますが、本来はコンテナごとに作成するか、共通のルートパスを指定します。
# MAGIC 今回はシンプルに `bronze` コンテナを `ext_bronze` として定義し、他の層も同様に定義します。

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Bronze用
# MAGIC CREATE EXTERNAL LOCATION IF NOT EXISTS ext_bronze
# MAGIC URL 'abfss://bronze@lakenorthwindharu.dfs.core.windows.net/'
# MAGIC WITH (STORAGE CREDENTIAL azure_adls_credential)
# MAGIC COMMENT 'Bronze Layer';
# MAGIC 
# MAGIC -- Silver用
# MAGIC CREATE EXTERNAL LOCATION IF NOT EXISTS ext_silver
# MAGIC URL 'abfss://silver@lakenorthwindharu.dfs.core.windows.net/'
# MAGIC WITH (STORAGE CREDENTIAL azure_adls_credential)
# MAGIC COMMENT 'Silver Layer';
# MAGIC 
# MAGIC -- Gold用
# MAGIC CREATE EXTERNAL LOCATION IF NOT EXISTS ext_gold
# MAGIC URL 'abfss://gold@lakenorthwindharu.dfs.core.windows.net/'
# MAGIC WITH (STORAGE CREDENTIAL azure_adls_credential)
# MAGIC COMMENT 'Gold Layer';

# COMMAND ----------

# MAGIC %sql
# MAGIC -- 確認
# MAGIC SHOW EXTERNAL LOCATIONS;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Catalog 作成
# MAGIC 
# MAGIC `northwind_catalog` を作成します。

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE CATALOG IF NOT EXISTS northwind_catalog
# MAGIC MANAGED LOCATION 'abfss://bronze@lakenorthwindharu.dfs.core.windows.net/managed'
# MAGIC COMMENT 'Northwind Data Lake Catalog';

# COMMAND ----------

# MAGIC %sql
# MAGIC USE CATALOG northwind_catalog;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Schema 作成
# MAGIC 
# MAGIC Bronze, Silver, Gold のスキーマを作成します。
# MAGIC 各スキーマの `MANAGED LOCATION` は、それぞれのADLSコンテナを指定します。

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Bronze
# MAGIC CREATE SCHEMA IF NOT EXISTS bronze
# MAGIC MANAGED LOCATION 'abfss://bronze@lakenorthwindharu.dfs.core.windows.net/managed_schema'
# MAGIC COMMENT 'Raw data';
# MAGIC 
# MAGIC -- Silver
# MAGIC CREATE SCHEMA IF NOT EXISTS silver
# MAGIC MANAGED LOCATION 'abfss://silver@lakenorthwindharu.dfs.core.windows.net/managed_schema'
# MAGIC COMMENT 'Cleaned data';
# MAGIC 
# MAGIC -- Gold
# MAGIC CREATE SCHEMA IF NOT EXISTS gold
# MAGIC MANAGED LOCATION 'abfss://gold@lakenorthwindharu.dfs.core.windows.net/managed_schema'
# MAGIC COMMENT 'Aggregated data';

# COMMAND ----------

# MAGIC %sql
# MAGIC -- 確認
# MAGIC SHOW SCHEMAS IN northwind_catalog;

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ セットアップ完了
# MAGIC 
# MAGIC 以下が作成されていることを確認してください：
# MAGIC 1. Storage Credential: `azure_adls_credential`
# MAGIC 2. External Locations: `ext_bronze`, `ext_silver`, `ext_gold`
# MAGIC 3. Catalog: `northwind_catalog`
# MAGIC 4. Schemas: `bronze`, `silver`, `gold`