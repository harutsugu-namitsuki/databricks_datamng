"""
RDS 停止用 Lambda 関数 / RDS Stop Lambda Function
======================================================================
Story 1-6: NAT Gateway・RDS 時間制限運用

この Python コードは AWS Lambda にデプロイするコードです。
Databricks ノートブックではなく、Lambda コンソールの lambda_function.py に貼り付けてください。

This Python code is deployed to AWS Lambda.
Paste it into lambda_function.py in the Lambda console, NOT a Databricks notebook.

処理内容 / What it does:
1. RDS インスタンスの現在の状態を確認する / Check current RDS instance status
2. 起動中であれば停止リクエストを送信する / Send stop request if available
3. 既に停止中・停止済みの場合は何もしない（冪等） / Do nothing if already stopping/stopped (idempotent)

備考 / Note:
- このLambdaは停止リクエストを送信するだけで、RDSがStoppedになるまで待機しません
- cleanup ノートブック（nb_06_cleanup.py）から呼び出されます
- 安全ネットとして EventBridge Schedule（02:00 JST）からも呼び出されます
"""

import json
import boto3

REGION = "ap-northeast-1"
DB_INSTANCE_ID = "northwind-db"

rds = boto3.client("rds", region_name=REGION)


def lambda_handler(event, context):
    """RDS インスタンスを停止する。既に停止中なら何もしない（冪等）。"""
    print(f"=== RDS 停止を開始: {DB_INSTANCE_ID} ===")

    # 現在の状態を確認
    response = rds.describe_db_instances(DBInstanceIdentifier=DB_INSTANCE_ID)
    status = response["DBInstances"][0]["DBInstanceStatus"]
    print(f"  現在の状態: {status}")

    if status == "stopped":
        print("  既に停止済みです（冪等）")
        return {
            "statusCode": 200,
            "body": {"message": "RDS already stopped (idempotent)", "status": status},
        }

    if status == "stopping":
        print("  既に停止処理中です（冪等）")
        return {
            "statusCode": 200,
            "body": {"message": "RDS already stopping (idempotent)", "status": status},
        }

    if status != "available":
        msg = f"RDS is in unexpected state: {status}. Cannot stop."
        print(f"  ERROR: {msg}")
        return {"statusCode": 400, "body": {"message": msg, "status": status}}

    # 停止
    rds.stop_db_instance(DBInstanceIdentifier=DB_INSTANCE_ID)
    print(f"  RDS 停止リクエスト送信完了: {DB_INSTANCE_ID}")

    result = {
        "statusCode": 200,
        "body": {"message": "RDS stop initiated", "db_instance": DB_INSTANCE_ID, "status": "stopping"},
    }
    print(f"=== 完了 === {json.dumps(result)}")
    return result
