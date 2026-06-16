# Databricks notebook source
# Epic 4 / Story 4-1: EDA（探索的データ分析）- 売上分析と特徴量検討
# 時系列トレンド・分布・相関を分析し、予測対象と特徴量を決定する

# COMMAND ----------
# セル1: 月別売上推移（全体トレンド）

from pyspark.sql import functions as F

CATALOG_NAME = "northwind_catalog"

df_product = spark.table(f"{CATALOG_NAME}.gold.sales_by_product")

monthly_total = df_product.groupBy("order_year", "order_month").agg(
    F.sum("total_sales").alias("monthly_sales"),
    F.sum("total_quantity").alias("monthly_quantity"),
    F.sum("order_count").alias("monthly_orders"),
).withColumn(
    "order_date", F.make_date(F.col("order_year"), F.col("order_month"), F.lit(1))
).orderBy("order_date")

display(monthly_total)

# COMMAND ----------
# セル2: カテゴリ別売上推移

df_category = spark.table(f"{CATALOG_NAME}.gold.sales_by_category")

category_trend = df_category.withColumn(
    "order_date", F.make_date(F.col("order_year"), F.col("order_month"), F.lit(1))
).orderBy("order_date", "category_name")

display(category_trend)

# COMMAND ----------
# セル3: 商品別売上分布（ヒストグラム用）
# 全期間の商品別売上合計の分布を確認する

product_total = df_product.groupBy("product_id", "product_name").agg(
    F.sum("total_sales").alias("total_sales"),
    F.sum("total_quantity").alias("total_quantity"),
    F.avg("total_sales").alias("avg_monthly_sales"),
).orderBy(F.col("total_sales").desc())

display(product_total)

# COMMAND ----------
# セル4: 売上上位10商品の月次推移

from pyspark.sql.window import Window

top10 = [row["product_name"] for row in product_total.limit(10).collect()]

top10_trend = df_product.filter(
    F.col("product_name").isin(top10)
).withColumn(
    "order_date", F.make_date(F.col("order_year"), F.col("order_month"), F.lit(1))
).orderBy("order_date", "product_name")

display(top10_trend)

# COMMAND ----------
# セル5: total_sales / total_quantity / order_count 間の相関

# pandas に変換して相関行列を算出
pdf = df_product.select("total_sales", "total_quantity", "order_count").toPandas()
correlation = pdf.corr()
print("相関行列:")
print(correlation)
print()
print("total_sales と total_quantity の相関:", round(correlation.loc["total_sales", "total_quantity"], 4))
print("total_sales と order_count の相関:", round(correlation.loc["total_sales", "order_count"], 4))

# COMMAND ----------
# セル6: 月（季節性）による売上の違い

monthly_seasonality = df_product.groupBy("order_month").agg(
    F.avg("total_sales").alias("avg_sales"),
    F.sum("total_sales").alias("total_sales"),
    F.count("*").alias("data_points"),
).orderBy("order_month")

display(monthly_seasonality)

# COMMAND ----------
# セル7: 顧客別売上の分布

df_customer = spark.table(f"{CATALOG_NAME}.gold.sales_by_customer")

customer_total = df_customer.groupBy("company_name", "country").agg(
    F.sum("total_sales").alias("total_sales"),
    F.sum("order_count").alias("total_orders"),
    F.avg("avg_order_value").alias("avg_order_value"),
).orderBy(F.col("total_sales").desc())

display(customer_total)

# COMMAND ----------
# セル8: 国別売上集計

country_sales = df_customer.groupBy("country").agg(
    F.sum("total_sales").alias("total_sales"),
    F.countDistinct("company_name").alias("customer_count"),
).orderBy(F.col("total_sales").desc())

display(country_sales)

# COMMAND ----------
# セル9: 特徴量候補のまとめ
# （分析結果を踏まえた結論）

print("""
========================================================
予測対象と特徴量の決定（EDA結論）
========================================================

■ 予測対象（Target）
  → total_sales（商品別月次売上金額）

■ 予測粒度
  → 商品 × 月（gold.sales_by_product の1行が1サンプル）

■ 特徴量候補（Features）
  1. product_name   : 商品名（カテゴリカル）
  2. order_year     : 年（トレンド捕捉）
  3. order_month    : 月（季節性捕捉）
  4. total_quantity  : 注文数量（※リーケージ注意、AutoMLで判断）
  5. order_count     : 注文件数（※リーケージ注意、AutoMLで判断）

■ AutoML で検証すべきこと
  - total_quantity / order_count は target と強い相関
    → リーケージ（データ漏洩）の可能性があるため、
      AutoML の結果を見て除外を検討する
  - product_name のカーディナリティが高い場合の影響
========================================================
""")
