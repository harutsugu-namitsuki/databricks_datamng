# データディスカバリ・AIメタデータ管理 実施手順書（Epic 3 / Sprint 1）

## 概要

| 項目 | 内容 |
|-----|------|
| 対象 Story | 3-1, 3-2, 3-3, 3-4, 3-5 |
| Epic | Epic 3: データディスカバリとAIメタデータ管理 |
| 目的 | データカタログを整備し、データを探しやすく・理解しやすくする |
| 前提 | Phase 5（ETLパイプライン）完了済み。全テーブルが Bronze/Silver/Gold/Ops に存在すること |

### 関連ドキュメント

| ドキュメント | 用途 |
|------------|------|
| [epic3_コメントカタログ.md](epic3_コメントカタログ.md) | 全テーブル・カラムのコメント定義一覧（Phase 1 で参照） |
| [epic3_タグ分類体系.md](epic3_タグ分類体系.md) | タグのタクソノミー設計・マッピング表（Phase 2 で参照） |

### 前提条件チェック

Databricks ノートブック上で以下を実行し、全テーブルが存在することを確認する。

`nb_00_prerequisite_check.py`

全テーブルが `[OK]` であることを確認してから次に進む。

---

## Phase 1: テーブル・カラムコメント付与（Story 3-1）

### 目的

Unity Catalog 上の全テーブル・主要カラムに対して、業務上の意味を示すコメント（日本語）を手動で付与する。

### Step 1-1: コメント定義の確認

[epic3_コメントカタログ.md](epic3_コメントカタログ.md) を開き、全テーブル・カラムのコメント内容を確認する。

### Step 1-2: テーブルコメント付与（全25テーブル）

以下のコードを Databricks ノートブックで実行する。

`nb_01_comments.py`

### Step 1-3: カラムコメント付与（全カラム）

以下のコードを Databricks ノートブックで実行する。コードが長いため、層ごとにセルを分けて実行することを推奨する。

#### Bronze / Silver / Gold / Ops 層カラムコメント

`nb_01_comments.py`（セル2〜5：各層ごとに分かれています）

### Step 1-4: 付与結果の確認

`nb_01_comments.py`（セル6：確認）

---

## Phase 2: タグ付与（Story 3-2）

### 目的

全テーブルにタグを付与し、タグによるデータ検索・分類を可能にする。

### Step 2-1: タグ設計の確認

[epic3_タグ分類体系.md](epic3_タグ分類体系.md) を開き、タグキー定義とマッピング表を確認する。

### Step 2-2: テーブルタグ付与（全25テーブル）

`nb_02_tags.py`

### Step 2-3: PII カラムタグ付与

`nb_02_tags.py`

### Step 2-4: 付与結果の確認

`nb_02_tags.py`

---

## Phase 3: 検索・探索検証（Story 3-3）

### 目的

タグ検索・キーワード検索を行い、「売上に関するテーブルを探す」「個人情報を含むテーブルを探す」が容易にできることを確認する。

### Step 3-1: テストケース1 — 売上に関するテーブルを探す

**成功条件**: `domain` タグが `sales` のテーブルが **8件**（`bronze.orders`, `bronze.order_details`, `silver.orders`, `silver.order_details`, `gold.sales_by_product`, `gold.sales_by_customer`, `gold.sales_by_category`, `gold.order_summary`）抽出されること。

`nb_03_search_verify.py`

### Step 3-2: テストケース2 — 個人情報を含むテーブルを探す

**成功条件**: 
- **テーブルレベル**: `pii` タグが `true` のテーブルが **3件**（`bronze.customers`, `bronze.employees`, `silver.customers`）抽出されること。
- **カラムレベル**: `pii` タグが `true` のカラムが **12件**（上記3テーブルの対象カラム各4件）抽出されること。

`nb_03_search_verify.py`

### Step 3-3: テストケース3 — Gold 層の集計テーブルを探す

**成功条件**: `data_type` タグが `aggregate` のテーブルが **4件**（`gold.sales_by_product`, `gold.sales_by_customer`, `gold.sales_by_category`, `gold.order_summary`）抽出されること。

`nb_03_search_verify.py`

### Step 3-4: テストケース4 — キーワード「売上」でコメント検索

**成功条件**: コメントに「売上」を含むテーブルが **5件**（`silver.order_details`, `gold.sales_by_product`, `gold.sales_by_customer`, `gold.sales_by_category`, `gold.order_summary`）抽出されること。

`nb_03_search_verify.py`

### Step 3-5: テストケース5 — 複合条件（layer:gold AND domain:sales）

