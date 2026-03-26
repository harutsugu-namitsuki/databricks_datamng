# AWS IAM ロール・ポリシー設定リファレンス / AWS IAM Role & Policy Reference

> **このドキュメントの目的 / Purpose:**
> AWS Console でのロール・ポリシー設定作業で詰まりやすいポイントをまとめたリファレンス。実装手順書を書く際・読む際の参照用。

---

## 基本ルール: ポリシーを先に作ってからロールを作る

AWS Console のロール作成ウィザードでは、カスタムポリシーを**途中で新規作成することができません**。

「Add permissions」画面には既存ポリシーの検索・選択しかないため、カスタム JSON ポリシーが必要な場合は**ポリシー → ロールの順**で作成する。

```
1. IAM → ポリシー → ポリシーの作成（JSON で作成）
2. IAM → ロール  → ロールを作成（↑のポリシーをアタッチ）
```

---

## ポリシーの作成手順 / How to Create a Policy

### 1. IAM → ポリシー（Policies）→「ポリシーの作成（Create policy）」

### 2. JSON エディタに切り替える

ポリシーエディタはデフォルトで **「ビジュアル（Visual）」** モード（ドロップダウン式）。

**エディタ上部の「JSON」ボタン**をクリック → テキスト入力エリアが表示される。

```
[ ビジュアル | JSON ]  ← エディタ上部に2つのボタンがある
                ↑ ここをクリック
```

### 3. JSON を貼り付け → 「次へ」→ ポリシー名を入力 → 「ポリシーの作成」

---

## ロールの作成手順 / How to Create a Role

### 1. IAM → ロール（Roles）→「ロールを作成（Create role）」

### 2. 信頼エンティティを選ぶ

| 選択肢 | 使いどころ |
|--------|-----------|
| **AWS のサービス → Lambda** | Lambda 用ロール（最も一般的）。信頼ポリシーが**自動設定**される（JSON 不要） |
| **AWS のサービス → EventBridge Scheduler** | EventBridge Scheduler 用ロール |
| カスタム信頼ポリシー | 上記以外の複雑な信頼関係（通常は不要） |

### 3. 「許可を追加（Add permissions）」画面

検索バーにポリシー名を入力 → チェックボックスにチェック → 「次へ」

### 4. ロール名を入力 → 「ロールを作成」

---

## 信頼ポリシー vs 許可ポリシー / Trust Policy vs. Permissions Policy

| | 信頼ポリシー | 許可ポリシー |
|---|---|---|
| 意味 | **誰が**このロールを使えるか | このロールが**何を**できるか |
| 例 | Lambda がこのロールを引き受けられる | EC2 の NAT Gateway を作成できる |
| 設定方法 | サービス選択で自動 or カスタム信頼ポリシーで JSON | 上記「ポリシー先行作成」で JSON |
| JSON の要否 | Lambda/EventBridge なら**不要** | **必要**（カスタム権限の場合） |

---

## よくあるパターン / Common Patterns

### Lambda 実行ロール（カスタム権限付き）

```
Step 1: IAM → ポリシー → ポリシーの作成 → JSON
        → "northwind-xxx-policy" 作成

Step 2: IAM → ロール → ロールを作成
        → 信頼: AWS のサービス → Lambda
        → 許可: "northwind-xxx-policy" を検索してアタッチ
        → "northwind-xxx-role" 作成
```

### EventBridge Scheduler ロール

```
Step 1: IAM → ポリシー → ポリシーの作成 → JSON
        → lambda:InvokeFunction のみ許可するポリシーを作成

Step 2: IAM → ロール → ロールを作成
        → 信頼: AWS のサービス → EventBridge Scheduler
        → 許可: ↑のポリシーをアタッチ
```

### Databricks ワークスペースロールへのインラインポリシー追加

ロール作成後に Lambda 呼出権限を**追加**する場合:

```
IAM → ロール → "northwind-workspace-role" を開く
→「許可を追加（Add permissions）」→「インラインポリシーを作成（Create inline policy）」
→ JSON タブ → JSON 貼り付け → ポリシー名 → 「ポリシーの作成」
```

> インラインポリシーはロールに直接埋め込まれ、再利用不可。
> 単一ロール専用の追加権限に使う。

---

---

## Lambda コードのよくあるミス / Common Lambda Code Mistakes

### `Runtime.ImportModuleError: No module named 'lambda_function'`

**原因**: Lambda のデフォルトハンドラーは `lambda_function.lambda_handler` で、ファイル名 `lambda_function.py` を期待している。コードをファイルとしてアップロードすると名前が変わり、このエラーが出る。

**正しいコード貼り付け手順:**

1. Lambda コンソール → 関数を開く → **「コード」タブ**
2. エディタ左側ファイルツリーで **`lambda_function.py`** が選択されていることを確認
3. エディタ内の既存コードを **Ctrl+A → Delete** で全消去
4. ノートブックファイルの内容をまるごとコピーして貼り付ける
5. **「Deploy」** をクリック

> `nb_01_nat_create_lambda.py` などのノートブックファイルを**ファイルとしてアップロードしない**こと。必ず `lambda_function.py` の中身を置き換える。

**既にエラーが出た場合の修正（方法 A）:**
→ `lambda_function.py` の中身を正しく置き換えて「Deploy」

**既にエラーが出た場合の修正（方法 B）:**
→ Configuration → General configuration → **Handler** を `nb_01_nat_create_lambda.lambda_handler` に変更

---

## 変更履歴 / History

| 日付 | 内容 |
|------|------|
| 2026-03-26 | Story 1-6 実装時の UI 相違（「Create policy」ボタン不在）を教訓として初版作成 |
