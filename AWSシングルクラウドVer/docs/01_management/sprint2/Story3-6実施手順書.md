# Genie Space 構築 実施手順書（Story 3-6）

## 概要

| 項目 | 内容 |
|-----|------|
| 対象 Story | 3-6 |
| Epic | Epic 3: データ可視化・分析基盤の構築 |
| 目的 | 整備済みメタデータと Databricks AI/BI Genie を活用し、自然言語でデータに質問できるチャットスペースを構築する |
| 前提 | 実装手順書 Phase 3〜5 完了済み（UC スキーマ・データ・ETL）。Sprint 1 Story 3-1 完了済み（テーブル・カラムへの日本語コメント付与）。Story 3-2 完了済み（タグ付与）。 |

### 使用するテーブル

| テーブル | 層 | 用途 |
|---------|-----|------|
| `northwind_catalog.silver.customers` | Silver | 顧客マスタ |
| `northwind_catalog.silver.orders` | Silver | 注文ヘッダ |
| `northwind_catalog.silver.order_details` | Silver | 注文明細 |
| `northwind_catalog.silver.products` | Silver | 商品マスタ |
| `northwind_catalog.bronze.categories` | bronze | 商品カテゴリ |
| `northwind_catalog.bronze.suppliers` | bronze | 仕入先マスタ（任意） |
| `northwind_catalog.bronze.employees` | bronze | 従業員マスタ（任意） |

### 外部ファイル一覧

| ファイル | 用途 |
|---------|------|
| `notebooks_sprint2/story3-6/3-6_sample_query_01_sales_by_country.sql` | サンプルクエリ: 国別売上ランキング |
| `notebooks_sprint2/story3-6/3-6_sample_query_02_sales_by_category.sql` | サンプルクエリ: カテゴリ別売上 |
| `notebooks_sprint2/story3-6/3-6_sample_query_03_top10_customers.sql` | サンプルクエリ: 売上 TOP10 顧客 |
| `notebooks_sprint2/story3-6/3-6_sample_query_04_out_of_stock.sql` | サンプルクエリ: 在庫切れ商品一覧 |
| `notebooks_sprint2/story3-6/3-6_genie_text_instructions.txt` | Genie Space 用テキスト指示 |

---

## Phase 1: 前提条件の確認（Story 3-6）

### 目的

Genie Space を構築するための前提環境が整っていることを確認する。

### Step 1-1: 前提条件チェック

以下がすべて満たされていることを確認する。

| # | 確認項目 | 詳細 |
|---|---------|------|
| 1 | Unity Catalog | Northwind データが Unity Catalog に登録済みであること |
| 2 | ビジネスメタデータ | テーブル・カラムにコメント（説明）を付与済みであること |
| 3 | SQL Warehouse | **Pro** または **Serverless** の SQL Warehouse が起動可能であること |
| 4 | 権限（Permissions） | SQL Warehouse に対する **CAN USE** 権限、Northwind テーブルに対する **SELECT** 権限があること |
| 5 | Databricks SQL Entitlement | ワークスペースで Databricks SQL が使える状態であること |
| 6 | Partner-powered AI features | アカウント管理者がこの機能を有効にしていること |

> **注意**: Partner-powered AI features が無効だと Genie は利用できない。管理者（Admin）に確認すること。

---

## Phase 2: Genie Space の作成とテーブル追加（Story 3-6）

### 目的

Genie Space を新規作成し、分析対象の Northwind テーブルを追加する。

### Step 2-1: Genie 画面を開く

1. Databricks UI 左サイドバーの **SQL** セクションから **Genie** をクリック

### Step 2-2: 新しいスペースを作成

1. 画面右上の **New** ボタンをクリック

### Step 2-3: テーブルを選択

ダイアログで以下の手順でテーブルを追加する。

1. カタログ名（Catalog）を選択
2. スキーマ名（Schema）を選択
3. テーブル名にチェックを入れる

追加するテーブルの選定基準：

| 優先度 | テーブル名 | 層 | 内容 | 推奨 |
|--------|-----------|-----|------|------|
| 高 | `silver.customers` | Silver | 顧客マスタ | 必須 |
| 高 | `silver.orders` | Silver | 注文ヘッダ | 必須 |
| 高 | `silver.order_details` | Silver | 注文明細 | 必須 |
| 高 | `silver.products` | Silver | 商品マスタ | 必須 |
| 中 | `bronze.categories` | Bronze | 商品カテゴリ | 推奨 |
| 中 | `bronze.suppliers` | Bronze | 仕入先マスタ | 任意 |
| 低 | `bronze.employees` | Bronze | 従業員マスタ | 任意 |

