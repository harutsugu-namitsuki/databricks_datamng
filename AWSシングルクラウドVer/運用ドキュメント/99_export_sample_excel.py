# Databricks notebook source
# ==========================================
# サンプルデータ Excel 一括出力
# ==========================================
# Unity Catalog 上の全テーブルからサンプルデータを取得し、
# レイヤー別シート構成の Excel ブックとして Volume に出力する。
#
# 出力イメージ:
#   シート「bronze→」(空) → 「categories」→ 「customers」→ ...
#   シート「silver→」(空) → 「customers」→ 「order_details」→ ...
#   シート「gold→」(空)   → 「order_summary」→ ...
#   シート「ops→」(空)    → 「dq_results」→ ...

# COMMAND ----------

# ==========================================
# 1. 初期設定
# ==========================================
import subprocess
subprocess.run(["pip", "install", "openpyxl"], check=True)

from datetime import datetime

TARGET_CATALOG = "northwind_catalog"
EXPORT_SCHEMA  = "exports"
EXPORT_VOLUME  = "sample_data"
SAMPLE_LIMIT   = 10

# レイヤー表示順（この順番でシートが並ぶ）
LAYER_ORDER = ["bronze", "silver", "gold", "ops"]

# 除外するスキーマ
SKIP_SCHEMAS = {"information_schema", EXPORT_SCHEMA}

# 出力ファイル名（タイムスタンプ付き）
timestamp = datetime.now().strftime("%Y%m%d%H%M")
OUTPUT_FILENAME = f"サンプルデータ_{timestamp}.xlsx"

# COMMAND ----------

# ==========================================
# 2. 出力先 Volume の準備
# ==========================================
print("出力先の準備を行っています...")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {TARGET_CATALOG}.{EXPORT_SCHEMA}")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {TARGET_CATALOG}.{EXPORT_SCHEMA}.{EXPORT_VOLUME}")

OUTPUT_BASE_PATH = f"/Volumes/{TARGET_CATALOG}/{EXPORT_SCHEMA}/{EXPORT_VOLUME}"
OUTPUT_FILE_PATH = f"{OUTPUT_BASE_PATH}/{OUTPUT_FILENAME}"
print(f"出力先: {OUTPUT_FILE_PATH}")

# COMMAND ----------

# ==========================================
# 3. カタログからテーブル一覧を収集
# ==========================================
# { スキーマ名: [テーブル名, ...] } の辞書を構築
schema_tables = {}

schemas = spark.sql(f"SHOW SCHEMAS IN {TARGET_CATALOG}").collect()

for schema_row in schemas:
    schema_name = schema_row["databaseName"]
    if schema_name in SKIP_SCHEMAS:
        continue

    try:
        tables = spark.sql(f"SHOW TABLES IN {TARGET_CATALOG}.{schema_name}").collect()
    except Exception as e:
        print(f"スキーマ {schema_name} のテーブル取得をスキップ: {e}")
        continue

    table_names = sorted([
        row["tableName"] for row in tables if not row["isTemporary"]
    ])
    if table_names:
        schema_tables[schema_name] = table_names
        print(f"  {schema_name}: {len(table_names)} テーブル → {table_names}")

print(f"\n合計: {sum(len(v) for v in schema_tables.values())} テーブル")

# COMMAND ----------

# ==========================================
# 4. Excel ブック作成
# ==========================================
import pandas as pd
from io import BytesIO

buffer = BytesIO()

with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
    sheet_count = 0

    for layer in LAYER_ORDER:
        if layer not in schema_tables:
            print(f"スキーマ {layer} はカタログに存在しないためスキップ")
            continue

        # レイヤー区切りシート（空）
        separator_name = f"{layer}→"
        pd.DataFrame().to_excel(writer, sheet_name=separator_name, index=False)
        sheet_count += 1
        print(f"  シート: {separator_name} (区切り)")

        # テーブルごとにシート作成
        for table_name in schema_tables[layer]:
            full_name = f"{TARGET_CATALOG}.{layer}.{table_name}"
            try:
                sample_df = spark.sql(f"SELECT * FROM {full_name} LIMIT {SAMPLE_LIMIT}")

                if sample_df.isEmpty():
                    print(f"  シート: {table_name} → データなし、スキップ")
                    continue

                pdf = sample_df.toPandas()
                pdf.to_excel(writer, sheet_name=table_name, index=False)
                sheet_count += 1
                print(f"  シート: {table_name} ({len(pdf)} 行)")

            except Exception as e:
                print(f"  シート: {table_name} → エラー: {e}")

    # LAYER_ORDER に含まれないスキーマがあれば末尾に追加
    extra_schemas = sorted(set(schema_tables.keys()) - set(LAYER_ORDER))
    for schema_name in extra_schemas:
        separator_name = f"{schema_name}→"
        pd.DataFrame().to_excel(writer, sheet_name=separator_name, index=False)
        sheet_count += 1
        print(f"  シート: {separator_name} (区切り)")

        for table_name in schema_tables[schema_name]:
            full_name = f"{TARGET_CATALOG}.{schema_name}.{table_name}"
            try:
                sample_df = spark.sql(f"SELECT * FROM {full_name} LIMIT {SAMPLE_LIMIT}")
                if sample_df.isEmpty():
                    continue
                pdf = sample_df.toPandas()
                pdf.to_excel(writer, sheet_name=table_name, index=False)
                sheet_count += 1
                print(f"  シート: {table_name} ({len(pdf)} 行)")
            except Exception as e:
                print(f"  シート: {table_name} → エラー: {e}")

print(f"\n合計 {sheet_count} シートを作成")

# COMMAND ----------

# ==========================================
# 5. Volume に Excel を書き出し
# ==========================================
excel_bytes = buffer.getvalue()

with open(OUTPUT_FILE_PATH, "wb") as f:
    f.write(excel_bytes)

print(f"出力完了: {OUTPUT_FILE_PATH}")
print(f"ファイルサイズ: {len(excel_bytes) / 1024:.1f} KB")
print(f"\nダウンロード方法:")
print(f"  カタログ > {TARGET_CATALOG} > {EXPORT_SCHEMA} > {EXPORT_VOLUME} > {OUTPUT_FILENAME}")