**成功条件**: `layer` タグが `gold` 且つ `domain` タグが `sales` のテーブルが **4件**（`gold.sales_by_product`, `gold.sales_by_customer`, `gold.sales_by_category`, `gold.order_summary`）抽出されること。

`nb_03_search_verify.py`

### Step 3-6: Catalog Explorer UI での手動検証

> **💡 UI検証の目的:** 一般ユーザーが画面（UI）を通じて、**「迷わず探せる利便性（4）」** と **「安全に扱える注意喚起（5）」** の恩恵を受けられるかを証明するため。

以下の操作を Databricks UI 上で実施し、スクリーンショットを取得する。

1. **Catalog Explorer** を開く（左メニュー → Catalog）
2. `northwind_catalog` を選択
3. 検索バーに「売上」と入力 → 該当テーブル（**5件**: `silver.order_details`, `gold.sales_by_product`, `gold.sales_by_customer`, `gold.sales_by_category`, `gold.order_summary`）が表示されることを確認 → **スクリーンショット取得**
4. **タグでの絞り込み（リファレンス検索）**
   - 以下の手順でタグを使って検索する：
     - 左メニューの **Search**（🔍アイコン）をクリックする。
     - 検索バーに **`sales`**（タグのValue）と入力して検索を実行する。
     - 画面左側のフィルターパネルの「Tags」項目を展開し、**`domain : sales`** にチェックを入れる。
   - 該当テーブル（**8件**: `bronze.orders`, `bronze.order_details`, `silver.orders`, `silver.order_details`, `gold.sales_by_product`, `gold.sales_by_customer`, `gold.sales_by_category`, `gold.order_summary`）が一覧表示されることを確認 → **スクリーンショット取得**
5. `bronze.employees` を開き、カラム（`birth_date`, `address`, `home_phone`, `photo` 等）にPIIタグが表示されていることを確認 → **スクリーンショット取得**

---

## Phase 4: AI 自動生成・品質比較（Story 3-4）

### 目的

Databricks の AI 機能を活用してコメント・タグを自動生成させ、手動作成との品質を比較する。

### Step 4-1: 手動コメントのスナップショット取得

Phase 1 で付与したコメントを `ops.metadata_comparison_manual` テーブルに保存する。

`nb_04_metadata_snapshot.py`

### Step 4-2: AI Assist によるコメント自動生成

以下の手順で Databricks AI Assist を使用してコメントを自動生成する。

> **前提**: ワークスペースの Admin Settings → AI Assist が有効であること

1. **Catalog Explorer** で対象テーブルを開く（例: `bronze.orders`）
2. テーブルの Overview 画面で **AI generated** ボタン（またはペンアイコン）をクリック
3. AI Assist が提案するコメントを確認する（**まだ Accept しない**）
4. 提案されたコメントをテキストファイルにコピーして記録する
5. 以下の主要テーブルについて繰り返す:
   - `bronze.orders`
   - `bronze.employees`
   - `bronze.products`
   - `silver.order_details`
   - `gold.sales_by_product`
   - `gold.sales_by_customer`

> **注意**: AI Assist が利用不可の場合は、Step 4-2 をスキップし、Step 4-3 の比較は「AI機能が未有効のため比較不可」と記録する。

### Step 4-3: 比較評価

以下の6観点で、手動コメントと AI 生成コメントを比較評価する。

| # | 評価項目 | 説明 | 配点 |
|---|---------|------|------|
| 1 | 正確性 | テーブル/カラムの実際の用途を正しく説明しているか | 5点 |
| 2 | 業務理解度 | Northwind の業務文脈を反映しているか | 5点 |
| 3 | 日本語品質 | 自然な日本語で書かれているか | 3点 |
| 4 | 情報量 | 適切な詳細度で記述されているか（過少/過多でないか） | 3点 |
| 5 | PII 注記 | 個人情報を含むカラムに適切な注記があるか | 2点 |
| 6 | FK 注記 | リレーションシップが明記されているか | 2点 |

#### 比較結果記録テンプレート

以下のテンプレートを使って、テーブルごとの比較結果を記録する。

```
### テーブル: bronze.orders

| 項目 | 手動 | AI生成 |
|------|------|--------|
| テーブルコメント | 受注データ（Raw）。顧客からの注文ヘッダ情報（注文日・配送先・運賃）。約830件。RDSから日次取り込み。 | （AI生成のコメントを記入） |
| 正確性 (5点) | /5 | /5 |
| 業務理解度 (5点) | /5 | /5 |
| 日本語品質 (3点) | /3 | /3 |
| 情報量 (3点) | /3 | /3 |
| PII注記 (2点) | /2 | /2 |
| FK注記 (2点) | /2 | /2 |
| 合計 (20点) | /20 | /20 |
| 所感 | | |
```

