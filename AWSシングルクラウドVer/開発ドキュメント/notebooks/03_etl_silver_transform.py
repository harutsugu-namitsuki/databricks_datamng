# Databricks notebook source
# MAGIC %md
# MAGIC # 03. Silver層 変換（AWSシングルクラウド版）
# MAGIC
# MAGIC Bronze層のデータをクレンジング・標準化してSilver層に保存します。
# MAGIC
# MAGIC **処理内容**:
# MAGIC - Null処理、型変換
# MAGIC - 文字列トリム・標準化
# MAGIC - 品質チェック（DQ Check）

# COMMAND ----------

from pyspark.sql.functions import col, trim, upper, when, lit, current_timestamp
from datetime import date

CATALOG_NAME = "northwind_catalog"
load_date = date.today()

print(f"✅ Silver Transform 開始 (load_date: {load_date})")

# COMMAND ----------

spark.sql(f"USE CATALOG {CATALOG_NAME}")
print(f"✅ current_catalog() = {spark.sql('SELECT current_catalog()').collect()[0][0]}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Silver変換: Customers

# COMMAND ----------

df_customers = spark.table(f"{CATALOG_NAME}.bronze.customers") \
    .filter(col("_load_date") == str(load_date))

silver_customers = df_customers \
    .withColumn("company_name", trim(col("company_name"))) \
    .withColumn("contact_name", trim(col("contact_name"))) \
    .withColumn("country", trim(upper(col("country")))) \
    .withColumn("city", trim(col("city"))) \
    .withColumn("region", when(col("region").isNull(), lit("N/A")).otherwise(trim(col("region")))) \
    .withColumn("postal_code", when(col("postal_code").isNull(), lit("")).otherwise(trim(col("postal_code")))) \
    .drop("_run_id", "_load_date", "_ingest_ts", "_source_system")

silver_customers.write \
    .format("delta") \
    .mode("overwrite") \
    .saveAsTable(f"{CATALOG_NAME}.silver.customers")

print(f"✅ silver.customers: {silver_customers.count()} 件")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Silver変換: Orders

# COMMAND ----------

df_orders = spark.table(f"{CATALOG_NAME}.bronze.orders") \
    .filter(col("_load_date") == str(load_date))

silver_orders = df_orders \
    .withColumn("order_date", col("order_date").cast("date")) \
    .withColumn("required_date", col("required_date").cast("date")) \
    .withColumn("shipped_date", col("shipped_date").cast("date")) \
    .withColumn("freight", when(col("freight").isNull(), lit(0.0)).otherwise(col("freight"))) \
    .withColumn("ship_country", trim(upper(col("ship_country")))) \
    .drop("_run_id", "_load_date", "_ingest_ts", "_source_system")

silver_orders.write \
    .format("delta") \
    .mode("overwrite") \
    .saveAsTable(f"{CATALOG_NAME}.silver.orders")

print(f"✅ silver.orders: {silver_orders.count()} 件")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Silver変換: Order Details

# COMMAND ----------

df_order_details = spark.table(f"{CATALOG_NAME}.bronze.order_details") \
    .filter(col("_load_date") == str(load_date))

silver_order_details = df_order_details \
    .withColumn("unit_price", col("unit_price").cast("decimal(10,2)")) \
    .withColumn("discount", col("discount").cast("decimal(4,2)")) \
    .withColumn("line_total", (col("unit_price") * col("quantity") * (1 - col("discount"))).cast("decimal(10,2)")) \
    .drop("_run_id", "_load_date", "_ingest_ts", "_source_system")

silver_order_details.write \
    .format("delta") \
    .mode("overwrite") \
    .saveAsTable(f"{CATALOG_NAME}.silver.order_details")

print(f"✅ silver.order_details: {silver_order_details.count()} 件")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Silver変換: Products

# COMMAND ----------

df_products = spark.table(f"{CATALOG_NAME}.bronze.products") \
    .filter(col("_load_date") == str(load_date))

silver_products = df_products \
    .withColumn("product_name", trim(col("product_name"))) \
    .withColumn("unit_price", col("unit_price").cast("decimal(10,2)")) \
    .withColumn("units_in_stock", when(col("units_in_stock").isNull(), lit(0)).otherwise(col("units_in_stock"))) \
    .withColumn("units_on_order", when(col("units_on_order").isNull(), lit(0)).otherwise(col("units_on_order"))) \
    .withColumn("reorder_level", when(col("reorder_level").isNull(), lit(0)).otherwise(col("reorder_level"))) \
    .drop("_run_id", "_load_date", "_ingest_ts", "_source_system")

silver_products.write \
    .format("delta") \
    .mode("overwrite") \
    .saveAsTable(f"{CATALOG_NAME}.silver.products")

print(f"✅ silver.products: {silver_products.count()} 件")

# COMMAND ----------

# MAGIC %md
# MAGIC ## データ品質チェック

# COMMAND ----------

from pyspark.sql import Row
import uuid

run_id = str(uuid.uuid4())
dq_results = []

# DQ-001: customers のNull件数チェック
null_count = silver_customers.filter(col("company_name").isNull()).count()
dq_results.append(Row(run_id=run_id, rule_name="null_check_company_name", table_name="silver.customers",
                       fail_count=null_count, threshold=0, result="PASS" if null_count <= 0 else "FAIL"))

# DQ-002: orders の重複チェック
dup_count = silver_orders.count() - silver_orders.dropDuplicates(["order_id"]).count()
dq_results.append(Row(run_id=run_id, rule_name="dup_check_order_id", table_name="silver.orders",
                       fail_count=dup_count, threshold=0, result="PASS" if dup_count <= 0 else "FAIL"))

# DQ-003: order_details の金額整合性（unit_price >= 0）
neg_price = silver_order_details.filter(col("unit_price") < 0).count()
dq_results.append(Row(run_id=run_id, rule_name="positive_unit_price", table_name="silver.order_details",
                       fail_count=neg_price, threshold=0, result="PASS" if neg_price <= 0 else "FAIL"))

# DQ結果を保存
dq_df = spark.createDataFrame(dq_results)
dq_df.write.format("delta").mode("append").saveAsTable(f"{CATALOG_NAME}.ops.dq_results")

print("\n📊 DQ Check 結果:")
for r in dq_results:
    icon = "✅" if r.result == "PASS" else "❌"
    print(f"  {icon} {r.rule_name}: {r.result} (fail_count: {r.fail_count})")

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ 完了チェックリスト
# MAGIC
# MAGIC - [ ] silver.customers が作成された
# MAGIC - [ ] silver.orders が作成された
# MAGIC - [ ] silver.order_details が作成された（line_total計算済み）
# MAGIC - [ ] silver.products が作成された
# MAGIC - [ ] DQ結果が ops.dq_results に記録された
# MAGIC
# MAGIC **次のステップ**: `04_etl_gold_aggregate.py`
