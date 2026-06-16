# Databricks notebook source
# Epic 4 / Story 4-1: EDA（探索的データ分析）- データ概要確認
# Gold層マートテーブルの基本統計量・データ分布を把握する

# COMMAND ----------
# セル1: Gold層テーブルの件数・期間確認

CATALOG_NAME = "northwind_catalog"

gold_tables = [
    "sales_by_product",
    "sales_by_customer",
    "sales_by_category",
    "order_summary",
]

print("=" * 70)
print("Gold層 テーブル概要")
print("=" * 70)
print(f"{'テーブル':<25} {'件数':>8}  {'カラム数':>8}")
print("-" * 70)

for t in gold_tables:
    df = spark.table(f"{CATALOG_NAME}.gold.{t}")
    print(f"  gold.{t:<22} {df.count():>8,}  {len(df.columns):>8}")

# COMMAND ----------
# セル2: sales_by_product のスキーマとサンプルデータ

df_product = spark.table(f"{CATALOG_NAME}.gold.sales_by_product")
df_product.printSchema()
display(df_product.limit(20))

# COMMAND ----------
# セル3: sales_by_product の基本統計量

display(df_product.describe())

# COMMAND ----------
# セル4: データ期間の確認（年月の範囲）

from pyspark.sql import functions as F

period = df_product.agg(
    F.min(F.make_date(F.col("order_year"), F.col("order_month"), F.lit(1))).alias("min_date"),
    F.max(F.make_date(F.col("order_year"), F.col("order_month"), F.lit(1))).alias("max_date"),
    F.countDistinct("product_name").alias("product_count"),
    F.countDistinct(F.concat(F.col("order_year"), F.lit("-"), F.col("order_month"))).alias("month_count"),
)
display(period)

# COMMAND ----------
# セル5: 商品ごとのレコード数（全期間にデータがあるか確認）

product_coverage = df_product.groupBy("product_name").agg(
    F.count("*").alias("month_count"),
    F.sum("total_sales").alias("lifetime_sales"),
).orderBy(F.col("lifetime_sales").desc())

display(product_coverage)

# COMMAND ----------
# セル6: NULL・ゼロ値の確認

from pyspark.sql import functions as F

null_check = df_product.select(
    F.count("*").alias("total_rows"),
    F.sum(F.when(F.col("total_sales").isNull(), 1).otherwise(0)).alias("null_sales"),
    F.sum(F.when(F.col("total_sales") == 0, 1).otherwise(0)).alias("zero_sales"),
    F.sum(F.when(F.col("total_quantity").isNull(), 1).otherwise(0)).alias("null_qty"),
    F.sum(F.when(F.col("order_count").isNull(), 1).otherwise(0)).alias("null_orders"),
)
display(null_check)

# COMMAND ----------
# セル7: order_summary テーブルの概要

df_order = spark.table(f"{CATALOG_NAME}.gold.order_summary")
df_order.printSchema()
display(df_order.describe())
