# Databricks notebook source

# MAGIC %md
# MAGIC # NAT Gateway 動的管理 — 動作確認ノートブック / Verification Notebook
# MAGIC
# MAGIC Story 1-6: NAT Gateway 時間制限運用
# MAGIC
# MAGIC このノートブックは **Databricks 上で実行** します。
# MAGIC Lambda 関数の呼び出しと NAT Gateway の状態確認を行います。
# MAGIC
# MAGIC This notebook runs **on Databricks**.
# MAGIC It invokes Lambda functions and checks NAT Gateway status.

# COMMAND ----------

# MAGIC %md
# MAGIC ## セル1: NAT Gateway 作成 Lambda を呼び出す / Invoke NAT Gateway Create Lambda
# MAGIC
# MAGIC **目的 / Purpose**: `northwind-nat-create` Lambda を呼び出して NAT Gateway を作成する。
# MAGIC Databricks Workflows の `nat_create` タスクではこのセルの内容をノートブックとして使用する。

# COMMAND ----------

import boto3
import json
import time
from botocore.config import Config

# Lambda の同期呼出は最大5〜10分かかるため、read_timeout を延長する
# Extend read_timeout since synchronous Lambda invocation can take 5-10 minutes
lambda_config = Config(
    read_timeout=600,  # 10分 / 10 minutes
    retries={"max_attempts": 0},  # Lambda 再試行は不要 / No retries for Lambda
)

# Lambda 関数を呼び出す / Invoke Lambda function
lambda_client = boto3.client("lambda", region_name="ap-northeast-1", config=lambda_config)

print("NAT Gateway 作成 Lambda を呼び出し中... / Invoking NAT Gateway create Lambda...")
print("(完了まで2〜5分かかります / Takes 2-5 minutes to complete)")

response = lambda_client.invoke(
    FunctionName="northwind-nat-create",
    InvocationType="RequestResponse",  # 同期呼び出し（完了まで待つ） / Synchronous (wait for completion)
)

# レスポンスを解析する / Parse response
payload = json.loads(response["Payload"].read().decode("utf-8"))
status_code = payload.get("statusCode", 0)

print(f"\nLambda 実行結果 / Lambda result:")
print(json.dumps(payload, indent=2, ensure_ascii=False))

if status_code == 200:
    nat_id = payload.get("body", {}).get("nat_gateway_id", "unknown")
    print(f"\n✅ NAT Gateway 作成成功: {nat_id}")
    print("パイプラインはインターネットアクセスが可能です / Pipeline has internet access")
