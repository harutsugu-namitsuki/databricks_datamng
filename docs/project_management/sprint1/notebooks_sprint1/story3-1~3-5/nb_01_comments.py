# Databricks notebook source
# Epic 3 / Sprint 1 - Story 3-1: テーブル・カラムコメント付与
# Step 1-2: テーブルコメント → Step 1-3: カラムコメント（各層） → Step 1-4: 確認
# 全テーブルおよび各カラムに対して、論理名や説明などのコメント（メタデータ）を付与するファイルです。
# テーブル・カラムごとのコメント文をPythonの辞書で一元的に定義しています。
# ループ処理の中でCOMMENT ON TABLEやALTER COLUMNのSQLを動的に生成・実行してメタデータを登録します。


# COMMAND ----------
# Step 1-2: テーブルコメント付与（全25テーブル）

CATALOG_NAME = "northwind_catalog"

# ── テーブルコメント定義 ──
table_comments = {
    # Bronze層（14テーブル）
    "bronze.categories":            "カテゴリマスタ（Raw）。商品を分類するカテゴリ情報。RDS PostgreSQLから日次取り込み。",
    "bronze.customers":             "顧客マスタ（Raw）。取引先企業の基本情報（社名・担当者・住所）。担当者氏名・連絡先等の個人情報を含む。RDSから日次取り込み。",
    "bronze.employees":             "従業員マスタ（Raw）。Northwind社の従業員情報（氏名・役職・連絡先）。個人情報を含む。RDSから日次取り込み。",
    "bronze.suppliers":             "仕入先マスタ（Raw）。商品の仕入先企業情報。RDSから日次取り込み。",
    "bronze.shippers":              "配送業者マスタ（Raw）。注文の配送を担当する業者情報。RDSから日次取り込み。",
    "bronze.products":              "商品マスタ（Raw）。販売商品の基本情報（商品名・価格・在庫数）。RDSから日次取り込み。",
    "bronze.region":                "地域マスタ（Raw）。米国の地域区分（Eastern, Western等）。RDSから日次取り込み。",
    "bronze.orders":                "受注データ（Raw）。顧客からの注文ヘッダ情報（注文日・配送先・運賃）。約830件。RDSから日次取り込み。",
    "bronze.order_details":         "受注明細データ（Raw）。注文ごとの商品明細（商品ID・単価・数量・割引）。約2,155件。RDSから日次取り込み。",
    "bronze.territories":           "テリトリマスタ（Raw）。営業担当エリアの定義。地域（region）に紐づく。RDSから日次取り込み。",
    "bronze.us_states":             "米国州マスタ（Raw）。米国の州名・略称・地域区分。参照用マスタ。RDSから日次取り込み。",
    "bronze.employee_territories":  "従業員テリトリ関連（Raw）。従業員とテリトリの多対多関連テーブル。RDSから日次取り込み。",
    "bronze.customer_demographics": "顧客デモグラフィクス（Raw）。顧客の属性分類定義。現在データなし。RDSから日次取り込み。",
    "bronze.customer_customer_demo":"顧客デモ関連（Raw）。顧客とデモグラフィクスの関連テーブル。現在データなし。RDSから日次取り込み。",
    # Silver層（4テーブル）
    "silver.customers":             "顧客マスタ（クレンジング済み）。文字列トリム・国名大文字化・NULL補完済み。担当者氏名・連絡先等の個人情報を含む。分析用途に適した品質。",
    "silver.orders":                "受注データ（クレンジング済み）。日付型変換・運賃NULL→0補完・配送先国名大文字化済み。",
    "silver.order_details":         "受注明細（クレンジング済み）。金額をDECIMAL変換済み。line_total（明細売上額）を計算追加。",
    "silver.products":              "商品マスタ（クレンジング済み）。商品名トリム・単価DECIMAL変換・在庫数NULL→0補完済み。",
    # Gold層（4テーブル）
    "gold.sales_by_product":        "商品別月次売上集計。商品×年月の粒度で売上額・数量・注文件数を集計したマートテーブル。",
    "gold.sales_by_customer":       "顧客別月次売上集計。顧客×年月の粒度で売上額・注文件数・平均注文額を集計したマートテーブル。",
    "gold.sales_by_category":       "カテゴリ別月次売上集計。カテゴリ×年月の粒度で売上額・数量・注文件数を集計したマートテーブル。",
    "gold.order_summary":           "日次受注サマリ。日別の明細件数・売上合計・平均明細単価を集計したマートテーブル。",
    # Ops層（3テーブル）
    "ops.job_runs":                 "ジョブ実行ログ。ETLノートブックの実行開始・終了時刻、成否ステータスを記録。",
    "ops.ingestion_log":            "テーブル別取り込みログ。Bronze層への取り込み件数・所要時間・成否を記録。",
    "ops.dq_results":               "データ品質チェック結果。DQルールごとの違反件数・閾値・判定結果（PASS/FAIL）を記録。",
}