> ベストプラクティスとして、最初は **5 テーブル以下** に絞ることが推奨されている。Genie Space には最大 30 テーブルまで追加可能だが、少ないほど精度が向上する。

### Step 2-4: スペースを作成

1. テーブル選択後、**Create** ボタンをクリック

### Step 2-5: クエリ提案の確認（Review query suggestions）

テーブル追加後、Genie がワークスペース内の既存クエリを分析し、Popular query suggestions を自動表示する場合がある。

1. **Data** タブに通知が表示されたら **Review** をクリック
2. 提案されたクエリを確認し、**Approve** / **Reject** / **Edit** を選択

---

## Phase 3: ナレッジストア（Knowledge Store）の構築（Story 3-6）

### 目的

テーブルメタデータ・同義語・JOIN 関係・SQL 式を定義し、Genie の回答精度を向上させる。これが最も重要なフェーズとなる。

### Step 3-1: テーブル・カラムのメタデータを確認・編集

1. Genie Space 画面で **Configure** をクリック
2. **Data** タブをクリック
3. テーブル名（例: customers）をクリック
4. テーブルの説明（Description）とカラム一覧を確認する

確認・編集ポイント：

| 確認項目 | 操作 |
|---------|------|
| テーブルの説明（Table Description） | Unity Catalog で付与した説明が表示される。Genie Space 用にさらに具体的に編集可能（元の UC メタデータは変更されない） |
| カラムの説明（Column Description） | 各カラムの説明を確認し、不足があれば鉛筆アイコンで追加 |
| 不要カラムの非表示（Hide columns） | Genie に認識させたくないカラムは目のアイコンで非表示にする |

> **Bronze テーブルのメタデータカラムは非表示にすること**: `bronze.categories`、`bronze.suppliers`、`bronze.employees` には ETL が付与したメタデータカラム（`_run_id`、`_load_date`、`_ingest_ts`、`_source_system`）が含まれる。これらはビジネス質問には不要なため、すべて非表示に設定する。
>
> **Sprint 1 Story 3-1 の成果を引き継ぐ**: Unity Catalog に付与済みの日本語コメントは、テーブル追加時に Genie Space へ自動的に取り込まれる。ここでは内容を確認し、Genie の回答精度向上のために必要な箇所のみ追記・調整する（UC のメタデータ本体には影響しない）。

Northwind 用の編集例：

| テーブル | カラム | 説明の編集例 |
|---------|--------|-------------|
| `orders` | `order_date` | 注文日。顧客が注文を確定した日付。売上分析の基準日として使用する |
| `orders` | `shipped_date` | 出荷日。商品が倉庫から出荷された日付 |
| `order_details` | `unit_price` | 注文時点の商品単価（税抜き） |
| `order_details` | `quantity` | 注文数量 |
| `order_details` | `discount` | 割引率。0.0 - 1.0 の範囲（例: 0.1 = 10%割引） |
| `products` | `units_in_stock` | 現在の在庫数 |
| `products` | `discontinued` | 販売終了フラグ。1 = 販売終了、0 = 販売中 |
| `customers` | `country` | 顧客の所在国。英語表記（例: Germany, France, USA） |

> Genie Space 内での編集は Unity Catalog のメタデータに影響しない。

### Step 3-2: カラムの同義語（Synonyms）を追加

ビジネスユーザーが使う言葉とカラム名が異なる場合に設定する。

1. **Configure** > **Data** > テーブル名をクリック
2. カラム名の横の鉛筆アイコンをクリック
3. **Synonyms** 欄にビジネス用語を入力
4. **Save** をクリック

Northwind 用の同義語設定例：

