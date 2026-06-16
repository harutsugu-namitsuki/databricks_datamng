# Databricksデータマネジメントプロジェクト フォルダ構成再設計提案書

本資料は、現在の「時期（フェーズ）」をベースとしたフォルダ構成を、直感的かつメンテナンス性の高い「役割（コード・ドキュメント・インフラ）」ベースのフォルダ構成に再整理するための提案書です。

> [!NOTE]
> ユーザー様からの指示に基づき、本提案に伴うファイル・フォルダの実際の移動や修正は一切実施しておりません。

---

## 1. 現状の構成（Before）における課題

1. **時期（フェーズ）によるトップレベルの分断**
   - `（～4月）AWSシングルクラウドVer` と `（5月～）APP開発` という時期別のフォルダがトップレベルに並列配置されており、それぞれに個別の `docs` や `README.md`、`src` が散在しています。これにより、プロジェクトの全体像が把握しづらくなっています。
2. **ドキュメント配下へのコード・IaCの混在**
   - `docs/03_development/...` の下に `cloudformation.yaml` や `notebooks/` (Databricks用PySparkコード) が、`docs/04_operation` の下にサンプルデータ出力用Pythonスクリプトが混在しており、「ドキュメント」と「実行コード」の境界線が曖昧です。
3. **リポジトリ全体の俯瞰用 README の欠如**
   - リポジトリのルート直後に時期別フォルダが配置されているため、初見でどのファイルから参照すべきかが分かりづらくなっています。
4. **参考資料（skills/）のトップレベル配置**
   - プロジェクトコードとは直接関係のないClaude向け参考スキル群がトップレベルに置かれており、ディレクトリの認知的負荷を高めています。

---

## 2. 提案するフォルダ構成（After）の設計方針

1. **「コード (src/databricks/infrastructure)」と「ドキュメント (docs/)」の完全分離**
   - 時期別という括りを排除し、ファイルの性質（アプリケーションコード、データ処理コード、IaC、設計・運用ドキュメント）ごとに一元管理します。
2. **Databricks関連コードの集約**
   - Databricks上で動かすNotebookや、運用スクリプトなどのデータ系コードを `databricks/` ディレクトリに集約します。
3. **設計ドキュメントのカテゴリ別統合**
   - AWSシングルクラウドのデータプラットフォーム設計とAPP開発のシステム・画面設計を `docs/design/` の中でカテゴリ分けして整理し、システム全体のアーキテクチャを一箇所で俯瞰できるようにします。
4. **トップレベル README の新設**
   - リポジトリのトップレベルに総合 `README.md` を作成し、プロジェクト概要や新しいフォルダ構造の案内を記述します。

---

## 3. Before ➔ After フォルダ構成マッピング表

| 分類 | Before（移行前） | After（移行後） | 移行の目的・意図 |
| :--- | :--- | :--- | :--- |
| **ルート** | (なし) | `[NEW] /README.md` | リポジトリ全体の目的、構成、起動手順を俯瞰する総合ドキュメントの配置。 |
| **ルート** | `CLAUDE.md` | `CLAUDE.md` | 新しいフォルダパスに合わせて記述を更新（Notebookの実行順など）。 |
| **アプリコード** | `（5月～）APP開発/src/` | `/src/` | アプリケーションの主要コードとしてトップレベルに昇格。 |
| **アプリコード** | `（5月～）APP開発/.env.example`<br>`（5月～）APP開発/requirements.txt`<br>`（5月～）APP開発/start_api.sh` | `/.env.example`<br>`/requirements.txt`<br>`/start_api.sh` | アプリケーション開発に必要な設定・起動ファイルをルート、または `src/` 直下に配置。 |
| **データコード** | `（～4月）AWSシングルクラウドVer/docs/03_development/00_初期環境構築手順_インフラ/notebooks/*` | `[NEW] /databricks/notebooks/` | Databricks上で実行するPySpark Notebook群を一元化し、ドキュメント配下から分離。 |
| **インフラコード** | `（～4月）AWSシングルクラウドVer/docs/03_development/00_初期環境構築手順_インフラ/cloudformation.yaml` (他関連txt含む) | `[NEW] /infrastructure/` | AWSインフラを定義するIaCコード（CloudFormationテンプレート）を独立して管理。 |
| **管理ドキュメント** | `（～4月）AWSシングルクラウドVer/docs/01_management/` | `/docs/project_management/` | スプリントのバックログやリスク管理など、プロジェクト管理系の文書を集約。<br>※sprint0〜4フォルダや検討フォルダも配下に整理。 |
| **管理ドキュメント** | `（5月～）APP開発/docs/01_app_management/` | `/docs/project_management/` | アプリ開発用のバックログ等を上記管理フォルダに統合。 |
| **設計ドキュメント** | `（～4月）AWSシングルクラウドVer/docs/02_design/01_基本設計・要件定義/` | `/docs/design/system/` | 要件定義書、アーキテクチャ図、システム構成図、コスト比較などの共通設計書を集約。 |
| **設計ドキュメント** | `（～4月）AWSシングルクラウドVer/docs/02_design/02_インフラ・ガバナンス設計/`<br>`（～4月）AWSシングルクラウドVer/docs/02_design/03_データエンジニアリング設計/`<br>`（～4月）AWSシングルクラウドVer/docs/02_design/04_データサイエンス・BI設計/` | `/docs/design/data_platform/` | Unity Catalog設計、メダリオン設計、テーブル設計、データフローなどデータ基盤関連の設計書を集約。 |
| **設計ドキュメント** | `（5月～）APP開発/docs/design/`<br>`（～4月）AWSシングルクラウドVer/docs/02_design/05_アプリ統合設計/` | `/docs/design/app_development/` | システム設計、画面設計、なぜ画面がないの？の回答、E2E連携設計などのアプリ開発関連設計書を集約。 |
| **手順書・マニュアル** | `（～4月）AWSシングルクラウドVer/docs/03_development/` の手順書関連<br>- `環境構築手順書.md`<br>- `実装手順書.md`<br>- `CloudFormation更新手順_UI編.md`<br>- `Notebook仕様書.md`<br>- `01_機能実装マニュアル/XX_...` | `/docs/guides/` | 各種手順書・マニュアルをドキュメント直下の手順書フォルダに整理。<br>- `setup_infrastructure.md`<br>- `implementation_guide.md`<br>- `notebook_specification.md`<br>- `pipeline_development.md` 等 |
| **検証ドキュメント** | `（～4月）AWSシングルクラウドVer/docs/03_development/02_テスト・検証/テスト計画書.md` | `/docs/guides/test_plan.md` | テスト計画・仕様書も手順書・検証ガイドの一部として配置。 |
| **運用・サンプル** | `（～4月）AWSシングルクラウドVer/docs/04_operation/` のデータ・puml・xlsx | `/docs/operations/` | サンプルデータ（Excel）や関連するPlantUML等の運用関連アセットを配置。 |
| **運用コード** | `（～4月）AWSシングルクラウドVer/docs/04_operation/` のPythonコード群（`99_export_sample_excel.py` 等） | `/databricks/operations/` | 運用スクリプトを実行コードとして `databricks/` 配下に分離。 |
| **参考資料** | `skills/` | `/docs/reference/skills/` | Claudeのスキル等、プロジェクト外の参考資料をメインのルートから移動。 |
| **アーカイブ** | `（～4月）AWSシングルクラウドVer/old/` | `/docs/archive/` | 過去のバックアップや古いドキュメントをアーカイブフォルダに移動。 |

