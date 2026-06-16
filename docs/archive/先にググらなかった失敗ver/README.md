# Northwind データレイクハウス プロジェクト（AWSシングルクラウド版）

## 概要

Unity Catalog を活用したデータガバナンス基盤の構築プロジェクトです。
メダリオンアーキテクチャ（Bronze/Silver/Gold）によるETLパイプラインを **AWS単一クラウド** 上に実装します。

> **設計思想**: すべてのリソースをAWS上に集約し、クロスクラウド通信コスト・管理オーバーヘッドを排除する。

---

## データソース

| 項目 | 値 |
|------|-----|
| リポジトリ | [pthom/northwind_psql](https://github.com/pthom/northwind_psql) |
| SQLファイル | [northwind.sql](https://raw.githubusercontent.com/pthom/northwind_psql/master/northwind.sql) |
| 形式 | PostgreSQL ネイティブ（変換不要） |
| テーブル数 | **14テーブル**（フルデータ） |
| ローカルコピー | `設計ドキュメント/northwind.sql` |

---

## アーキテクチャ

```
AWS RDS (Northwind — Private Subnet)
    ↓ JDBC（VPC内通信）
AWS Databricks (Unity Catalog)
    ↓ IAM Role (Instance Profile)
AWS S3 (Bronze/Silver/Gold/Ops — Delta Lake)
```

---

## ドキュメント構成

```
AWSシングルクラウドVer/
├── README.md（本ファイル）
├── 設計ドキュメント/
│   ├── 要件定義書.md
│   ├── アーキ図（論理アーキテクチャ）.md
│   ├── システム構成図.md
│   ├── システム構成図の要素一覧.md
│   ├── データフロー図.md
│   ├── システムフロー図.md
│   ├── テーブル設計書.md
│   ├── UnityCatalog設計書.md
│   ├── データ配置設計.md
│   ├── 権限設計.md
│   ├── 運用設計.md
│   ├── コスト比較.md
│   └── northwind.sql（データソース）
├── 開発ドキュメント/
│   ├── 実装手順書.md            ← 実施順序ガイド
│   ├── 環境構築手順書.md
│   ├── cloudformation.yaml
│   ├── Notebook仕様書.md
│   ├── テスト計画書.md
│   └── notebooks/
│       ├── 00_setup_unity_catalog.py
│       ├── 01_load_northwind_to_rds.py
│       ├── 02_etl_bronze_ingest.py
│       ├── 03_etl_silver_transform.py
│       └── 04_etl_gold_aggregate.py
└── old/（旧版）
```

---

## クイックスタート

**→ `開発ドキュメント/実装手順書.md` を参照してください。**

実施順序：
```
Phase 1: CloudFormation デプロイ
  └→ Phase 2: Databricks設定 + Storage Credential + Secrets
       └→ Phase 3: 00_setup_unity_catalog.py
            └→ Phase 4: 01_load_northwind_to_rds.py
                 └→ Phase 5: 02 → 03 → 04 (日次)
```

---

## 技術スタック

| カテゴリ | 技術 |
|---------|------|
| Databricks | AWS Databricks (Premium) |
| ストレージ | AWS S3 (Delta Lake) |
| ソースDB | AWS RDS PostgreSQL |
| データフォーマット | Delta Lake |
| ガバナンス | Unity Catalog |
| 認証 | IAM Role (Instance Profile) |
| 監視 | CloudWatch + SNS |
| 秘匿情報管理 | AWS Secrets Manager / Databricks Secret Scope |

---

## マルチクラウド版との比較

| 項目 | マルチクラウドVer | 本バージョン |
|------|------------------|-------------|
| Databricks | Azure Databricks | **AWS Databricks** |
| データレイク | Azure ADLS Gen2 | **AWS S3** |
| RDS接続 | インターネット経由 | **VPC内通信（Private Subnet）** |
| 認証 | Managed Identity | **IAM Role** |
| Northwindデータ | 手書き簡易サンプル | **pthom/northwind_psql フルデータ** |
| テーブル数 | 7テーブル | **14テーブル** |
| コスト | 高（クロスクラウド通信） | **低（AWS内完結）** |

---

## 今後の課題

### Northwindテーブル拡張

現在の pthom/northwind_psql は **14テーブル** を提供しているが、
オリジナルの Northwind データベースには **約19テーブル** が存在する。
今後、差分の **約5テーブル** を追加投入する予定。

追加候補テーブル:
- 追加の業務テーブル（ビュー含む）
- 上記のうち、Bronze/Silver/Gold 各層への反映も必要

> この対応時には、以下のドキュメントも合わせて更新すること:
> - `設計ドキュメント/要件定義書.md` — テーブル一覧
> - `設計ドキュメント/テーブル設計書.md` — Bronze層テーブル一覧
> - `開発ドキュメント/Notebook仕様書.md` — 対象テーブル表
> - `開発ドキュメント/notebooks/01_load_northwind_to_rds.py` — DDL/INSERT
> - `開発ドキュメント/notebooks/02_etl_bronze_ingest.py` — source_tables
> - `開発ドキュメント/テスト計画書.md` — 期待件数

---

## 変更履歴

| 日付 | 変更内容 |
|------|----------|
| 2026-03-08 | 初版作成（マルチクラウド→シングルクラウドに設計変更） |
| 2026-03-08 | 開発ドキュメント追加、pthom/northwind_psql 採用（14テーブル） |
