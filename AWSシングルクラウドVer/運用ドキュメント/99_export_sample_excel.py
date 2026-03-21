# Databricks notebook source
# ==========================================
# サンプルデータ Excel 一括出力
# ==========================================
# Unity Catalog 上の全テーブルからサンプルデータを取得し、
# レイヤー別シート構成の Excel ブックとして Volume に出力する。
#
# 出力イメージ:
#   シート「gold→」(空) → 「order_summary (gold)」→ ...
#   シート「silver→」(空) → 「customers (silver)」→ ...
#   シート「bronze→」(空) → 「categories (bronze)」→ ...
#   シート「ops→」(空)   → 「dq_results (ops)」→ ...
#
# 100行以下のテーブルは全量出力、それ以外はサンプル10行

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
FULL_EXPORT_THRESHOLD = 100  # この行数以下なら全量出力

# レイヤー表示順（gold → silver → bronze → ops）
LAYER_ORDER = ["gold", "silver", "bronze", "ops"]

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
from openpyxl.utils import get_column_letter
from io import BytesIO

buffer = BytesIO()

with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
    sheet_count = 0

    def write_layer(layer_name):
        """指定レイヤーの区切りシート + テーブルシートを書き出す"""
        nonlocal sheet_count

        if layer_name not in schema_tables:
            print(f"スキーマ {layer_name} はカタログに存在しないためスキップ")
            return

        # レイヤー区切りシート（空）
        separator_name = f"{layer_name}→"
        pd.DataFrame().to_excel(writer, sheet_name=separator_name, index=False)
        sheet_count += 1
        print(f"  シート: {separator_name} (区切り)")

        # テーブルごとにシート作成
        for table_name in schema_tables[layer_name]:
            full_name = f"{TARGET_CATALOG}.{layer_name}.{table_name}"
            sheet_name = f"{table_name} ({layer_name})"

            try:
                # まず全量の行数を確認
                total_count = spark.sql(f"SELECT COUNT(*) AS cnt FROM {full_name}").collect()[0]["cnt"]

                if total_count == 0:
                    print(f"  シート: {sheet_name} → データなし、スキップ")
                    continue

                # 100行以下なら全量、それ以外はサンプル
                if total_count <= FULL_EXPORT_THRESHOLD:
                    sample_df = spark.sql(f"SELECT * FROM {full_name}")
                    mode = "全量"
                else:
                    sample_df = spark.sql(f"SELECT * FROM {full_name} LIMIT {SAMPLE_LIMIT}")
                    mode = f"サンプル{SAMPLE_LIMIT}"

                pdf = sample_df.toPandas()
                pdf.to_excel(writer, sheet_name=sheet_name, index=False)
                sheet_count += 1
                print(f"  シート: {sheet_name} ({len(pdf)}/{total_count} 行, {mode})")

            except Exception as e:
                print(f"  シート: {sheet_name} → エラー: {e}")

    # LAYER_ORDER 順にシート出力
    for layer in LAYER_ORDER:
        write_layer(layer)

    # LAYER_ORDER に含まれないスキーマがあれば末尾に追加
    extra_schemas = sorted(set(schema_tables.keys()) - set(LAYER_ORDER))
    for schema_name in extra_schemas:
        write_layer(schema_name)

    # --- 列幅の自動調整 ---
    for ws in writer.book.worksheets:
        for col_idx, col_cells in enumerate(ws.columns, 1):
            max_length = 0
            for cell in col_cells:
                if cell.value is not None:
                    cell_len = len(str(cell.value))
                    if cell_len > max_length:
                        max_length = cell_len
            # 余白を少し足す（日本語は幅が広いので係数調整）
            adjusted_width = min(max_length + 3, 50)
            ws.column_dimensions[get_column_letter(col_idx)].width = adjusted_width

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
