# NAT Gateway 時間制限運用 実施手順書 / NAT Gateway Time-Limited Operation Guide（Story 1-6 / Sprint 2）

## 概要 / Overview

| 項目 / Item | 内容 / Details |
|-----|------|
| 対象 Story | 1-6 |
| Epic | Epic 1: パイプラインの仕上げと自動化 / Pipeline Finalization & Automation |
| 目的 / Purpose | NAT Gateway をパイプライン実行時のみ作成し、終了後に削除することでコストを最小化する / Minimize costs by creating NAT Gateway only during pipeline execution and deleting it afterward |
| 前提 / Prerequisites | Story 1-3（Databricks Workflows Job `northwind_daily_pipeline`）が設定済みであること / Story 1-3 (Databricks Workflows Job) must be configured |

### なぜ NAT Gateway の時間制限運用が必要なのか？ / Why is time-limited NAT Gateway operation needed?

NAT Gateway（ナットゲートウェイ）とは、プライベートサブネット内のリソース（Databricks のクラスターなど）がインターネットに出るための「出口」です。

| 状態 / State | 月額コスト / Monthly Cost | 説明 / Description |
|---|---|---|
| 常時起動（24h/365日） / Always-on | **約 $45/月** | 使っていない時間も課金される / Charged even when idle |
| パイプライン実行時のみ（約30分/日） / Pipeline-only (~30min/day) | **約 $0.95/月** | 必要な時だけ起動 → **約97%コスト削減** / Created on-demand → ~97% cost reduction |

### 仕組みの全体像 / Architecture Overview

> **重要な設計ポイント / Critical Design Point:**
> Databricks の Job Cluster はコントロールプレーンとの通信に NAT Gateway が必要です。つまり、NAT Gateway が存在しない状態では Job Cluster を起動できません（鶏と卵問題）。
> この問題を解決するため、NAT Gateway の作成は **EventBridge Scheduler** で Databricks Job の開始 **10分前** に自動実行します。
>
> Databricks Job Clusters require NAT Gateway for control plane communication. Without NAT Gateway, clusters cannot start (chicken-and-egg problem).
> To solve this, NAT Gateway creation is triggered **10 minutes before** the Databricks Job via **EventBridge Scheduler**.

```
┌──────────────────────────────────────────────────────────────┐
│  Amazon EventBridge Scheduler                                │
│                                                              │
│  スケジュール / Schedule:                                      │
│  cron(0 21 ? * * *)  ← 毎日 06:00 JST (UTC 21:00)           │
│     → northwind-nat-create Lambda を実行                      │
│     → NAT Gateway 作成（約3分で完了）                          │
│     → Create NAT Gateway (~3 min to complete)                │
└──────────────────────────────────────────────────────────────┘
                         ↓  10分後 / 10 min later
┌──────────────────────────────────────────────────────────────┐
│  Databricks Workflows Job: northwind_daily_pipeline          │
│  スケジュール / Schedule: 06:10 JST                            │
│  （NAT Gateway が既に Available のため、クラスター起動可能）      │
│  (NAT Gateway is already Available, so cluster can start)    │
│                                                              │
│  ┌──────────────┐                                            │
│  │ Task 1       │                                            │
│  │ bronze_ingest│  既存のETLパイプライン                        │
│  └──────┬───────┘  Existing ETL pipeline                     │
│         ↓                                                    │
│  ┌──────────────┐                                            │
│  │ Task 2       │                                            │
│  │ silver_      │                                            │
│  │ transform    │                                            │
│  └──────┬───────┘                                            │
│         ↓                                                    │
│  ┌──────────────┐                                            │
│  │ Task 3       │                                            │
│  │ gold_        │                                            │
│  │ aggregate    │                                            │
│  └──────┬───────┘                                            │
│         ↓                                                    │
│  ┌──────────────┐                                            │
│  │ Task 4       │  Lambda を呼び出して                         │
│  │ nat_delete   │  NAT Gateway を削除する                      │
│  │ (Lambda呼出) │  Call Lambda to delete NAT Gateway           │
│  │ Run if:      │  成功でも失敗でも実行                         │
│  │ All done     │  Runs on success or failure                  │
│  └──────────────┘                                            │
└──────────────────────────────────────────────────────────────┘
```

### 関連ノートブック / Related Notebooks

| ノートブック / Notebook | 用途 / Purpose |
|------------|------|
| `notebooks_sprint2/story1-6/nb_01_nat_create_lambda.py` | NAT Gateway 作成用 Lambda 関数コード / Lambda function code to create NAT Gateway |
| `notebooks_sprint2/story1-6/nb_02_nat_delete_lambda.py` | NAT Gateway 削除用 Lambda 関数コード / Lambda function code to delete NAT Gateway |
| `notebooks_sprint2/story1-6/nb_03_nat_verify.py` | 動作確認用ノートブック（Databricks上で実行） / Verification notebook (run on Databricks) |

---

## Phase 1: 既存 NAT Gateway の削除（手動） / Remove Existing NAT Gateway (Manual)

### 目的 / Purpose

現在 CloudFormation で常時起動している NAT Gateway を削除し、Lambda による動的管理に切り替える準備をする。

Remove the always-on NAT Gateway currently managed by CloudFormation, preparing for dynamic management via Lambda.

### Step 1-1: 現在の NAT Gateway を確認する / Confirm current NAT Gateway

**目的**: 削除対象の NAT Gateway が存在することを確認する。

1. ブラウザで **AWS Management Console** にログインする
   - Login to the AWS Management Console in your browser
2. 画面上部の検索バー（Search bar）に **`VPC`** と入力し、**VPC サービス** を開く
   - Type `VPC` in the top search bar and open the VPC service
3. 左メニューから **「NAT ゲートウェイ」（NAT gateways）** をクリックする
   - Click **"NAT gateways"** in the left menu
4. `northwind-nat` という名前の NAT Gateway が **Available** 状態であることを確認する
   - Confirm that `northwind-nat` is in **Available** state

> **用語解説 / Glossary:**
> - **NAT Gateway**: プライベートネットワーク内のサーバーがインターネットにアクセスするための「翻訳機」。外からは入れないが、中からは出られる仕組み。
>   A "translator" that allows servers in a private network to access the internet. Traffic can go out but not come in.
> - **Available**: 正常に動作中の状態。
>   Operational and running state.

### Step 1-2: CloudFormation テンプレートから NAT Gateway リソースを除外する / Remove NAT Gateway resources from CloudFormation template

**目的**: CloudFormation の管理対象から NAT Gateway を外し、Lambda で管理できるようにする。

> **重要 / IMPORTANT**: CloudFormation テンプレートからリソース定義を削除してスタック更新すると、実際の AWS リソースも自動的に削除されます。手動で AWS コンソールから NAT Gateway を削除する必要はありません。
>
> When you remove resource definitions from a CloudFormation template and update the stack, the actual AWS resources are automatically deleted. You do NOT need to manually delete the NAT Gateway from the AWS console.

