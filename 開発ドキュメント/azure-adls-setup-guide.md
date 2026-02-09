# Azure ADLS Gen2 構築手順書

この手順書に従って、Azure Data Lake Storage Gen2（ADLS Gen2）をセットアップしてください。

## 1. ストレージアカウントの作成

### Azure Portal での操作

1. **Azure Portal** にログイン
2. **「リソースの作成」** → **「ストレージアカウント」** を選択
3. 以下のように設定：

| 項目 | 設定値 |
|------|--------|
| サブスクリプション | ご自身のサブスクリプション |
| リソースグループ | 新規作成: `rg-northwind-datalake` |
| ストレージアカウント名 | `lakenorthwind<あなたのイニシャル>` (例: `lakenorthwindharu`) ※結果"lakenorthwindharu_1770645250229"|
| リージョン | `Japan East` または `Japan West` |
| パフォーマンス | `Standard` |
| 冗長性 | `LRS` (ローカル冗長) |

4. **「詳細」タブ** で以下を設定：

| 項目 | 設定値 |
|------|--------|
| **階層型名前空間を有効にする** | ✅ **オン** (これが重要！) |

5. **「確認と作成」** → **「作成」**

> [!IMPORTANT]
> **「階層型名前空間を有効にする」** を必ずオンにしてください。これがないとADLS Gen2として機能しません。

---

## 2. コンテナの作成

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

## 3. Access Connector for Azure Databricks の作成

1. Azure Portal で **「リソースの作成」** をクリック
2. 検索ボックスに **「Access Connector for Azure Databricks」** と入力
3. **「作成」** をクリック
4. 以下のように設定：

| 項目 | 設定値 |
|------|--------|
| サブスクリプション | ご自身のサブスクリプション |
| リソースグループ | `rg-northwind-datalake` (上で作ったもの) |
| 名前 | `adb-access-connector-northwind` |
| リージョン | ストレージと同じリージョン |

5. **「確認と作成」** → **「作成」**

---

## 4. ロール割り当て（IAM）

**重要**: この設定は「Access Connector」の画面ではなく、作成した**「ストレージアカウント」の画面**で行います。Access Connector（Managed Identity）に対して、ストレージへのアクセス権を許可するためです。

1. Azure Portal の検索バーで、作成した **ストレージアカウント**（`lakenorthwind...`）を検索して開く
2. 左メニュー **「アクセス制御 (IAM)」** をクリック
3. **「+ 追加」** → **「ロールの割り当ての追加」** を選択
4. 以下のように設定：

| 項目 | 設定 | 備考 |
|------|------|------|
| **ロール** | `Storage Blob Data Contributor`<br>（ストレージ BLOB データ共同作成者） | 検索窓に入力して選択 |
| **アクセスの割り当て先** | `マネージド ID` | ラジオボタンを選択 |
| **メンバー** | `+ メンバーを選択`<br>→ サブスクリプション: (自分のもの)<br>→ マネージド ID: `Access Connector for Azure Databricks`<br>→ `adb-access-connector-northwind` を選択 | 最後に「選択」ボタンを押す |

5. **「レビューと割り当て」** をクリックして完了

---

## 5. 作成した情報をメモ

以下の情報を後で使用しますのでメモしておいてください：

| 項目 | 値 |
|------|-----|
| ストレージアカウント名 | `lakenorthwind____` |
| Access Connector リソースID | (概要ページの「リソースID」) |

### Access Connector リソースIDの確認方法

1. Access Connector のリソースを開く
2. 左メニュー **「プロパティ」** をクリック
3. **「リソースID」** をコピー

形式: `/subscriptions/{subscription-id}/resourceGroups/{rg}/providers/Microsoft.Databricks/accessConnectors/{name}`

---

## 次のステップ

上記が完了したら、以下の情報を教えてください：
1. ストレージアカウント名
2. Access Connector のリソースID

これらを使って、Databricksの設定とノートブックの修正を行います。
