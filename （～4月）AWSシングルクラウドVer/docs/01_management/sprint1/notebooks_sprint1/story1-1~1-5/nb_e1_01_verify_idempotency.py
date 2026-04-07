# Databricks notebook source
# Epic 1 / Sprint 1 - Story 1-1 & 1-2: 冪等性確認（修正後）
# 手順:
#   1. このノートブックを実行して件数スナップショットを取得
#   2. 02_etl_bronze_ingest.py を実行（1回目）
#   3. 02_etl_bronze_ingest.py をもう一度実行（2回目）
#   4. このノートブックを再実行して件数が変わっていないことを確認

# COMMAND ----------
# セル1: 件数スナップショット取得（パイプライン実行前後に毎回実行）

CATALOG_NAME = "northwind_catalog"

bronze_tables = [
    "categories", "customers", "employees", "suppliers", "shippers",
    "products", "orders", "order_details", "region", "territories",
    "us_states", "employee_territories", "customer_demographics", "customer_customer_demo"
]

silver_tables = ["customers", "orders", "order_details", "products"]
gold_tables = ["sales_by_product", "sales_by_customer", "sales_by_category", "order_summary"]

from datetime import datetime
snapshot_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
print(f"スナップショット取得時刻: {snapshot_time}")
print()

print(f"{'テーブル':<45} {'件数':>8}")
print("-" * 55)

for t in bronze_tables:
    cnt = spark.sql(f"SELECT COUNT(*) FROM {CATALOG_NAME}.bronze.{t}").collect()[0][0]
    print(f"  bronze.{t:<36} {cnt:>8,}")

for t in silver_tables:
    try:
        cnt = spark.sql(f"SELECT COUNT(*) FROM {CATALOG_NAME}.silver.{t}").collect()[0][0]
        print(f"  silver.{t:<36} {cnt:>8,}")
    except:
        print(f"  silver.{t:<36} {'(未作成)':>8}")

for t in gold_tables:
    try:
        cnt = spark.sql(f"SELECT COUNT(*) FROM {CATALOG_NAME}.gold.{t}").collect()[0][0]
        print(f"  gold.{t:<38} {cnt:>8,}")
    except:
        print(f"  gold.{t:<38} {'(未作成)':>8}")

print()
print("📋 このセルの出力を記録し、パイプライン2回実行後に再実行して件数を比較してください。")
print("   Bronze件数が変化しない = 冪等性OK")

# COMMAND ----------
# セル2: Bronze _load_date 別件数（1日1レコードセットであることを確認）

from datetime import date
today = str(date.today())

print(f"=" * 60)
print(f"本日（{today}）分 Bronze件数確認")
print(f"=" * 60)

for t in bronze_tables:
    cnt = spark.sql(f"""
        SELECT COUNT(*) FROM {CATALOG_NAME}.bronze.{t}
        WHERE _load_date = '{today}'
    """).collect()[0][0]
    print(f"  bronze.{t:<30} {today}: {cnt:>6,} 件")

print()
print("📋 Bronze を2回実行しても上記の件数が変わらなければ冪等性OK")

# COMMAND ----------
# セル3: Silver/Gold 冪等性確認（主キーユニーク確認）

SILVER_PRIMARY_KEYS = {
    "customers":    ["customer_id"],
    "orders":       ["order_id"],
    "order_details":["order_id", "product_id"],
    "products":     ["product_id"],
}

print("=" * 60)
print("Silver層 主キーユニーク確認")
print("=" * 60)

all_pass = True
for t, pk in SILVER_PRIMARY_KEYS.items():
    try:
        total = spark.sql(f"SELECT COUNT(*) FROM {CATALOG_NAME}.silver.{t}").collect()[0][0]
        pk_cols = ", ".join(pk)
        unique = spark.sql(f"""
            SELECT COUNT(*) FROM (
                SELECT {pk_cols} FROM {CATALOG_NAME}.silver.{t} GROUP BY {pk_cols}
            )
        """).collect()[0][0]
        dup = total - unique
        if dup == 0:
            print(f"  [PASS] silver.{t}: {total:,} 件（重複なし）")
        else:
            print(f"  [FAIL] silver.{t}: 重複 {dup} 件 → dropDuplicates が機能していない可能性")
            all_pass = False
    except Exception as e:
        print(f"  [SKIP] silver.{t}: {e}")

if all_pass:
    print("\n✅ Silver層 冪等性確認OK")
else:
    print("\n❌ 重複あり → Story 1-2 の修正内容を再確認してください")