1. リポジトリ内の `cloudformation.yaml` を開く
   - Open `cloudformation.yaml` in the repository

2. 以下の **3つのリソース** をコメントアウトまたは削除する
   - Comment out or delete the following **3 resources**:

```yaml
# ---- 削除対象 1: Elastic IP (NAT Gateway 用の固定IPアドレス) ----
# ---- Resource to remove 1: Elastic IP for NAT Gateway ----
  # NatGatewayEIP:
  #   Type: AWS::EC2::EIP
  #   ...

# ---- 削除対象 2: NAT Gateway 本体 ----
# ---- Resource to remove 2: NAT Gateway itself ----
  # NatGateway:
  #   Type: AWS::EC2::NatGateway
  #   ...

# ---- 削除対象 3: プライベートルートの NAT Gateway 参照 ----
# ---- Resource to remove 3: Private route referencing NAT Gateway ----
  # DefaultPrivateRoute の NatGatewayId 行を削除
```

3. `DefaultPrivateRoute` は **削除せず**、ルートテーブル自体は残す（Lambda が後でルートを追加・削除するため）
   - Do **NOT** delete `DefaultPrivateRoute` — keep the route table (Lambda will add/remove routes dynamically)

具体的には、`DefaultPrivateRoute` を以下のように変更する:

**変更前 / Before:**
```yaml
  DefaultPrivateRoute:
    Type: AWS::EC2::Route
    Properties:
      RouteTableId: !Ref PrivateRouteTable
      DestinationCidrBlock: 0.0.0.0/0
      NatGatewayId: !Ref NatGateway
```

**変更後 / After（リソースごと削除する）:**
```yaml
  # DefaultPrivateRoute: Lambda による動的管理に移行 / Migrated to Lambda dynamic management
```

### Step 1-3: CloudFormation スタックを更新する / Update CloudFormation stack

**目的**: テンプレートの変更を AWS に反映し、NAT Gateway を実際に削除する。

1. AWS Management Console → **CloudFormation** を開く
   - Open **CloudFormation** in the AWS Management Console
2. スタック `northwind-lakehouse` をクリックする
   - Click on stack `northwind-lakehouse`
3. 画面右上の **「更新」（Update）** ボタンをクリックする
   - Click the **"Update"** button in the top right
4. **「既存テンプレートを置き換える」（Replace existing template）** を選択する
   - Select **"Replace existing template"**
5. **「テンプレートファイルのアップロード」（Upload a template file）** を選択し、修正した `cloudformation.yaml` をアップロードする
   - Select **"Upload a template file"** and upload the modified `cloudformation.yaml`
6. **「次へ」（Next）** を3回クリックし、確認画面まで進む
   - Click **"Next"** 3 times to reach the review screen
7. 「変更セットのプレビュー（Change set preview）」で以下を確認する:
   - Confirm the following in the "Change set preview":
   - `NatGatewayEIP` — **Remove**
   - `NatGateway` — **Remove**
   - `DefaultPrivateRoute` — **Remove**
8. **IAM 承認チェックボックス** にチェックを入れ、**「送信」（Submit）** をクリックする
   - Check the **IAM acknowledgment checkbox** and click **"Submit"**
9. ステータスが **`UPDATE_COMPLETE`** になるまで待つ（2〜5分）
   - Wait until the status shows **`UPDATE_COMPLETE`** (2-5 minutes)

### Step 1-4: NAT Gateway が削除されたことを確認する / Verify NAT Gateway deletion

1. **VPC** → **NAT ゲートウェイ（NAT gateways）** を開く
   - Open **VPC** → **NAT gateways**
2. `northwind-nat` のステータスが **Deleted** になっていることを確認する
   - Confirm `northwind-nat` status is **Deleted**

> **確認ポイント / Checkpoint**: この時点で NAT Gateway は存在しないため、Databricks クラスターからインターネットへの外向き通信（GitHub からのダウンロードなど）はできなくなります。パイプラインが正常に動くのは Lambda が NAT Gateway を動的に作成してからです。
>
> At this point, outbound internet access from Databricks clusters is unavailable. The pipeline will only work after Lambda dynamically creates the NAT Gateway.

---

## Phase 2: Lambda 関数の作成 / Create Lambda Functions

### 目的 / Purpose

NAT Gateway を作成する Lambda 関数と、削除する Lambda 関数の2つを AWS 上に作成する。

Create two Lambda functions on AWS: one to create the NAT Gateway and one to delete it.

> **用語解説 / Glossary:**
> - **Lambda 関数（Lambda function）**: AWS 上で短いプログラムを実行するサービス。サーバーを用意する必要がなく、呼び出された時だけ動く。
>   An AWS service that runs short programs. No server setup needed — runs only when invoked.
> - **IAM ロール（IAM Role）**: Lambda 関数に「何をしていいか」を定義する権限証明書のようなもの。
>   A permissions certificate defining what the Lambda function is allowed to do.

### Step 2-1: Lambda 用 IAM ポリシーとロールを作成する / Create IAM Policy and Role for Lambda

**目的**: Lambda 関数が NAT Gateway・Elastic IP・ルートテーブルを操作できるようにする権限を与える。

> **手順の流れ / Flow:**
> AWS Console のロール作成ウィザードでは、カスタムポリシーを途中で新規作成することができません。そのため**「ポリシー → ロール」の順**で作成します。
>
> In AWS Console, you cannot create a new custom policy mid-way through the role creation wizard. Therefore, create them in order: **policy first, then role**.

#### Step 2-1a: ポリシーを先に作成する / Create the permissions policy first

1. AWS Management Console → 検索バーに **`IAM`** と入力 → **IAM** を開く
   - Search for `IAM` and open the IAM service
2. 左メニューから **「ポリシー」（Policies）** をクリックする
   - Click **"Policies"** in the left menu
3. **「ポリシーの作成」（Create policy）** ボタンをクリックする
   - Click **"Create policy"**
4. **「ポリシーエディタ（Policy editor）」** セクションが表示される。デフォルトは **「ビジュアル（Visual）」** モード（ドロップダウン選択形式）になっている
   - The **"Policy editor"** section appears. It defaults to **Visual** mode (dropdown selectors).
5. エディタ上部の **「JSON」** ボタンをクリックして JSON 入力モードに切り替える
   - Click the **"JSON"** button at the top of the editor to switch to JSON input mode

   > **場所の目安 / Location**: エディタの上部に「ビジュアル（Visual）」「JSON」の 2 つのボタンがある。「JSON」をクリックするとテキスト入力エリアが表示される。
   > There are two buttons at the top of the editor: "Visual" and "JSON". Clicking "JSON" reveals a text input area.

