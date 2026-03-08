# Northwind データレイクハウス プロジェクト（AWSシングルクラウド版）

## 概要

Unity Catalog を活用したデータガバナンス基盤の構築プロジェクトです。
メダリオンアーキテクチャ（Bronze/Silver/Gold）によるETLパイプラインを **AWS単一クラウド** 上に実装します。

> **設計思想**: すべてのリソースをAWS上に集約し、クロスクラウド通信コスト・管理オーバーヘッドを排除する。

---

## アーキテクチャ

```
AWS RDS (Northwind)
    ↓ JDBC（VPC内通信）
AWS Databricks (Unity Catalog)
    ↓ IAM Role (Instance Profile)
AWS S3 (Bronze/Silver/Gold — Delta Lake)
```

---

## ドキュメント構成

```
AWSシングルクラウドVer/
├── README.md
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
│   └── コスト比較.md
├── 開発ドキュメント/          （今後追加）
├── 運用ドキュメント/          （今後追加）
└── old/                       （旧版）
```

---

## クイックスタート

### 1. AWS環境構築
```bash
# CloudFormation でVPC + RDS + S3作成
aws cloudformation create-stack \
  --stack-name northwind-lakehouse \
  --template-body file://cloudformation.yaml
```

### 2. Databricks設定
→ `開発ドキュメント/環境構築手順書.md` 参照（今後追加）

### 3. ETL実行
```
00_setup_unity_catalog.py → 01_load_northwind_to_rds.py → 02〜04
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
| RDS接続 | インターネット経由 | **VPC内通信** |
| 認証 | Managed Identity | **IAM Role** |
| コスト | 高（クロスクラウド通信） | **低（AWS内完結）** |

---

## 変更履歴

| 日付 | 変更内容 |
|------|----------|
| 2026-03-08 | 初版作成（マルチクラウド→シングルクラウドに設計変更） |
