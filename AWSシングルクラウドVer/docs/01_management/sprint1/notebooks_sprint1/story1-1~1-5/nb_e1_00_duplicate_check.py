# Databricks notebook source
# Epic 1 / Sprint 1 - Story 1-1: 冪等性確認（修正前の現状チェック）
# Bronze層の重複状況・_load_date 別件数を確認する
# 修正前に実行して現状把握、修正後に再実行して改善を確認する

# COMMAND ----------
# セル1: Bronze層 _load_date 別件数（重複発生の確認）

CATALOG_NAME = "northwind_catalog"

bronze_tables = [
    "categories", "customers", "employees", "suppliers", "shippers",
    "products", "orders", "order_details", "region", "territories",
    "us_states", "employee_territories", "customer_demographics", "customer_customer_demo"
]

print("=" * 70)
print("Bronze層 _load_date 別件数")
print("=" * 70)
print(f"{'テーブル':<30} {'_load_date':<14} {'件数':>8}")
print("-" * 70)

for t in bronze_tables:
    rows = spark.sql(f"""
        SELECT _load_date, COUNT(*) as cnt
        FROM {CATALOG_NAME}.bronze.{t}
        GROUP BY _load_date
        ORDER BY _load_date
    """).collect()
    for r in rows:
        print(f"  bronze.{t:<26} {str(r['_load_date']):<14} {r['cnt']:>8,}")

# COMMAND ----------
# セル2: Bronze層 主キー重複チェック

PRIMARY_KEYS = {
    "categories":            ["category_id"],
    "customers":             ["customer_id"],
    "employees":             ["employee_id"],
    "suppliers":             ["supplier_id"],
    "shippers":              ["shipper_id"],
    "products":              ["product_id"],
    "orders":                ["order_id"],
    "order_details":         ["order_id", "product_id"],
    "region":                ["region_id"],
    "territories":           ["territory_id"],
    "us_states":             ["state_id"],
    "employee_territories":  ["employee_id", "territory_id"],
    "customer_demographics": ["customer_type_id"],
    "customer_customer_demo":["customer_id", "customer_type_id"],
}

print("\n" + "=" * 70)
print("Bronze層 主キー重複チェック（全期間）")
print("=" * 70)

has_dup = False
for t, pk in PRIMARY_KEYS.items():
    total = spark.sql(f"SELECT COUNT(*) FROM {CATALOG_NAME}.bronze.{t}").collect()[0][0]
    pk_cols = ", ".join(pk)
    unique = spark.sql(f"""
        SELECT COUNT(*) FROM (
            SELECT {pk_cols} FROM {CATALOG_NAME}.bronze.{t} GROUP BY {pk_cols}
        )
    """).collect()[0][0]
    dup = total - unique
    status = "[DUP]" if dup > 0 else "[ OK]"
    if dup > 0:
        has_dup = True
    print(f"  {status} bronze.{t:<30} 全{total:>6,}件 / ユニーク{unique:>6,}件 / 重複{dup:>5,}件")

if has_dup:
    print("\n⚠️  重複が検出されました。Story 1-1 の冪等化修正が必要です。")
else:
    print("\n✅ 重複なし（または初回実行のみのため問題なし）")

# COMMAND ----------
# セル3: Silver層 主キー重複チェック

SILVER_PRIMARY_KEYS = {
    "customers":    ["customer_id"],
    "orders":       ["order_id"],
    "order_details":["order_id", "product_id"],
    "products":     ["product_id"],
}

print("\n" + "=" * 70)
print("Silver層 主キー重複チェック")
print("=" * 70)

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
        status = "[DUP]" if dup > 0 else "[ OK]"
        print(f"  {status} silver.{t:<30} 全{total:>6,}件 / ユニーク{unique:>6,}件 / 重複{dup:>5,}件")
    except Exception as e:
        print(f"  [ERR] silver.{t}: {e}")
