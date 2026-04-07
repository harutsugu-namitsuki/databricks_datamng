"""
NAT Gateway 作成用 Lambda 関数 / NAT Gateway Creation Lambda Function
======================================================================
Story 1-6: NAT Gateway 時間制限運用

この Python コードは AWS Lambda にデプロイするコードです。
Databricks ノートブックではなく、Lambda コンソールの lambda_function.py に貼り付けてください。

This Python code is deployed to AWS Lambda.
Paste it into lambda_function.py in the Lambda console, NOT a Databricks notebook.

処理内容 / What it does:
1. Elastic IP（固定IPアドレス）を新規取得する / Allocate a new Elastic IP
2. NAT Gateway を Public Subnet に作成する / Create NAT Gateway in the Public Subnet
3. NAT Gateway が Available になるまで待機する / Wait until NAT Gateway becomes Available
4. Private Route Table に 0.0.0.0/0 → NAT Gateway のルートを追加する / Add route 0.0.0.0/0 → NAT Gateway to Private Route Table
"""

import json
import time
import boto3

# ==============================================================================
# 設定値 / Configuration
# ==============================================================================
# ★ 以下の値を自分の環境に合わせて変更してください
# ★ Update the values below to match your environment

# Public Subnet ID（NAT Gateway を配置するサブネット）
# AWS Console → VPC → Subnets → 「northwind-public」の Subnet ID をコピー
PUBLIC_SUBNET_ID = "subnet-xxxxxxxxxxxxxxxxx"  # ← 自分の Public Subnet ID に変更

# Private Route Table ID（プライベートサブネットのルートテーブル）
# AWS Console → VPC → Route tables → 「northwind-private-rt」の Route Table ID をコピー
PRIVATE_ROUTE_TABLE_ID = "rtb-xxxxxxxxxxxxxxxxx"  # ← 自分の Private Route Table ID に変更

# タグ用の環境名 / Environment name for tags
ENVIRONMENT_NAME = "northwind"

# リージョン / Region
REGION = "ap-northeast-1"

# ==============================================================================
# Lambda ハンドラー / Lambda Handler
# ==============================================================================
ec2 = boto3.client("ec2", region_name=REGION)