# ── 実行 ──
for table_fqn, comment in table_comments.items():
    escaped = comment.replace("'", "\\'")
    spark.sql(f"COMMENT ON TABLE {CATALOG_NAME}.{table_fqn} IS '{escaped}'")
    print(f"  [OK] {table_fqn}")

print(f"\nテーブルコメント付与完了: {len(table_comments)} テーブル")

# COMMAND ----------
# Step 1-3: カラムコメント付与 — Bronze 層

# ── Bronze 共通メタデータカラム ──
bronze_metadata_comments = {
    "_run_id":        "ジョブ実行ID（UUID、同一バッチの識別子）",
    "_load_date":     "取り込み基準日（DATE型）",
    "_ingest_ts":     "取り込みタイムスタンプ（実行時刻）",
    "_source_system": "ソースシステム名（固定値: rds_northwind）",
}

# ── Bronze 業務カラム ──
bronze_column_comments = {
    "bronze.categories": {
        "category_id":   "カテゴリID（主キー）",
        "category_name": "カテゴリ名（例: Beverages, Seafood）",
        "description":   "カテゴリの説明文",
        "picture":       "カテゴリ画像（バイナリ）",
    },
    "bronze.customers": {
        "customer_id":   "顧客ID（主キー、5文字コード）",
        "company_name":  "取引先企業名",
        "contact_name":  "担当者名【PII】",
        "contact_title": "担当者の役職",
        "address":       "住所（通り名・番地）【PII】",
        "city":          "都市名",
        "region":        "地域・州",
        "postal_code":   "郵便番号",
        "country":       "国名",
        "phone":         "電話番号【PII】",
        "fax":           "FAX番号【PII】",
    },
    "bronze.employees": {
        "employee_id":       "従業員ID（主キー）",
        "last_name":         "姓",
        "first_name":        "名",
        "title":             "役職（例: Sales Representative）",
        "title_of_courtesy": "敬称（Mr./Ms./Dr.）",
        "birth_date":        "生年月日【PII】",
        "hire_date":         "入社日",
        "address":           "自宅住所【PII】",
        "city":              "居住都市",
        "region":            "居住地域",
        "postal_code":       "居住郵便番号",
        "country":           "居住国",
        "home_phone":        "自宅電話番号【PII】",
        "extension":         "内線番号",
        "photo":             "顔写真（バイナリ）【PII】",
        "notes":             "経歴・備考",
        "reports_to":        "上司の従業員ID（自己結合外部キー）",
        "photo_path":        "写真ファイルパス",
    },
    "bronze.suppliers": {
        "supplier_id":   "仕入先ID（主キー）",
        "company_name":  "仕入先企業名",
        "contact_name":  "担当者名",
        "contact_title": "担当者の役職",
        "address":       "住所",
        "city":          "都市名",
        "region":        "地域・州",
        "postal_code":   "郵便番号",
        "country":       "国名",
        "phone":         "電話番号",
        "fax":           "FAX番号",
        "homepage":      "ホームページURL",
    },
    "bronze.shippers": {
        "shipper_id":   "配送業者ID（主キー）",
        "company_name": "配送業者名",
        "phone":        "電話番号",
    },
    "bronze.products": {
        "product_id":        "商品ID（主キー）",
        "product_name":      "商品名",
        "supplier_id":       "仕入先ID（外部キー → suppliers）",
        "category_id":       "カテゴリID（外部キー → categories）",
        "quantity_per_unit":  "単位あたりの数量（例: 24 - 12 oz bottles）",
        "unit_price":        "単価（USD）",
        "units_in_stock":    "現在庫数",
        "units_on_order":    "発注中数量",
        "reorder_level":     "発注点（この数を下回ると要発注）",
        "discontinued":      "販売終了フラグ（1=終了）",
    },
    "bronze.region": {
        "region_id":          "地域ID（主キー）",
        "region_description": "地域名称（Eastern, Western, Northern, Southern）",
    },
    "bronze.orders": {
        "order_id":         "注文ID（主キー）",
        "customer_id":      "顧客ID（外部キー → customers）",
        "employee_id":      "担当従業員ID（外部キー → employees）",
        "order_date":       "注文日",
        "required_date":    "希望納期",
        "shipped_date":     "出荷日（NULL=未出荷）",
        "ship_via":         "配送業者ID（外部キー → shippers）",
        "freight":          "運賃（USD）",
        "ship_name":        "配送先名",
        "ship_address":     "配送先住所",
        "ship_city":        "配送先都市",
        "ship_region":      "配送先地域",
        "ship_postal_code": "配送先郵便番号",
        "ship_country":     "配送先国名",
    },
    "bronze.order_details": {
        "order_id":   "注文ID（複合主キーの一部、外部キー → orders）",
        "product_id": "商品ID（複合主キーの一部、外部キー → products）",
        "unit_price": "注文時点の単価（USD）",
        "quantity":   "注文数量",
        "discount":   "割引率（0.0〜1.0）",
    },
    "bronze.territories": {
        "territory_id":          "テリトリID（主キー）",
        "territory_description": "テリトリ名称",
        "region_id":             "地域ID（外部キー → region）",
    },
    "bronze.us_states": {
        "state_id":     "州ID（主キー）",
        "state_name":   "州名（正式名称）",
        "state_abbr":   "州略称（2文字コード）",
        "state_region": "所属地域",
    },
    "bronze.employee_territories": {
        "employee_id":  "従業員ID（複合主キーの一部、外部キー → employees）",
        "territory_id": "テリトリID（複合主キーの一部、外部キー → territories）",
    },
    "bronze.customer_demographics": {
        "customer_type_id": "顧客タイプID（主キー）",
        "customer_desc":    "顧客タイプの説明",
    },
    "bronze.customer_customer_demo": {
        "customer_id":      "顧客ID（複合主キーの一部、外部キー → customers）",
        "customer_type_id": "顧客タイプID（複合主キーの一部、外部キー → customer_demographics）",
    },
}