6. 既存の内容を**すべて削除**し、以下の JSON を貼り付ける
   - **Delete all** existing content and paste the following JSON:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "NATGatewayManagement",
      "Effect": "Allow",
      "Action": [
        "ec2:CreateNatGateway",
        "ec2:DeleteNatGateway",
        "ec2:DescribeNatGateways",
        "ec2:AllocateAddress",
        "ec2:ReleaseAddress",
        "ec2:DescribeAddresses",
        "ec2:CreateRoute",
        "ec2:DeleteRoute",
        "ec2:DescribeRouteTables",
        "ec2:DescribeSubnets",
        "ec2:CreateTags"
      ],
      "Resource": "*"
    },
    {
      "Sid": "CloudWatchLogs",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

7. **「次へ」（Next）** をクリックする
   - Click **"Next"**
8. ポリシー名（Policy name）に **`northwind-nat-gateway-manager-policy`** と入力する
   - Enter **`northwind-nat-gateway-manager-policy`** as the policy name
9. **「ポリシーの作成」（Create policy）** をクリックする
   - Click **"Create policy"**

#### Step 2-1b: ロールを作成し、ポリシーをアタッチする / Create the role and attach the policy

1. 左メニューから **「ロール」（Roles）** をクリックする
   - Click **"Roles"** in the left menu
2. **「ロールを作成」（Create role）** ボタンをクリックする
   - Click **"Create role"**
3. 以下を設定する / Configure as follows:

| 設定項目 / Setting | 値 / Value | 説明 / Explanation |
|---|---|---|
| 信頼されたエンティティタイプ / Trusted entity type | **AWS のサービス / AWS service** | Lambda がこのロールを使えるようにする |
| ユースケース / Use case | **Lambda** | Lambda 専用のロール |

4. **「次へ」（Next）** をクリックする
5. **「許可を追加」（Add permissions）** 画面の検索バーに **`northwind-nat-gateway-manager-policy`** と入力して検索する
   - On the "Add permissions" screen, search for **`northwind-nat-gateway-manager-policy`**
6. 表示されたポリシーの**チェックボックス**にチェックを入れる
   - Check the **checkbox** next to the policy
7. **「次へ」（Next）** をクリックする
   - Click **"Next"**
8. ロール名（Role name）に **`northwind-nat-gateway-lambda-role`** と入力する
   - Enter **`northwind-nat-gateway-lambda-role`** as the role name
9. **「ロールを作成」（Create role）** をクリックする
   - Click **"Create role"**

> **補足: 「信頼ポリシー」と「許可ポリシー」の違い / Trust policy vs. Permissions policy:**
> - **信頼ポリシー（Trust policy）**: 「誰がこのロールを使えるか」= Lambda がこのロールを使える。「AWS のサービス → Lambda」選択時に自動設定（JSON 不要）。
> - **許可ポリシー（Permissions policy）**: 「このロールが何をできるか」= Step 2-1a で作成した JSON がこれ（ec2:CreateNatGateway 等）。
>
> - **Trust policy**: "Who can assume this role" = Lambda can use it. Auto-configured by selecting "AWS service → Lambda" (no JSON needed).
> - **Permissions policy**: "What this role can do" = the JSON created in Step 2-1a (ec2:CreateNatGateway, etc.).

### Step 2-1c: Lambda コードで使用する実際の ID を取得する / Get the actual resource IDs for Lambda code

**目的**: CloudFormation で定義されたリソース（Public Subnet、Private Route Table）の実際の ID を取得する。

> **背景 / Background:**
> CloudFormation テンプレートにはリソースの定義がありますが、実際の ID（`subnet-0abc...`、`rtb-0abc...`）は AWS が自動生成するため、コンソールで確認する必要があります。

#### 方法 1: CloudFormation の「リソース」タブから取得（最も簡単）

1. AWS Management Console → 検索バーに **`CloudFormation`** と入力 → **CloudFormation** を開く
   - Search for `CloudFormation` and open the CloudFormation service
2. スタック一覧から **`northwind-lakehouse`** をクリックする
   - Click on **`northwind-lakehouse`** stack
3. **「リソース」（Resources）** タブをクリックする
   - Click the **"Resources"** tab
4. 以下の 2 つのリソースを探して、**「物理 ID」（Physical ID）** をコピーする:
   - Search for the following 2 resources and copy their **"Physical ID"**:

| 論理 ID / Logical ID | リソース名 / Resource Name | コピー対象 / Copy Value |
|---|---|---|
| `PublicSubnet` | northwind-public-subnet | **`subnet-0xxxxxxxxxx`** → `PUBLIC_SUBNET_ID` に設定 |
| `PrivateRouteTable` | northwind-private-rt | **`rtb-0xxxxxxxxxx`** → `PRIVATE_ROUTE_TABLE_ID` に設定 |

#### 方法 2: VPC コンソールから取得（確認用）

**Public Subnet ID を確認:**
1. AWS Console → **VPC** → **「サブネット」（Subnets）** をクリック
   - Click **VPC** → **"Subnets"**
2. `northwind-public` または `northwind-public-subnet` を検索して見つける
   - Search for `northwind-public` or `northwind-public-subnet`
3. **「サブネット ID」（Subnet ID）** をコピーする
   - Copy the **"Subnet ID"**

**Private Route Table ID を確認:**
1. AWS Console → **VPC** → **「ルートテーブル」（Route tables）** をクリック
   - Click **VPC** → **"Route tables"**
2. `northwind-private-rt` または `northwind-private` を検索して見つける
   - Search for `northwind-private-rt` or `northwind-private`
3. **「ルートテーブル ID」（Route Table ID）** をコピーする
   - Copy the **"Route Table ID"**

#### コードに設定する / Set in Lambda code

取得した ID を、後ほど作成する Lambda 関数コード内の以下の部分に設定します:

```python
PUBLIC_SUBNET_ID = "subnet-0xxxxxxxxxx"  # ← 上記で取得した Public Subnet ID
PRIVATE_ROUTE_TABLE_ID = "rtb-0xxxxxxxxxx"  # ← 上記で取得した Private Route Table ID
```

---

### Step 2-2: NAT Gateway 作成用 Lambda 関数を作成する / Create the NAT Gateway Creation Lambda

**目的**: EventBridge Scheduler から呼び出されて NAT Gateway を自動作成する Lambda 関数を作る。

1. AWS Management Console → 検索バーに **`Lambda`** と入力 → **Lambda** を開く
   - Search for `Lambda` and open the Lambda service
2. **「関数の作成」（Create function）** をクリックする
   - Click **"Create function"**
3. 以下を設定する / Configure as follows:

| 設定項目 / Setting | 値 / Value |
|---|---|
| オプション / Option | **一から作成 / Author from scratch** |
| 関数名 / Function name | **`northwind-nat-create`** |
| ランタイム / Runtime | **Python 3.12** |
| アーキテクチャ / Architecture | **x86_64** |
| 実行ロール / Execution role | **既存のロールを使用する / Use an existing role** |
| 既存のロール / Existing role | **`northwind-nat-gateway-lambda-role`**（Step 2-1 で作成したもの） |

4. **「関数の作成」（Create function）** をクリックする
   - Click **"Create function"**

5. コードエディタが表示される。以下の手順でコードを貼り付ける:
   - The code editor appears. Follow these steps to paste the code:

   1. エディタ左側のファイルツリーで **`lambda_function.py`** タブが選択されていることを確認する
      - Confirm **`lambda_function.py`** tab is selected in the file tree on the left side of the editor
   2. エディタ内の既存コード（`import json` 等のデフォルトコード）を**すべて選択して削除**する（Ctrl+A → Delete）
      - Select all existing code in the editor and delete it (Ctrl+A → Delete)
   3. **`nb_01_nat_create_lambda.py`** の内容を**まるごとコピーして貼り付ける**※lambda_function.pyというファイル名は直さないこと
      - Copy the entire content of **`nb_01_nat_create_lambda.py`** and paste it
   4. - Public Subnet ID、Private Route Table IDはダミーから実際の値を記入すること。
### 方法 1: CloudFormation の Outputs / リソースから取得（最も簡単）
1. AWS Console → **CloudFormation** → スタック **`northwind-lakehouse`** をクリック
2. **「リソース」（Resources）** タブをクリック
3. 以下を探して **「物理 ID」** をコピーする：
### 方法 2: VPC コンソールから取得

**Public Subnet ID:**
1. AWS Console → **VPC** → **サブネット（Subnets）**
2. **`northwind-public-subnet`** を探す
3. **Subnet ID** をコピー

**Private Route Table ID:**
1. AWS Console → **VPC** → **ルートテーブル（Route tables）**
2. **`northwind-private-rt`** を探す
3. **Route Table ID** をコピー


| 論理 ID（Logical ID） | 探す名前 | コピーする値（物理 ID） |
|---|---|---|
| **`PublicSubnet`** | `northwind-public-subnet` | `subnet-0xxxxxxxxxx` |
| **`PrivateRouteTable`** | `northwind-private-rt` | `rtb-0xxxxxxxxxx` |


   > **重要 / IMPORTANT**: `nb_01_nat_create_lambda.py` というファイル名のままアップロードしないこと。**必ず `lambda_function.py` の中身を置き換える形で**貼り付ける。ファイル名が違うと Lambda が `lambda_function` モジュールを見つけられず `Runtime.ImportModuleError` が発生する。
   >
   > Do NOT upload `nb_01_nat_create_lambda.py` as a file. **Always paste its content into `lambda_function.py`**. If the file name differs, Lambda cannot find the `lambda_function` module and throws `Runtime.ImportModuleError`.

6. **「Deploy」** ボタンをクリックしてデプロイする
   - Click the **"Deploy"** button to deploy

7. **「設定」（Configuration）** タブ → **「一般設定」（General configuration）** → **「編集」（Edit）** をクリックする
   - Click **"Configuration"** tab → **"General configuration"** → **"Edit"**

8. **タイムアウト（Timeout）** を **5分（5 min 0 sec）** に変更する（NAT Gateway の作成には1〜3分かかるため）
   - Change **Timeout** to **5 minutes** (NAT Gateway creation takes 1-3 minutes)

9. **「保存」（Save）** をクリックする
   - Click **"Save"**

> **冪等性について / About Idempotency:**
> この Lambda 関数には**冪等性チェック**が組み込まれています。既に Lambda が管理する NAT Gateway（`ManagedBy=lambda-nat-manager` タグ）が存在する場合、新しい NAT Gateway を作成せずに既存のものを返します。これにより、EventBridge Scheduler の二重実行や手動での誤呼出しでも安全です。
>
> This Lambda function has a built-in **idempotency check**. If a Lambda-managed NAT Gateway (tagged `ManagedBy=lambda-nat-manager`) already exists, it returns the existing one instead of creating a new one. This makes it safe even if EventBridge fires twice or the function is manually invoked.

### Step 2-3: NAT Gateway 削除用 Lambda 関数を作成する / Create the NAT Gateway Deletion Lambda

**目的**: パイプライン終了後に NAT Gateway を自動削除する Lambda 関数を作る。

Step 2-2 と同様の手順で、以下の設定で作成する:

| 設定項目 / Setting | 値 / Value |
|---|---|
| 関数名 / Function name | **`northwind-nat-delete`** |
| ランタイム / Runtime | **Python 3.12** |
| 実行ロール / Existing role | **`northwind-nat-gateway-lambda-role`**（同じロールを使用） |
| タイムアウト / Timeout | **10分（10 min 0 sec）** |
| コード / Code | `lambda_function.py` の中身を削除し、**`nb_02_nat_delete_lambda.py`** の内容を貼り付ける（Step 2-2 の手順5と同様） ※lambda_function.pyというファイル名は直さないこと|

> **タイムアウトが10分の理由 / Why 10 minutes:**
> 削除 Lambda は NAT Gateway の削除待機（最大15秒 x 20回 = 5分）+ Elastic IP の解放を行います。全体で5分を超える可能性があるため、余裕を持って **10分** に設定します。
>
> The delete Lambda polls for NAT Gateway deletion (up to 15s x 20 = 5 min) plus EIP release. The total may exceed 5 minutes, so we set **10 minutes** for safety.

### Step 2-4: Lambda 関数のテスト（作成） / Test Lambda Function (Create)

**目的**: NAT Gateway が正しく作成されることを確認する。

1. Lambda コンソールで **`northwind-nat-create`** を開く
   - Open **`northwind-nat-create`** in the Lambda console
2. **「テスト」（Test）** タブをクリックする
   - Click the **"Test"** tab
3. テストイベント名（Event name）に **`test-create`** と入力する
   - Enter **`test-create`** as the event name
4. イベント JSON はデフォルトの `{}` のまま、**「テスト」（Test）** ボタンをクリックする
   - Leave the event JSON as default `{}` and click **"Test"**
5. 実行結果が **Succeeded**（緑色）になることを確認する
   - Confirm the execution result is **Succeeded** (green)
6. レスポンスに以下が含まれることを確認する:
   - Confirm the response contains:
   - `"statusCode": 200`
   - `"nat_gateway_id": "nat-xxxxx"`
   - `"state": "available"`

> **注意 / Note**: NAT Gateway の作成には1〜3分かかります。Lambda のタイムアウトが5分に設定されていることを確認してください。
>
> NAT Gateway creation takes 1-3 minutes. Ensure the Lambda timeout is set to 5 minutes.

> **冪等性の確認 / Verify Idempotency**: テストボタンを **もう一度クリック** して、2回目のレスポンスに `"message": "NAT Gateway already exists (idempotent)"` が含まれることを確認してください。これにより、二重作成が防止されていることが確認できます。
>
> Click **Test again** and verify the second response contains `"message": "NAT Gateway already exists (idempotent)"`. This confirms duplicate creation is prevented.

### Step 2-5: Lambda 関数のテスト（削除） / Test Lambda Function (Delete)

**目的**: NAT Gateway が正しく削除されることを確認する。

1. Lambda コンソールで **`northwind-nat-delete`** を開く
   - Open **`northwind-nat-delete`** in the Lambda console
2. **「テスト」（Test）** タブで、イベント JSON を `{}` のまま **「テスト」（Test）** をクリックする
   - In the **"Test"** tab, leave event JSON as `{}` and click **"Test"**
3. 実行結果が **Succeeded**（緑色）になることを確認する
   - Confirm the execution result is **Succeeded** (green)
4. レスポンスに `"statusCode": 200` が含まれることを確認する
   - Confirm the response contains `"statusCode": 200`

### Step 2-6: AWS コンソールで結果を確認する / Verify results in AWS Console

1. **VPC** → **NAT ゲートウェイ（NAT gateways）** を開く
   - Open **VPC** → **NAT gateways**
2. Step 2-4 で作成された NAT Gateway が **Deleted** 状態になっていることを確認する（削除後しばらく表示される）
   - Confirm the NAT Gateway created in Step 2-4 is in **Deleted** state

---

## Phase 3: EventBridge Scheduler の設定 / Configure EventBridge Scheduler

### 目的 / Purpose

Databricks Job の開始前に NAT Gateway を自動的に作成する EventBridge スケジュールを設定する。

Configure an EventBridge schedule to automatically create the NAT Gateway before the Databricks Job starts.

> **なぜ EventBridge Scheduler を使うのか？ / Why use EventBridge Scheduler?**
>
> Databricks の Job Cluster が起動するとき、コントロールプレーン（Databricks のクラウドサービス側）との通信が必要です。この通信には NAT Gateway 経由のインターネットアクセスが必要です。
>
> もし NAT Gateway の作成を Databricks Job のタスクとして実行しようとすると、「NAT Gateway がないから Job Cluster が起動できない → Job Cluster が起動できないから NAT Gateway を作成できない」という**鶏と卵問題（chicken-and-egg problem）**が発生します。
>
> EventBridge Scheduler は AWS 側で独立して動作するため、Databricks に依存せずに Lambda 関数を定期実行できます。
>
> When a Databricks Job Cluster starts, it needs internet access via NAT Gateway to communicate with the control plane. If we tried to create the NAT Gateway as a Databricks task, we'd face a **chicken-and-egg problem**: no NAT → cluster can't start → can't create NAT.
>
> EventBridge Scheduler runs independently on the AWS side, so it can invoke Lambda without depending on Databricks.

> **用語解説 / Glossary:**
> - **EventBridge Scheduler**: AWS が提供するスケジュール実行サービス。cron 式で定期的にターゲット（Lambda など）を自動実行できる。CloudWatch Events の後継サービス。
>   An AWS scheduling service. Automatically executes targets (like Lambda) on a cron schedule. Successor to CloudWatch Events.
> - **cron 式**: 「毎日何時に実行する」などのスケジュールを記述する書式。`cron(分 時 日 月 曜日 年)` の形式。
>   A format to describe schedules like "run daily at a specific time". Format: `cron(min hour day month weekday year)`.

### Step 3-1: EventBridge Scheduler 用 IAM ロールを作成する / Create IAM Role for EventBridge Scheduler

**目的**: EventBridge Scheduler が Lambda 関数を呼び出せるようにする権限を与える。

1. AWS Management Console → **IAM** → **「ロール」（Roles）** を開く
   - Open **IAM** → **"Roles"**
2. **「ロールを作成」（Create role）** をクリックする
   - Click **"Create role"**
3. 以下を設定する / Configure as follows:

| 設定項目 / Setting | 値 / Value | 説明 / Explanation |
|---|---|---|
| 信頼されたエンティティタイプ / Trusted entity type | **AWS のサービス / AWS service** | EventBridge がこのロールを使えるようにする |
| ユースケース / Use case | 検索バーに **`EventBridge`** と入力 → **EventBridge Scheduler** を選択 | EventBridge Scheduler 専用のロール |

4. **「次へ」（Next）** をクリックする

5. **「許可を追加」（Add permissions）** 画面で、**「ポリシーを作成」（Create policy）** をクリックする（新しいタブが開く）

6. **JSON** タブで以下を貼り付ける:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "InvokeNATCreateLambda",
      "Effect": "Allow",
      "Action": "lambda:InvokeFunction",
      "Resource": "arn:aws:lambda:ap-northeast-1:*:function:northwind-nat-create"
    }
  ]
}
```

7. ポリシー名に **`northwind-eventbridge-nat-policy`** と入力し、**「ポリシーの作成」（Create policy）** をクリック
   - Enter **`northwind-eventbridge-nat-policy`** and click **"Create policy"**
8. 元のタブに戻り、更新 → **`northwind-eventbridge-nat-policy`** を検索・選択する
   - Return, refresh, search and select **`northwind-eventbridge-nat-policy`**
9. **「次へ」（Next）** をクリックする
10. ロール名に **`northwind-eventbridge-nat-role`** と入力する
    - Enter **`northwind-eventbridge-nat-role`** as the role name
11. **「ロールを作成」（Create role）** をクリックする
    - Click **"Create role"**

### Step 3-2: EventBridge スケジュールを作成する / Create EventBridge Schedule

**目的**: 毎日 06:00 JST に NAT Gateway 作成 Lambda を自動実行するスケジュールを作成する。

1. AWS Management Console → 検索バーに **`EventBridge`** と入力 → **Amazon EventBridge** を開く
   - Search for `EventBridge` and open Amazon EventBridge
2. 左メニューから **「スケジュール」（Schedules）** をクリックする（「Scheduler」セクション内）
   - Click **"Schedules"** in the left menu (under the "Scheduler" section)
3. **「スケジュールを作成」（Create schedule）** をクリックする
   - Click **"Create schedule"**

4. **「スケジュールの詳細を指定」（Specify schedule detail）** で以下を設定する:

| 設定項目 / Setting | 値 / Value | 説明 / Explanation |
|---|---|---|
| スケジュール名 / Schedule name | **`northwind-nat-create-schedule`** | わかりやすい名前 |
| スケジュールグループ / Schedule group | **default** | デフォルトグループを使用 |
| スケジュールの種類 / Schedule type | **定期的なスケジュール / Recurring schedule** | 毎日繰り返し実行 |
| スケジュールの種類 / Schedule type | **cron ベースのスケジュール / Cron-based schedule** | cron 式で指定 |
| cron 式 / Cron expression | **`cron(0 21 ? * * *)`** | UTC 21:00 = JST 06:00 |
| フレキシブルタイムウィンドウ / Flexible time window | **オフ / Off** | 正確な時刻に実行する |
| タイムゾーン / Timezone | **UTC** | cron 式は UTC で指定済み |

> **cron 式の読み方 / How to read the cron expression:**
> `cron(0 21 ? * * *)` = 「毎日 UTC 21:00（= JST 06:00）に実行する」
> - `0` = 0分（毎時0分）
> - `21` = 21時（UTC）= 日本時間 06:00
> - `?` = 日（特定の日は指定しない）
> - `*` = 毎月、毎曜日、毎年

5. **「次へ」（Next）** をクリックする

6. **「ターゲットを選択」（Select target）** で以下を設定する:

| 設定項目 / Setting | 値 / Value |
|---|---|
| ターゲット API / Target API | **AWS Lambda — Invoke** |
| Lambda 関数 / Lambda function | **`northwind-nat-create`** |
| ペイロード / Payload | `{}` （デフォルトのまま） |

7. **「次へ」（Next）** をクリックする

8. **「設定」（Settings）** で以下を設定する:

| 設定項目 / Setting | 値 / Value | 説明 / Explanation |
|---|---|---|
| リトライポリシー / Retry policy | **有効 / Enabled** | 失敗時にリトライする |
| 最大リトライ回数 / Maximum retry attempts | **2** | 最大2回リトライ |
| 最大イベント経過時間 / Maximum event age | **1時間 / 1 hour** | 1時間以内にリトライ |
| 実行ロール / Execution role | **既存のロールを使用 / Use existing role** → **`northwind-eventbridge-nat-role`** | Step 3-1 で作成したロール |

9. **「次へ」（Next）** をクリックし、確認画面で **「スケジュールを作成」（Create schedule）** をクリックする
   - Click **"Next"** and then **"Create schedule"** on the review screen

### Step 3-3: Databricks Job のスケジュールを確認・調整する / Verify/Adjust Databricks Job Schedule

**目的**: Databricks Job が EventBridge によるNAT Gateway 作成の **10分後** に開始するようにする。

> **タイミングの考え方 / Timing rationale:**
> NAT Gateway の作成には通常1〜3分かかります。10分の余裕があれば、NAT Gateway が確実に Available 状態になった後に Databricks Job が開始されます。
>
> NAT Gateway creation typically takes 1-3 minutes. A 10-minute buffer ensures the NAT Gateway is Available before the Databricks Job starts.

1. Databricks UI → 左メニュー **「ジョブとパイプライン」（Jobs）** をクリック
   - Click **"Jobs"** in the Databricks left menu
2. **`northwind_daily_pipeline`** をクリックして開く
   - Click to open **`northwind_daily_pipeline`**
3. **「スケジュール」（Schedule）** セクションを確認する
   - Check the **"Schedule"** section
4. スケジュールが設定されている場合、開始時刻を EventBridge スケジュールの **10分後**（例: **06:10 JST**）に設定する
   - If a schedule is configured, set the start time to **10 minutes after** the EventBridge schedule (e.g., **06:10 JST**)

| EventBridge (NAT 作成) | Databricks Job (パイプライン) | 差分 |
|---|---|---|
| 06:00 JST | **06:10 JST** | 10分の余裕 |

**スクリーンショットを取得する / Take a screenshot**

---

## Phase 4: Databricks Workflows Job の更新 / Update Databricks Workflows Job

### 目的 / Purpose

既存の `northwind_daily_pipeline` Job に NAT Gateway 削除タスクを追加し、パイプライン完了後に NAT Gateway を自動削除する構成にする。

Add a NAT Gateway deletion task to the existing `northwind_daily_pipeline` Job so the NAT Gateway is automatically deleted after pipeline completion.

> **注意 / Note**: NAT Gateway の**作成**は Phase 3 で設定した EventBridge Scheduler が行います。Databricks Job 内では**削除のみ**を行います。
>
> NAT Gateway **creation** is handled by EventBridge Scheduler (Phase 3). The Databricks Job only handles **deletion**.

### Step 4-1: Lambda 削除呼出権限の追加 / Add Lambda delete invocation permission

**目的**: Databricks クラスター（EC2）が NAT Gateway 削除 Lambda を呼び出せるようにする。

1. AWS Management Console → **IAM** → **「ロール」（Roles）** を開く
   - Open **IAM** → **"Roles"** in AWS Console
2. Databricks のワークスペースロール（例: `northwind-workspace-role`）を検索して開く
   - Search for and open the Databricks workspace role (e.g., `northwind-workspace-role`)
3. **「許可を追加」（Add permissions）** → **「インラインポリシーを作成」（Create inline policy）** をクリック
   - Click **"Add permissions"** → **"Create inline policy"**
4. **JSON** タブで以下を貼り付ける:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "InvokeNATDeleteLambda",
      "Effect": "Allow",
      "Action": "lambda:InvokeFunction",
      "Resource": "arn:aws:lambda:ap-northeast-1:*:function:northwind-nat-delete"
    }
  ]
}
```

