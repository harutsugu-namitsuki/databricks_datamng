# Notebook仕様書

## 1. Notebook一覧

| # | ファイル名 | 目的 | 実行順序 |
|---|-----------|------|---------|
| 0 | 00_setup_unity_catalog.py | Unity Catalog初期設定 | 最初に1回 |
| 1 | 01_load_northwind_to_rds.py | RDSへテストデータ投入 | 最初に1回 |
| 2 | 02_etl_bronze_ingest.py | Bronze層取り込み | 日次 |
| 3 | 03_etl_silver_transform.py | Silver層変換 | 日次 |
| 4 | 04_etl_gold_aggregate.py | Gold層集計 | 日次 |

---

## 2. 各Notebookの詳細

### 2.1 00_setup_unity_catalog.py

| 項目 | 内容 |
|------|------|
| **目的** | Unity Catalogの初期設定 |
| **実行タイミング** | 初回のみ |
| **入力** | なし |
| **出力** | カタログ、スキーマ、Storage Credential、External Location |

**処理内容**:
1. カタログ作成（northwind_catalog）
2. スキーマ作成（bronze, silver, gold）
3. Storage Credential作成
4. External Location作成

---

### 2.2 01_load_northwind_to_rds.py

| 項目 | 内容 |
|------|------|
| **目的** | RDSにNorthwindテストデータを投入 |
| **実行タイミング** | 初回のみ |
| **入力** | RDS接続情報 |
| **出力** | RDS上のテーブル・データ |

**処理内容**:
1. テーブル作成（DDL実行）
2. サンプルデータINSERT

---

### 2.3 02_etl_bronze_ingest.py

| 項目 | 内容 |
|------|------|
| **目的** | RDSからBronze層へデータ取り込み |
| **実行タイミング** | 日次（スケジュール実行） |
| **入力** | RDS各テーブル |
| **出力** | Bronze層Delta Lake |

**処理内容**:
1. RDSから全テーブル読み込み
2. メタデータカラム追加（_load_date等）
3. Bronze層へAppend

---

### 2.4 03_etl_silver_transform.py

| 項目 | 内容 |
|------|------|
| **目的** | Bronze→Silverの変換処理 |
| **実行タイミング** | 日次 |
| **入力** | Bronze層 |
| **出力** | Silver層 |

**処理内容**:
1. Null処理、型変換
2. データクレンジング
3. Silver層へ保存

---

### 2.5 04_etl_gold_aggregate.py

| 項目 | 内容 |
|------|------|
| **目的** | Silver→Goldの集計処理 |
| **実行タイミング** | 日次 |
| **入力** | Silver層 |
| **出力** | Gold層（マート） |

**処理内容**:
1. 集計クエリ実行
2. マートテーブル作成
3. Gold層へ保存

---

## 3. パラメータ一覧

| パラメータ | 説明 | デフォルト |
|-----------|------|-----------|
| `load_date` | 処理日付 | 当日 |
| `catalog_name` | カタログ名 | northwind_catalog |

---

## 変更履歴

| 日付 | 変更内容 |
|------|----------|
| 2026-02-09 | 初版作成 |