# ── 実行: 業務カラム ──
total = 0
for table_fqn, cols in bronze_column_comments.items():
    for col_name, comment in cols.items():
        escaped = comment.replace("'", "\\'")
        spark.sql(f"ALTER TABLE {CATALOG_NAME}.{table_fqn} ALTER COLUMN {col_name} COMMENT '{escaped}'")
    total += len(cols)
    print(f"  [OK] {table_fqn}: {len(cols)} カラム")

# ── 実行: メタデータカラム（全Bronze 14テーブル共通） ──
bronze_tables = list(bronze_column_comments.keys())
for table_fqn in bronze_tables:
    for col_name, comment in bronze_metadata_comments.items():
        escaped = comment.replace("'", "\\'")
        spark.sql(f"ALTER TABLE {CATALOG_NAME}.{table_fqn} ALTER COLUMN {col_name} COMMENT '{escaped}'")
    total += len(bronze_metadata_comments)

print(f"\nBronze層カラムコメント付与完了: {total} カラム")

# COMMAND ----------
# Step 1-3: カラムコメント付与 — Silver 層

silver_column_comments = {
    "silver.customers": {
        "customer_id":   "顧客ID（主キー、5文字コード）",
        "company_name":  "取引先企業名（トリム済み）",
        "contact_name":  "担当者名（トリム済み）【PII】",
        "contact_title": "担当者の役職",
        "address":       "住所【PII】",
        "city":          "都市名（トリム済み）",
        "region":        "地域・州（NULL→N/Aに補完済み）",
        "postal_code":   "郵便番号（NULL→空文字に補完済み）",
        "country":       "国名（大文字化・トリム済み）",
        "phone":         "電話番号【PII】",
        "fax":           "FAX番号【PII】",
    },
    "silver.orders": {
        "order_id":         "注文ID（主キー）",
        "customer_id":      "顧客ID（外部キー → customers）",
        "employee_id":      "担当従業員ID（外部キー → employees）",
        "order_date":       "注文日（DATE型に変換済み）",
        "required_date":    "希望納期（DATE型に変換済み）",
        "shipped_date":     "出荷日（DATE型に変換済み、NULL=未出荷）",
        "ship_via":         "配送業者ID（外部キー → shippers）",
        "freight":          "運賃（USD、NULL→0.0に補完済み）",
        "ship_name":        "配送先名",
        "ship_address":     "配送先住所",
        "ship_city":        "配送先都市",
        "ship_region":      "配送先地域",
        "ship_postal_code": "配送先郵便番号",
        "ship_country":     "配送先国名（大文字化済み）",
    },
    "silver.order_details": {
        "order_id":   "注文ID（複合主キーの一部）",
        "product_id": "商品ID（複合主キーの一部）",
        "unit_price": "注文時点の単価（DECIMAL(10,2)に変換済み）",
        "quantity":   "注文数量",
        "discount":   "割引率（DECIMAL(4,2)に変換済み）",
        "line_total": "明細売上額（unit_price × quantity × (1 - discount)、計算カラム）",
    },
    "silver.products": {
        "product_id":       "商品ID（主キー）",
        "product_name":     "商品名（トリム済み）",
        "supplier_id":      "仕入先ID（外部キー → suppliers）",
        "category_id":      "カテゴリID（外部キー → categories）",
        "quantity_per_unit": "単位あたりの数量",
        "unit_price":       "単価（DECIMAL(10,2)に変換済み）",
        "units_in_stock":   "現在庫数（NULL→0に補完済み）",
        "units_on_order":   "発注中数量（NULL→0に補完済み）",
        "reorder_level":    "発注点（NULL→0に補完済み）",
        "discontinued":     "販売終了フラグ",
    },
}

