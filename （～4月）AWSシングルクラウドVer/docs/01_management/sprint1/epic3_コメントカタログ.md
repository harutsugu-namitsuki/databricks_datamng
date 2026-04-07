# テーブル・カラム コメントカタログ（Epic 3 / Story 3-1）

Unity Catalog 上の全テーブル・全カラムに付与する日本語コメントの定義一覧。
本カタログの内容を `COMMENT ON TABLE` / `ALTER TABLE ... ALTER COLUMN ... COMMENT` で適用する。

---

## 凡例

- **【PII】** … 個人情報を含むカラム
- **（主キー）** … テーブルの主キー
- **（外部キー → xxx）** … 参照先テーブル

---

## 1. Bronze 層（14テーブル）

### 共通メタデータカラム（全14テーブル共通）

| カラム名 | コメント |
|---------|---------|
| `_run_id` | ジョブ実行ID（UUID、同一バッチの識別子） |
| `_load_date` | 取り込み基準日（DATE型） |
| `_ingest_ts` | 取り込みタイムスタンプ（実行時刻） |
| `_source_system` | ソースシステム名（固定値: rds_northwind） |

---

### 1-1. `bronze.categories`

**テーブルコメント:** カテゴリマスタ（Raw）。商品を分類するカテゴリ情報。RDS PostgreSQLから日次取り込み。

| カラム名 | コメント |
|---------|---------|
| `category_id` | カテゴリID（主キー） |
| `category_name` | カテゴリ名（例: Beverages, Seafood） |
| `description` | カテゴリの説明文 |
| `picture` | カテゴリ画像（バイナリ） |

---

### 1-2. `bronze.customers`

**テーブルコメント:** 顧客マスタ（Raw）。取引先企業の基本情報（社名・担当者・住所）。担当者氏名・連絡先等の個人情報を含む。RDSから日次取り込み。

| カラム名 | コメント |
|---------|---------|
| `customer_id` | 顧客ID（主キー、5文字コード） |
| `company_name` | 取引先企業名 |
| `contact_name` | 担当者名【PII】 |
| `contact_title` | 担当者の役職 |
| `address` | 住所（通り名・番地）【PII】 |
| `city` | 都市名 |
| `region` | 地域・州 |
| `postal_code` | 郵便番号 |
| `country` | 国名 |
| `phone` | 電話番号【PII】 |
| `fax` | FAX番号【PII】 |

---

### 1-3. `bronze.employees`

**テーブルコメント:** 従業員マスタ（Raw）。Northwind社の従業員情報（氏名・役職・連絡先）。個人情報を含む。RDSから日次取り込み。

| カラム名 | コメント |
|---------|---------|
| `employee_id` | 従業員ID（主キー） |
| `last_name` | 姓 |
| `first_name` | 名 |
| `title` | 役職（例: Sales Representative） |
| `title_of_courtesy` | 敬称（Mr./Ms./Dr.） |
| `birth_date` | 生年月日【PII】 |
| `hire_date` | 入社日 |
| `address` | 自宅住所【PII】 |
| `city` | 居住都市 |
| `region` | 居住地域 |
| `postal_code` | 居住郵便番号 |
| `country` | 居住国 |
| `home_phone` | 自宅電話番号【PII】 |
| `extension` | 内線番号 |
| `photo` | 顔写真（バイナリ）【PII】 |
| `notes` | 経歴・備考 |
| `reports_to` | 上司の従業員ID（自己結合外部キー） |
| `photo_path` | 写真ファイルパス |

---

### 1-4. `bronze.suppliers`

**テーブルコメント:** 仕入先マスタ（Raw）。商品の仕入先企業情報。RDSから日次取り込み。

| カラム名 | コメント |
|---------|---------|
| `supplier_id` | 仕入先ID（主キー） |
| `company_name` | 仕入先企業名 |
| `contact_name` | 担当者名 |
| `contact_title` | 担当者の役職 |
| `address` | 住所 |
| `city` | 都市名 |
| `region` | 地域・州 |
| `postal_code` | 郵便番号 |
| `country` | 国名 |
| `phone` | 電話番号 |
| `fax` | FAX番号 |
| `homepage` | ホームページURL |

