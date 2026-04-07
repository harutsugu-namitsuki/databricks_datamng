# Databricks notebook source
# Epic 4 / Story 4-2: AutoML 用データ準備
# gold.sales_by_product から学習データセットを作成する

# COMMAND ----------
# セル1: ベースデータの読み込み

from pyspark.sql import functions as F

CATALOG_NAME = "northwind_catalog"
TRAINING_TABLE = f"{CATALOG_NAME}.gold.ml_training_sales"

df = spark.table(f"{CATALOG_NAME}.gold.sales_by_product")

print(f"元データ件数: {df.count()}")
display(df.limit(10))

# COMMAND ----------
# セル2: 特徴量エンジニアリング
# - order_date 列の追加（AutoML の時系列認識用）
# - カテゴリ情報の結合

df_products = spark.table(f"{CATALOG_NAME}.silver.products").select(
    "product_id", "category_id", "unit_price"
)
df_categories = spark.table(f"{CATALOG_NAME}.bronze.categories").select(
    "category_id", "category_name"
)

training_df = (
    df
    .withColumn("order_date", F.make_date(F.col("order_year"), F.col("order_month"), F.lit(1)))
    .join(df_products, on="product_id", how="left")
    .join(df_categories, on="category_id", how="left")
    .select(
        "order_date",
        "order_year",
        "order_month",
        "product_id",
        "product_name",
        "category_name",
        "unit_price",
        "total_quantity",
        "order_count",
        "total_sales",  # ← 予測対象（target）
    )
    .orderBy("order_date", "product_id")
)

print(f"学習データ件数: {training_df.count()}")
training_df.printSchema()
display(training_df.limit(20))

# COMMAND ----------
# セル3: 学習データをテーブルとして保存
# AutoML は Unity Catalog テーブルを入力にできる

training_df.write.format("delta").mode("overwrite").saveAsTable(TRAINING_TABLE)

print(f"✅ 学習データを {TRAINING_TABLE} に保存しました")
print(f"   件数: {spark.table(TRAINING_TABLE).count()}")

# COMMAND ----------
# セル4: 保存データの確認

display(spark.table(TRAINING_TABLE).describe())
