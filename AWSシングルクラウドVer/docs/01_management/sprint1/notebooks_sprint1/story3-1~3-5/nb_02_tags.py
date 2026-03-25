# Databricks notebook source
# Epic 3 / Sprint 1 - Story 3-2: タグ付与
# Step 2-2: テーブルタグ → Step 2-3: PIIカラムタグ → Step 2-4: 確認
# データディスカバリやガバナンス向上のため、テーブルと特定カラム（PII等）にカスタムタグを付与するファイルです。
# ドメイン、レイヤー、PIIの有無などを辞書に定義し、ALTER TABLE ... SET TAGS構文を用いて適用しています。
# 最後にsystem.information_schemaのビューを検索し、タグが正しく付与されたかをクエリで確認・集計します。

# COMMAND ----------
# Step 2-1: テーブルタグ付与（全25テーブル）
# ※事前にCatalog Explorer UI（管理タグ）にてキーと許容値を定義しておくこと

CATALOG_NAME = "northwind_catalog"



# ── テーブルタグ定義 ──
table_tags = {
    # Bronze層
    "bronze.categories":            {"domain": "product",    "layer": "bronze", "pii": "false", "update_frequency": "daily", "data_type": "master"},
    "bronze.customers":             {"domain": "customer",   "layer": "bronze", "pii": "true",  "update_frequency": "daily", "data_type": "master"},
    "bronze.employees":             {"domain": "employee",   "layer": "bronze", "pii": "true",  "update_frequency": "daily", "data_type": "master"},
    "bronze.suppliers":             {"domain": "logistics",  "layer": "bronze", "pii": "false", "update_frequency": "daily", "data_type": "master"},
    "bronze.shippers":              {"domain": "logistics",  "layer": "bronze", "pii": "false", "update_frequency": "daily", "data_type": "master"},
    "bronze.products":              {"domain": "product",    "layer": "bronze", "pii": "false", "update_frequency": "daily", "data_type": "master"},
    "bronze.region":                {"domain": "reference",  "layer": "bronze", "pii": "false", "update_frequency": "daily", "data_type": "reference"},
    "bronze.orders":                {"domain": "sales",      "layer": "bronze", "pii": "false", "update_frequency": "daily", "data_type": "transaction"},
    "bronze.order_details":         {"domain": "sales",      "layer": "bronze", "pii": "false", "update_frequency": "daily", "data_type": "transaction"},
    "bronze.territories":           {"domain": "reference",  "layer": "bronze", "pii": "false", "update_frequency": "daily", "data_type": "reference"},
    "bronze.us_states":             {"domain": "reference",  "layer": "bronze", "pii": "false", "update_frequency": "daily", "data_type": "reference"},
    "bronze.employee_territories":  {"domain": "employee",   "layer": "bronze", "pii": "false", "update_frequency": "daily", "data_type": "reference"},
    "bronze.customer_demographics": {"domain": "customer",   "layer": "bronze", "pii": "false", "update_frequency": "daily", "data_type": "reference"},
    "bronze.customer_customer_demo":{"domain": "customer",   "layer": "bronze", "pii": "false", "update_frequency": "daily", "data_type": "reference"},
    # Silver層
    "silver.customers":             {"domain": "customer",   "layer": "silver", "pii": "true",  "update_frequency": "daily", "data_type": "master"},
    "silver.orders":                {"domain": "sales",      "layer": "silver", "pii": "false", "update_frequency": "daily", "data_type": "transaction"},
    "silver.order_details":         {"domain": "sales",      "layer": "silver", "pii": "false", "update_frequency": "daily", "data_type": "transaction"},
    "silver.products":              {"domain": "product",    "layer": "silver", "pii": "false", "update_frequency": "daily", "data_type": "master"},
    # Gold層
    "gold.sales_by_product":        {"domain": "sales",      "layer": "gold",   "pii": "false", "update_frequency": "daily", "data_type": "aggregate"},
    "gold.sales_by_customer":       {"domain": "sales",      "layer": "gold",   "pii": "false", "update_frequency": "daily", "data_type": "aggregate"},
    "gold.sales_by_category":       {"domain": "sales",      "layer": "gold",   "pii": "false", "update_frequency": "daily", "data_type": "aggregate"},
    "gold.order_summary":           {"domain": "sales",      "layer": "gold",   "pii": "false", "update_frequency": "daily", "data_type": "aggregate"},
    # Ops層
    "ops.job_runs":                 {"domain": "operations", "layer": "ops",    "pii": "false", "update_frequency": "append", "data_type": "log"},
    "ops.ingestion_log":            {"domain": "operations", "layer": "ops",    "pii": "false", "update_frequency": "append", "data_type": "log"},
    "ops.dq_results":               {"domain": "operations", "layer": "ops",    "pii": "false", "update_frequency": "append", "data_type": "log"},
}