total = 0
for table_fqn, cols in silver_column_comments.items():
    for col_name, comment in cols.items():
        escaped = comment.replace("'", "\\'")
        spark.sql(f"ALTER TABLE {CATALOG_NAME}.{table_fqn} ALTER COLUMN {col_name} COMMENT '{escaped}'")
    total += len(cols)
    print(f"  [OK] {table_fqn}: {len(cols)} カラム")

print(f"\nSilver層カラムコメント付与完了: {total} カラム")

# COMMAND ----------
# Step 1-3: カラムコメント付与 — Gold 層

gold_column_comments = {
    "gold.sales_by_product": {
        "product_id":     "商品ID",
        "product_name":   "商品名",
        "order_year":     "注文年",
        "order_month":    "注文月",
        "total_sales":    "売上合計額（USD）",
        "total_quantity": "販売数量合計",
        "order_count":    "注文件数",
    },
    "gold.sales_by_customer": {
        "customer_id":     "顧客ID",
        "company_name":    "取引先企業名",
        "country":         "国名",
        "order_year":      "注文年",
        "order_month":     "注文月",
        "total_sales":     "売上合計額（USD）",
        "order_count":     "注文件数",
        "avg_order_value": "平均注文額（USD）",
    },
    "gold.sales_by_category": {
        "category_id":    "カテゴリID",
        "category_name":  "カテゴリ名",
        "order_year":     "注文年",
        "order_month":    "注文月",
        "total_sales":    "売上合計額（USD）",
        "total_quantity": "販売数量合計",
        "order_count":    "注文件数",
    },
    "gold.order_summary": {
        "order_date":     "注文日",
        "line_count":     "明細件数",
        "total_sales":    "売上合計額（USD）",
        "avg_line_value": "平均明細単価（USD）",
    },
}

