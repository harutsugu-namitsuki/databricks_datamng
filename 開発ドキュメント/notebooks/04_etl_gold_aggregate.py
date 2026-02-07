# Databricks notebook source
# MAGIC %md
# MAGIC # 04. ETL Gold層：集計・分析マート作成
# MAGIC 
# MAGIC このノートブックでは、Silver層のデータを集計・結合してGold層の分析マートを作成します。
# MAGIC 
# MAGIC **作成するマート**:
# MAGIC 1. `sales_summary` - 売上サマリ（日別・月別）
# MAGIC 2. `product_performance` - 商品別売上パフォーマンス
# MAGIC 3. `customer_analytics` - 顧客分析マート

# COMMAND ----------

# MAGIC %md
# MAGIC ## 設定値

# COMMAND ----------

from pyspark.sql.functions import (
    col, sum, count, avg, max, min, 
    year, month, dayofmonth, date_format,
    row_number, dense_rank, current_timestamp
)
from pyspark.sql.window import Window

# Unity Catalog設定
CATALOG = "northwind"
SILVER_SCHEMA = "silver"
GOLD_SCHEMA = "gold"

# COMMAND ----------

# MAGIC %sql
# MAGIC USE CATALOG northwind;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Sales Summary マート

# COMMAND ----------

def create_sales_summary():
    """
    日別・月別の売上サマリマートを作成
    """
    # Silver層からデータ取得
    orders = spark.table(f"{CATALOG}.{SILVER_SCHEMA}.orders")
    order_details = spark.table(f"{CATALOG}.{SILVER_SCHEMA}.order_details")
    
    # 注文と明細を結合
    sales_df = orders.join(
        order_details, 
        on="order_id", 
        how="inner"
    )
    
    # 日別サマリ
    daily_summary = sales_df \
        .groupBy(
            col("order_date"),
            year("order_date").alias("order_year"),
            month("order_date").alias("order_month"),
            dayofmonth("order_date").alias("order_day")
        ) \
        .agg(
            count("order_id").alias("total_orders"),
            sum("line_total").alias("total_revenue"),
            sum("quantity").alias("total_quantity"),
            avg("line_total").alias("avg_order_value")
        ) \
        .withColumn("_created_at", current_timestamp())
    
    # Gold層に保存
    daily_summary.write \
        .format("delta") \
        .mode("overwrite") \
        .saveAsTable(f"{CATALOG}.{GOLD_SCHEMA}.sales_summary")
    
    return daily_summary.count()

# COMMAND ----------

# 売上サマリマート作成
count = create_sales_summary()
print(f"✅ sales_summary: {count} records created")

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM northwind.gold.sales_summary ORDER BY order_date;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Product Performance マート

# COMMAND ----------

def create_product_performance():
    """
    商品別の売上パフォーマンスマートを作成
    """
    # Silver層からデータ取得
    products = spark.table(f"{CATALOG}.{SILVER_SCHEMA}.products")
    categories = spark.table(f"{CATALOG}.{SILVER_SCHEMA}.categories")
    order_details = spark.table(f"{CATALOG}.{SILVER_SCHEMA}.order_details")
    
    # 商品・カテゴリ・売上を結合して集計
    product_perf = order_details \
        .join(products, on="product_id", how="inner") \
        .join(categories, on="category_id", how="left") \
        .groupBy(
            products["product_id"],
            products["product_name"],
            categories["category_name"],
            products["unit_price"].alias("list_price")
        ) \
        .agg(
            count("order_id").alias("order_count"),
            sum("quantity").alias("total_quantity_sold"),
            sum("line_total").alias("total_revenue"),
            avg(order_details["unit_price"]).alias("avg_selling_price")
        )
    
    # ランキング追加
    window_spec = Window.orderBy(col("total_revenue").desc())
    
    product_perf_ranked = product_perf \
        .withColumn("revenue_rank", dense_rank().over(window_spec)) \
        .withColumn("_created_at", current_timestamp())
    
    # Gold層に保存
    product_perf_ranked.write \
        .format("delta") \
        .mode("overwrite") \
        .saveAsTable(f"{CATALOG}.{GOLD_SCHEMA}.product_performance")
    
    return product_perf_ranked.count()

# COMMAND ----------

# 商品パフォーマンスマート作成
count = create_product_performance()
print(f"✅ product_performance: {count} records created")

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM northwind.gold.product_performance ORDER BY revenue_rank LIMIT 10;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Customer Analytics マート

# COMMAND ----------

def create_customer_analytics():
    """
    顧客分析マートを作成
    """
    # Silver層からデータ取得
    customers = spark.table(f"{CATALOG}.{SILVER_SCHEMA}.customers")
    orders = spark.table(f"{CATALOG}.{SILVER_SCHEMA}.orders")
    order_details = spark.table(f"{CATALOG}.{SILVER_SCHEMA}.order_details")
    
    # 注文と明細を結合
    order_totals = orders \
        .join(order_details, on="order_id", how="inner") \
        .groupBy("order_id", "customer_id", "order_date") \
        .agg(sum("line_total").alias("order_total"))
    
    # 顧客別集計
    customer_stats = order_totals \
        .groupBy("customer_id") \
        .agg(
            count("order_id").alias("total_orders"),
            sum("order_total").alias("lifetime_value"),
            avg("order_total").alias("avg_order_value"),
            min("order_date").alias("first_order_date"),
            max("order_date").alias("last_order_date")
        )
    
    # 顧客マスタと結合
    customer_analytics = customers \
        .join(customer_stats, on="customer_id", how="left") \
        .select(
            customers["customer_id"],
            customers["company_name"],
            customers["contact_name"],
            customers["city"],
            customers["country"],
            col("total_orders"),
            col("lifetime_value"),
            col("avg_order_value"),
            col("first_order_date"),
            col("last_order_date")
        ) \
        .withColumn("_created_at", current_timestamp())
    
    # Gold層に保存
    customer_analytics.write \
        .format("delta") \
        .mode("overwrite") \
        .saveAsTable(f"{CATALOG}.{GOLD_SCHEMA}.customer_analytics")
    
    return customer_analytics.count()

# COMMAND ----------

# 顧客分析マート作成
count = create_customer_analytics()
print(f"✅ customer_analytics: {count} records created")

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM northwind.gold.customer_analytics 
# MAGIC ORDER BY lifetime_value DESC NULLS LAST 
# MAGIC LIMIT 10;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold層テーブル一覧

# COMMAND ----------

# MAGIC %sql
# MAGIC SHOW TABLES IN northwind.gold;

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ 完了チェックリスト
# MAGIC 
# MAGIC - [ ] `sales_summary` マートが作成された
# MAGIC - [ ] `product_performance` マートが作成された
# MAGIC - [ ] `customer_analytics` マートが作成された
# MAGIC - [ ] 全マートがUnity Catalogに登録されている
# MAGIC 
# MAGIC 🎉 **ETLパイプライン完成！**
# MAGIC 
# MAGIC これで Bronze → Silver → Gold のMedallion Architectureが実装されました。
