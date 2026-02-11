# Azure ADLS Gen2 + Databricks Unity Catalog セットアップ手順書

この手順書に従って、Azure Data Lake Storage Gen2 と Databricks Unity Catalog をセットアップしてください。

> [!IMPORTANT]
> この手順書は **Azureポータル** と **Databricks UI** での操作をカバーします。
> Notebook で自動化できるステップ（External Location、Schema作成等）は `00_setup_unity_catalog.py` に含まれています。

---

## Phase 1: Azure リソース構築（Azureポータル）

### 1.1 ストレージアカウントの作成

1. **Azure Portal** にログイン
2. **「リソースの作成」** → **「ストレージアカウント」** を選択
3. 以下のように設定：

| 項目 | 設定値 |
|------|--------|
| サブスクリプション | ご自身のサブスクリプション |
| リソースグループ | 新規作成: `rg-northwind-datalake` |
| ストレージアカウント名 | `lakenorthwind<あなたのイニシャル>` (例: `lakenorthwindharu`) |
| リージョン | `Japan East` または `Japan West` |
| パフォーマンス | `Standard` |
| 冗長性 | `LRS` (ローカル冗長) |

4. **「詳細」タブ** で **「階層型名前空間を有効にする」** を ✅ **オン**
5. **「確認と作成」** → **「作成」**

> [!CAUTION]
> **「階層型名前空間を有効にする」** を必ずオンにしてください。これがないとADLS Gen2として機能しません。

### 1.2 コンテナの作成

ストレージアカウント作成後：

1. 作成したストレージアカウントを開く
2. 左メニュー **「コンテナー」** をクリック
3. **「+ コンテナー」** で以下の3つを作成：

| コンテナー名 | アクセスレベル |
|-------------|---------------|
| `bronze` | プライベート |
| `silver` | プライベート |
| `gold` | プライベート |

---

## Phase 2: IAM 権限設定（Azureポータル）

### 2.1 Access Connector の確認

> [!NOTE]
> Databricksワークスペース作成時に Access Connector が**自動生成**されている場合があります。
> 自分で作成した `adb-access-connector-northwind` ではなく、**ワークスペースが実際に使っているもの**を使用してください。

#### 実際に使われている Access Connector の確認方法

1. Databricks → 左メニュー **「カタログ」** → 右上 **⚙️** → **「資格情報」** タブ
2. ワークスペースデフォルトの資格情報（例: `dbx_northwind_ws`）をクリック
3. **「コネクター ID」** に表示されている Access Connector 名をメモ
   - 例: `unity-catalog-access-connector`（自動生成のもの）

### 2.2 Storage Blob Data Contributor の割り当て

**⚠️ 2.1 で確認した Access Connector に対して行ってください！**

1. Azureポータル → ストレージアカウント（`lakenorthwindharu` 等）を開く
2. 左メニュー → **「アクセス制御 (IAM)」**
3. **「+ 追加」** → **「ロールの割り当ての追加」**
4. ロール: **「ストレージ BLOB データ共同作成者」**（Storage Blob Data Contributor）
5. メンバー:
   - **マネージドID** を選択
   - **「+ メンバーを選択する」** → `unity-catalog-access-connector`（2.1で確認したもの）を選択
6. **「確認と割り当て」**

> [!WARNING]
> IAM ロールの反映には **最大10分** かかります。割り当て後、5分以上待ってから次のステップに進んでください。

---

## Phase 3: Databricks UI 操作

### 3.1 Storage Credential

ワークスペース作成時に自動作成された `dbx_northwind_ws` をそのまま使用します。**追加作成は不要です。**

確認方法: カタログ → ⚙️ → 資格情報 → `dbx_northwind_ws` が存在すること

### 3.2 カタログの作成（UI操作が必須）

> [!IMPORTANT]
> カタログの作成は **SQL では実行できません**（Default Storage を使用する場合）。
> 必ず Databricks UI から作成してください。

1. 左メニュー → **「カタログ」**
2. **「+ 追加」** → **「カタログを追加」**
3. 以下を入力：
   - **カタログ名**: `northwind_catalog`
   - **ストレージの場所**: **Default Storage** を選択
4. **「作成」** をクリック

### 3.3 クラスターの設定

Notebook を実行するクラスターは **「専用（旧: シングルユーザー）」** モードで作成してください。

| 項目 | 設定値 |
|------|--------|
| アクセスモード | **専用（旧: シングルユーザー）** |
| ノードタイプ | 任意（コスト削減なら最小構成） |

> [!NOTE]
> アクセス権制御の実験を行う場合は、後から **「標準（旧: 共有済み）」** モードのクラスターを追加作成してください。

---

## Phase 4: Notebook 実行

Phase 1〜3 が完了したら、以下のNotebookを順に実行します。

| 順番 | Notebook | 内容 |
|------|----------|------|
| 1 | `00_setup_unity_catalog.py` | 前提条件チェック + External Location + Schema 作成 |
| 2 | `01_load_northwind_to_rds.py` | RDS に Northwind データ投入 |
| 3 | `02_etl_bronze_ingest.py` | RDS → Bronze層（Unity Catalog）にデータ取り込み |
| 4 | `03_etl_silver_transform.py` | Silver層への変換 |
| 5 | `04_etl_gold_aggregate.py` | Gold層への集計 |

---

## トラブルシューティング

| エラー | 原因 | 対処 |
|--------|------|------|
| `PARSE_SYNTAX_ERROR at or near 'STORAGE'` | クラスターのアクセスモードが不正 | 「専用（Single User）」に変更 |
| `PERMISSION_DENIED: Managed Identity does not have permissions` | Access Connector に IAM ロール未付与、または反映待ち | ロール付与 → 5分待機 |
| `workspace default credential is only allowed to access...` | カタログに `MANAGED LOCATION` を指定している | `MANAGED LOCATION` を削除、UIから Default Storage でカタログ作成 |
| `Metastore storage root URL does not exist` | SQLでカタログ作成時にメタストアルート未設定 | UIからカタログ作成（Default Storage使用） |