5. ポリシー名に **`northwind-lambda-invoke-policy`** と入力し、**「ポリシーの作成」（Create policy）** をクリック
   - Enter **`northwind-lambda-invoke-policy`** as the name and click **"Create policy"**

### Step 4-2: NAT 削除用ノートブックを Databricks にアップロードする / Upload NAT delete notebook to Databricks

**目的**: `nat_delete` タスクで使用するノートブックを Databricks ワークスペースに配置する。

1. Databricks UI → 左メニュー **「ワークスペース」（Workspace）** をクリック
   - Click **"Workspace"** in the Databricks left menu
2. 適切なフォルダ（例: `/Workspace/northwind/operations/`）に移動する
   - Navigate to an appropriate folder (e.g., `/Workspace/northwind/operations/`)
3. 新しいノートブックを作成し、名前を **`nat_delete`** とする
   - Create a new notebook named **`nat_delete`**
4. 以下のコードを貼り付ける（`nb_03_nat_verify.py` のセル3相当）:

```python
import boto3
import json
from botocore.config import Config

# boto3 の read_timeout を延長する（Lambda の同期呼出は最大10分かかるため）
# Extend boto3 read_timeout (synchronous Lambda invocation takes up to 10 min)
lambda_config = Config(
    read_timeout=900,  # 15分 / 15 minutes (delete Lambda timeout is 10 min)
    retries={"max_attempts": 0},
)
lambda_client = boto3.client("lambda", region_name="ap-northeast-1", config=lambda_config)

print("NAT Gateway 削除 Lambda を呼び出し中... / Invoking NAT Gateway delete Lambda...")
print("(完了まで2〜5分かかります / Takes 2-5 minutes to complete)")

response = lambda_client.invoke(
    FunctionName="northwind-nat-delete",
    InvocationType="RequestResponse",
)

payload = json.loads(response["Payload"].read().decode("utf-8"))
status_code = payload.get("statusCode", 0)

print(f"\nLambda 実行結果 / Lambda result:")
print(json.dumps(payload, indent=2, ensure_ascii=False))

if status_code == 200:
    deleted = payload.get("body", {}).get("deleted_gateways", [])
    released = payload.get("body", {}).get("released_eips", [])
    print(f"\n NAT Gateway 削除成功")
    print(f"   削除した NAT Gateway: {deleted}")
    print(f"   解放した Elastic IP : {released}")
else:
    raise Exception(f"NAT Gateway 削除失敗 / NAT Gateway deletion failed: {payload}")
```

