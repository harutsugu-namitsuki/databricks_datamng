# 実装手順書（初心者向け詳細ガイド - Gemini版）

この手順書は、AWSやDatabricksの操作に慣れていない方でも、画面のどこをクリックし、何をコピーすればよいのかを1歩ずつ進められるようにした「超・詳細版」の構築マニュアルです。

---

## 全体の流れ（5つのステップ）

1. **AWSの準備**: ネットワークやデータベース（RDS）、保存場所（S3）を自動で作ります。
2. **Databricksの準備（外側）**: Databricksのワークスペース（作業場所）を作ります。
3. **Databricksの準備（内側）**: パソコン（クラスター）の起動と、S3への接続設定をします。
4. **パスワードの登録**: データベースのパスワードを安全に登録します。
5. **プログラムの実行**: 実際にデータを流し込んで処理を行います。

---

## Phase 1: AWSの準備（CloudFormationによる自動構築）

ご推察の通り「DatabricksアカウントIDを取得して、YAMLファイルをCloudFormation（GUI）で起動する」だけでOKです！ターミナル（黒い画面）は使わずにブラウザから作成します。

### Step 1-1: DatabricksアカウントIDの取得
1. ブラウザで [Databricks Account Console](https://accounts.cloud.databricks.com/) にログインします。
2. 画面右上にあるユーザー名（またはアイコン）をクリックします。
3. メニューの中に **Account ID**（英数字の文字列）が表示されるので、それをコピーして手元にメモしておきます。

### Step 1-2: CloudFormation画面を開く
1. ブラウザで [AWS Management Console](https://aws.amazon.com/jp/console/) にログインします。
2. 画面上部の検索バーで `CloudFormation` と検索し、サービス一覧からクリックして開きます。
3. 画面右上のオレンジ色のボタン **[スタックの作成]** または **[Create stack]** をクリックし、「新しいリソースを使用 (標準)」を選びます。

### Step 1-3: 設定ファイル（YAML）のアップロード
1. 「テンプレートの準備」で **テンプレートの準備完了** を選びます。
2. 「テンプレートの指定」で **テンプレートファイルのアップロード** を選びます。
3. **[ファイルの選択]** ボタンを押し、ご自身のPCにある `開発ドキュメント/cloudformation.yaml` を選んでアップロードし、右下の **[次へ]** を押します。

### Step 1-4: パラメータの入力
スタックの詳細を指定する画面で、以下の通り入力します。
- **スタックの名前**: `northwind-lakehouse` （わかりやすい名前）
- **DatabricksAccountId**: Step 1-1でメモした文字列を貼り付けます
- **DBPassword**: RDS（データベース）のパスワードを **8文字以上** で自由に決めて入力します（例: `MySecretDBPass123` など）。⚠️ このパスワードは手元にメモしておいてください。
- （他の設定は変更せず、そのまま一番下の **[次へ]** を押します）

### Step 1-5: 作成の実行
1. 「スタックオプションの設定」画面は何も変更せずに一番下の **[次へ]** を押します。
2. 確認画面の一番下までスクロールし、「**AWS CloudFormation が IAM リソースを作成する場合があることを承認します。**」というチェックボックスに **チェックを入れます**。
3. **[送信]** または **[スタックの作成]** をクリックします。

### Step 1-6: 完成を待つ＆情報のコピー
1. `northwind-lakehouse` スタックのステータスが緑色の `CREATE_COMPLETE` になるまで待ちます（約5〜10分かかります。更新ボタンを押して確認してください）。
2. 完了したら、**「出力（Outputs）」** タブを開きます。
3. 以下の3つの値を手元にメモしてください。※あとで使います。
   - `DatabricksUnityRoleArn`: (arn:aws:iam::... から始まる文字列)
   - `RDSEndpoint`: (northwind-db.xxxx.ap-northeast-1.rds.amazonaws.com のような文字列)
   - `S3BucketName`: (lake-northwind-xxxx という文字列)

---

## Phase 2: Databricks ワークスペースの作成

### Step 2-1: ワークスペースの作成
1. [Databricks Account Console](https://accounts.cloud.databricks.com/) に戻ります。
2. 左メニューから **Workspaces** をクリックし、右上の **Create workspace** をクリックします。
3. **AWS region** を `ap-northeast-1` (東京) にします。
4. **VPC** の項目で、自身でVPCを持ち込むオプション（Customer-managed VPC）を選択し、Phase1で作った `northwind-vpc` とそのネットワークの設定（Private Subnetなど）を指定して作成を進めます。
   ※画面の案内に従って作成を完了させてください。作成には数分かかります。
5. 作成が終わったら **[Open workspace]** をクリックしてワークスペースに入ります。

---

## Phase 3: Databricks内での設定（クラスターと接続設定）

### Step 3-1: クラスター（計算処理するPC）の作成
1. ワークスペースの左メニューから **Compute** をクリックし、**Create compute** をクリックします。
2. 以下の設定に変更します：
   - Policy: `Unrestricted`
   - Access mode: **Single user**（ここが重要です！「専用」を選択してください）
   - Databricks Runtime Version: 14.3 LTS以上（デフォルトのままでOK）
   - Use Photon: チェックを外す（コスト削減のため）
   - Worker type: 最小のインスタンス（例: `i3.xlarge` など）を選択
   - Min workers: `1`, Max workers: `2`（小さく設定）
3. **Create compute** をクリックして起動を待ちます（緑色のチェックマークが出れば起動完了です）。

### Step 3-2: Storage Credential（S3と連携するための鍵）の作成
1. 左メニューの **Catalog**（カタログ）をクリックします。
2. 画面上部や左下のメニューから **External Data** > **Storage Credentials** を探して開きます。
3. 右上の **Create credential** をクリックします。
4. 以下の通り入力します：
   - Credential type: **AWS IAM Role**
   - Name: `aws_s3_credential` （一語一句間違えないように）
   - Role ARN: **Phase 1のStep 1-5でメモした『DatabricksUnityRoleArn』**の値を貼り付けます。
5. **Create** をクリックして保存します。

### Step 3-3: カタログの作成
1. 同じく **Catalog** メニューを開き、画面右上の **Create catalog** をクリックします。
2. Catalog name に `northwind_catalog` と入力し、**Create** をクリックします。

---

## Phase 4: パスワードの登録 (Databricks Secrets)

データベースのパスワードをプログラムに直接書くのは危険なので、Databricksの「秘密の金庫（Secrets）」に登録します。
黒い画面（CLI）は使わずに、**DatabricksのNotebookを使ってPythonコードで登録する** 一番簡単な方法を紹介します。

### Step 4-1: アクセストークンの発行
1. Databricks ワークスペースの右上にある自分のユーザー名をクリックし、**Settings** を開きます。
2. 左メニューの **Developer** をクリックし、Access tokens の **Manage** をクリックします。
3. **Generate new token** をクリックし、適当な名前（`setup`など）をつけて作成します。
4. `dapi...` から始まる長い文字列が表示されるので、コピーします（二度と表示されないので注意）。

### Step 4-2: Notebook（プログラム画面）を開いてコードを実行
1. ワークスペース左メニューから **+ New** > **Notebook** をクリックして新しいNotebookを作ります。
2. セル（コードを打つ箱）に以下のPythonコードを貼り付けます。
3. `<あなたのトークン>`、`<RDSEndpointの値>`、`<パスワードの値>` の **3箇所** を、これまでにメモしたものに書き換えます。

```python
import requests

# ①ワークスペースの情報を取得
host = "https://" + spark.conf.get("spark.databricks.workspaceUrl")
token = "<あなたのトークン>"   # 例: "dapi1234567890..."
headers = {"Authorization": f"Bearer {token}"}

# ②金庫（スコープ）の作成
requests.post(f"{host}/api/2.0/secrets/scopes/create", headers=headers, json={"scope": "northwind-secrets"})

# ③ホスト名の登録
requests.post(f"{host}/api/2.0/secrets/put", headers=headers, json={
    "scope": "northwind-secrets", "key": "rds-host", "string_value": "<RDSEndpointの値>"
})

# ④ユーザー名の登録（dbadmin）
requests.post(f"{host}/api/2.0/secrets/put", headers=headers, json={
    "scope": "northwind-secrets", "key": "rds-user", "string_value": "dbadmin"
})

# ⑤パスワードの登録
requests.post(f"{host}/api/2.0/secrets/put", headers=headers, json={
    "scope": "northwind-secrets", "key": "rds-password", "string_value": "<パスワードの値>"
})

print("✅ Secretsの登録が完了しました！")
```

4. 画面右上のプルダウンから、Phase 3で作ったクラスターを選択してアタッチします。
5. セルの右上にあるプレイボタン（▶️）を押して **Run cell** をクリックします。
6. `✅ Secretsの登録が完了しました！` と表示されれば成功です。このNotebookはもう消してしまって構いません。

---

## Phase 5: プログラム（Notebook）の実行

いよいよ作られた環境でデータを流し込みます。

### Step 5-1: Notebookのインポート
1. Databricksワークスペースの左メニューから **Workspace** をクリックし、自分のユーザー名のフォルダ（`Users/あなたのメールアドレス`）を開きます。
2. 右上の **⋮** または何も無い場所で右クリックし、**Import** を選択します。
3. 手元のPCから、以下の5つのファイルを全てアップロードします。
   - `00_setup_unity_catalog.py`
   - `01_load_northwind_to_rds.py`
   - `02_etl_bronze_ingest.py`
   - `03_etl_silver_transform.py`
   - `04_etl_gold_aggregate.py`

### Step 5-2: 順番に実行する
アップロードしたNotebookをダブルクリックして開き、以下の順番で実行していきます。

**実行のやり方（共通）**:
1. 画面左上のプルダウンで、Step 3-1 で作った「クラスター」を選択してアタッチします。
2. 画面右上の **Run all**（すべて実行）をクリックします。
3. 画面の下の方までスクロールし、エラー（赤い文字）が出ずに `✅ 完了しました` などの表示が出ればOKです。

**実行する順番**:
1. **`00_setup_unity_catalog.py`**
   （S3へのフォルダ作成と登録を行います）
2. **`01_load_northwind_to_rds.py`**
   （14個のテーブル一覧と「全14テーブルの件数が確認できた」と出れば成功です）
3. **`02_etl_bronze_ingest.py`**
   （RDSからS3のBronze層にデータをコピーします）
4. **`03_etl_silver_transform.py`**
   （Bronze層のデータをキレイにしてSilver層に置きます）
5. **`04_etl_gold_aggregate.py`**
   （データを分析しやすい形に集計してGold層に置きます）

---
🎉 **お疲れ様でした！これで全ての構築とデータ処理が完了です！** 🎉
左メニューの **Catalog** > `northwind_catalog` > `gold` スキーマの中に売上集計のテーブルが作成されているのを確認してみてください。