---

### 1-5. `bronze.shippers`

**テーブルコメント:** 配送業者マスタ（Raw）。注文の配送を担当する業者情報。RDSから日次取り込み。

| カラム名 | コメント |
|---------|---------|
| `shipper_id` | 配送業者ID（主キー） |
| `company_name` | 配送業者名 |
| `phone` | 電話番号 |

---

### 1-6. `bronze.products`

**テーブルコメント:** 商品マスタ（Raw）。販売商品の基本情報（商品名・価格・在庫数）。RDSから日次取り込み。

| カラム名 | コメント |
|---------|---------|
| `product_id` | 商品ID（主キー） |
| `product_name` | 商品名 |
| `supplier_id` | 仕入先ID（外部キー → suppliers） |
| `category_id` | カテゴリID（外部キー → categories） |
| `quantity_per_unit` | 単位あたりの数量（例: 24 - 12 oz bottles） |
| `unit_price` | 単価（USD） |
| `units_in_stock` | 現在庫数 |
| `units_on_order` | 発注中数量 |
| `reorder_level` | 発注点（この数を下回ると要発注） |
| `discontinued` | 販売終了フラグ（1=終了） |

---

### 1-7. `bronze.region`

**テーブルコメント:** 地域マスタ（Raw）。米国の地域区分（Eastern, Western等）。RDSから日次取り込み。

| カラム名 | コメント |
|---------|---------|
| `region_id` | 地域ID（主キー） |
| `region_description` | 地域名称（Eastern, Western, Northern, Southern） |

---

### 1-8. `bronze.orders`

**テーブルコメント:** 受注データ（Raw）。顧客からの注文ヘッダ情報（注文日・配送先・運賃）。約830件。RDSから日次取り込み。

| カラム名 | コメント |
|---------|---------|
| `order_id` | 注文ID（主キー） |
| `customer_id` | 顧客ID（外部キー → customers） |
| `employee_id` | 担当従業員ID（外部キー → employees） |
| `order_date` | 注文日 |
| `required_date` | 希望納期 |
| `shipped_date` | 出荷日（NULL=未出荷） |
| `ship_via` | 配送業者ID（外部キー → shippers） |
| `freight` | 運賃（USD） |
| `ship_name` | 配送先名 |
| `ship_address` | 配送先住所 |
| `ship_city` | 配送先都市 |
| `ship_region` | 配送先地域 |
| `ship_postal_code` | 配送先郵便番号 |
| `ship_country` | 配送先国名 |

---

### 1-9. `bronze.order_details`

**テーブルコメント:** 受注明細データ（Raw）。注文ごとの商品明細（商品ID・単価・数量・割引）。約2,155件。RDSから日次取り込み。

| カラム名 | コメント |
|---------|---------|
| `order_id` | 注文ID（複合主キーの一部、外部キー → orders） |
| `product_id` | 商品ID（複合主キーの一部、外部キー → products） |
| `unit_price` | 注文時点の単価（USD） |
| `quantity` | 注文数量 |
| `discount` | 割引率（0.0〜1.0） |

---

### 1-10. `bronze.territories`

**テーブルコメント:** テリトリマスタ（Raw）。営業担当エリアの定義。地域（region）に紐づく。RDSから日次取り込み。

| カラム名 | コメント |
|---------|---------|
| `territory_id` | テリトリID（主キー） |
| `territory_description` | テリトリ名称 |
| `region_id` | 地域ID（外部キー → region） |

---

### 1-11. `bronze.us_states`

**テーブルコメント:** 米国州マスタ（Raw）。米国の州名・略称・地域区分。参照用マスタ。RDSから日次取り込み。

| カラム名 | コメント |
|---------|---------|
| `state_id` | 州ID（主キー） |
| `state_name` | 州名（正式名称） |
| `state_abbr` | 州略称（2文字コード） |
| `state_region` | 所属地域 |

---

### 1-12. `bronze.employee_territories`

**テーブルコメント:** 従業員テリトリ関連（Raw）。従業員とテリトリの多対多関連テーブル。RDSから日次取り込み。

