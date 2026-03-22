# Databricks notebook source
# Epic 3 / Sprint 1 - Story 3-3: 検索・探索検証
# Step 3-1〜3-5: タグ検索・キーワード検索・複合条件のテストケース
# 付与したタグやコメントを利用して、目的のデータが正しく検索・抽出できるかをテストするファイルです。
# 「売上ドメイン」「PII含有」「Gold層かつ売上」といった実務的な検索条件をSQLで表現しています。
# 検索結果の件数が事前に定義した期待値と一致するかをassert文を使って自動検証します。

# COMMAND ----------
# Step 3-1: テストケース1 — 売上に関するテーブルを探す
# 成功条件: domain の値が 'sales' であるテーブルが 8 件（bronze.orders, bronze.order_details,
#           silver.orders, silver.order_details,
#           gold.sales_by_product, gold.sales_by_customer, gold.sales_by_category, gold.order_summary）抽出されること。

result_sales = spark.sql("""
    SELECT schema_name, table_name
    FROM system.information_schema.table_tags
    WHERE catalog_name = 'northwind_catalog'
      AND tag_name = 'domain'
      AND tag_value = 'sales'
    ORDER BY schema_name, table_name
""")
result_sales.show(truncate=False)

expected = 8
actual = result_sales.count()
assert actual == expected, f"FAIL: 期待 {expected} 件、実際 {actual} 件"
print(f"[PASS] テスト1: domain:sales で {actual} テーブル検出")

# COMMAND ----------
# Step 3-2: テストケース2 — 個人情報を含むテーブルを探す
# 成功条件:
# - テーブルレベル: pii の値が 'true' であるテーブルが 3 件（bronze.customers, bronze.employees, silver.customers）抽出されること。
# - カラムレベル: pii の値が 'true' であるカラムが 12 件（上記3テーブルの各4カラムずつ）抽出されること。

# テーブルレベル
result_pii = spark.sql("""
    SELECT schema_name, table_name
    FROM system.information_schema.table_tags
    WHERE catalog_name = 'northwind_catalog'
      AND tag_name = 'pii'
      AND tag_value = 'true'
    ORDER BY schema_name, table_name
""")
result_pii.show(truncate=False)

assert result_pii.count() == 3, f"FAIL: PII テーブル数が期待と異なる（実際: {result_pii.count()}）"
print(f"[PASS] テスト2a: pii:true で {result_pii.count()} テーブル検出")

# カラムレベル
result_pii_cols = spark.sql("""
    SELECT schema_name, table_name, column_name, tag_name, tag_value
    FROM system.information_schema.column_tags
    WHERE catalog_name = 'northwind_catalog'
      AND tag_name = 'pii'
      AND tag_value = 'true'
    ORDER BY column_name
""")
result_pii_cols.show(truncate=False)

assert result_pii_cols.count() == 12, f"FAIL: PII カラム数が期待と異なる（実際: {result_pii_cols.count()}）"
print(f"[PASS] テスト2b: PIIカラム {result_pii_cols.count()} 件検出")

# COMMAND ----------
# Step 3-3: テストケース3 — Gold 層の集計テーブルを探す
# 成功条件: data_type の値が 'aggregate' であるテーブルが 4 件（gold.sales_by_product, gold.sales_by_customer, gold.sales_by_category, gold.order_summary）抽出されること。

result_agg = spark.sql("""
    SELECT schema_name, table_name
    FROM system.information_schema.table_tags
    WHERE catalog_name = 'northwind_catalog'
      AND tag_name = 'data_type'
      AND tag_value = 'aggregate'
    ORDER BY table_name
""")
result_agg.show(truncate=False)

assert result_agg.count() == 4, f"FAIL: aggregate テーブル数が期待と異なる（実際: {result_agg.count()}）"
print(f"[PASS] テスト3: data_type:aggregate で {result_agg.count()} テーブル検出")

# COMMAND ----------
# Step 3-4: テストケース4 — キーワード「売上」でコメント検索
# 成功条件: コメントに「売上」を含むテーブルが 5 件（silver.order_details, gold.sales_by_product, gold.sales_by_customer, gold.sales_by_category, gold.order_summary）抽出されること。

result_keyword = spark.sql("""
    SELECT table_schema, table_name, comment
    FROM system.information_schema.tables
    WHERE table_catalog = 'northwind_catalog'
      AND comment LIKE '%売上%'
    ORDER BY table_schema, table_name
""")
result_keyword.show(truncate=False)

expected_k = 5
actual_k = result_keyword.count()
assert actual_k == expected_k, f"FAIL: 期待 {expected_k} 件、実際 {actual_k} 件"
print(f"[PASS] テスト4: キーワード '売上' で {actual_k} テーブル検出")

# COMMAND ----------
# Step 3-5: テストケース5 — 複合条件（layer:gold AND domain:sales）
# 成功条件: layer が 'gold' 且つ domain が 'sales' であるテーブルが 4 件（gold.sales_by_product, gold.sales_by_customer, gold.sales_by_category, gold.order_summary）抽出されること。

result_complex = spark.sql("""
    SELECT t1.schema_name, t1.table_name
    FROM system.information_schema.table_tags t1
    JOIN system.information_schema.table_tags t2
      ON t1.catalog_name = t2.catalog_name
     AND t1.schema_name = t2.schema_name
     AND t1.table_name = t2.table_name
    WHERE t1.catalog_name = 'northwind_catalog'
      AND t1.tag_name = 'layer' AND t1.tag_value = 'gold'
      AND t2.tag_name = 'domain' AND t2.tag_value = 'sales'
    ORDER BY t1.table_name
""")
result_complex.show(truncate=False)

assert result_complex.count() == 4, f"FAIL: 複合条件の結果が期待と異なる（実際: {result_complex.count()}）"
print(f"[PASS] テスト5: layer:gold AND domain:sales で {result_complex.count()} テーブル検出")
