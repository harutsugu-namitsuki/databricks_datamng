# Notebook仕様書（AWSシングルクラウド版）

## 1. Notebook一覧

| # | ファイル名 | 目的 | 実行順序 |
|---|-----------|------|---------| 
| 0 | 00_setup_unity_catalog.py | Unity Catalog初期設定（S3 External Location） | 最初に1回 |
| 1 | 01_load_northwind_to_rds.py | RDSへNorthwind全データ投入 | 最初に1回 |
| 2 | 02_etl_bronze_ingest.py | Bronze層取り込み（全14テーブル） | 日次 |
| 3 | 03_etl_silver_transform.py | Silver層変換 + DQチェック | 日次 |
| 4 | 04_etl_gold_aggregate.py | Gold層集計（4マート） | 日次 |

---

## 2. データソース

| 項目 | 値 |
|------|-----|
| リポジトリ | [pthom/northwind_psql](https://github.com/pthom/northwind_psql) |
| SQLファイル | [northwind.sql](https://raw.githubusercontent.com/pthom/northwind_psql/master/northwind.sql) |
| 形式 | PostgreSQL ネイティブ（変換不要） |
| テーブル数 | 14テーブル（フルデータ） |

---

## 3. 各Notebookの詳細

### 3.1 00_setup_unity_catalog.py

| 項目 | 内容 |
|------|------|
| **目的** | Unity Catalogの初期設定（S3ベース） |
| **実行タイミング** | 初回のみ |
| **入力** | なし |
| **出力** | External Location (ext_bronze/silver/gold/ops), Schema (bronze/silver/gold/ops) |
| **前提** | Storage Credential、カタログをUIで作成済み |

---

### 3.2 01_load_northwind_to_rds.py

| 項目 | 内容 |
|------|------|
| **目的** | RDSにNorthwind全データを投入 |
| **実行タイミング** | 初回のみ |
| **入力** | northwind.sql（GitHubから自動ダウンロード） |
| **出力** | RDS上の14テーブル + 全データ |
| **認証** | Databricks Secret Scope (`northwind-secrets`) |

**対象テーブル（14テーブル）**:

| テーブル | 件数 |
|---------|------|
| categories | 8 |
| customers | 91 |
| employees | 9 |
| suppliers | 29 |
| shippers | 3 |
| products | 77 |
| orders | 830 |
| order_details | 2,155 |
| region | 4 |
| territories | 53 |
| us_states | 51 |
| employee_territories | 49 |
| customer_demographics | 0 |
| customer_customer_demo | 0 |

---

### 3.3 02_etl_bronze_ingest.py

| 項目 | 内容 |
|------|------|
| **目的** | RDSからBronze層へ全テーブルを取り込み |
| **実行タイミング** | 日次（スケジュール実行） |
| **入力** | RDS 全14テーブル |
| **出力** | Bronze層 Delta Lake（S3） + ops.ingestion_log |
| **メタデータ** | _run_id, _load_date, _ingest_ts, _source_system |

---

### 3.4 03_etl_silver_transform.py

| 項目 | 内容 |
|------|------|
| **目的** | Bronze→Silverの変換 + DQチェック |
| **実行タイミング** | 日次 |
| **入力** | Bronze層（当日分） |
| **出力** | Silver層 (customers, orders, order_details, products) + ops.dq_results |

**クレンジングルール**:

| ルール | 対象 | 処理 |
|--------|------|------|
| Null→デフォルト | region, postal_code, freight | N/A, "", 0.0 |
| 型変換 | order_date, unit_price | date, decimal |
| 文字列正規化 | country | Trim + 大文字化 |
| 計算カラム | order_details | line_total 追加 |

---

### 3.5 04_etl_gold_aggregate.py

| 項目 | 内容 |
|------|------|
| **目的** | Silver→Gold集計 |
| **実行タイミング** | 日次 |
| **入力** | Silver層 |
| **出力** | Gold層 (4マート) + ops.job_runs |

**マートテーブル**:

| テーブル | 粒度 |
|---------|------|
| gold.sales_by_product | 商品×月 |
| gold.sales_by_customer | 顧客×月 |
| gold.sales_by_category | カテゴリ×月 |
| gold.order_summary | 日次 |

---

## 4. パラメータ一覧

| パラメータ | 説明 | デフォルト |
|-----------|------|-----------| 
| `S3_BUCKET_NAME` | S3バケット名 | `lake-northwind-<account-id>` |
| `CATALOG_NAME` | カタログ名 | `northwind_catalog` |
| `load_date` | 処理日付 | 当日 |

---

## 変更履歴

| 日付 | 変更内容 |
|------|----------|
| 2026-03-08 | シングルクラウド版として作成（pthom/northwind_psql フルデータ対応、14テーブル） |