> **boto3 の `read_timeout` について / About boto3 `read_timeout`:**
> Lambda の同期呼び出し（`RequestResponse`）では、Lambda の実行が完了するまで HTTP 接続を保持します。boto3 のデフォルト `read_timeout` は 60秒ですが、削除 Lambda は最大10分かかるため、**15分（900秒）** に延長しています。
>
> Synchronous Lambda invocation (`RequestResponse`) holds the HTTP connection until Lambda completes. boto3's default `read_timeout` is 60 seconds, but the delete Lambda can take up to 10 minutes, so we extend it to **15 minutes (900 seconds)**.

### Step 4-3: Job に nat_delete タスクを追加する / Add nat_delete task to the Job

**目的**: パイプライン最終タスクとして NAT Gateway 削除を追加する。

1. Databricks UI → 左メニュー **「ジョブとパイプライン」（Jobs）** をクリック
   - Click **"Jobs"** in the Databricks left menu
2. **`northwind_daily_pipeline`** をクリックして開く
   - Click to open **`northwind_daily_pipeline`**
3. **「タスク」（Tasks）** タブで編集画面を開く
   - Open the edit view in the **"Tasks"** tab

4. **「タスクを追加」（Add task）** をクリックし、以下を設定する:

| 設定項目 / Setting | 値 / Value |
|---|---|
| Task name | `nat_delete` |
| Type | **Notebook** |
| Source | Workspace |
| Path | `<Step 4-2 でアップロードしたノートブックのパス>` |
| Cluster | Job Cluster（既存設定を使用） |
| Depends on | `gold_aggregate` |