| カラム名 | コメント |
|---------|---------|
| `employee_id` | 従業員ID（複合主キーの一部、外部キー → employees） |
| `territory_id` | テリトリID（複合主キーの一部、外部キー → territories） |

---

### 1-13. `bronze.customer_demographics`

**テーブルコメント:** 顧客デモグラフィクス（Raw）。顧客の属性分類定義。現在データなし。RDSから日次取り込み。

| カラム名 | コメント |
|---------|---------|
| `customer_type_id` | 顧客タイプID（主キー） |
| `customer_desc` | 顧客タイプの説明 |

---

### 1-14. `bronze.customer_customer_demo`

**テーブルコメント:** 顧客デモ関連（Raw）。顧客とデモグラフィクスの関連テーブル。現在データなし。RDSから日次取り込み。

| カラム名 | コメント |
|---------|---------|
| `customer_id` | 顧客ID（複合主キーの一部、外部キー → customers） |
| `customer_type_id` | 顧客タイプID（複合主キーの一部、外部キー → customer_demographics） |

---

## 2. Silver 層（4テーブル）

### 2-1. `silver.customers`

**テーブルコメント:** 顧客マスタ（クレンジング済み）。文字列トリム・国名大文字化・NULL補完済み。担当者氏名・連絡先等の個人情報を含む。分析用途に適した品質。

| カラム名 | コメント |
|---------|---------|
| `customer_id` | 顧客ID（主キー、5文字コード） |
| `company_name` | 取引先企業名（トリム済み） |
| `contact_name` | 担当者名（トリム済み）【PII】 |
| `contact_title` | 担当者の役職 |
| `address` | 住所【PII】 |
| `city` | 都市名（トリム済み） |
| `region` | 地域・州（NULL→'N/A'に補完済み） |
| `postal_code` | 郵便番号（NULL→空文字に補完済み） |
| `country` | 国名（大文字化・トリム済み） |
| `phone` | 電話番号【PII】 |
| `fax` | FAX番号【PII】 |

---

### 2-2. `silver.orders`

**テーブルコメント:** 受注データ（クレンジング済み）。日付型変換・運賃NULL→0補完・配送先国名大文字化済み。

| カラム名 | コメント |
|---------|---------|
| `order_id` | 注文ID（主キー） |
| `customer_id` | 顧客ID（外部キー → customers） |
| `employee_id` | 担当従業員ID（外部キー → employees） |
| `order_date` | 注文日（DATE型に変換済み） |
| `required_date` | 希望納期（DATE型に変換済み） |
| `shipped_date` | 出荷日（DATE型に変換済み、NULL=未出荷） |
| `ship_via` | 配送業者ID（外部キー → shippers） |
| `freight` | 運賃（USD、NULL→0.0に補完済み） |
| `ship_name` | 配送先名 |
| `ship_address` | 配送先住所 |
| `ship_city` | 配送先都市 |
| `ship_region` | 配送先地域 |
| `ship_postal_code` | 配送先郵便番号 |
| `ship_country` | 配送先国名（大文字化済み） |

---

### 2-3. `silver.order_details`

**テーブルコメント:** 受注明細（クレンジング済み）。金額をDECIMAL変換済み。line_total（明細売上額）を計算追加。

| カラム名 | コメント |
|---------|---------|
| `order_id` | 注文ID（複合主キーの一部） |
| `product_id` | 商品ID（複合主キーの一部） |
| `unit_price` | 注文時点の単価（DECIMAL(10,2)に変換済み） |
| `quantity` | 注文数量 |
| `discount` | 割引率（DECIMAL(4,2)に変換済み） |
| `line_total` | 明細売上額（unit_price × quantity × (1 - discount)、計算カラム） |

---

### 2-4. `silver.products`

**テーブルコメント:** 商品マスタ（クレンジング済み）。商品名トリム・単価DECIMAL変換・在庫数NULL→0補完済み。

| カラム名 | コメント |
|---------|---------|
| `product_id` | 商品ID（主キー） |
| `product_name` | 商品名（トリム済み） |
| `supplier_id` | 仕入先ID（外部キー → suppliers） |
| `category_id` | カテゴリID（外部キー → categories） |
| `quantity_per_unit` | 単位あたりの数量 |
| `unit_price` | 単価（DECIMAL(10,2)に変換済み） |
| `units_in_stock` | 現在庫数（NULL→0に補完済み） |
| `units_on_order` | 発注中数量（NULL→0に補完済み） |
| `reorder_level` | 発注点（NULL→0に補完済み） |
| `discontinued` | 販売終了フラグ |

