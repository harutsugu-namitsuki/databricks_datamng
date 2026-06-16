"""
NAT Gateway 削除用 Lambda 関数 / NAT Gateway Deletion Lambda Function
======================================================================
Story 1-6: NAT Gateway 時間制限運用

この Python コードは AWS Lambda にデプロイするコードです。
Databricks ノートブックではなく、Lambda コンソールの lambda_function.py に貼り付けてください。

This Python code is deployed to AWS Lambda.
Paste it into lambda_function.py in the Lambda console, NOT a Databricks notebook.

処理内容 / What it does:
1. ManagedBy=lambda-nat-manager タグの NAT Gateway を検索する / Find NAT Gateway with ManagedBy tag
2. Private Route Table から 0.0.0.0/0 ルートを削除する / Delete 0.0.0.0/0 route from Private Route Table
3. NAT Gateway を削除する / Delete the NAT Gateway
4. NAT Gateway が Deleted になるまで待機する / Wait until NAT Gateway is Deleted
5. 関連する Elastic IP を解放する / Release the associated Elastic IP
"""

# ==============================================================================
# ★ Lambda タイムアウト設定 / Lambda Timeout Setting
# ==============================================================================
# この Lambda は NAT Gateway 削除待機（最大 15秒 × 20回 = 300秒）+ EIP 解放で
# 5分を超える可能性があります。Lambda コンソールでタイムアウトを **10分** に設定してください。
#
# This Lambda may exceed 5 min due to NAT deletion polling (15s × 20 = 300s)
# plus EIP release. Set Lambda timeout to **10 minutes** in the Lambda console.
# ==============================================================================

import json
import time
import boto3

# ==============================================================================
# 設定値 / Configuration
# ==============================================================================
# ★ nb_01_nat_create_lambda.py と同じ値を設定してください
# ★ Set the same values as nb_01_nat_create_lambda.py

# Private Route Table ID（プライベートサブネットのルートテーブル）
PRIVATE_ROUTE_TABLE_ID = "rtb-xxxxxxxxxxxxxxxxx"  # ← 自分の Private Route Table ID に変更

# リージョン / Region
REGION = "ap-northeast-1"

# ==============================================================================
# Lambda ハンドラー / Lambda Handler
# ==============================================================================
ec2 = boto3.client("ec2", region_name=REGION)


def lambda_handler(event, context):
    """
    Lambda が作成した NAT Gateway を検索して削除する。
    Find and delete NAT Gateways created by the Lambda manager.
    """
    print("=== NAT Gateway 削除を開始 / Starting NAT Gateway deletion ===")

    # ---- Step 1: Lambda が作成した NAT Gateway を検索する / Find managed NAT Gateways ----
    print("Step 1: ManagedBy=lambda-nat-manager の NAT Gateway を検索中...")
    response = ec2.describe_nat_gateways(
        Filters=[
            {"Name": "tag:ManagedBy", "Values": ["lambda-nat-manager"]},
            {"Name": "state", "Values": ["available", "pending"]},
        ]
    )

    nat_gateways = response.get("NatGateways", [])
    if not nat_gateways:
        print("  削除対象の NAT Gateway が見つかりません / No NAT Gateways to delete")
        return {
            "statusCode": 200,
            "body": {"message": "No NAT Gateways found to delete"},
        }

    print(f"  {len(nat_gateways)} 個の NAT Gateway を検出 / Found {len(nat_gateways)} NAT Gateway(s)")

    deleted_gateways = []
    released_eips = []

    for nat_gw in nat_gateways:
        nat_gateway_id = nat_gw["NatGatewayId"]
        print(f"\n--- NAT Gateway を処理中: {nat_gateway_id} ---")

        # ---- Step 2: ルートテーブルから 0.0.0.0/0 を削除する / Delete route ----
        print("Step 2: ルートテーブルからルートを削除中...")
        try:
            ec2.delete_route(
                RouteTableId=PRIVATE_ROUTE_TABLE_ID,
                DestinationCidrBlock="0.0.0.0/0",
            )
            print("  ルート削除完了: 0.0.0.0/0")
        except ec2.exceptions.ClientError as e:
            if "InvalidParameterValue" in str(e) or "no route" in str(e).lower():
                print("  ルートが存在しません（すでに削除済み） / Route does not exist (already deleted)")
            else:
                print(f"  ルート削除でエラー（続行します）: {e}")

        # ---- Step 3: NAT Gateway を削除する / Delete NAT Gateway ----
        print(f"Step 3: NAT Gateway を削除中: {nat_gateway_id}...")
        # 関連する EIP の Allocation ID を先に記録する（削除後は取得できないため）
        eip_allocation_ids = []
        for addr in nat_gw.get("NatGatewayAddresses", []):
            alloc_id = addr.get("AllocationId")
            if alloc_id:
                eip_allocation_ids.append(alloc_id)

        ec2.delete_nat_gateway(NatGatewayId=nat_gateway_id)
        print(f"  NAT Gateway 削除リクエスト送信完了: {nat_gateway_id}")
        deleted_gateways.append(nat_gateway_id)

        # ---- Step 4: Deleted になるまで待機する / Wait for Deleted state ----
        print("Step 4: NAT Gateway が Deleted になるまで待機中...")
        print("  (通常1〜3分かかります / Usually takes 1-3 minutes)")
        for attempt in range(20):
            time.sleep(15)
            status_response = ec2.describe_nat_gateways(
                NatGatewayIds=[nat_gateway_id]
            )
            state = status_response["NatGateways"][0]["State"]
            print(f"  状態確認 ({attempt + 1}/20): {state}")
            if state == "deleted":
                print(f"  NAT Gateway が Deleted になりました: {nat_gateway_id}")
                break
        else:
            print(f"  WARNING: タイムアウト。NAT Gateway がまだ削除中の可能性があります")

        # ---- Step 5: Elastic IP を解放する / Release Elastic IP ----
        print("Step 5: Elastic IP を解放中...")
        for alloc_id in eip_allocation_ids:
            try:
                ec2.release_address(AllocationId=alloc_id)
                print(f"  Elastic IP 解放完了: {alloc_id}")
                released_eips.append(alloc_id)
            except ec2.exceptions.ClientError as e:
                if "InvalidAllocationID.NotFound" in str(e):
                    print(f"  Elastic IP がすでに解放済み: {alloc_id}")
                else:
                    print(f"  Elastic IP 解放でエラー（続行します）: {e}")

    # ---- 完了 / Done ----
    result = {
        "statusCode": 200,
        "body": {
            "message": "NAT Gateway(s) deleted successfully",
            "deleted_gateways": deleted_gateways,
            "released_eips": released_eips,
        },
    }
    print(f"=== 完了 / Done === {json.dumps(result)}")
    return result
