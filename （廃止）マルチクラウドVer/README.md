# Northwind データレイクハウス プロジェクト

## 概要

Unity Catalog を活用したデータガバナンス基盤の構築プロジェクトです。
メダリオンアーキテクチャ（Bronze/Silver/Gold）によるETLパイプラインを実装します。

---

## アーキテクチャ

```
AWS RDS (Northwind) 
    ↓ JDBC
Azure Databricks (Unity Catalog)
    ↓ Managed Identity
Azure ADLS Gen2 (Bronze/Silver/Gold)
```

---

## ドキュメント構成

```
databricks_datamng/
├── 設計ドキュメント/
│   └── 移行前/
│       ├── 要件定義書.md
│       ├── システム構成図.md
│       ├── アーキ図（論理アーキテクチャ）.md
│       ├── データフロー.md
│       ├── システムフロー図.md
│       ├── システム構成図の要素一覧.md
│       ├── テーブル設計書.md
│       └── UnityCatalog設計書.md
├── 開発ドキュメント/
│   ├── 環境構築手順書.md
│   ├── azure-adls-setup-guide.md
│   ├── テスト計画書.md
│   ├── Notebook仕様書.md
│   ├── cloudformation-premigration.yaml
│   └── notebooks/
│       ├── 00_setup_unity_catalog.py
│       ├── 01_load_northwind_to_rds.py
│       ├── 02_etl_bronze_ingest.py
│       ├── 03_etl_silver_transform.py
│       └── 04_etl_gold_aggregate.py
└── 運用ドキュメント/
    ├── 運用手順書.md
    ├── トラブルシューティングガイド.md
    └── 用語集.md
```

---

## クイックスタート

### 1. AWS環境構築
```bash
# CloudFormation でRDS作成
aws cloudformation create-stack ...
```

### 2. Azure環境構築
→ `開発ドキュメント/azure-adls-setup-guide.md` 参照

### 3. Databricks設定
→ `開発ドキュメント/環境構築手順書.md` 参照

### 4. ETL実行
```
00_setup_unity_catalog.py → 01_load_northwind_to_rds.py → 02〜04
```

---

## 技術スタック

| カテゴリ | 技術 |
|---------|------|
| Databricks | Azure Databricks (Premium) |
| ストレージ | Azure ADLS Gen2 |
| ソースDB | AWS RDS PostgreSQL |
| データフォーマット | Delta Lake |
| ガバナンス | Unity Catalog |

---

## 変更履歴

| 日付 | 変更内容 |
|------|----------|
| 2026-02-09 | 初版作成 |