def lambda_handler(event, context):
    """
    NAT Gateway を作成し、ルートテーブルにルートを追加する。
    Create a NAT Gateway and add a route to the route table.

    冪等性 / Idempotency:
    既に Lambda が管理する NAT Gateway が存在する場合は新規作成せずに既存のものを返す。
    If a Lambda-managed NAT Gateway already exists, return it instead of creating a new one.
    """
    print("=== NAT Gateway 作成を開始 / Starting NAT Gateway creation ===")

    # ---- 冪等性チェック: 既存の NAT Gateway を確認 / Idempotency check ----
    print("Step 0: 既存の Lambda 管理 NAT Gateway を確認中... / Checking for existing managed NAT Gateway...")
    existing = ec2.describe_nat_gateways(
        Filters=[
            {"Name": "tag:ManagedBy", "Values": ["lambda-nat-manager"]},
            {"Name": "state", "Values": ["available", "pending"]},
        ]
    )
    existing_nats = existing.get("NatGateways", [])

    if existing_nats:
        nat = existing_nats[0]
        nat_id = nat["NatGatewayId"]
        state = nat["State"]
        print(f"  既存の NAT Gateway を検出: {nat_id} (state={state})")
        print(f"  Found existing NAT Gateway: {nat_id} (state={state})")

        if state == "pending":
            print("  pending 状態のため、available になるまで待機中...")
            print("  Waiting for pending NAT Gateway to become available...")
            waiter = ec2.get_waiter("nat_gateway_available")
            waiter.wait(
                NatGatewayIds=[nat_id],
                WaiterConfig={"Delay": 15, "MaxAttempts": 20},
            )
            print(f"  NAT Gateway が Available になりました: {nat_id}")

        # 既存の NAT Gateway を返す（新規作成しない）
        result = {
            "statusCode": 200,
            "body": {
                "message": "NAT Gateway already exists (idempotent)",
                "nat_gateway_id": nat_id,
                "state": "available",
            },
        }
        print(f"=== 既存を再利用して完了 / Done (reused existing) === {json.dumps(result)}")
        return result

    print("  既存の NAT Gateway なし。新規作成します / No existing NAT Gateway. Creating new one.")

    # ---- Step 1: Elastic IP を取得する / Allocate Elastic IP ----
    print("Step 1: Elastic IP を取得中... / Allocating Elastic IP...")
    eip_response = ec2.allocate_address(
        Domain="vpc",
        TagSpecifications=[
            {
                "ResourceType": "elastic-ip",
                "Tags": [
                    {"Key": "Name", "Value": f"{ENVIRONMENT_NAME}-nat-eip-dynamic"},
                    {"Key": "ManagedBy", "Value": "lambda-nat-manager"},
                ],
            }
        ],
    )
    allocation_id = eip_response["AllocationId"]
    print(f"  Elastic IP 取得完了: {allocation_id}")

    # ---- Step 2: NAT Gateway を作成する / Create NAT Gateway ----
    print("Step 2: NAT Gateway を作成中... / Creating NAT Gateway...")
    nat_response = ec2.create_nat_gateway(
        SubnetId=PUBLIC_SUBNET_ID,
        AllocationId=allocation_id,
        TagSpecifications=[
            {
                "ResourceType": "natgateway",
                "Tags": [
                    {"Key": "Name", "Value": f"{ENVIRONMENT_NAME}-nat-dynamic"},
                    {"Key": "ManagedBy", "Value": "lambda-nat-manager"},
                ],
            }
        ],
    )
    nat_gateway_id = nat_response["NatGateway"]["NatGatewayId"]
    print(f"  NAT Gateway 作成開始: {nat_gateway_id}")

    # ---- Step 3: Available になるまで待機する / Wait for Available state ----
    print("Step 3: NAT Gateway が Available になるまで待機中...")
    print("  (通常1〜3分かかります / Usually takes 1-3 minutes)")
    waiter = ec2.get_waiter("nat_gateway_available")
    waiter.wait(
        NatGatewayIds=[nat_gateway_id],
        WaiterConfig={"Delay": 15, "MaxAttempts": 20},  # 15秒間隔 × 最大20回 = 最大5分
    )
    print(f"  NAT Gateway が Available になりました: {nat_gateway_id}")

    # ---- Step 4: ルートテーブルにルートを追加する / Add route to route table ----
    print("Step 4: ルートテーブルにルートを追加中...")
    try:
        ec2.create_route(
            RouteTableId=PRIVATE_ROUTE_TABLE_ID,
            DestinationCidrBlock="0.0.0.0/0",
            NatGatewayId=nat_gateway_id,
        )
        print(f"  ルート追加完了: 0.0.0.0/0 → {nat_gateway_id}")
    except ec2.exceptions.ClientError as e:
        if "RouteAlreadyExists" in str(e):
            # 既存ルートがある場合は置き換える / Replace existing route
            print("  既存ルートを置き換え中... / Replacing existing route...")
            ec2.replace_route(
                RouteTableId=PRIVATE_ROUTE_TABLE_ID,
                DestinationCidrBlock="0.0.0.0/0",
                NatGatewayId=nat_gateway_id,
            )
            print(f"  ルート置き換え完了: 0.0.0.0/0 → {nat_gateway_id}")
        else:
            raise

    # ---- 完了 / Done ----
    result = {
        "statusCode": 200,
        "body": {
            "message": "NAT Gateway created successfully",
            "nat_gateway_id": nat_gateway_id,
            "allocation_id": allocation_id,
            "state": "available",
        },
    }
    print(f"=== 完了 / Done === {json.dumps(result)}")
    return result
