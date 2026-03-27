# Northwind データレイクハウス プロジェクト（AWSシングルクラウド版）

## 概要

Unity Catalog を活用したデータガバナンス基盤の構築プロジェクトです。
メダリオンアーキテクチャ（Bronze/Silver/Gold）によるETLパイプラインを **AWS単一クラウド** 上に実装します。

**【現在の開発アプローチ】**
AWSとDatabricksのインフラ基盤構築が概ね完了したため、現在は細かいパイプライン・機能実装などを、**1人アジャイル（スプリント運用もどき）**でイテレーティブに進めています。

> **設計思想**: すべてのリソースをAWS上に集約し、クロスクラウド通信コスト・管理オーバーヘッドを排除する。

> **参照**: [AWSを使用したDatabricksの環境構築 (Flect)](https://cloud.flect.co.jp/entry/2024/10/07/103341)

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
Databricks Control Plane (SaaS)
    ↓ クラスタ管理 (ワークスペースロール)
AWS Databricks (Unity Catalog — Customer-managed VPC)
    ↓ IAM Role (カタログロール)
AWS S3 (Bronze/Silver/Gold/Ops — Delta Lake)

AWS RDS (Northwind — Private Subnet)
    ↑ JDBC（VPC内通信）
AWS Databricks Compute (EC2)
```

### IAMロール構成（2ロール）

| ロール | 信頼先 (Principal) | 用途 |
|-------|-------------------|------|
| **カタログロール** | `arn:aws:iam::414351767826:role/unity-catalog-prod-UCMasterRole-...` | Unity Catalog → S3 メタデータ管理 |
| **ワークスペースロール** | `arn:aws:iam::414351767826:root` + `ec2.amazonaws.com` | Databricks → EC2 クラスタ管理 |

---

## ドキュメント構成

```
AWSシングルクラウドVer/
├── README.md（本ファイル）
├── docs/
│   ├── 01_management/                          ← プロジェクト管理
│   │   ├── 00_sprint_backlog.md
│   │   ├── 00_sprint_backlog_import.csv
│   │   ├── sprint1/                            ← Sprint1 の成果物（実施手順書など）
│   │   ├── sprint2/                            ← Sprint2 の成果物
│   │   ├── sprint3/                            ← Sprint3 の成果物
│   │   ├── sprint4/                            ← Sprint4 の成果物
│   │   ├── 実施手順書_作成規約.md
│   │   └── 検討フォルダ/                        ← 振り返り・検討メモ
│   │
│   ├── 02_design/                              ← 設計ドキュメント
│   │   ├── 01_基本設計・要件定義/
│   │   │   ├── 要件定義書.md
│   │   │   ├── アーキ図（論理アーキテクチャ）.md
│   │   │   ├── システム構成図.md
│   │   │   ├── システム構成図の要素一覧.md
│   │   │   ├── データフロー図.md
│   │   │   ├── システムフロー図.md
│   │   │   └── コスト比較.md
│   │   ├── 02_インフラ・ガバナンス設計/
│   │   │   ├── UnityCatalog設計書.md
│   │   │   ├── 権限設計.md
│   │   │   ├── 運用設計.md
│   │   │   └── CI_CD_IaC設計書.md
│   │   ├── 03_データエンジニアリング設計/
│   │   │   ├── テーブル設計書.md
│   │   │   ├── データ配置設計.md
│   │   │   ├── メダリオンアーキテクチャ設計書.md
│   │   │   └── northwind.sql（データソース）
│   │   ├── 04_データサイエンス・BI設計/
│   │   │   ├── ダッシュボード設計書.md
│   │   │   ├── データディスカバリ設計.md
│   │   │   └── 機械学習モデル運用要件.md
│   │   └── 05_アプリ統合設計/
│   │       └── E2Eアプリ連携設計書.md
│   │
│   ├── 03_development/                         ← 開発ドキュメント
│   │   ├── 00_初期環境構築手順_インフラ/
│   │   │   ├── 実装手順書.md                    ← 実施順序ガイド
│   │   │   ├── 環境構築手順書.md
│   │   │   ├── CloudFormation更新手順_UI編.md
│   │   │   ├── cloudformation.yaml
│   │   │   ├── Notebook仕様書.md
│   │   │   └── notebooks/
│   │   │       ├── 00_setup_unity_catalog.py
│   │   │       ├── 01_load_northwind_to_rds.py
│   │   │       ├── 02_etl_bronze_ingest.py
│   │   │       ├── 03_etl_silver_transform.py
│   │   │       └── 04_etl_gold_aggregate.py
│   │   ├── 01_機能実装マニュアル/
│   │   │   ├── XX_パイプライン開発手順.md
│   │   │   ├── XX_BIダッシュボード作成手順.md
│   │   │   └── XX_CI_CDデプロイ自動化手順.md
│   │   └── 02_テスト・検証/
│   │       └── テスト計画書.md
│   │
│   └── 04_operation/                           ← 運用（サンプルデータ出力等）
│       ├── 99_export_sample_excel.py
│       └── サンプルデータ統合_202603211807.xlsx
│
├── 運用ドキュメント/                             ← 運用ドキュメント（準備中）
└── old/                                        ← 旧版・バックアップ
```

---

## クイックスタート

**→ `docs/03_development/00_初期環境構築手順_インフラ/実装手順書.md` を参照してください。**

実施順序：
```
Phase 0: Databricks アカウント作成 + Account ID 取得
  └→ Phase 1: CloudFormation デプロイ (IAMロール2種 + VPC + S3 + RDS)
       └→ Phase 2: Cloud Resources登録 → ワークスペース作成 → Storage Credential + Secrets
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
| 認証 (カタログ) | IAM Role (UCMasterRole信頼) |
| 認証 (ワークスペース) | IAM Role (クロスアカウント) |
| ネットワーク | Customer-managed VPC + S3 VPCエンドポイント |
| 監視 | CloudWatch + SNS |
| 秘匿情報管理 | AWS Secrets Manager / Databricks Secret Scope |

---

## マルチクラウド版との比較

| 項目 | マルチクラウドVer | 本バージョン |
|------|------------------|-------------|
| Databricks | Azure Databricks | **AWS Databricks** |
| データレイク | Azure ADLS Gen2 | **AWS S3** |
| RDS接続 | インターネット経由 | **VPC内通信（Private Subnet）** |
| 認証 | Managed Identity | **IAM Role x2（カタログ/ワークスペース）** |
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
>
> - `docs/02_design/01_基本設計・要件定義/要件定義書.md` — テーブル一覧
> - `docs/02_design/03_データエンジニアリング設計/テーブル設計書.md` — Bronze層テーブル一覧
> - `docs/03_development/00_初期環境構築手順_インフラ/Notebook仕様書.md` — 対象テーブル表
> - `docs/03_development/00_初期環境構築手順_インフラ/notebooks/01_load_northwind_to_rds.py` — DDL/INSERT
> - `docs/03_development/00_初期環境構築手順_インフラ/notebooks/02_etl_bronze_ingest.py` — source_tables
> - `docs/03_development/02_テスト・検証/テスト計画書.md` — 期待件数

---

## 変更履歴

| 日付 | 変更内容 |
|------|----------|
| 2026-03-08 | 初版作成（マルチクラウド→シングルクラウドに設計変更） |
| 2026-03-08 | 開発ドキュメント追加、pthom/northwind_psql 採用（14テーブル） |
| 2026-03-09 | Flectブログ参照版として再作成。IAMロール2種、SG要件準拠、VPCエンドポイント追加 |
| 2026-03-20 | フォルダ再構築：`設計ドキュメント/`・`開発ドキュメント/` → `docs/` 配下に分類体系化 |
| 2026-03-22 | README.md をフォルダ再構築後の実態に合わせて全面更新 |
