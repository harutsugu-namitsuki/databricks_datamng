# Databricks notebook source
# MAGIC %md
# MAGIC # 03. ETL Silver層：クレンジング・標準化
# MAGIC 
# MAGIC このノートブックでは、Bronze層のデータをクレンジング・標準化してSilver層に保存します。
# MAGIC 
# MAGIC **処理内容**:
# MAGIC - NULL値のハンドリング
# MAGIC - データ型の標準化
# MAGIC - カラム名の標準化（snake_case）
# MAGIC - 重複データの除去
# MAGIC - 品質チェック

# COMMAND ----------

# MAGIC %md
# MAGIC ## 設定値

# COMMAND ----------

from pyspark.sql.functions import col, trim, lower, upper, when, coalesce, lit, current_timestamp
from pyspark.sql.types import DecimalType, DateType

# Unity Catalog設定
CATALOG = "northwind"
BRONZE_SCHEMA = "bronze"
SILVER_SCHEMA = "silver"

# COMMAND ----------

# MAGIC %sql
# MAGIC USE CATALOG northwind;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Silver層変換関数

# COMMAND ----------

def transform_categories():
    """categories テーブルのSilver変換"""
    df = spark.table(f"{CATALOG}.{BRONZE_SCHEMA}.categories")
    
    df_silver = df \
        .select(
            col("category_id"),
            trim(col("category_name")).alias("category_name"),
            coalesce(trim(col("description")), lit("")).alias("description"),
            col("_load_date"),
            col("_load_timestamp")
        ) \
        .dropDuplicates(["category_id"])
    
    df_silver.write \
        .format("delta") \
        .mode("overwrite") \
        .saveAsTable(f"{CATALOG}.{SILVER_SCHEMA}.categories")
    
    return df_silver.count()

# COMMAND ----------

def transform_suppliers():
    """suppliers テーブルのSilver変換"""
    df = spark.table(f"{CATALOG}.{BRONZE_SCHEMA}.suppliers")
    
    df_silver = df \
        .select(
            col("supplier_id"),
            trim(col("company_name")).alias("company_name"),
            coalesce(trim(col("contact_name")), lit("Unknown")).alias("contact_name"),
            coalesce(trim(col("contact_title")), lit("")).alias("contact_title"),
            coalesce(trim(col("city")), lit("")).alias("city"),
            coalesce(upper(trim(col("country"))), lit("")).alias("country"),
            coalesce(trim(col("phone")), lit("")).alias("phone"),
            col("_load_date"),
            col("_load_timestamp")
        ) \
        .dropDuplicates(["supplier_id"])
    
    df_silver.write \
        .format("delta") \
        .mode("overwrite") \
        .saveAsTable(f"{CATALOG}.{SILVER_SCHEMA}.suppliers")
    
    return df_silver.count()

# COMMAND ----------

def transform_customers():
    """customers テーブルのSilver変換"""
    df = spark.table(f"{CATALOG}.{BRONZE_SCHEMA}.customers")
    
    df_silver = df \
        .select(
            upper(trim(col("customer_id"))).alias("customer_id"),
            trim(col("company_name")).alias("company_name"),
            coalesce(trim(col("contact_name")), lit("Unknown")).alias("contact_name"),
            coalesce(trim(col("city")), lit("")).alias("city"),
            coalesce(upper(trim(col("country"))), lit("")).alias("country"),
            col("_load_date"),
            col("_load_timestamp")
        ) \
        .dropDuplicates(["customer_id"])
    
    df_silver.write \
        .format("delta") \
        .mode("overwrite") \
        .saveAsTable(f"{CATALOG}.{SILVER_SCHEMA}.customers")
    
    return df_silver.count()

# COMMAND ----------

def transform_employees():
    """employees テーブルのSilver変換"""
    df = spark.table(f"{CATALOG}.{BRONZE_SCHEMA}.employees")
    
    df_silver = df \
        .select(
            col("employee_id"),
            trim(col("first_name")).alias("first_name"),
            trim(col("last_name")).alias("last_name"),
            coalesce(trim(col("title")), lit("")).alias("title"),
            col("hire_date"),
            coalesce(trim(col("city")), lit("")).alias("city"),
            coalesce(upper(trim(col("country"))), lit("")).alias("country"),
            col("_load_date"),
            col("_load_timestamp")
        ) \
        .dropDuplicates(["employee_id"])
    
    df_silver.write \
        .format("delta") \
        .mode("overwrite") \
        .saveAsTable(f"{CATALOG}.{SILVER_SCHEMA}.employees")
    
    return df_silver.count()