---

## 3. Gold 層（4テーブル）

### 3-1. `gold.sales_by_product`

**テーブルコメント:** 商品別月次売上集計。商品×年月の粒度で売上額・数量・注文件数を集計したマートテーブル。

| カラム名 | コメント |
|---------|---------|
| `product_id` | 商品ID |
| `product_name` | 商品名 |
| `order_year` | 注文年 |
| `order_month` | 注文月 |
| `total_sales` | 売上合計額（USD） |
| `total_quantity` | 販売数量合計 |
| `order_count` | 注文件数 |

---

### 3-2. `gold.sales_by_customer`

**テーブルコメント:** 顧客別月次売上集計。顧客×年月の粒度で売上額・注文件数・平均注文額を集計したマートテーブル。

| カラム名 | コメント |
|---------|---------|
| `customer_id` | 顧客ID |
| `company_name` | 取引先企業名 |
| `country` | 国名 |
| `order_year` | 注文年 |
| `order_month` | 注文月 |
| `total_sales` | 売上合計額（USD） |
| `order_count` | 注文件数 |
| `avg_order_value` | 平均注文額（USD） |

---

### 3-3. `gold.sales_by_category`

**テーブルコメント:** カテゴリ別月次売上集計。カテゴリ×年月の粒度で売上額・数量・注文件数を集計したマートテーブル。

| カラム名 | コメント |
|---------|---------|
| `category_id` | カテゴリID |
| `category_name` | カテゴリ名 |
| `order_year` | 注文年 |
| `order_month` | 注文月 |
| `total_sales` | 売上合計額（USD） |
| `total_quantity` | 販売数量合計 |
| `order_count` | 注文件数 |

---

### 3-4. `gold.order_summary`

**テーブルコメント:** 日次受注サマリ。日別の明細件数・売上合計・平均明細単価を集計したマートテーブル。

| カラム名 | コメント |
|---------|---------|
| `order_date` | 注文日 |
| `line_count` | 明細件数 |
| `total_sales` | 売上合計額（USD） |
| `avg_line_value` | 平均明細単価（USD） |

---

## 4. Ops 層（3テーブル）

### 4-1. `ops.job_runs`

**テーブルコメント:** ジョブ実行ログ。ETLノートブックの実行開始・終了時刻、成否ステータスを記録。

| カラム名 | コメント |
|---------|---------|
| `run_id` | ジョブ実行ID（UUID） |
| `job_name` | ジョブ名（ノートブックファイル名） |
| `start_time` | 実行開始時刻 |
| `end_time` | 実行終了時刻 |
| `status` | 実行ステータス（SUCCESS/FAILURE） |
| `executed_by` | 実行ユーザー |
| `notebook_path` | 実行ノートブックのパス |

---

### 4-2. `ops.ingestion_log`

**テーブルコメント:** テーブル別取り込みログ。Bronze層への取り込み件数・所要時間・成否を記録。

| カラム名 | コメント |
|---------|---------|
| `run_id` | ジョブ実行ID（UUID、job_runsと結合可能） |
| `table_name` | 取り込み対象テーブル名 |
| `row_count` | 取り込み件数 |
| `duration_sec` | 取り込み所要時間（秒） |
| `load_date` | 取り込み基準日 |
| `status` | 取り込みステータス |

---

### 4-3. `ops.dq_results`

**テーブルコメント:** データ品質チェック結果。DQルールごとの違反件数・閾値・判定結果（PASS/FAIL）を記録。

| カラム名 | コメント |
|---------|---------|
| `run_id` | ジョブ実行ID（UUID） |
| `rule_name` | DQルール名（例: null_check_company_name） |
| `table_name` | チェック対象テーブル名 |
| `fail_count` | ルール違反件数 |
| `threshold` | 許容閾値 |
| `result` | 判定結果（PASS/FAIL） |