| テーブル | カラム名 | 追加する同義語 |
|---------|---------|---------------|
| `customers` | `company_name` | 会社名, 顧客名, 取引先名 |
| `customers` | `contact_name` | 担当者名, 連絡先 |
| `customers` | `country` | 国, 国名, 所在国 |
| `orders` | `order_date` | 注文日, 受注日 |
| `orders` | `shipped_date` | 出荷日, 発送日 |
| `orders` | `freight` | 送料, 運賃, 配送料 |
| `products` | `product_name` | 商品名, 製品名 |
| `products` | `unit_price` | 単価, 価格, 定価 |
| `products` | `units_in_stock` | 在庫数, 在庫, 残数 |
| `categories` | `category_name` | カテゴリ名, 分類名, 商品分類 |

### Step 3-3: プロンプトマッチング（Prompt Matching）を確認

テーブル追加時に Genie が自動的に有効化する 2 つの機能を確認する。

| 機能 | 説明 |
|------|------|
| Format Assistance | カラムの代表的な値をサンプリングし、データ形式を Genie に理解させる |
| Entity Matching | カテゴリ型カラム（国名、カテゴリ名など）の実際の値リストを Genie に提供し、入力と正確にマッチさせる |

確認手順：

1. **Configure** > **Data** > テーブル名をクリック
2. カラム名の横の鉛筆アイコンをクリック
3. **Advanced settings** をクリック
4. **Format Assistance** と **Entity Matching** の ON/OFF を確認
5. **Save**

Entity Matching を有効にすべきカラム：

| テーブル | カラム | 理由 |
|---------|--------|------|
| `customers` | `country` | 「フランス」→「France」のマッチングが必要 |
| `customers` | `city` | 都市名の表記ゆれ対応 |
| `categories` | `category_name` | 「飲料」→「Beverages」のマッチング |
| `products` | `product_name` | 商品名の部分一致対応 |
| `suppliers` | `country` | 仕入先の国名マッチング |

> Entity Matching は **文字列型（String）カラムのみ** 対応。

### Step 3-4: JOIN 関係（Join Relationships）を定義

Genie が複数テーブルにまたがる質問に正しく答えるために、テーブル間の結合条件を定義する。

1. **Configure** > **Data** タブ内の **Joins** をクリック
2. **Add** をクリック
3. Left table と Right table をドロップダウンから選択
4. Join condition を入力
5. Relationship Type を選択
6. **Save**

以下をすべて登録する：

| # | 左テーブル | 右テーブル | 結合条件 | 関係タイプ |
|---|-----------|-----------|---------|-----------|
| 1 | `orders` | `customers` | `orders.customer_id = customers.customer_id` | Many to one |
| 2 | `order_details` | `orders` | `order_details.order_id = orders.order_id` | Many to one |
| 3 | `order_details` | `products` | `order_details.product_id = products.product_id` | Many to one |
| 4 | `products` | `categories` | `products.category_id = categories.category_id` | Many to one |
| 5 | `products` | `suppliers` | `products.supplier_id = suppliers.supplier_id` | Many to one |
| 6 | `orders` | `employees` | `orders.employee_id = employees.employee_id` | Many to one |

> Unity Catalog で主キー（Primary Key）/ 外部キー（Foreign Key）を定義済みの場合、Genie が自動的に JOIN 関係を検出・保存してくれることがある（ナレッジマイニング機能）。

### Step 3-5: SQL 式（SQL Expressions）を定義

ビジネスで頻繁に使う指標（KPI）やフィルタ条件を、再利用可能な定義として登録する。

1. **Configure** > **Instructions** > **SQL Expressions** タブ
2. **Add** をクリック
3. 種類を選択: **Measure** / **Filter** / **Dimension**
4. Name、Code、Synonyms、Instructions を入力
5. **Save**

Measure（集計指標）：

| 名前 | コード | 同義語 | 指示 |
|------|--------|--------|------|
| 売上金額 | `SUM(order_details.unit_price * order_details.quantity * (1 - order_details.discount))` | 売上, 売上高, revenue, sales | 注文明細の単価 x 数量 x (1-割引率) の合計。売上を聞かれたらこの計算を使うこと |
| 注文件数 | `COUNT(DISTINCT orders.order_id)` | 注文数, order count | ユニークな注文 ID の数 |
| 平均注文金額 | `SUM(order_details.unit_price * order_details.quantity * (1 - order_details.discount)) / COUNT(DISTINCT orders.order_id)` | 平均単価, 客単価, average order value | 売上金額 / 注文件数 |

Filter（絞り込み条件）：

