# Databricks notebook source
# MAGIC %md
# MAGIC # 02. Bronze層 取り込み（AWSシングルクラウド版）
# MAGIC
# MAGIC RDS PostgreSQL (Northwind) から全テーブルを読み込み、
# MAGIC S3上のBronze層（Delta Lake）にAppendします。
# MAGIC
# MAGIC **データソース**: [pthom/northwind_psql](https://github.com/pthom/northwind_psql)（全14テーブル）

# COMMAND ----------

import uuid
from datetime import date, datetime

# 設定
CATALOG_NAME = "northwind_catalog"
SCHEMA_NAME = "bronze"

# ジョブ実行メタデータ
run_id = str(uuid.uuid4())
load_date = date.today()
ingest_ts = datetime.now()

print(f"✅ Bronze Ingest 開始")
print(f"   run_id: {run_id}")
print(f"   load_date: {load_date}")
print(f"   Catalog: {CATALOG_NAME}.{SCHEMA_NAME}")

# COMMAND ----------

# 接続情報（Secrets経由）
DB_HOST = dbutils.secrets.get(scope="northwind-secrets", key="rds-host")
DB_USER = dbutils.secrets.get(scope="northwind-secrets", key="rds-user")
DB_PASSWORD = dbutils.secrets.get(scope="northwind-secrets", key="rds-password")
DB_NAME = "northwind"
DB_PORT = 5432

jdbc_url = f"jdbc:postgresql://{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
connection_properties = {
    "user": DB_USER,
    "password": DB_PASSWORD,
    "driver": "org.postgresql.Driver"
}

# COMMAND ----------

# MAGIC %md
# MAGIC ## 全テーブルをBronze層に取り込み

# COMMAND ----------

from pyspark.sql.functions import lit, current_timestamp

# 取り込み対象テーブル（全14テーブル）
source_tables = [
    "categories",
    "customers",
    "employees",
    "suppliers",
    "shippers",
    "products",
    "orders",
    "order_details",
    "region",
    "territories",
    "us_states",
    "employee_territories",
    "customer_demographics",
    "customer_customer_demo"
]

# 取り込み実行
results = []
for table_name in source_tables:
    try:
        start_time = datetime.now()

        # RDSからデータ読み込み
        df = spark.read.jdbc(
            url=jdbc_url,
            table=table_name,
            properties=connection_properties
        )

        # メタデータカラム追加
        df_with_meta = df \
            .withColumn("_run_id", lit(run_id)) \
            .withColumn("_load_date", lit(str(load_date))) \
            .withColumn("_ingest_ts", current_timestamp()) \
            .withColumn("_source_system", lit("rds_northwind"))

        # Bronze層に保存（当日分のみ上書き → 冪等）
        bronze_table = f"{CATALOG_NAME}.{SCHEMA_NAME}.{table_name}"
        df_with_meta.write \
            .format("delta") \
            .mode("overwrite") \
            .option("replaceWhere", f"_load_date = '{load_date}'") \
            .saveAsTable(bronze_table)

        row_count = df.count()
        duration = (datetime.now() - start_time).total_seconds()
        results.append({"table": table_name, "rows": row_count, "duration": duration, "status": "✅"})
        print(f"  ✅ {table_name}: {row_count} 件 ({duration:.1f}秒)")

    except Exception as e:
        results.append({"table": table_name, "rows": 0, "duration": 0, "status": "❌"})
        print(f"  ❌ {table_name}: {str(e)[:100]}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Ingestion Log 記録

# COMMAND ----------

from pyspark.sql import Row

# ログテーブルに記録
log_rows = [
    Row(
        run_id=run_id,
        table_name=r["table"],
        row_count=r["rows"],
        duration_sec=r["duration"],
        load_date=str(load_date),
        status=r["status"]
    )
    for r in results
]

log_df = spark.createDataFrame(log_rows)
log_df.write \
    .format("delta") \
    .mode("append") \
    .saveAsTable(f"{CATALOG_NAME}.ops.ingestion_log")

print(f"✅ Ingestion Log 記録完了: {len(results)} テーブル")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 取り込み結果サマリ

# COMMAND ----------

print(f"\n{'='*50}")
print(f"Bronze Ingest 完了サマリ")
print(f"{'='*50}")
print(f"run_id: {run_id}")
print(f"load_date: {load_date}")
total_rows = sum(r["rows"] for r in results)
success_count = sum(1 for r in results if r["status"] == "✅")
print(f"成功: {success_count}/{len(results)} テーブル")
print(f"合計: {total_rows} 件")
print(f"{'='*50}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ 完了チェックリスト
# MAGIC
# MAGIC - [ ] 全14テーブルが Bronze 層に取り込まれた
# MAGIC - [ ] メタデータカラム（_run_id, _load_date, _ingest_ts, _source_system）が付与されている
# MAGIC - [ ] Ingestion Log が ops.ingestion_log に記録された
# MAGIC
# MAGIC **次のステップ**: `03_etl_silver_transform.py`
