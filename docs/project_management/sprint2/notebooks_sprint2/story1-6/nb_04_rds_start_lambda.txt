"""
RDS 起動用 Lambda 関数 / RDS Start Lambda Function
======================================================================
Story 1-6: NAT Gateway・RDS 時間制限運用

この Python コードは AWS Lambda にデプロイするコードです。
Databricks ノートブックではなく、Lambda コンソールの lambda_function.py に貼り付けてください。

This Python code is deployed to AWS Lambda.
Paste it into lambda_function.py in the Lambda console, NOT a Databricks notebook.

処理内容 / What it does:
1. RDS インスタンスの現在の状態を確認する / Check current RDS instance status
2. 停止中であれば起動リクエストを送信する / Send start request if stopped
3. 既に起動中・起動済みの場合は何もしない（冪等） / Do nothing if already starting/available (idempotent)

備考 / Note:
- このLambdaは起動リクエストを送信するだけで、RDSがAvailableになるまで待機しません
- RDSが実際にAvailableになるまで10〜15分かかります
- EventBridgeのスケジュールタイミング（05:45 JST）で余裕を吸収します
"""

import json
import boto3

REGION = "ap-northeast-1"
DB_INSTANCE_ID = "northwind-db"

rds = boto3.client("rds", region_name=REGION)


def lambda_handler(event, context):
    """RDS インスタンスを起動する。既に起動中なら何もしない（冪等）。"""
    print(f"=== RDS 起動を開始: {DB_INSTANCE_ID} ===")

    # 現在の状態を確認
    response = rds.describe_db_instances(DBInstanceIdentifier=DB_INSTANCE_ID)
    status = response["DBInstances"][0]["DBInstanceStatus"]
    print(f"  現在の状態: {status}")

    if status == "available":
        print("  既に起動済みです（冪等）")
        return {
            "statusCode": 200,
            "body": {"message": "RDS already available (idempotent)", "status": status},
        }

    if status == "starting":
        print("  既に起動処理中です（冪等）")
        return {
            "statusCode": 200,
            "body": {"message": "RDS already starting (idempotent)", "status": status},
        }

    if status != "stopped":
        msg = f"RDS is in unexpected state: {status}. Cannot start."
        print(f"  ERROR: {msg}")
        return {"statusCode": 400, "body": {"message": msg, "status": status}}

    # 起動
    rds.start_db_instance(DBInstanceIdentifier=DB_INSTANCE_ID)
    print(f"  RDS 起動リクエスト送信完了: {DB_INSTANCE_ID}")

    result = {
        "statusCode": 200,
        "body": {"message": "RDS start initiated", "db_instance": DB_INSTANCE_ID, "status": "starting"},
    }
    print(f"=== 完了 === {json.dumps(result)}")
    return result