# COMMAND ----------

def transform_products():
    """products テーブルのSilver変換"""
    df = spark.table(f"{CATALOG}.{BRONZE_SCHEMA}.products")
    
    df_silver = df \
        .select(
            col("product_id"),
            trim(col("product_name")).alias("product_name"),
            col("supplier_id"),
            col("category_id"),
            coalesce(col("unit_price"), lit(0.0)).cast(DecimalType(10, 2)).alias("unit_price"),
            coalesce(col("units_in_stock"), lit(0)).alias("units_in_stock"),
            coalesce(col("discontinued"), lit(False)).alias("discontinued"),
            col("_load_date"),
            col("_load_timestamp")
        ) \
        .dropDuplicates(["product_id"])
    
    df_silver.write \
        .format("delta") \
        .mode("overwrite") \
        .saveAsTable(f"{CATALOG}.{SILVER_SCHEMA}.products")
    
    return df_silver.count()

# COMMAND ----------

def transform_orders():
    """orders テーブルのSilver変換"""
    df = spark.table(f"{CATALOG}.{BRONZE_SCHEMA}.orders")
    
    df_silver = df \
        .select(
            col("order_id"),
            upper(trim(col("customer_id"))).alias("customer_id"),
            col("employee_id"),
            col("order_date"),
            col("shipped_date"),
            coalesce(col("freight"), lit(0.0)).cast(DecimalType(10, 2)).alias("freight"),
            coalesce(trim(col("ship_city")), lit("")).alias("ship_city"),
            coalesce(upper(trim(col("ship_country"))), lit("")).alias("ship_country"),
            col("_load_date"),
            col("_load_timestamp")
        ) \
        .dropDuplicates(["order_id"])
    
    df_silver.write \
        .format("delta") \
        .mode("overwrite") \
        .saveAsTable(f"{CATALOG}.{SILVER_SCHEMA}.orders")
    
    return df_silver.count()

# COMMAND ----------

def transform_order_details():
    """order_details テーブルのSilver変換"""
    df = spark.table(f"{CATALOG}.{BRONZE_SCHEMA}.order_details")
    
    df_silver = df \
        .select(
            col("order_id"),
            col("product_id"),
            col("unit_price").cast(DecimalType(10, 2)).alias("unit_price"),
            col("quantity"),
            coalesce(col("discount"), lit(0.0)).cast(DecimalType(4, 2)).alias("discount"),
            # 計算カラム追加
            (col("unit_price") * col("quantity") * (1 - coalesce(col("discount"), lit(0)))).alias("line_total"),
            col("_load_date"),
            col("_load_timestamp")
        ) \
        .dropDuplicates(["order_id", "product_id"])
    
    df_silver.write \
        .format("delta") \
        .mode("overwrite") \
        .saveAsTable(f"{CATALOG}.{SILVER_SCHEMA}.order_details")
    
    return df_silver.count()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Silver変換実行

# COMMAND ----------

# 変換処理のマッピング
transform_functions = {
    "categories": transform_categories,
    "suppliers": transform_suppliers,
    "customers": transform_customers,
    "employees": transform_employees,
    "products": transform_products,
    "orders": transform_orders,
    "order_details": transform_order_details
}

# 全テーブル変換実行
transform_results = []

for table_name, transform_func in transform_functions.items():
    try:
        count = transform_func()
        print(f"✅ {table_name}: {count} records")
        transform_results.append({"table": table_name, "status": "success", "count": count})
    except Exception as e:
        print(f"❌ {table_name}: {str(e)}")
        transform_results.append({"table": table_name, "status": "failed", "error": str(e)})

# COMMAND ----------

# MAGIC %md
# MAGIC ## Silver層テーブル確認

# COMMAND ----------

# MAGIC %sql
# MAGIC SHOW TABLES IN northwind.silver;

# COMMAND ----------

# サンプルデータ確認
# MAGIC %sql
# MAGIC SELECT * FROM northwind.silver.order_details LIMIT 5;

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ 完了チェックリスト
# MAGIC 
# MAGIC - [ ] 全テーブルがSilver層に変換された
# MAGIC - [ ] NULL値が適切にハンドリングされている
# MAGIC - [ ] データ型が標準化されている
# MAGIC - [ ] 重複が除去されている
# MAGIC 
# MAGIC 次のステップ: `04_etl_gold_aggregate.py` でGold層の集計マートを作成します
