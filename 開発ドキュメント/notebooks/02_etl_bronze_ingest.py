# Databricks notebook source
# MAGIC %md
# MAGIC # 02. ETL Bronze層：RDS → ADLS Gen2取り込み
# MAGIC 
# MAGIC このノートブックでは、RDS PostgreSQLからデータを抽出し、Bronze層（ADLS Gen2）に保存します。
# MAGIC 
# MAGIC **処理内容**:
# MAGIC - RDSからJDBC経由でデータ取得
# MAGIC - メタデータ付与（`_load_date`, `_source_system`）
# MAGIC - Bronze層にDelta形式で保存
# MAGIC - Unity Catalogにテーブル登録
# MAGIC 
# MAGIC **前提条件**:
# MAGIC - `00_setup_unity_catalog.py` が実行済みであること
# MAGIC - `01_load_northwind_to_rds.py` でRDSデータが準備されていること

# COMMAND ----------

# MAGIC %md
# MAGIC ## ⚠️ 設定値を入力してください

# COMMAND ----------

# ============================================
# 👇 ここに実際の値を入力してください 👇
# ============================================

# RDS接続情報（Secretsから取得することを推奨しますが、簡略化のため直接書く場合は注意）
# ※本番環境では必ず dbutils.secrets.get() を使用してください
DB_HOST = "premigration-northwind-db.cb0as2s6sr83.ap-southeast-2.rds.amazonaws.com"  # RDSEndpoint
DB_USER = "dbadmin"
DB_PASSWORD = "Yi2345678"
DB_NAME = "northwind"
DB_PORT = 5432

# Unity Catalog設定
CATALOG = "northwind_catalog" # ADLS用に変更
BRONZE_SCHEMA = "bronze"

# 処理対象テーブル
SOURCE_TABLES = [
    "categories",
    "suppliers", 
    "customers",
    "employees",
    "products",
    "orders",
    "order_details",
    "shippers" # 追加
]

print(f"✅ 設定値")
print(f"   DB Host: {DB_HOST}")
print(f"   Catalog: {CATALOG}.{BRONZE_SCHEMA}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## JDBC接続設定

# COMMAND ----------

# JDBC URL構築
jdbc_url = f"jdbc:postgresql://{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"

connection_properties = {
    "user": DB_USER,
    "password": DB_PASSWORD,
    "driver": "org.postgresql.Driver"
}

print(f"✅ JDBC接続準備完了: {DB_HOST}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Catalogの使用設定

# COMMAND ----------

# カタログ・スキーマの存在確認と作成は 00_setup_unity_catalog.py で行われている前提

spark.sql(f"USE CATALOG {CATALOG}")
spark.sql(f"USE SCHEMA {BRONZE_SCHEMA}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Bronze層へのデータ取り込み関数

# COMMAND ----------

# 必要なライブラリのインポート
from datetime import datetime
from pyspark.sql.functions import lit, current_timestamp

def ingest_to_bronze(table_name: str):
    """
    RDSからテーブルを読み込み、Bronze層に保存する
    
    Args:
        table_name: ソーステーブル名
    """
    print(f"📥 Processing: {table_name}")
    
    # RDSからデータ読み込み
    try:
        df = spark.read.jdbc(
            url=jdbc_url,
            table=table_name,
            properties=connection_properties
        )
    except Exception as e:
        print(f"❌ Error reading from RDS table {table_name}: {e}")
        raise e
    
    # メタデータ付与
    df_with_meta = df \
        .withColumn("_load_date", lit(datetime.now().strftime("%Y-%m-%d"))) \
        .withColumn("_load_timestamp", current_timestamp()) \
        .withColumn("_source_system", lit("rds_northwind"))
    
    # Bronze層に保存（Delta形式、Overwrite）
    # ※BronzeはRawデータのスナップショットあるいはAppendとするケースが多いが、
    # 学習用のためシンプルにOverwrite（洗い替え）とする
    target_table = f"{CATALOG}.{BRONZE_SCHEMA}.{table_name}"
    
    df_with_meta.write \
        .format("delta") \
        .mode("overwrite") \
        .option("mergeSchema", "true") \
        .saveAsTable(target_table)
    
    record_count = df_with_meta.count()
    print(f"✅ Completed: {target_table} ({record_count} records)")
    
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
# MAGIC -- 変数がSQLセルで直接使えないため、Python変数を一時ビューなどに渡すか、ハードコードで確認
# MAGIC -- ここでは SHOW TABLES を実行
# MAGIC SHOW TABLES IN northwind_catalog.bronze;

# COMMAND ----------

# サンプルデータ確認（orders）
# MAGIC %sql
# MAGIC SELECT * FROM northwind_catalog.bronze.orders LIMIT 5;

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ 完了チェックリスト
# MAGIC 
# MAGIC - [ ] 全テーブルがBronze層に取り込まれた
# MAGIC - [ ] メタデータ（`_load_date`, `_source_system`）が付与されている
# MAGIC - [ ] Unity Catalog (`northwind_catalog.bronze.*`) に登録されている
# MAGIC 
# MAGIC 次のステップ: `03_etl_silver_transform.py` でSilver層への変換を実行します
