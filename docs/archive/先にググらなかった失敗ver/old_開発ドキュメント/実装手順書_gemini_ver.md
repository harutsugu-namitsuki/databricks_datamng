# 実装手順書（初心者向け詳細ガイド - Gemini版）

この手順書は、AWSやDatabricksの操作に慣れていない方でも、画面のどこをクリックし、何をコピーすればよいのかを1歩ずつ進められるようにした「超・詳細版」の構築マニュアルです。

---

## 全体の流れ（6つのステップ）

0. **アカウント登録**: Databricksの無料アカウントを作成します（初回のみ）。
1. **AWSの準備**: ネットワークやデータベース（RDS）、保存場所（S3）を自動で作ります。
2. **Databricksの準備（外側）**: Databricksのワークスペース（作業場所）を作ります。
3. **Databricksの準備（内側）**: パソコン（クラスター）の起動と、S3への接続設定をします。
4. **パスワードの登録**: データベースのパスワードを安全に登録します。
5. **プログラムの実行**: 実際にデータを流し込んで処理を行います。

---

## Phase 0: Databricks アカウントの準備（初回のみ）

AWSの設定を始める前に、ご自身のDatabricksアカウントIDを取得します。
ご自身の状況に合わせて、パターンAかパターンBのどちらかを実施してください。

### パターンA: これから初めてアカウントを作る方
**※途中でAWS画面を経由しますが、これは「連携」の作業です。インフラ自体はPhase 1のCloudFormationで作るので安心してください。**

