# Databricks notebook source
# Epic 4 / Story 4-2: AutoML 実験の実行
# Databricks AutoML API を使って回帰モデルを自動生成する

# COMMAND ----------
# セル1: 学習データの読み込み

import datetime

CATALOG_NAME = "northwind_catalog"
TRAINING_TABLE = f"{CATALOG_NAME}.gold.ml_training_sales"
EXPERIMENT_NAME = f"northwind_sales_automl_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

df_train = spark.table(TRAINING_TABLE)
print(f"学習データ件数: {df_train.count()}")
display(df_train.limit(10))

# COMMAND ----------
# セル2: AutoML 回帰実験の実行

from databricks import automl

summary = automl.regress(
    dataset=df_train,
    target_col="total_sales",
    time_col="order_date",
    primary_metric="rmse",
    timeout_minutes=30,
    experiment_name=EXPERIMENT_NAME,
)

# COMMAND ----------
# セル3: AutoML 結果サマリの表示

print("=" * 60)
print("AutoML 実験結果サマリ")
print("=" * 60)
metrics = summary.best_trial.metrics
rmse = metrics.get('val_rmse', metrics.get('test_rmse', metrics.get('val_root_mean_squared_error', 'N/A')))
r2 = metrics.get('val_r2_score', metrics.get('test_r2_score', 'N/A'))
mae = metrics.get('val_mae', metrics.get('test_mae', metrics.get('val_mean_absolute_error', 'N/A')))

print(f"ベストモデルの RMSE : {rmse if isinstance(rmse, str) else f'{rmse:.4f}'}")
print(f"ベストモデルの R²   : {r2 if isinstance(r2, str) else f'{r2:.4f}'}")
print(f"ベストモデルの MAE  : {mae if isinstance(mae, str) else f'{mae:.4f}'}")
print(f"MLflow Run ID      : {summary.best_trial.mlflow_run_id}")
print(f"生成ノートブック    : {summary.best_trial.notebook_path}")
print("=" * 60)

# COMMAND ----------
# セル4: ベストモデルのノートブックリンク
# AutoML が生成したノートブックを開いて、モデルの詳細を確認する

print(f"""
次のステップ:
1. 上記の「生成ノートブック」リンクを開く
2. AutoML が生成したコードを確認する
3. 特徴量の重要度（Feature Importance）を確認する
4. Story 4-3 でこのノートブックをカスタマイズする
""")
