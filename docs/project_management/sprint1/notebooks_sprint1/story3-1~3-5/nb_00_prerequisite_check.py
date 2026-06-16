# Databricks notebook source
# Epic 3 / Sprint 1: 前提条件チェック
# 全テーブルが Bronze/Silver/Gold/Ops に存在することを確認する
# 処理の前提となる各層（Bronze/Silver/Gold/Ops）のテーブルが全て存在するか確認するファイルです。
# 期待される全25テーブルの名前を辞書型で事前に定義しています。
# SHOW TABLESコマンドで取得した実際のテーブル一覧と突き合わせて、欠損がないかをループ処理で判定します。

# COMMAND ----------

CATALOG_NAME = "northwind_catalog"
spark.sql(f"USE CATALOG {CATALOG_NAME}")

expected_tables = {
    "bronze": [
        "categories", "customers", "employees", "suppliers", "shippers",
        "products", "region", "orders", "order_details", "territories",
        "us_states", "employee_territories", "customer_demographics", "customer_customer_demo"
    ],
    "silver": ["customers", "orders", "order_details", "products"],
    "gold": ["sales_by_product", "sales_by_customer", "sales_by_category", "order_summary"],
    "ops": ["job_runs", "ingestion_log", "dq_results"],
}

for schema, tables in expected_tables.items():
    existing = [r.tableName for r in spark.sql(f"SHOW TABLES IN {CATALOG_NAME}.{schema}").collect()]
    for t in tables:
        status = "OK" if t in existing else "MISSING"
        print(f"  [{status}] {schema}.{t}")

print(f"\n合計テーブル数: {sum(len(v) for v in expected_tables.values())}")
