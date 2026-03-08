# Databricks notebook source
# MAGIC %md
# MAGIC # 04. Gold層 集計（AWSシングルクラウド版）
# MAGIC
# MAGIC Silver層のデータを集計してGold層（マートテーブル）を作成します。
# MAGIC
# MAGIC **集計テーブル**:
# MAGIC - gold_sales_by_product: 商品別売上
# MAGIC - gold_sales_by_customer: 顧客別売上
# MAGIC - gold_sales_by_category: カテゴリ別売上
# MAGIC - gold_order_summary: 受注サマリ（日次）

# COMMAND ----------

from pyspark.sql.functions import col, sum as _sum, count, avg, year, month, concat_ws

CATALOG_NAME = "northwind_catalog"

print("✅ Gold Aggregate 開始")

# COMMAND ----------

# MAGIC %sql
# MAGIC USE CATALOG northwind_catalog;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold: 商品別売上（gold_sales_by_product）

# COMMAND ----------

df_od = spark.table("silver.order_details")
df_p = spark.table("silver.products")
df_o = spark.table("silver.orders")

gold_sales_by_product = df_od \
    .join(df_p, "product_id") \
    .join(df_o, "order_id") \
    .withColumn("order_year", year("order_date")) \
    .withColumn("order_month", month("order_date")) \
    .groupBy("product_id", "product_name", "order_year", "order_month") \
    .agg(
        _sum("line_total").alias("total_sales"),
        _sum("quantity").alias("total_quantity"),
        count("order_id").alias("order_count")
    ) \
    .orderBy("product_name", "order_year", "order_month")

gold_sales_by_product.write \
    .format("delta") \
    .mode("overwrite") \
    .saveAsTable(f"{CATALOG_NAME}.gold.sales_by_product")

print(f"✅ gold.sales_by_product: {gold_sales_by_product.count()} 件")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold: 顧客別売上（gold_sales_by_customer）

# COMMAND ----------

df_c = spark.table("silver.customers")

gold_sales_by_customer = df_od \
    .join(df_o, "order_id") \
    .join(df_c, "customer_id") \
    .withColumn("order_year", year("order_date")) \
    .withColumn("order_month", month("order_date")) \
    .groupBy("customer_id", "company_name", "country", "order_year", "order_month") \
    .agg(
        _sum("line_total").alias("total_sales"),
        count("order_id").alias("order_count"),
        avg("line_total").alias("avg_order_value")
    ) \
    .orderBy("company_name", "order_year", "order_month")

gold_sales_by_customer.write \
    .format("delta") \
    .mode("overwrite") \
    .saveAsTable(f"{CATALOG_NAME}.gold.sales_by_customer")

print(f"✅ gold.sales_by_customer: {gold_sales_by_customer.count()} 件")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold: カテゴリ別売上（gold_sales_by_category）

# COMMAND ----------

df_cat = spark.table("bronze.categories") \
    .select("category_id", "category_name")

gold_sales_by_category = df_od \
    .join(df_p, "product_id") \
    .join(df_o, "order_id") \
    .join(df_cat, "category_id") \
    .withColumn("order_year", year("order_date")) \
    .withColumn("order_month", month("order_date")) \
    .groupBy("category_id", "category_name", "order_year", "order_month") \
    .agg(
        _sum("line_total").alias("total_sales"),
        _sum("quantity").alias("total_quantity"),
        count("order_id").alias("order_count")
    ) \
    .orderBy("category_name", "order_year", "order_month")

gold_sales_by_category.write \
    .format("delta") \
    .mode("overwrite") \
    .saveAsTable(f"{CATALOG_NAME}.gold.sales_by_category")

print(f"✅ gold.sales_by_category: {gold_sales_by_category.count()} 件")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold: 受注サマリ（gold_order_summary）

# COMMAND ----------

gold_order_summary = df_o \
    .join(df_od, "order_id") \
    .groupBy("order_date") \
    .agg(
        count("order_id").alias("line_count"),
        _sum("line_total").alias("total_sales"),
        avg("line_total").alias("avg_line_value")
    ) \
    .orderBy("order_date")

gold_order_summary.write \
    .format("delta") \
    .mode("overwrite") \
    .saveAsTable(f"{CATALOG_NAME}.gold.order_summary")

print(f"✅ gold.order_summary: {gold_order_summary.count()} 件")

# COMMAND ----------

# MAGIC %md
# MAGIC ## ジョブ完了ログ

# COMMAND ----------

from pyspark.sql import Row
from datetime import datetime
import uuid

run_id = str(uuid.uuid4())
job_log = [Row(
    run_id=run_id,
    job_name="04_etl_gold_aggregate",
    start_time=datetime.now(),
    end_time=datetime.now(),
    status="SUCCESS",
    executed_by="databricks",
    notebook_path="/notebooks/04_etl_gold_aggregate"
)]

spark.createDataFrame(job_log).write \
    .format("delta") \
    .mode("append") \
    .saveAsTable(f"{CATALOG_NAME}.ops.job_runs")

print("✅ ジョブ完了ログを記録しました")

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ 完了チェックリスト
# MAGIC
# MAGIC - [ ] gold.sales_by_product が作成された
# MAGIC - [ ] gold.sales_by_customer が作成された
# MAGIC - [ ] gold.sales_by_category が作成された
# MAGIC - [ ] gold.order_summary が作成された
# MAGIC - [ ] ジョブ完了ログが ops.job_runs に記録された
# MAGIC
# MAGIC **パイプライン完了** 🎉