else:
    raise Exception(f"NAT Gateway 作成失敗 / NAT Gateway creation failed: {payload}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## セル2: NAT Gateway の現在の状態を確認する / Check Current NAT Gateway Status
# MAGIC
# MAGIC **目的 / Purpose**: 現在の NAT Gateway の状態を確認する（デバッグ・動作確認用）。

# COMMAND ----------

ec2_client = boto3.client("ec2", region_name="ap-northeast-1")

print("=== NAT Gateway 状態確認 / NAT Gateway Status Check ===\n")

# Lambda が管理する NAT Gateway を検索 / Find Lambda-managed NAT Gateways
response = ec2_client.describe_nat_gateways(
    Filters=[
        {"Name": "tag:ManagedBy", "Values": ["lambda-nat-manager"]},
    ]
)

nat_gateways = response.get("NatGateways", [])

if not nat_gateways:
    print("Lambda が管理する NAT Gateway は存在しません / No Lambda-managed NAT Gateways found")
    print("(これはパイプライン実行前の正常な状態です / This is the normal state before pipeline execution)")
else:
    for nat_gw in nat_gateways:
        nat_id = nat_gw["NatGatewayId"]
        state = nat_gw["State"]
        create_time = nat_gw.get("CreateTime", "N/A")
        subnet_id = nat_gw.get("SubnetId", "N/A")

        # 名前タグを取得 / Get Name tag
        name = "N/A"
        for tag in nat_gw.get("Tags", []):
            if tag["Key"] == "Name":
                name = tag["Value"]
                break

        print(f"NAT Gateway ID : {nat_id}")
        print(f"Name           : {name}")
        print(f"State          : {state}")
        print(f"Subnet ID      : {subnet_id}")
        print(f"Created        : {create_time}")

        # EIP 情報 / EIP info
        for addr in nat_gw.get("NatGatewayAddresses", []):
            print(f"Public IP      : {addr.get('PublicIp', 'N/A')}")
            print(f"Allocation ID  : {addr.get('AllocationId', 'N/A')}")

        # 状態に応じたメッセージ / Status-based message
        if state == "available":
            print("\n✅ NAT Gateway は稼働中です / NAT Gateway is running")
        elif state == "pending":
            print("\n⏳ NAT Gateway は起動中です / NAT Gateway is starting up")
        elif state == "deleted":
            print("\n🗑️ NAT Gateway は削除済みです / NAT Gateway has been deleted")
        elif state == "failed":
            print("\n❌ NAT Gateway の作成に失敗しました / NAT Gateway creation failed")
        print("-" * 50)

# COMMAND ----------

# MAGIC %md
# MAGIC ## セル3: NAT Gateway 削除 Lambda を呼び出す / Invoke NAT Gateway Delete Lambda
# MAGIC
# MAGIC **目的 / Purpose**: `northwind-nat-delete` Lambda を呼び出して NAT Gateway を削除する。
# MAGIC Databricks Workflows の `nat_delete` タスクではこのセルの内容をノートブックとして使用する。

# COMMAND ----------

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
    print(f"\n✅ NAT Gateway 削除成功")
    print(f"   削除した NAT Gateway: {deleted}")
    print(f"   解放した Elastic IP : {released}")
else:
    raise Exception(f"NAT Gateway 削除失敗 / NAT Gateway deletion failed: {payload}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## セル4: インターネット接続テスト / Internet Connectivity Test
# MAGIC
# MAGIC **目的 / Purpose**: NAT Gateway が作成された後、インターネットへのアクセスが可能か確認する。
# MAGIC セル1（NAT 作成）の後に実行してください。

# COMMAND ----------

import urllib.request

test_url = "https://raw.githubusercontent.com/pthom/northwind_psql/master/README.md"

print(f"インターネット接続テスト / Internet connectivity test")
print(f"URL: {test_url}\n")

try:
    response = urllib.request.urlopen(test_url, timeout=10)
    status = response.getcode()
    content_length = len(response.read())
    print(f"✅ 接続成功 / Connection successful")
    print(f"   HTTP Status: {status}")
    print(f"   Content Length: {content_length} bytes")
    print(f"\n   NAT Gateway が正常に機能しています / NAT Gateway is working correctly")
except urllib.error.URLError as e:
    print(f"❌ 接続失敗 / Connection failed: {e}")
    print(f"\n   NAT Gateway が存在しないか、まだ Available になっていない可能性があります")
    print(f"   The NAT Gateway may not exist or may not yet be Available")

# COMMAND ----------

# MAGIC %md
# MAGIC ## セル5: コスト見積もり確認 / Cost Estimate Review
# MAGIC
# MAGIC **目的 / Purpose**: 時間制限運用によるコスト削減効果を確認する。

# COMMAND ----------

# コスト計算 / Cost calculation
NAT_HOURLY_RATE = 0.062  # USD/hour (ap-northeast-1)
HOURS_PER_DAY = 24
DAYS_PER_MONTH = 30

# 常時起動の場合 / Always-on
always_on_monthly = NAT_HOURLY_RATE * HOURS_PER_DAY * DAYS_PER_MONTH

# 時間制限運用の場合（1日30分 = 0.5時間） / Time-limited (30 min/day = 0.5 hour)
pipeline_hours = 0.5
time_limited_monthly = NAT_HOURLY_RATE * pipeline_hours * DAYS_PER_MONTH

# 削減率 / Reduction rate
reduction = (1 - time_limited_monthly / always_on_monthly) * 100

print("=== NAT Gateway コスト比較 / Cost Comparison ===\n")
print(f"NAT Gateway 時間単価 / Hourly rate : ${NAT_HOURLY_RATE}/hour")
print(f"リージョン / Region                 : ap-northeast-1 (Tokyo)\n")
print(f"{'運用方式 / Operation Mode':<40} {'月額コスト / Monthly Cost':>20}")
print(f"{'-'*60}")
print(f"{'常時起動 (24h/day) / Always-on':<40} {'${:,.2f}'.format(always_on_monthly):>20}")
print(f"{'時間制限 (0.5h/day) / Time-limited':<40} {'${:,.2f}'.format(time_limited_monthly):>20}")
print(f"{'-'*60}")
print(f"{'月間削減額 / Monthly savings':<40} {'${:,.2f}'.format(always_on_monthly - time_limited_monthly):>20}")
print(f"{'削減率 / Reduction rate':<40} {'{:.1f}%'.format(reduction):>20}")
print(f"\n{'年間削減額 / Annual savings':<40} {'${:,.2f}'.format((always_on_monthly - time_limited_monthly) * 12):>20}")