| 名前 | コード | 同義語 | 指示 |
|------|--------|--------|------|
| 販売中の商品 | `products.discontinued = 0` | 現行商品, active products | 販売終了していない商品のみに絞る |
| 在庫切れ | `products.units_in_stock = 0` | 欠品, out of stock | 在庫がゼロの商品 |

Dimension（分析軸）：

| 名前 | コード | 同義語 | 指示 |
|------|--------|--------|------|
| 注文年月 | `DATE_FORMAT(orders.order_date, 'yyyy-MM')` | 年月, month | 注文日を年月単位にグルーピングする際に使用 |
| 注文年 | `YEAR(orders.order_date)` | 年, year | 注文日を年単位にグルーピングする際に使用 |

---

## Phase 4: サンプル SQL クエリとテキスト指示の登録（Story 3-6）

### 目的

Genie の回答品質を向上させるために、サンプルクエリとテキスト指示を登録する。

### Step 4-1: サンプル SQL クエリを登録

1. **Configure** > **Instructions** をクリック
2. **SQL queries** タブを選択
3. **Add** をクリック
4. クエリ名（タイトル）と SQL を入力
5. **Save**

以下の SQL ファイルの内容をそれぞれ登録する：

| ファイル | タイトル |
|---------|---------|
| `notebooks_sprint2/story3-6/3-6_sample_query_01_sales_by_country.sql` | 国別の売上ランキング |
| `notebooks_sprint2/story3-6/3-6_sample_query_02_sales_by_category.sql` | 商品カテゴリ別の売上 |
| `notebooks_sprint2/story3-6/3-6_sample_query_03_top10_customers.sql` | 売上上位10社の顧客 |
| `notebooks_sprint2/story3-6/3-6_sample_query_04_out_of_stock.sql` | 在庫切れの商品一覧 |

### Step 4-2: テキスト指示を登録

1. **Configure** > **Instructions** をクリック
2. **Text** タブを選択
3. テキストボックスに指示を入力
4. **Save**

以下のファイルの内容をコピーして貼り付ける：

`notebooks_sprint2/story3-6/3-6_genie_text_instructions.txt`

> テキスト指示はグローバルに適用される内容のみに使う。特定のクエリパターンに関する指示は、サンプル SQL クエリとして登録する方が効果的。

---

## Phase 5: テストと調整（Story 3-6）

### 目的

Genie Space が正しく動作することを検証し、必要に応じて設定を調整する。

### Step 5-1: チャットでテスト

1. Genie Space 画面で **New chat** アイコンをクリック
2. 画面下部のテキスト入力欄に質問を入力
3. Enter キーで送信

### Step 5-2: テスト質問の実行

以下の質問を 1 つずつ試し、結果を確認する：

| # | テスト質問 | 期待する動作 |
|---|-----------|-------------|
| 1 | 「売上が一番多い国はどこですか?」 | 国別売上の集計結果が返る |
| 2 | 「カテゴリ別の売上を教えて」 | カテゴリ別売上とグラフが返る |
| 3 | 「売上 TOP5 の顧客は?」 | 上位 5 社の顧客名と売上金額 |
| 4 | 「在庫切れの商品はありますか?」 | 在庫ゼロの商品一覧 |
| 5 | 「ドイツの顧客一覧を見せて」 | country = Germany の顧客リスト |
| 6 | 「月別の注文件数の推移を見せて」 | 月別集計と折れ線グラフ |
| 7 | 「飲料カテゴリで一番売れている商品は?」 | Beverages カテゴリの売上 TOP 商品 |

### Step 5-3: 回答の確認方法

各回答の **Analysis** セクションを展開し、以下を確認する：

| 確認項目 | 説明 |
|---------|------|
| Understanding the question | 質問の理解が正しいか |
| Found relevant data | 適切なテーブル・カラムを使っているか |
| Referenced trusted example | 登録済みサンプルクエリを参照しているか |
| Thinking steps | 思考ステップに問題がないか |
| Show code | 生成された SQL が正しいか |

### Step 5-4: 問題があった場合の対処

| 問題 | 対処法 |
|------|--------|
| 間違ったカラムを使っている | Step 3-1 に戻ってカラムの説明を修正 |
| JOIN が正しくない | Step 3-4 に戻って JOIN 関係を確認・修正 |
| 売上の計算が違う | Step 3-5 の SQL 式（Measure）を確認 |
| 日本語の用語が認識されない | Step 3-2 に戻って同義語を追加 |
| 国名が一致しない | Step 3-3 の Entity Matching を有効化 |