# ── 実行 ──
for table_fqn, tags in table_tags.items():
    tag_pairs = ", ".join([f"'{k}' = '{v}'" for k, v in tags.items()])
    spark.sql(f"ALTER TABLE {CATALOG_NAME}.{table_fqn} SET TAGS ({tag_pairs})")
    print(f"  [OK] {table_fqn}: {len(tags)} タグ")

print(f"\nテーブルタグ付与完了: {len(table_tags)} テーブル")

# COMMAND ----------
# Step 2-2: PII カラムタグ付与

# ── PIIカラムタグ定義 ──
pii_column_tags = {
    "bronze.customers": {
        "contact_name": {"pii": "true", "pii_type": "name"},
        "address":      {"pii": "true", "pii_type": "address"},
        "phone":        {"pii": "true", "pii_type": "phone"},
        "fax":          {"pii": "true", "pii_type": "phone"},
    },
    "bronze.employees": {
        "birth_date": {"pii": "true", "pii_type": "birth_date"},
        "address":    {"pii": "true", "pii_type": "address"},
        "home_phone": {"pii": "true", "pii_type": "phone"},
        "photo":      {"pii": "true", "pii_type": "photo"},
    },
    "silver.customers": {
        "contact_name": {"pii": "true", "pii_type": "name"},
        "address":      {"pii": "true", "pii_type": "address"},
        "phone":        {"pii": "true", "pii_type": "phone"},
        "fax":          {"pii": "true", "pii_type": "phone"},
    },
}

# ── 実行 ──
for table_fqn, columns in pii_column_tags.items():
    for col_name, tags in columns.items():
        tag_pairs = ", ".join([f"'{k}' = '{v}'" for k, v in tags.items()])
        spark.sql(f"ALTER TABLE {CATALOG_NAME}.{table_fqn} ALTER COLUMN {col_name} SET TAGS ({tag_pairs})")
        print(f"  [OK] {table_fqn}.{col_name}: {tags}")

print("\nPIIカラムタグ付与完了")

# COMMAND ----------
# Step 2-3: 付与結果の確認

# テーブルタグの確認
print("=" * 70)
print("テーブルタグ一覧")
print("=" * 70)

df_tags = spark.sql("""
    SELECT schema_name, table_name, tag_name, tag_value
    FROM system.information_schema.table_tags
    WHERE catalog_name = 'northwind_catalog'
    ORDER BY schema_name, table_name, tag_name
""")
df_tags.show(200, truncate=False)
print(f"テーブルタグ総数: {df_tags.count()}")

# カラムタグの確認
print("\n" + "=" * 70)
print("カラムタグ一覧（PIIカラム）")
print("=" * 70)

df_col_tags = spark.sql("""
    SELECT schema_name, table_name, column_name, tag_name, tag_value
    FROM system.information_schema.column_tags
    WHERE catalog_name = 'northwind_catalog'
    ORDER BY schema_name, table_name, column_name, tag_name
""")
df_col_tags.show(50, truncate=False)
print(f"カラムタグ総数: {df_col_tags.count()}")