---

## 4. 移行後のフォルダ構成イメージ（After）

移行後のリポジトリ構成は以下のようになります：

```
databricks_datamng/
├── .agent/
├── .claude/
├── .vscode/
├── private/                            # 変更なし（.gitignoreによる除外を維持）
│   ├── 昇進会議_...
│   └── 昇進会議向け_報告書ドラフト.md
├── CLAUDE.md                           # 最新のパス構成を反映
├── README.md                           # [NEW] リポジトリ総合案内
├── requirements.txt                    # ルートに配置
├── .env.example                        # ルートに配置
├── start_api.sh                        # ルートに配置
│
├── src/                                # APP開発のソースコード
│   ├── admin/
│   ├── api/
│   ├── common/
│   ├── store/
│   └── web/
│
├── databricks/                         # データ系コードの集約
│   ├── notebooks/                      # Databricks実行用Notebook (PySpark)
│   │   ├── 00_setup_unity_catalog.py
│   │   ├── 01_load_northwind_to_rds.py
│   │   └── ...
│   └── operations/                     # 運用補助スクリプト
│       └── 99_export_sample_excel.py
│
├── infrastructure/                     # インフラ（IaC）コードの集約
│   ├── cloudformation.yaml
│   └── cloudformation_lambda.yaml
│
└── docs/                               # ドキュメント（設計・運用・管理）の一元管理
    ├── project_management/             # プロジェクト管理・スプリント
    │   ├── sprint_backlog_aws.md
    │   ├── sprint_backlog_app.md
    │   ├── sprint_history/             # sprint0〜sprint4の履歴
    │   ├── 実施手順書_作成規約.md
    │   └── Sprint4-5共通_事故リスク.md
    │
    ├── design/                         # 設計書
    │   ├── system/                     # 共通・インフラ設計
    │   │   ├── 要件定義書.md
    │   │   ├── アーキ図（論理アーキテクチャ）.md
    │   │   ├── システム構成図.md
    │   │   └── コスト比較.md
    │   ├── data_platform/              # Unity Catalog・データ設計
    │   │   ├── UnityCatalog設計書.md
    │   │   ├── メダリオンアーキテクチャ設計書.md
    │   │   ├── テーブル設計書.md
    │   │   └── データフロー図.md
    │   └── app_development/            # アプリ・画面設計
    │       ├── システム設計.md
    │       ├── 画面設計.md
    │       └── E2Eアプリ連携設計書.md
    │
    ├── guides/                         # 手順書・マニュアル・テスト
    │   ├── setup_infrastructure.md
    │   ├── implementation_guide.md
    │   ├── notebook_specification.md
    │   ├── pipeline_development.md
    │   └── test_plan.md
    │
    ├── operations/                     # 運用補助データ・成果物
    │   ├── サンプルデータ_202603211807/
    │   └── サンプルデータ統合_202603211807.xlsx
    │
    ├── reference/                      # プロジェクト外の参考資料
    │   └── skills/                     # 旧 skills/ (Claude用スキル群)
    │
    └── archive/                        # バックアップ・廃止資料の退避先
        ├── 20260308フォルダ構成前backup/
        └── 先にググらなかった失敗ver/
```
