# Databricks notebook source
# MAGIC %md
# MAGIC # 00. Unity Catalog セットアップ
# MAGIC 
# MAGIC このノートブックでは以下を設定します：
# MAGIC 1. Storage Credential（IAM Role経由でS3アクセス）
# MAGIC 2. External Location（S3バケット）
# MAGIC 3. Catalog / Schema 作成

# COMMAND ----------

# MAGIC %md
# MAGIC ## 前提条件
# MAGIC - AWS CloudFormation スタックがデプロイ済み（IAM Role作成済み）
# MAGIC - Unity Catalog のメタストアがワークスペースに紐づけ済み
# MAGIC - Account Admin または Metastore Admin 権限が必要

# COMMAND ----------

# 設定値（CloudFormation出力から取得）
AWS_ACCOUNT_ID = "312871631496"  # あなたのAWSアカウントID
S3_BUCKET_NAME = f"lake-northwind-{AWS_ACCOUNT_ID}"
IAM_ROLE_ARN = f"arn:aws:iam::{AWS_ACCOUNT_ID}:role/premigration-databricks-unity-role"
STORAGE_CREDENTIAL_NAME = "aws_s3_credential"
EXTERNAL_LOCATION_NAME = "northwind_datalake"
CATALOG_NAME = "northwind"

print(f"✅ 設定値")
print(f"   S3バケット: {S3_BUCKET_NAME}")
print(f"   IAM Role ARN: {IAM_ROLE_ARN}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Storage Credential 作成
# MAGIC 
# MAGIC **⚠️ 注意**: このステップは **Databricks UI** で実行してください
# MAGIC 
# MAGIC **手順**:
# MAGIC 1. Databricks UI左メニュー → **Catalog** をクリック
# MAGIC 2. 右上の **⚙️ (歯車)** → **資格情報** を選択
# MAGIC 3. **資格情報を作成** をクリック
# MAGIC 4. 以下を入力:
# MAGIC    - **資格情報のタイプ**: `AWS IAMロール` を選択
# MAGIC    - **Name**: `aws_s3_credential`
# MAGIC    - **IAMロール (ARN)**: 上のセルで表示された `IAM_ROLE_ARN` の値を入力
# MAGIC 5. **作成** をクリック
# MAGIC 
# MAGIC > **📝 ARNの例**: `arn:aws:iam::312871631496:role/premigration-databricks-unity-role`

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: External Location 作成
# MAGIC 
# MAGIC Storage Credential作成後、以下のSQLを実行してください

# COMMAND ----------

# MAGIC %sql
# MAGIC -- External Location を作成
# MAGIC CREATE EXTERNAL LOCATION IF NOT EXISTS northwind_datalake
# MAGIC URL 's3://lake-northwind-312871631496/'
# MAGIC WITH (STORAGE CREDENTIAL aws_s3_credential)
# MAGIC COMMENT 'Northwind Data Lake on AWS S3';

# COMMAND ----------

# MAGIC %sql
# MAGIC -- External Location の確認
# MAGIC SHOW EXTERNAL LOCATIONS;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Catalog 作成

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Northwind用のCatalogを作成
# MAGIC CREATE CATALOG IF NOT EXISTS northwind
# MAGIC COMMENT 'Northwind sample data catalog';

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Catalogを使用
# MAGIC USE CATALOG northwind;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Schema（Database）作成
# MAGIC 
# MAGIC Medallion Architectureに基づいてスキーマを作成します

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Bronze: 生データ層
# MAGIC CREATE SCHEMA IF NOT EXISTS bronze
# MAGIC MANAGED LOCATION 's3://lake-northwind-312871631496/bronze/'
# MAGIC COMMENT 'Raw data from source systems';

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Silver: クレンジング済みデータ層
# MAGIC CREATE SCHEMA IF NOT EXISTS silver
# MAGIC MANAGED LOCATION 's3://lake-northwind-312871631496/silver/'
# MAGIC COMMENT 'Cleansed and standardized data';

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Gold: 集計・分析用データ層
# MAGIC CREATE SCHEMA IF NOT EXISTS gold
# MAGIC MANAGED LOCATION 's3://lake-northwind-312871631496/gold/'
# MAGIC COMMENT 'Aggregated and business-ready data';

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Ops: 運用ログ・品質データ層
# MAGIC CREATE SCHEMA IF NOT EXISTS ops
# MAGIC MANAGED LOCATION 's3://lake-northwind-312871631496/ops/'
# MAGIC COMMENT 'Operational logs and data quality results';

# COMMAND ----------

# MAGIC %sql
# MAGIC -- 作成したSchemaの確認
# MAGIC SHOW SCHEMAS IN northwind;

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ セットアップ完了チェックリスト
# MAGIC 
# MAGIC 以下が全て完了していることを確認してください：
# MAGIC 
# MAGIC - [ ] Storage Credential `aws_s3_credential` が作成された（IAM Role ARN使用）
# MAGIC - [ ] External Location `northwind_datalake` が作成された
# MAGIC - [ ] Catalog `northwind` が作成された
# MAGIC - [ ] Schema `bronze`, `silver`, `gold`, `ops` が作成された
# MAGIC 
# MAGIC 次のステップ: `01_load_northwind_to_rds.py` でNorthwindデータをRDSに投入します