total = 0
for table_fqn, cols in gold_column_comments.items():
    for col_name, comment in cols.items():
        escaped = comment.replace("'", "\\'")
        spark.sql(f"ALTER TABLE {CATALOG_NAME}.{table_fqn} ALTER COLUMN {col_name} COMMENT '{escaped}'")
    total += len(cols)
    print(f"  [OK] {table_fqn}: {len(cols)} カラム")

print(f"\nGold層カラムコメント付与完了: {total} カラム")

# COMMAND ----------
# Step 1-3: カラムコメント付与 — Ops 層

ops_column_comments = {
    "ops.job_runs": {
        "run_id":        "ジョブ実行ID（UUID）",
        "job_name":      "ジョブ名（ノートブックファイル名）",
        "start_time":    "実行開始時刻",
        "end_time":      "実行終了時刻",
        "status":        "実行ステータス（SUCCESS/FAILURE）",
        "executed_by":   "実行ユーザー",
        "notebook_path": "実行ノートブックのパス",
    },
    "ops.ingestion_log": {
        "run_id":       "ジョブ実行ID（UUID、job_runsと結合可能）",
        "table_name":   "取り込み対象テーブル名",
        "row_count":    "取り込み件数",
        "duration_sec": "取り込み所要時間（秒）",
        "load_date":    "取り込み基準日",
        "status":       "取り込みステータス",
    },
    "ops.dq_results": {
        "run_id":     "ジョブ実行ID（UUID）",
        "rule_name":  "DQルール名（例: null_check_company_name）",
        "table_name": "チェック対象テーブル名",
        "fail_count": "ルール違反件数",
        "threshold":  "許容閾値",
        "result":     "判定結果（PASS/FAIL）",
    },
}

total = 0
for table_fqn, cols in ops_column_comments.items():
    for col_name, comment in cols.items():
        escaped = comment.replace("'", "\\'")
        spark.sql(f"ALTER TABLE {CATALOG_NAME}.{table_fqn} ALTER COLUMN {col_name} COMMENT '{escaped}'")
    total += len(cols)
    print(f"  [OK] {table_fqn}: {len(cols)} カラム")

print(f"\nOps層カラムコメント付与完了: {total} カラム")

# COMMAND ----------
# Step 1-4: 付与結果の確認

print("=" * 70)
print("テーブルコメント一覧")
print("=" * 70)

for schema in ["bronze", "silver", "gold", "ops"]:
    tables = spark.sql(f"SHOW TABLES IN {CATALOG_NAME}.{schema}").collect()
    for t in tables:
        table_fqn = f"{CATALOG_NAME}.{schema}.{t.tableName}"
        desc = spark.sql(f"DESCRIBE TABLE EXTENDED {table_fqn}").collect()
        comment_row = [r for r in desc if r.col_name == "Comment"]
        comment = comment_row[0].data_type if comment_row and comment_row[0].data_type else "(なし)"
        print(f"  {schema}.{t.tableName}: {comment}")

print("\n" + "=" * 70)
print("カラムコメント確認（サンプル: bronze.employees）")
print("=" * 70)
spark.sql(f"DESCRIBE TABLE {CATALOG_NAME}.bronze.employees").show(truncate=False)