### Step 4-4: 比較総括の記録

全テーブルの比較を終えたら、以下をまとめる:

- 手動 vs AI の平均スコア
- AI が優れていた点
- AI が劣っていた点
- 今後の運用における AI 活用方針（手動をベースにし AI でドラフト → 人間がレビュー、等）

---

## Phase 5: リネージ可視化（Story 3-5）

### 目的

現時点のリネージ（Bronze → Silver → Gold）を Unity Catalog のリネージ機能で可視化し、スクリーンショットを記録する。

### 前提条件

- **Single User (Assigned) クラスター**でパイプラインを実行済みであること（Shared クラスターではリネージが記録されない）
- **Databricks Premium プラン以上**であること（`system.access.table_lineage` の利用に必要）

### 期待されるリネージパス

```
RDS PostgreSQL（外部）
  ↓ JDBC
bronze.categories ──────────────────────────────────→ gold.sales_by_category
bronze.customers ──→ silver.customers ──→ gold.sales_by_customer
bronze.orders ────→ silver.orders ────→ gold.sales_by_product
                                       → gold.sales_by_customer
                                       → gold.sales_by_category
                                       → gold.order_summary
bronze.order_details → silver.order_details → gold.sales_by_product
                                             → gold.sales_by_customer
                                             → gold.sales_by_category
                                             → gold.order_summary
bronze.products ──→ silver.products ──→ gold.sales_by_product
                                       → gold.sales_by_category
```

> **注意**: `bronze.categories` は Silver 層を経由せず、Gold 集計（`04_etl_gold_aggregate.py` 行93）で直接参照されている。

### Step 5-1: リネージのプログラム的確認

`nb_05_lineage_check.py`

### Step 5-2: 期待リネージパスの検証

`nb_05_lineage_check.py`

### Step 5-3: Catalog Explorer UI でのリネージ確認・スクリーンショット取得

以下の操作を Databricks UI 上で実施し、スクリーンショットを取得する。

1. **Catalog Explorer** → `northwind_catalog` → `gold` → `sales_by_product` を開く
2. **Lineage** タブをクリック
3. リネージグラフが表示される → **スクリーンショット取得**
4. 以下のテーブルについても同様に Lineage タブを確認・スクリーンショット取得:
   - `gold.sales_by_customer`
   - `gold.sales_by_category`（← `bronze.categories` からの直接パスが見えるか確認）
   - `gold.order_summary`
5. **カラムレベルリネージ**: `gold.sales_by_product` の `total_sales` カラムをクリックし、`silver.order_details.line_total` からの派生が表示されることを確認 → **スクリーンショット取得**

---

## 注意事項

| 項目 | 内容 |
|------|------|
| DBR バージョン | `ALTER TABLE SET TAGS` 構文は Databricks Runtime **13.3 以上**が必要 |
| information_schema | `system.information_schema.table_tags` / `column_tags` は DBR 13.3+ で利用可能 |
| table_lineage | `system.access.table_lineage` は **Premium プラン以上**でのみ利用可能 |
| AI Assist | ワークスペース設定（Admin Settings → AI Assist）で有効化されている必要がある |
| クラスターモード | リネージは **Single User (Assigned)** クラスターでの実行時のみ記録される |
| コメントのエスケープ | 日本語コメント内にシングルクォート `'` が含まれる場合、`\'` にエスケープが必要 |

---

## 実施順序まとめ

```
Phase 1（Story 3-1）: コメント付与
  └── Step 1-2 → 1-3 → 1-4
        ↓
Phase 2（Story 3-2）: タグ付与
  └── Step 2-2 → 2-3 → 2-4
        ↓
Phase 3（Story 3-3）: 検索検証
  └── Step 3-1 → 3-2 → 3-3 → 3-4 → 3-5 → 3-6（UI）
        ↓
Phase 4（Story 3-4）: AI 比較
  └── Step 4-1 → 4-2（UI）→ 4-3 → 4-4
        ↓
Phase 5（Story 3-5）: リネージ検証
  └── Step 5-1 → 5-2 → 5-3（UI）
```

---

## 変更履歴

| 日付 | 内容 |
|------|------|
| 2026-03-22 | 初版作成。Story 3-1〜3-5 を Sprint 1 に組み込み |