1. [Databricks 無料トライアルページ](https://databricks.com/jp/try-databricks) にアクセスします。
2. 名前や会社名（個人の場合は個人名可）、メールアドレス等を入力して「次へ」を押します。
3. **「クラウド・プロバイダーを選択してください」**という画面になるので、**Amazon Web Services (AWS)** にチェックを入れて「無料で開始」を押します。
4. ※ここが紛らわしいポイントです※
   画面が自動的に**AWS Manajemenet Console（AWS MarketplaceのDatabricksサブスクリプション画面）**に遷移します。
   このステップは「AWS経由での支払い連携」をするためのものです。
   - 画面の案内に従い、「View permissions」等を確認して連携（Subscribe）を進めます。
   - 最終的に**「Create account（または Set up your account）」**というボタンが出てくるので、それをクリックします。
5. （AWSから飛ばされて）**再びDatabricksの画面が開きます**。ここで最終的なパスワード設定等を行い、アカウントのセットアップが完了です。
6. 設定が終わると、**Databricks Account Console** ([accounts.cloud.databricks.com](https://accounts.cloud.databricks.com/)) という「Databricks全体の管理画面」にようやくログインできるようになります。

### パターンB: すでにアカウントをお持ちの方
過去にDatabricksのアカウントを作成したことがある方は、以下の方法でAWS連携が済んでいるかを確認します。

1. **Databricks Account Console** ([accounts.cloud.databricks.com](https://accounts.cloud.databricks.com/)) に直接アクセスし、ログインできるかを確認します。
   - ログイン後、左メニューに **Workspaces** などの項目が表示されていれば、アカウント自体は正常に動作しています。
2. そのまま右上のユーザー名（またはアイコン）をクリックして開くメニューから、まずは **Account ID** が取得できればOKです。このままPhase 1へ進んでください。
3. **【AWSとの連携状態について】**
   もし過去にAWSとの課金・連携設定（サブスクリプションの登録）を行っていないアカウントの場合、Phase 2でワークスペースを作成しようとしたり、クラウド・リソース（Cloud resources）を登録しようとしたタイミングでエラーが出たり、**AWS Marketplaceでの連携を促されるポップアップ**が表示されることがあります。
   その場合は、画面の案内に従ってAWSコンソールへ飛び、連携作業（Subscribe）を完了させてから、再度ワークスペースの作成を再開してください。

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

Databricksを利用するには、まず「Phase 0で作ったアカウント」にログインし、その後に「ワークスペース（実際の作業場所）」を作るという段階になります。

### Step 2-1: AWS Marketplace サブスクリプションの有効化（必須）
AWSリソース（VPCやS3など）をDatabricksから自動設定させるためには、DatabricksアカウントとAWSアカウントを「支払い・権限の面で連携」させる必要があります。
※すでに過去にAWS連携を済ませているアカウントの場合は、このステップは不要（設定済み）ですので Step 2-2 へ進んでください。

1. **Databricks Account Console** ([accounts.cloud.databricks.com](https://accounts.cloud.databricks.com/)) の左メニューの下部にある **Settings**（または雲のアイコン）から **AWS subscription** などの項目を開くか、クラウド・リソースの登録画面に進もうとすると、**「AWSとの連携（サブスクリプション）が必要です」という警告や案内**が出ます。
2. 案内に従って **Link AWS Account** などのボタンをクリックすると、自動的に **AWSのManagement Console（AWS Marketplace画面）**が開きます。
3. Marketplaceの画面で Databricks の内容を確認し、右上の **[Continue to Subscribe]**（または Subscribe）をクリックします。
4. Terms and Conditions（利用規約）に同意し、セットアップを進めます。
5. 処理が完了すると、自動的にDatabricksの画面に戻るか、「Set up your account」ボタンが出てDatabricksに遷移します。これで連携は完了です。

※アカウントを管理→（左側）設定→サブスクリプションと請求→支払方法→AWSに画面遷移→サブスライブをクリック

### Step 2-2: クラウド・リソース（AWSとの連携設定）の登録
Phase 1で作ったAWSのネットワーク環境にワークスペースを構築するため、Account Consoleの左メニューにある **Cloud resources** (クラウド・リソース) から以下3つの設定を事前に行います。

**① Credentials（資格情報）の登録**
DatabricksがあなたのAWSアカウント上に「クラスター（計算用EC2）」を自動で作成・起動・停止するための権限（クロスアカウントIAMロール）を登録します。
1. **Cloud resources** 画面の中の **Credentials**（または Identity）タブを開き、「Add credential」をクリックします。
2. 任意の名前（例: `northwind-credential`）を入力します。
3. 画面に表示される **外部ID (External ID)** （例: `cc35...` または `fc1...`）をコピーし、手元に控えます。
4. **【AWS側での手動設定】** 別のタブで [AWS IAM 管理画面 (Roles)](https://us-east-1.console.aws.amazon.com/iam/home?region=ap-northeast-1#/roles) を開きます。
5. IAM→ロール→ロールを作成※右上の **[ロールを作成]** をクリックします。
6. 「信頼されたエンティティタイプ」で **[AWS アカウント]** を選択します。
7. 「AWS アカウント」の項目で **[別のアカウント]** を選び、アカウントIDに **Databricks社の固定AWSアカウントID** である **`414351767826`** を入力します。
8. オプションで **「外部 ID を要求する」** にチェックを入れます。
   - ⚠️ **【超重要ポイント】** ここに入力する値は「414351767826」**ではありません**！（400エラーの原因になります）
   - 手順3でコピーした**あなた専用の「外部ID」**（アカウントIDと同一、`cc35cba6...` や `fc1...` などハイフンを含む英数字）を必ず貼り付けてから、**[次へ]** を押します。
9. 「許可ポリシーを追加」画面では何も選択せずに **[次へ]** を押します。
10. 「ロール名」に `northwind-databricks-workspace-role` 等のわかりやすい名前を付け、**[ロールを作成]** を押します。
11. 今作ったロール（`northwind-databricks-workspace-role`）を一覧から検索して開き、右側の **「ARN」** （`arn:aws:iam::...`）をコピーします。
12. ロール画面下の **「許可」タブ** ＞ **「許可を追加」** ＞ **「インラインポリシーを作成」** をクリックします。
13. 「JSON」タブに切り替え、本ドキュメントと同階層にある **`databricks_workspace_policy.json`** の中身を**すべてコピーして貼り付け**ます。
    - ※このファイルには、DatabricksがAWS環境（VPC等）内にWorkspaceとなるクラスタ（EC2等）を自動構築・管理するために必要な権限がまとまっています。
    - ※このファイルの出所はhttps://docs.databricks.com/aws/en/admin/workspace/create-uc-workspaceです。20260308時点では修正箇所あり。"ec2:DescribeNetworkAcls","ec2:DescribeVpcAttribute"。また、S3の権限も付与。詳細は別ドキュメント「northwind-databricks-workspace-role差分事件」参照。

14. 「次へ」＞ ポリシー名（例: `databricks-workspace-policy`）を付けて保存します。
15. **【Databricks画面へ戻る】** Databricksの登録画面に戻り、コピーした **ロールARN** を貼り付けて「Save（または Add）」をクリックして保存します。

**② Storage（ストレージ設定）の登録**
Databricksがワークスペースのライブラリやログなどを保存するためのS3バケットを登録します。
1. **【Databricks画面】** **Cloud resources** 画面の中の **Storage** タブを開き、「Add storage configuration」をクリックします。
2. **【Databricks画面】** 以下の項目を入力します：
   - **ストレージ設定名**: 任意の名前（例: `northwind-storage`）
   - **バケット名**: Phase 1のCloudFormation出力にある **`S3BucketName`** の値（例: `lake-northwind-78XXXXXXXXXX`）を入力します。
   - **IAMロールARN**: 今度は IAMロールARN に northwind-databricks-workspace-role のARN を入力してください（空欄にしない）。
3. **【Databricks画面】** **「ポリシーを生成」** ボタンをクリックすると、このS3バケットに設定すべき「バケットポリシーのJSONコード」が表示されます。
   - ⚠️ **【超重要ポイント】** この「ポリシー生成」作業は、**必ずこのタイミング（ストレージ設定の追加画面が開いている間、追加を押すまで）**にやってください。これをやらないと、後でjsonコードが自動生成されなくなります。
  - 💡 **もしポリシーのコピーを忘れたり、画面を閉じてしまった場合**：
     - 本ドキュメントと同階層にある **`databricks_bucket_policy_template.json`** を開きます。
     - コード内の `<s3-bucket-name>`（2箇所）を実際のバケット名に**`S3BucketName`** の値（例: `lake-northwind-78XXXXXXXXXX`）に書き換えれば、同じポリシーとして機能します。これをS3に貼り付けてください。
4. **【AWS画面】** そのポリシーJSONをコピーした状態で、別タブで **AWS S3 管理画面** を開きます。
   - 該当バケット（`lake-northwind-...`）を開き、**「アクセス許可」タブ** ＞ **「バケットポリシー」** の「編集」をクリックし、先ほどのJSONを貼り付けて保存（上書き）します。
   - ※これでDenyだったものがallowになります。
5. **【Databricks画面】** AWS側での保存が終わったらDatabricks画面に戻り、右下の「Save（または Add）」をクリックして保存します。

**③ Network（ネットワーク）の登録**
Phase 1で作成した自分のVPCをDatabricksが使えるようネットワーク設定を登録します。
1. **【Databricks画面】** **Cloud resources** 画面の中の **Network** タブを開き、「Add network configuration」をクリックします。
2. **【Databricks画面】** 以下の項目を入力します：
   - **ネットワーク設定名**: 任意の名前（例: `northwind-network`）
   - **VPC ID**: Phase 1のCloudFormation出力にある **`VPCId`** の値（例: `vpc-08XXXXXXXXXXXXX`）
   - **サブネットID** (2つ必要): Phase 1のCloudFormation出力にある **`PrivateSubnetId`** の値と、もう一つのPrivate SubnetのIDを入力します。
     - ※2つ目のサブネットIDはCloudFormation出力にないため、**【AWS画面】** VPC管理画面 ＞ 左メニュー「サブネット」から `northwind-private-subnet-2` を検索してIDをコピーしてきてください。
     - ※ただのバックアップサーバー用のサブネット。CloudFormationで指定を省略した。
   - **セキュリティグループID**: CloudFormation出力の **`DatabricksComputeSGId`** の値（例: `sg-XXXXXXXXXXXXX`）を指定します。
     - ⚠️ `RDSSecurityGroupId`（RDS用）ではない方です。名前に「Compute」または「Databricks」が含まれている方を選んでください。
   - **バックエンドプライベート接続 (VPCエンドポイント)**: 
     - 「セキュアなクラスター接続を中継するためのVPCエンドポイント」
     - 「REST API用のVPCエンドポイント」
     - 今回の構成ではこの2つは使用しないため、**両方とも空欄のままでOK**です。
3. **【Databricks画面】** 右下の「Add」をクリックして保存します。

### Step 2-3: ワークスペースの作成
準備が整ったので、ついにワークスペースを作ります。
1. **【Databricks画面】** Account Consoleの左メニューから **Workspaces** をクリックし、右上の **Create workspace** をクリックします。
2. **【Databricks画面】** 画面の入力方法として「Quickstart」ではなく、詳細設定ができる **Custom**（または Custom workspace）を選択します。（UIによっては最初からCustom入力画面になっています）
3. **【Databricks画面】** 以下の通り入力します：
   - **ワークスペース名**: 任意の名前（例: `northwind-workspace`）
   - **リージョン**: `Tokyo (ap-northeast-1)`
   - **ストレージとコンピュート**: ⚠️必ず **「既存のクラウドアカウントを使用」** を選択してください。（これが、これまで作ってきた自前のVPCやStorageを使うための設定です）
   - **Credential**（資格情報）: Step 2-2①で作ったもの（`northwind-credential`）を選択
   - **Storage configuration**（ストレージ設定）: Step 2-2②で作ったもの（`northwind-storage`）を選択
   - **Network configuration**（ネットワーク設定）: Step 2-2③で作ったもの（`northwind-network`）を選択
4. **【Databricks画面】** 右下の **Save**（または Create）をクリックします。
5. **【Databricks画面】** 構築が始まります。ステータスが `Running`（緑色）になったら、作成されたワークスペース名のリンク、または **[Open workspace]** をクリックしてワークスペースに入ります。

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