### Step 5-5: フィードバックを送信

各回答の下に表示されるボタンで Genie にフィードバックを送る：

| ボタン | 用途 |
|--------|------|
| **Yes** | 正しい回答の場合。Genie がクエリパターンを学習し、Knowledge Mining として新しい SQL 式や JOIN 関係を提案する場合がある |
| **Fix it** | 間違っている場合。理由を選択して送信 |

---

## Phase 6: ユーザーへの共有（Story 3-6）

### 目的

構築した Genie Space を他のユーザーに共有する。

### Step 6-1: 権限を付与

1. Genie Space 画面右上の **Share** ボタンをクリック
2. 共有したいユーザーまたはグループを検索・追加
3. 権限レベルを選択する

| 権限レベル | 説明 |
|-----------|------|
| CAN VIEW | チャットのみ利用可能（一般ユーザー向け） |
| CAN EDIT | 設定の編集も可能 |
| CAN MANAGE | 全権限（モニタリング含む） |

### Step 6-2: 共有相手に必要な権限

共有相手にも以下が必要となる。管理者に依頼すること：

| 必要な権限 | 説明 |
|-----------|------|
| Databricks SQL Entitlement | ワークスペースで SQL 機能が使えること |
| テーブルへの SELECT 権限 | Northwind テーブルのデータを読み取れること |

> SQL Warehouse の CAN USE 権限については、Genie Space に SQL Warehouse が紐付けられていれば、Genie Space の作成者の資格情報（Credentials）が使われるため、共有相手には不要な場合がある。ただし環境によるため、エラーが出た場合は CAN USE 権限も付与する。

### Step 6-3: サンプル質問を設定（任意）

ユーザーがチャット画面を開いたときに表示されるサンプル質問を設定できる。

1. **Configure** > **Settings** > **Configuration**
2. **Sample questions** を追加

設定例：
- 「売上が一番多い国はどこですか?」
- 「カテゴリ別の売上を教えてください」
- 「在庫切れの商品はありますか?」

---

## 完成チェックリスト

| # | 項目 | 確認 |
|---|------|------|
| 1 | Genie Space が作成されている | |
| 2 | Northwind の主要テーブル（4-7 個）が追加されている | |
| 3 | テーブル・カラムの説明が日本語で充実している | |
| 4 | 主要カラムに同義語（Synonyms）が設定されている | |
| 5 | country, category_name 等に Entity Matching が有効 | |
| 6 | JOIN 関係が 4-6 個定義されている | |
| 7 | SQL 式（売上金額、注文件数など）が定義されている | |
| 8 | サンプル SQL クエリが 3-5 個登録されている | |
| 9 | テキスト指示（日本語回答、売上の定義など）が設定されている | |
| 10 | テスト質問 7 問中、5 問以上が正しく回答される | |

---

## 用語対照表

| 日本語 | 英語 | 説明 |
|--------|------|------|
| ジーニースペース | Genie Space | 自然言語チャットの空間 |
| 構成 / 設定 | Configure | スペースの設定画面 |
| データ | Data | テーブル管理タブ |
| 手順 / 指示 | Instructions | クエリ例・テキスト指示タブ |
| ナレッジストア | Knowledge Store | メタデータ・JOIN・SQL 式の総称 |
| 結合 | Joins | テーブル間の結合関係 |
| SQL式 | SQL Expressions | Measure / Filter / Dimension |
| メジャー | Measure | 集計指標（KPI） |
| フィルタ | Filter | 絞り込み条件 |
| ディメンション | Dimension | 分析軸・グルーピング項目 |
| 同義語 / シノニム | Synonyms | カラムの別名・ビジネス用語 |
| フォーマットアシスタンス | Format Assistance | 値のサンプリング機能 |
| エンティティマッチング | Entity Matching | 値の辞書マッチング機能 |
| プロンプトマッチング | Prompt Matching | 上記 2 つの総称 |
| サーバーレス SQL ウェアハウス | Serverless SQL Warehouse | コンピュート資源 |
| ユニティカタログ | Unity Catalog | データガバナンス基盤 |
| パートナー提供 AI 機能 | Partner-powered AI features | Genie 利用に必要な設定 |
