# Unity Catalog セットアップ：振り返りと改善提案

## 1. 何が起きたか — 問題の時系列

| # | 症状 | 根本原因 | 実際の解決策 | Notebookに書いてあったこと |
|---|------|---------|-------------|------------------------|
| 1 | `PARSE_SYNTAX_ERROR at or near 'STORAGE'` | クラスターのアクセスモードが「分離なし共有」だった、またはUC非対応の設定だった | クラスターを **「専用（Single User）」** に変更 | 記載なし（前提条件に書くべきだった） |
| 2 | 同じSyntax Error（クラスター変更後も） | `CREATE STORAGE CREDENTIAL` はこの環境ではSQL未サポート。資格情報はUI経由で作成する必要があった | `dbx_northwind_ws`（UI作成済み）をそのまま使用 | `CREATE STORAGE CREDENTIAL` をSQLで実行しようとしていた |
| 3 | `PERMISSION_DENIED: Managed Identity does not have permissions` | `dbx_northwind_ws` が参照する Access Connector (`unity-catalog-access-connector`) に Storage Blob Data Contributor が未付与 | `unity-catalog-access-connector` にロール付与 | `adb-access-connector-northwind`（別のコネクタ）を前提としていた |
| 4 | 同じ PERMISSION_DENIED（ロール付与後） | Azure IAM のロール反映に数分かかる | **5分待って再実行** | 記載なし（待機時間の注意喚起が必要だった） |
| 5 | `workspace default credential is only allowed to access...` | カタログに `MANAGED LOCATION` を指定 → workspace default credential では外部ストレージに書けない | `MANAGED LOCATION` を**削除** | 最初のバージョンでは `MANAGED LOCATION` を指定していた |
| 6 | `Metastore storage root URL does not exist` | `MANAGED LOCATION` なしだとメタストアのルートストレージが必要だが未設定 | **Databricks UIからカタログを作成**（Default Storage使用） | SQLでカタログ作成を試みていた |
| 7 | `SCHEMA_NOT_FOUND bronze` | カタログ作成後、スキーマ未作成のまま`02`を実行 | スキーマ作成SQLを先に実行 | 手順の依存関係が不明確だった |

---

## 2. 根本原因の分析

### ❌ 私（AI）の設計ミス

1. **環境の実態を把握せずにコードを書いた**
   - ワークスペースにどのAccess Connectorが紐付いているか、メタストアの構成がどうなっているかを**確認せずに**、一般的なドキュメントベースでNotebookを作成した
   - 結果、`adb-access-connector-northwind`（ユーザーが作ったもの）と `unity-catalog-access-connector`（Databricksが自動作成したもの）の混同が発生

2. **「SQLでなんでもできる」前提で書いた**
   - `CREATE STORAGE CREDENTIAL` はAzure DatabricksではSQL未サポートの場合がある
   - `CREATE CATALOG` もメタストア構成によってはSQLだけでは不十分
   - **UI操作が必須のステップをNotebookに含めるべきではなかった**

3. **`MANAGED LOCATION` の罠を理解していなかった**
   - workspace default credential は外部ストレージへの書き込みに使えない制約がある
   - Default Storage を使う場合はUI操作が必要

4. **前提条件の記載が不十分だった**
   - クラスターのアクセスモード指定なし
   - IAMロール反映の待機時間への言及なし
   - 既存のStorage Credentialの確認手順なし

---

## 3. あるべき姿 — 実際に成功した手順の整理

今回、**実際に成功した手順**を時系列で整理すると以下の通りです：

### Phase 0: Azure リソース準備（Azureポータル）
- ADLS Gen2 ストレージアカウント作成
- コンテナ（bronze, silver, gold）作成
- ※Access Connector はワークスペース作成時に自動生成された `unity-catalog-access-connector` を使用

### Phase 1: IAM 権限設定（Azureポータル）
- `unity-catalog-access-connector` に `Storage Blob Data Contributor` を付与
- **5分待機**（ロール反映待ち）

### Phase 2: Databricks UI 操作（ブラウザ）
- Storage Credential → 既存の `dbx_northwind_ws` をそのまま使用（作成不要）
- カタログ `northwind_catalog` → **UIから作成**（Default Storage使用）

### Phase 3: Databricks Notebook（SQL/Python）
- External Location 作成（SQL — これは成功した）
- Schema 作成（SQL — これも成功した）
- RDSからBronze層へのデータ取り込み（Python — これも成功した）

---

## 4. 改善提案：Notebook の再設計

### 現状の問題

| Notebook | 問題 |
|----------|------|
| `00_setup_unity_catalog.py` | Storage Credential作成（実際はUI必須）、Catalog作成（実際はUI必須）が含まれており、**Notebookだけでは完結しない** |
| `01_load_northwind_to_rds.py` | 問題なし（前回から成功） |
| `02_etl_bronze_ingest.py` | 問題なし（00と01が正しければ動く） |

### 提案：2つの選択肢

#### 選択肢A: Notebookを実態に合わせて書き直す（推奨）

```
00_setup_unity_catalog.py  → 「前提条件チェック + External Location + Schema作成」に縮小
                              Storage CredentialとCatalogはUI操作として手順書に分離
01_load_northwind_to_rds.py → 変更なし
02_etl_bronze_ingest.py     → 変更なし
```

> [!IMPORTANT]
> `00` の役割を「UI操作後の確認 + SQLで可能な設定のみ」に限定する。
> UI操作が必要な手順は、別途 **セットアップガイド文書** にまとめる。

#### 選択肢B: 手順書ベースに統合する

```
azure-adls-setup-guide.md   → Azure + Databricks UIの全手順を統合したマスター手順書
00_setup_unity_catalog.py   → 「確認・検証用」に特化（設定は手順書で完了している前提）
01_load_northwind_to_rds.py → 変更なし
02_etl_bronze_ingest.py     → 変更なし
```

---

## 5. 結論

**00のNotebookは「自動化できる部分」と「UI操作が必須の部分」を混同していたことが最大の問題**でした。Databricks Unity Catalog on Azure では、以下はNotebookのSQLでは対応できない（または環境依存でエラーになる）ことが判明しました：

- ❌ `CREATE STORAGE CREDENTIAL`（UI操作が必要）
- ❌ `CREATE CATALOG`（Default Storage使用時はUI操作が必要）
- ✅ `CREATE EXTERNAL LOCATION`（SQL OK）
- ✅ `CREATE SCHEMA`（SQL OK）
- ✅ `saveAsTable`（Python OK）

この学びを反映して、Notebookと手順書を再構成することを提案します。
