# ==========================================
# 1. 初期設定と出力先ボリュームの準備
# ==========================================
TARGET_CATALOG = "northwind_catalog"
EXPORT_SCHEMA = "exports"
EXPORT_VOLUME = "sample_data"
SAMPLE_LIMIT = 10

# 出力用のスキーマとVolumeを自動作成（既に存在する場合はスキップ）
print("出力先の準備を行っています...")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {TARGET_CATALOG}.{EXPORT_SCHEMA}")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {TARGET_CATALOG}.{EXPORT_SCHEMA}.{EXPORT_VOLUME}")

# 出力先のVolumeの絶対パス
OUTPUT_BASE_PATH = f"/Volumes/{TARGET_CATALOG}/{EXPORT_SCHEMA}/{EXPORT_VOLUME}"
print(f"出力先パス: {OUTPUT_BASE_PATH}\n" + "="*40)


# ==========================================
# 2. サンプルデータの抽出とCSV出力処理
# ==========================================
# カタログ内の全スキーマを取得
schemas = spark.sql(f"SHOW SCHEMAS IN {TARGET_CATALOG}").collect()

for schema_row in schemas:
    schema_name = schema_row['databaseName']
    
    # システムスキーマや、今回出力用に作成したスキーマは抽出対象から除外
    if schema_name in ['information_schema', EXPORT_SCHEMA]:
        continue

    # スキーマ内の全テーブルを取得
    try:
        tables = spark.sql(f"SHOW TABLES IN {TARGET_CATALOG}.{schema_name}").collect()
    except Exception as e:
        print(f"スキーマ {schema_name} のテーブル取得をスキップしました: {e}")
        continue

    for table_row in tables:
        table_name = table_row['tableName']
        is_temporary = table_row['isTemporary']
        
        # 一時ビューなどはスキップ
        if is_temporary:
            continue
            
        full_table_name = f"{TARGET_CATALOG}.{schema_name}.{table_name}"
        
        try:
            print(f"抽出中: {full_table_name}")
            # 指定件数（10件）のサンプルデータを取得
            sample_df = spark.sql(f"SELECT * FROM {full_table_name} LIMIT {SAMPLE_LIMIT}")
            
            # データが空の場合は出力しない
            if sample_df.isEmpty():
                print(f"  -> データが空のためスキップしました。")
                continue

            # CSVファイルとしての出力先パスを組み立てる（スキーマ名/テーブル名 のフォルダ構成）
            output_path = f"{OUTPUT_BASE_PATH}/{schema_name}/{table_name}"
            
            # CSV形式で保存（ヘッダー付き、既存ファイルは上書き）
            sample_df.write \
                .format("csv") \
                .option("header", "true") \
                .mode("overwrite") \
                .save(output_path)
                
            print(f"  -> 出力完了: {output_path}")
            
        except Exception as e:
            print(f"  -> テーブル {full_table_name} の処理中にエラーが発生しました: {e}")

print("="*40)
print(f"すべてのサンプルデータの出力が完了しました！")
print(f"Databricks左側メニューの「カタログ (Catalog)」> {TARGET_CATALOG} > {EXPORT_SCHEMA} > {EXPORT_VOLUME} から抽出したCSVファイルを確認・ダウンロードできます。")