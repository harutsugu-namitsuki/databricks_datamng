# Northwind Data Lakehouse

Databricks + Unity Catalog を AWS 上に構築した、**メダリオンアーキテクチャ（Bronze / Silver / Gold）** のリファレンス実装です。サンプルDB「Northwind」を題材に、データ基盤（ETL・カタログ・IaC）からアプリケーション（購買・業務管理）まで一気通貫で扱います。

---

## 全体アーキテクチャ

```
AWS RDS PostgreSQL (private subnet)
    │ JDBC
    ▼
Databricks Compute (EC2 / customer-managed VPC)
    │ Unity Catalog + IAM
    ▼
S3 (Delta Lake)
    ├── Bronze/   生データ・追記専用・メタ列付与
    ├── Silver/   クレンジング・型変換・DQチェック済み
    ├── Gold/     集約済みビジネスマート（4種）
    └── Ops/      ログ・DQ結果・ジョブ実行履歴
            │
            ▼
   アプリ層 (FastAPI + HTML/JS) ── 購買アプリ / 業務管理アプリ
```

---

## リポジトリ構成（役割ベース）

| ディレクトリ | 役割 | 主な中身 |
|---|---|---|
| [`src/`](src/) | アプリケーションコード | FastAPI バックエンド・HTML/JS フロント・Streamlit版（[README](src/README.md)） |
| [`databricks/`](databricks/) | データ基盤コード | `notebooks/`（PySpark ETL）、`operations/`（運用補助スクリプト） |
| [`infrastructure/`](infrastructure/) | IaC | CloudFormation テンプレート（VPC / RDS / S3 / IAM / SG） |
| [`docs/`](docs/) | ドキュメント全般 | `design/`・`guides/`・`project_management/`・`operations/`・`archive/` |
| `private/` | 非公開資料 | gitignore 対象（リポジトリには含まれない） |

> リポジトリは「時期・フェーズ別」ではなく **「役割別」** で整理しています。再編の経緯と Before/After は [`proposed_folder_structure_2.md`](proposed_folder_structure_2.md) を参照。

---

## Notebook 実行順序

`databricks/notebooks/` のノートブックは以下の順で実行します。

| Notebook | 実行頻度 | 目的 |
|---|---|---|
| `00_setup_unity_catalog.py` | 一度のみ | Unity Catalog に External Location とスキーマを作成 |
| `01_load_northwind_to_rds.py` | 一度のみ | Northwind SQL（14テーブル）を GitHub から RDS へロード |
| `02_etl_bronze_ingest.py` | 日次 | JDBC で RDS → Bronze（Delta、メタ列付与） |
| `03_etl_silver_transform.py` | 日次 | クレンジング・型変換・DQチェック → Silver |
| `04_etl_gold_aggregate.py` | 日次 | 集約 → Gold マート（4種） |

---

## データソース

[pthom/northwind_psql](https://github.com/pthom/northwind_psql) の Northwind DB（14テーブル）。

- **マスタ (7):** categories, customers, employees, suppliers, shippers, products, region
- **トランザクション (2):** orders（約830件）, order_details（約2,155件）
- **構成 (5):** territories, us_states, employee_territories, customer_demographics, customer_customer_demo

---

## クイックスタート

### 1. データ基盤の構築
1. [`infrastructure/cloudformation.yaml`](infrastructure/cloudformation.yaml) をデプロイ（手順: [`docs/guides/環境構築手順書.md`](docs/guides/環境構築手順書.md)）
2. `databricks/notebooks/` を上記の順で実行（手順: [`docs/guides/実装手順書.md`](docs/guides/実装手順書.md)）

> インフラには2種類の CloudFormation テンプレートがあります。
> - `cloudformation.yaml` … **NAT Gateway あり**構成
> - `cloudformation lambda.yaml` … **NAT Gateway なし**（コスト削減版）

### 2. アプリの起動
詳細は [`src/README.md`](src/README.md) を参照。

```bash
pip install -r requirements.txt
cp .env.example .env      # RDS 接続情報を記入
cd src && uvicorn api.main:app --reload --port 8000
```

| アプリ | URL |
|---|---|
| 購買アプリ（ストア） | http://localhost:8000/static/store/login.html |
| 業務管理アプリ | http://localhost:8000/static/admin/login.html |
| API ドキュメント | http://localhost:8000/docs |

---

## 主要ドキュメント

| 文書 | 内容 |
|---|---|
| [実装手順書](docs/guides/実装手順書.md) | 5フェーズの実装ガイド（実行の正本） |
| [環境構築手順書](docs/guides/環境構築手順書.md) | CloudFormation デプロイ手順 |
| [UnityCatalog設計書](docs/design/data_platform/UnityCatalog設計書.md) | カタログのネームスペース構造 |
| [権限設計](docs/design/data_platform/権限設計.md) | IAM ロールの権限詳細（2ロール設計） |
| [テーブル設計書](docs/design/data_platform/テーブル設計書.md) | 各レイヤの Delta テーブルスキーマ |
| [要件定義書](docs/design/system/要件定義書.md) | システム要件 |

---

## セキュリティ

RDS の認証情報は **AWS Secrets Manager** に保管し、**Databricks Secret Scope** 経由で参照します。**ノートブックに認証情報をハードコードしないでください。**