> **重要 / IMPORTANT**: `nat_delete` タスクは、パイプラインが **成功しても失敗しても** 実行されるように設定する必要があります。これにより、エラー時に NAT Gateway が残り続けてコストが発生することを防ぎます。
>
> The `nat_delete` task should run **whether the pipeline succeeds or fails**, preventing NAT Gateway costs from accumulating on error.

**失敗時にも実行する設定 / Run on failure setting:**

1. `nat_delete` タスクをクリックする
2. 依存関係の設定で、**「Run if」** を **「All done」（すべて完了時）** に変更する（デフォルトは「All succeeded」）
   - Change **"Run if"** to **"All done"** (default is "All succeeded")

### Step 4-4: 更新後のタスクフローを確認する / Verify the updated task flow

設定後、タスクの依存関係図が以下のようになっていることを確認する:

```
bronze_ingest → silver_transform → gold_aggregate → nat_delete
```

> **注意**: 旧設計と異なり、`nat_create` タスクは Databricks Job 内に**存在しません**。NAT Gateway の作成は EventBridge Scheduler（Phase 3）が Databricks Job の10分前に自動実行します。
>
> Unlike the previous design, `nat_create` is **NOT** a Databricks Job task. NAT Gateway creation is handled by EventBridge Scheduler (Phase 3), which runs 10 minutes before the Databricks Job.

