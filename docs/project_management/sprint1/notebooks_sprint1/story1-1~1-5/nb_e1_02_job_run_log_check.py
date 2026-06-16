# Databricks notebook source
# Epic 1 / Sprint 1 - Story 1-3〜1-5: Job実行ログ確認
# Databricks Workflows 設定後に実行し、
# ops.job_runs / ops.ingestion_log の記録を確認する

# COMMAND ----------
# セル1: 直近のJob実行履歴確認

CATALOG_NAME = "northwind_catalog"

print("=" * 70)
print("ops.job_runs 直近10件")
print("=" * 70)

try:
    spark.sql(f"""
        SELECT job_name, status, start_time, end_time, run_id
        FROM {CATALOG_NAME}.ops.job_runs
        ORDER BY start_time DESC
        LIMIT 10
    """).show(truncate=False)
except Exception as e:
    print(f"[WARN] ops.job_runs にアクセスできません: {e}")

# COMMAND ----------
# セル2: 直近のIngestion Log確認

print("=" * 70)
print("ops.ingestion_log 直近の取り込み結果（本日分）")
print("=" * 70)

from datetime import date
today = str(date.today())

try:
    spark.sql(f"""
        SELECT table_name, row_count, duration_sec, load_date, status
        FROM {CATALOG_NAME}.ops.ingestion_log
        WHERE load_date = '{today}'
        ORDER BY table_name
    """).show(30, truncate=False)
except Exception as e:
    print(f"[WARN] ops.ingestion_log にアクセスできません: {e}")

# COMMAND ----------
# セル3: パイプライン成否サマリ

print("=" * 70)
print("パイプライン実行サマリ（直近7日間）")
print("=" * 70)

try:
    spark.sql(f"""
        SELECT
            DATE(start_time) as run_date,
            job_name,
            status,
            COUNT(*) as run_count
        FROM {CATALOG_NAME}.ops.job_runs
        WHERE start_time >= DATEADD(DAY, -7, CURRENT_DATE())
        GROUP BY DATE(start_time), job_name, status
        ORDER BY run_date DESC, job_name
    """).show(truncate=False)
except Exception as e:
    print(f"[WARN]: {e}")

# COMMAND ----------
# セル4: 成功率チェック（アサーション）

print("=" * 70)
print("Job成功率チェック")
print("=" * 70)

try:
    result = spark.sql(f"""
        SELECT
            COUNT(*) as total_runs,
            SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as success_runs,
            ROUND(SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as success_rate
        FROM {CATALOG_NAME}.ops.job_runs
        WHERE start_time >= DATEADD(DAY, -7, CURRENT_DATE())
    """).collect()[0]

    print(f"  直近7日間 実行回数: {result['total_runs']}")
    print(f"  成功回数: {result['success_runs']}")
    print(f"  成功率: {result['success_rate']}%")

    if result['success_rate'] and result['success_rate'] >= 80:
        print("  [PASS] 成功率80%以上")
    else:
        print("  [WARN] 成功率が低い → Job設定・通知設定を確認してください")
except Exception as e:
    print(f"[INFO] ログが蓄積されていない場合は、Job実行後に再確認してください: {e}")
