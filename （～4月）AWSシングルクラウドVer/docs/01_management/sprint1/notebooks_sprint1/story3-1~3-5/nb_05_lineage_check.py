# Databricks notebook source
# Epic 3 / Sprint 1 - Story 3-5: リネージ可視化
# Step 5-1: system.access.table_lineage からリネージ取得
# Step 5-2: 期待リネージパスの検証
# 前提: Single User (Assigned) クラスター + Databricks Premium プラン以上
# テーブル間のデータ依存関係（リネージ）が、設計通りにシステムに記録されているかを確認するファイルです。
# システムテーブルsystem.access.table_lineageから実際のソースとターゲットのペアをクエリで取得します。
# プログラム内で定義した「期待されるリネージパス」のリストと照合し、網羅状況を出力（権限不足時はスキップ）します。

# COMMAND ----------
# Step 5-1: リネージのプログラム的確認

# system.access.table_lineage からリネージを取得
try:
    lineage_df = spark.sql("""
        SELECT
            source_table_full_name,
            target_table_full_name,
            event_time
        FROM system.access.table_lineage
        WHERE target_table_full_name LIKE 'northwind_catalog.%'
           OR source_table_full_name LIKE 'northwind_catalog.%'
        ORDER BY source_table_full_name, target_table_full_name
    """)

    print(f"リネージレコード数: {lineage_df.count()}")
    lineage_df.show(100, truncate=False)

except Exception as e:
    print(f"[WARN] system.access.table_lineage にアクセスできません: {e}")
    print("       → Premium プラン以上が必要です。UIでの確認に進んでください。")
    lineage_df = None

# COMMAND ----------
# Step 5-2: 期待リネージパスの検証

expected_lineage = [
    # Bronze → Silver
    ("northwind_catalog.bronze.customers",     "northwind_catalog.silver.customers"),
    ("northwind_catalog.bronze.orders",        "northwind_catalog.silver.orders"),
    ("northwind_catalog.bronze.order_details", "northwind_catalog.silver.order_details"),
    ("northwind_catalog.bronze.products",      "northwind_catalog.silver.products"),
    # Silver → Gold
    ("northwind_catalog.silver.order_details", "northwind_catalog.gold.sales_by_product"),
    ("northwind_catalog.silver.products",      "northwind_catalog.gold.sales_by_product"),
    ("northwind_catalog.silver.orders",        "northwind_catalog.gold.sales_by_product"),
    ("northwind_catalog.silver.order_details", "northwind_catalog.gold.sales_by_customer"),
    ("northwind_catalog.silver.customers",     "northwind_catalog.gold.sales_by_customer"),
    ("northwind_catalog.silver.orders",        "northwind_catalog.gold.sales_by_customer"),
    ("northwind_catalog.silver.order_details", "northwind_catalog.gold.sales_by_category"),
    ("northwind_catalog.silver.products",      "northwind_catalog.gold.sales_by_category"),
    ("northwind_catalog.silver.orders",        "northwind_catalog.gold.sales_by_category"),
    ("northwind_catalog.silver.order_details", "northwind_catalog.gold.order_summary"),
    ("northwind_catalog.silver.orders",        "northwind_catalog.gold.order_summary"),
    # Bronze → Gold（categories直接参照）
    ("northwind_catalog.bronze.categories",    "northwind_catalog.gold.sales_by_category"),
]

if lineage_df is not None and lineage_df.count() > 0:
    actual_pairs = set(
        (row.source_table_full_name, row.target_table_full_name)
        for row in lineage_df.collect()
    )
    found = 0
    not_found = 0
    for src, tgt in expected_lineage:
        if (src, tgt) in actual_pairs:
            print(f"  [PASS] {src} → {tgt}")
            found += 1
        else:
            print(f"  [MISS] {src} → {tgt}")
            not_found += 1

    print(f"\n検出: {found}/{len(expected_lineage)}、未検出: {not_found}/{len(expected_lineage)}")
else:
    print("[SKIP] lineage_df が取得できなかったため、UIで手動確認を実施してください。")
