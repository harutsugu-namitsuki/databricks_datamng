# Databricks notebook source
# Epic 3 / Sprint 1 - Story 3-4: 手動コメントのスナップショット取得
# Step 4-1: Phase 1 で付与したコメントを ops.metadata_comparison_manual に保存する
# 現在登録されているテーブルやカラムの手動コメント情報を抽出し、スナップショットとして保存するファイルです。
# 全テーブルに対してDESCRIBE TABLE EXTENDEDなどを実行し、抽出したコメントをリストに格納しています。
# 格納したデータをSpark DataFrameに変換し、ops層の管理用Deltaテーブルとして上書き保存（overwrite）します。

# COMMAND ----------

CATALOG_NAME = "northwind_catalog"

manual_comments = []

for schema in ["bronze", "silver", "gold", "ops"]:
    tables = spark.sql(f"SHOW TABLES IN {CATALOG_NAME}.{schema}").collect()
    for t in tables:
        table_fqn = f"{CATALOG_NAME}.{schema}.{t.tableName}"

        # テーブルコメント取得
        desc_ext = spark.sql(f"DESCRIBE TABLE EXTENDED {table_fqn}").collect()
        comment_row = [r for r in desc_ext if r.col_name == "Comment"]
        table_comment = comment_row[0].data_type if comment_row and comment_row[0].data_type else ""

        # カラムコメント取得
        cols = spark.sql(f"DESCRIBE TABLE {table_fqn}").collect()
        for c in cols:
            if c.col_name and not c.col_name.startswith("#"):
                manual_comments.append({
                    "schema_name":   schema,
                    "table_name":    t.tableName,
                    "column_name":   c.col_name,
                    "table_comment": table_comment,
                    "column_comment": c.comment if c.comment else "",
                })

df_manual = spark.createDataFrame(manual_comments)
df_manual.write.format("delta").mode("overwrite") \
    .saveAsTable(f"{CATALOG_NAME}.ops.metadata_comparison_manual")
print(f"手動コメントスナップショット保存完了: {df_manual.count()} 件")