**スクリーンショットを取得する / Take a screenshot**

---

## Phase 5: 結合テスト / Integration Test

### 目的 / Purpose

EventBridge Scheduler + Lambda + Databricks Workflows の一連の流れを通しでテストし、NAT Gateway が動的に作成・削除されることを確認する。

Test the end-to-end flow of EventBridge Scheduler + Lambda + Databricks Workflows, confirming NAT Gateway is dynamically created and deleted.

### Step 5-1: 事前確認 — NAT Gateway が存在しないこと / Pre-check — No NAT Gateway exists

1. AWS Console → **VPC** → **NAT ゲートウェイ（NAT gateways）** を開く
   - Open **VPC** → **NAT gateways** in AWS Console
2. `Available` 状態の NAT Gateway が **存在しない**ことを確認する
   - Confirm there are **no** NAT Gateways in `Available` state

### Step 5-2: NAT Gateway 作成 Lambda を手動実行する / Manually invoke NAT Gateway create Lambda

**目的**: EventBridge Scheduler の定期実行を待たずに、手動で NAT Gateway を作成してテストする。

1. AWS Console → **Lambda** → **`northwind-nat-create`** を開く
   - Open **Lambda** → **`northwind-nat-create`** in AWS Console
2. **「テスト」（Test）** タブで、イベント JSON を `{}` のまま **「テスト」（Test）** をクリックする
   - Click **"Test"** with default `{}` event JSON
3. 実行結果が **Succeeded** で `"state": "available"` が含まれることを確認する
   - Confirm result is **Succeeded** with `"state": "available"`
4. **VPC** → **NAT ゲートウェイ** で NAT Gateway が **Available** になったことを確認する
   - Confirm NAT Gateway is **Available** in VPC console

### Step 5-3: Databricks Job を手動実行する / Run the Databricks Job manually

1. Databricks UI → **`northwind_daily_pipeline`** を開く
   - Open **`northwind_daily_pipeline`** in Databricks UI
2. **「今すぐ実行」（Run now）** をクリックする
   - Click **"Run now"**
3. タスクの進行を監視する（全4タスクが順に実行される）:
   - Monitor the task progress (all 4 tasks run sequentially):
   - `bronze_ingest` → `Running` → `Succeeded`
   - `silver_transform` → `Running` → `Succeeded`
   - `gold_aggregate` → `Running` → `Succeeded`
   - `nat_delete` → `Running` → `Succeeded`

**スクリーンショットを取得する（全タスク Succeeded）/ Take a screenshot (all tasks Succeeded)**

### Step 5-4: 事後確認 — NAT Gateway が削除されたこと / Post-check — NAT Gateway deleted

1. AWS Console → **VPC** → **NAT ゲートウェイ（NAT gateways）** を開く
   - Open **VPC** → **NAT gateways** in AWS Console
