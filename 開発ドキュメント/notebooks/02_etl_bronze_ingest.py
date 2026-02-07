# Databricks notebook source
# MAGIC %md
# MAGIC # 02. ETL Bronze層：RDS → S3 Delta取り込み
# MAGIC 
# MAGIC このノートブックでは、RDS PostgreSQLからデータを抽出し、Bronze層（S3 Delta）に保存します。
# MAGIC 
# MAGIC **処理内容**:
# MAGIC - RDSからJDBC経由でデータ取得
# MAGIC - メタデータ付与（`_load_date`, `_source_system`）
# MAGIC - Bronze層にDelta形式で保存
# MAGIC - Unity Catalogにテーブル登録

# COMMAND ----------

# MAGIC %md
# MAGIC ## 設定値

# COMMAND ----------

from datetime import datetime
from pyspark.sql.functions import lit, current_timestamp

# Secrets設定
SECRET_SCOPE = "aws-credentials"
DB_HOST_SECRET = "rds-host"
DB_USER_SECRET = "rds-username"
DB_PASSWORD_SECRET = "rds-password"

# データベース設定
DB_NAME = "northwind"
DB_PORT = 5432

# Unity Catalog設定
CATALOG = "northwind"
BRONZE_SCHEMA = "bronze"

# 処理対象テーブル
SOURCE_TABLES = [
    "categories",
    "suppliers", 
    "customers",
    "employees",
    "products",
    "orders",
    "order_details"
]

# COMMAND ----------

# MAGIC %md
# MAGIC ## JDBC接続設定

# COMMAND ----------

# Secretsから認証情報を取得
db_host = dbutils.secrets.get(scope=SECRET_SCOPE, key=DB_HOST_SECRET)
db_user = dbutils.secrets.get(scope=SECRET_SCOPE, key=DB_USER_SECRET)
db_password = dbutils.secrets.get(scope=SECRET_SCOPE, key=DB_PASSWORD_SECRET)

# JDBC URL構築
jdbc_url = f"jdbc:postgresql://{db_host}:{DB_PORT}/{DB_NAME}?sslmode=require"

connection_properties = {
    "user": db_user,
    "password": db_password,
    "driver": "org.postgresql.Driver"
}

print(f"✅ JDBC接続準備完了: {db_host}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Catalogの使用設定

# COMMAND ----------

# MAGIC %sql
# MAGIC USE CATALOG northwind;
# MAGIC USE SCHEMA bronze;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Bronze層へのデータ取り込み

# COMMAND ----------

def ingest_to_bronze(table_name: str):
    """
    RDSからテーブルを読み込み、Bronze層に保存する
    
    Args:
        table_name: ソーステーブル名
    """
    print(f"📥 Processing: {table_name}")
    
    # RDSからデータ読み込み
    df = spark.read.jdbc(
        url=jdbc_url,
        table=table_name,
        properties=connection_properties
    )
    
    # メタデータ付与
    df_with_meta = df \
        .withColumn("_load_date", lit(datetime.now().strftime("%Y-%m-%d"))) \
        .withColumn("_load_timestamp", current_timestamp()) \
        .withColumn("_source_system", lit("rds_northwind"))
    
    # Bronze層に保存（Delta形式、Append）
    bronze_table = f"{CATALOG}.{BRONZE_SCHEMA}.{table_name}"
    
    df_with_meta.write \
        .format("delta") \
        .mode("overwrite") \
        .option("mergeSchema", "true") \
        .saveAsTable(bronze_table)
    
    record_count = df_with_meta.count()
    print(f"✅ Completed: {table_name} ({record_count} records)")
    
    return record_count

# COMMAND ----------

# MAGIC %md
# MAGIC ## 全テーブル取り込み実行

# COMMAND ----------

# 取り込み結果を記録
ingestion_results = []

for table in SOURCE_TABLES:
    try:
        count = ingest_to_bronze(table)
        ingestion_results.append({
            "table": table,
            "status": "success",
            "record_count": count
        })
    except Exception as e:
        print(f"❌ Error processing {table}: {str(e)}")
        ingestion_results.append({
            "table": table,
            "status": "failed",
            "error": str(e)
        })

# COMMAND ----------

# MAGIC %md
# MAGIC ## 取り込み結果サマリ

# COMMAND ----------

# 結果をDataFrameで表示
results_df = spark.createDataFrame(ingestion_results)
display(results_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Bronze層テーブル確認

# COMMAND ----------

# MAGIC %sql
# MAGIC SHOW TABLES IN northwind.bronze;

# COMMAND ----------

# サンプルデータ確認（orders）
# MAGIC %sql
# MAGIC SELECT * FROM northwind.bronze.orders LIMIT 5;

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ 完了チェックリスト
# MAGIC 
# MAGIC - [ ] 全テーブルがBronze層に取り込まれた
# MAGIC - [ ] メタデータ（`_load_date`, `_source_system`）が付与されている
# MAGIC - [ ] Unity Catalogに登録されている
# MAGIC 
# MAGIC 次のステップ: `03_etl_silver_transform.py` でSilver層への変換を実行します
