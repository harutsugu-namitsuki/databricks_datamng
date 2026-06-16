# Databricks notebook source

# MAGIC %md
# MAGIC # Cleanup ノートブック / Cleanup Notebook
# MAGIC
# MAGIC Story 1-6: NAT Gateway・RDS 時間制限運用
# MAGIC
# MAGIC このノートブックは **Databricks Workflows の cleanup タスク** として実行されます。
# MAGIC パイプライン完了後（成功・失敗いずれの場合も）に RDS 停止 → NAT Gateway 削除を行います。
# MAGIC
# MAGIC This notebook runs as the **cleanup task in Databricks Workflows**.
# MAGIC It stops RDS and deletes NAT Gateway after pipeline completion (success or failure).
# MAGIC
# MAGIC **実行順序 / Execution order:**
# MAGIC 1. RDS 停止 Lambda を呼び出す（NAT Gateway がまだ存在する状態で実行）
# MAGIC 2. NAT Gateway 削除 Lambda を呼び出す（最後に実行）
# MAGIC
# MAGIC **順番が重要 / Order matters:**
# MAGIC RDS 停止の API 呼出しはインターネット経由のため NAT Gateway が必要です。
# MAGIC NAT Gateway を先に削除すると RDS 停止 API 呼出しが失敗します。

# COMMAND ----------

import boto3
import json
from botocore.config import Config

# Unity Catalog サービスクレデンシャルを使用して認証
# 参照: 課題報告_NoCredentialsError.md - 対策C
SERVICE_CREDENTIAL_NAME = "northwind-lambda-invoke-credential"
AWS_REGION = "ap-northeast-1"

boto3_session = boto3.Session(
    botocore_session=dbutils.credentials.getServiceCredentialsProvider(
        SERVICE_CREDENTIAL_NAME
    ),
    region_name=AWS_REGION,
)

# boto3 の read_timeout を延長する（NAT削除Lambda の同期呼出は最大10分かかるため）
lambda_config = Config(
    read_timeout=900,  # 15分
    retries={"max_attempts": 0},
)
lambda_client = boto3_session.client("lambda", config=lambda_config)

# ============================================================
# Step 1: RDS 停止（NAT Gateway がまだ存在する状態で実行）
# Step 1: Stop RDS (while NAT Gateway still exists)
# ============================================================
print("=" * 60)
print("Step 1: RDS 停止 Lambda を呼び出し中... / Invoking RDS stop Lambda...")
print("=" * 60)

rds_response = lambda_client.invoke(
    FunctionName="northwind-rds-stop",
    InvocationType="RequestResponse",
)

rds_payload = json.loads(rds_response["Payload"].read().decode("utf-8"))
rds_status = rds_payload.get("statusCode", 0)

print(f"RDS Lambda 実行結果 / RDS Lambda result:")
print(json.dumps(rds_payload, indent=2, ensure_ascii=False))

if rds_status == 200:
    print("✅ RDS 停止リクエスト成功")
else:
    print(f"⚠️ RDS 停止で問題発生（続行します）: {rds_payload}")
    # RDS停止に失敗してもNAT削除は続行する（コスト防止のため）

# ============================================================
# Step 2: NAT Gateway 削除（最後に実行）
# Step 2: Delete NAT Gateway (execute last)
# ============================================================
print()
print("=" * 60)
print("Step 2: NAT Gateway 削除 Lambda を呼び出し中... / Invoking NAT Gateway delete Lambda...")
print("(完了まで2〜5分かかります / Takes 2-5 minutes to complete)")
print("=" * 60)

nat_response = lambda_client.invoke(
    FunctionName="northwind-nat-delete",
    InvocationType="RequestResponse",
)

nat_payload = json.loads(nat_response["Payload"].read().decode("utf-8"))
nat_status = nat_payload.get("statusCode", 0)

print(f"NAT Lambda 実行結果 / NAT Lambda result:")
print(json.dumps(nat_payload, indent=2, ensure_ascii=False))

if nat_status == 200:
    deleted = nat_payload.get("body", {}).get("deleted_gateways", [])
    released = nat_payload.get("body", {}).get("released_eips", [])
    print(f"\n✅ NAT Gateway 削除成功")
    print(f"   削除した NAT Gateway: {deleted}")
    print(f"   解放した Elastic IP : {released}")
else:
    raise Exception(f"NAT Gateway 削除失敗 / NAT Gateway deletion failed: {nat_payload}")

# ============================================================
# 最終サマリー / Final Summary
# ============================================================
print()
print("=" * 60)
print("Cleanup 完了サマリー / Cleanup Summary")
print("=" * 60)
print(f"  RDS 停止:        {'✅ 成功' if rds_status == 200 else '⚠️ 要確認'}")
print(f"  NAT Gateway 削除: {'✅ 成功' if nat_status == 200 else '❌ 失敗'}")