2. 直前に作成された NAT Gateway が **Deleted** 状態になっていることを確認する
   - Confirm the recently created NAT Gateway is in **Deleted** state

**スクリーンショットを取得する / Take a screenshot**

### Step 5-5: Databricks 上で確認ノートブックを実行する（任意） / Run verification notebook on Databricks (optional)

`nb_03_nat_verify.py` を Databricks ノートブック上で実行し、NAT Gateway の作成→削除のライフサイクルログを確認する。

Run `nb_03_nat_verify.py` on a Databricks notebook and review the NAT Gateway create→delete lifecycle log.

> **注意 / Note**: `nb_03_nat_verify.py` は手動確認用のノートブックです。セル1（作成）とセル3（削除）を順に実行してライフサイクル全体を確認できます。ただし、NAT Gateway がない状態ではクラスターの起動自体ができないため、先に Step 5-2 で NAT Gateway を手動作成してから実行してください。
>
> `nb_03_nat_verify.py` is a manual verification notebook. Run Cell 1 (create) and Cell 3 (delete) sequentially. Note: since cluster startup requires NAT Gateway, create one via Step 5-2 first.

### Step 5-6: 失敗時の動作確認（任意） / Failure scenario test (optional)

**目的**: パイプラインが途中で失敗しても NAT Gateway が削除されることを確認する。

1. Step 5-2 と同様に、Lambda を手動実行して NAT Gateway を作成する
   - Create a NAT Gateway by manually invoking the Lambda (same as Step 5-2)
2. `bronze_ingest` ノートブックの先頭に一時的に `raise Exception("test failure")` を追加する
   - Temporarily add `raise Exception("test failure")` at the beginning of the `bronze_ingest` notebook
3. Databricks Job を **「今すぐ実行」（Run now）** する
   - Click **"Run now"**
4. `bronze_ingest` が **Failed** になった後、`nat_delete` が **実行される**ことを確認する
   - Confirm that after `bronze_ingest` **fails**, `nat_delete` still **runs**
5. AWS Console で NAT Gateway が **Deleted** になっていることを確認する
   - Confirm NAT Gateway is **Deleted** in AWS Console
6. テスト後、`raise Exception("test failure")` を **必ず削除する**
   - **Make sure to remove** `raise Exception("test failure")` after testing

---

## 注意事項 / Notes

| 項目 / Item | 内容 / Details |
|------|------|
| NAT Gateway 作成時間 / Creation time | NAT Gateway の作成には1〜3分かかる。作成 Lambda のタイムアウトは5分に設定すること / Takes 1-3 min. Set create Lambda timeout to 5 min |
| NAT Gateway 削除時間 / Deletion time | 削除 Lambda はポーリング + EIP 解放で5分を超える可能性がある。タイムアウトは **10分** に設定すること / Delete Lambda may exceed 5 min. Set timeout to **10 min** |
| Elastic IP の上限 / EIP limit | リージョンあたりの Elastic IP 数にはデフォルト上限（5個）がある。不要な EIP は解放すること / Default limit is 5 per region. Release unused EIPs |
| 冪等性 / Idempotency | 作成 Lambda には冪等性チェックが組み込まれている。既存の NAT Gateway がある場合は新規作成しない / Create Lambda has built-in idempotency. Won't create if one already exists |
| 失敗時の NAT 残留 / NAT leftover on failure | `nat_delete` を「All done」で設定することで、パイプライン失敗時にも NAT が削除される / `nat_delete` with "All done" ensures cleanup on failure |
| S3 アクセス / S3 access | S3 へのアクセスは **VPC Endpoint（Gateway 型）** を使用しているため、NAT Gateway がなくても S3 への読み書きは可能 / S3 VPC Endpoint allows S3 access without NAT |
| コントロールプレーン通信 / Control plane | Databricks コントロールプレーンとの通信には NAT Gateway が必要。EventBridge Scheduler が Databricks Job の **10分前** に NAT Gateway を作成するため、クラスター起動時には Available 状態になっている / Control plane needs NAT. EventBridge creates it **10 min before** the Job, ensuring availability at cluster startup |
| RDS アクセス / RDS access | RDS は同じ VPC 内にあるため、NAT Gateway がなくてもアクセス可能 / RDS is in the same VPC — accessible without NAT |
| EventBridge Scheduler コスト / EventBridge cost | EventBridge Scheduler は月14百万回まで無料。1日1回の実行では事実上無料 / Free up to 14M invocations/month. Essentially free for daily use |
| boto3 read_timeout | Databricks から Lambda を同期呼出する際は `read_timeout` を十分に長く設定する必要がある（デフォルト60秒では不足） / When invoking Lambda synchronously from Databricks, extend `read_timeout` (default 60s is insufficient) |

---

## 実施順序まとめ / Execution Order Summary

```
Phase 1: 既存 NAT Gateway の削除 / Remove existing NAT Gateway
  └── Step 1-1（確認）→ Step 1-2（CFn修正）→ Step 1-3（スタック更新）→ Step 1-4（削除確認）
        ↓
Phase 2: Lambda 関数の作成 / Create Lambda functions
  └── Step 2-1（IAMロール）→ Step 2-2（作成Lambda）→ Step 2-3（削除Lambda）
      → Step 2-4（作成テスト）→ Step 2-5（削除テスト）→ Step 2-6（結果確認）
        ↓
Phase 3: EventBridge Scheduler の設定 / Configure EventBridge Scheduler
  └── Step 3-1（IAMロール）→ Step 3-2（スケジュール作成）→ Step 3-3（Databricksスケジュール調整）
        ↓
Phase 4: Databricks Workflows Job の更新 / Update Workflows Job
  └── Step 4-1（権限追加）→ Step 4-2（ノートブック配置）→ Step 4-3（タスク追加）→ Step 4-4（フロー確認）
        ↓
Phase 5: 結合テスト / Integration test
  └── Step 5-1（事前確認）→ Step 5-2（Lambda手動実行）→ Step 5-3（Job実行）
      → Step 5-4（事後確認）→ Step 5-5（ノートブック確認・任意）→ Step 5-6（失敗テスト・任意）
```

---

## 変更履歴 / Change History

| 日付 / Date | 内容 / Details |
|------|------|
| 2026-03-23 | 初版作成。Sprint 2 スコープとして Story 1-6 の実装手順を策定 / Initial version. Story 1-6 implementation guide for Sprint 2 |
| 2026-03-23 | 実現可能性評価に基づく改修: EventBridge Scheduler による NAT Gateway 事前作成方式に変更、冪等性チェック追加、Lambda タイムアウト修正、boto3 read_timeout 設定追加 / Revised based on feasibility assessment: switched to EventBridge Scheduler for NAT pre-creation, added idempotency check, fixed Lambda timeout, added boto3 read_timeout |
