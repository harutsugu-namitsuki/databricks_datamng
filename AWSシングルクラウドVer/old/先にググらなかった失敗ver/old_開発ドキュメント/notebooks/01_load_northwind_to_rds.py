# Databricks notebook source
# MAGIC %md
# MAGIC # 01. Northwindデータ → RDS PostgreSQL 投入（AWSシングルクラウド版）
# MAGIC
# MAGIC このノートブックでは、[pthom/northwind_psql](https://github.com/pthom/northwind_psql) の
# MAGIC PostgreSQLネイティブ `northwind.sql` をRDSに投入します。
# MAGIC
# MAGIC **データソース**:
# MAGIC - リポジトリ: https://github.com/pthom/northwind_psql
# MAGIC - SQLファイル: https://raw.githubusercontent.com/pthom/northwind_psql/master/northwind.sql
# MAGIC - ローカルコピー: `設計ドキュメント/northwind.sql`
# MAGIC
# MAGIC **前提条件**:
# MAGIC - RDS PostgreSQL が起動している（CloudFormation デプロイ済み）
# MAGIC - Databricks Compute が RDS と同じ VPC 内にある
# MAGIC - Secret Scope `northwind-secrets` に接続情報が登録済み
# MAGIC
# MAGIC **対象テーブル（全14テーブル）**:
# MAGIC categories, customers, employees, suppliers, shippers, products,
# MAGIC orders, order_details, region, territories, us_states,
# MAGIC employee_territories, customer_demographics, customer_customer_demo

# COMMAND ----------

# MAGIC %md
# MAGIC ## 接続情報の取得

# COMMAND ----------

# Databricks Secretsから接続情報を取得
DB_HOST = dbutils.secrets.get(scope="northwind-secrets", key="rds-host")
DB_USER = dbutils.secrets.get(scope="northwind-secrets", key="rds-user")
DB_PASSWORD = dbutils.secrets.get(scope="northwind-secrets", key="rds-password")
DB_NAME = "northwind"
DB_PORT = 5432

print(f"✅ 接続情報を取得しました")
print(f"   DB Host: {DB_HOST}")
print(f"   DB User: {DB_USER}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## JDBC接続情報の構築

# COMMAND ----------

# JDBC URL構築（VPC内通信 - sslmode=require推奨）
jdbc_url = f"jdbc:postgresql://{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"

connection_properties = {
    "user": DB_USER,
    "password": DB_PASSWORD,
    "driver": "org.postgresql.Driver"
}

print(f"JDBC URL: {jdbc_url}")
print(f"✅ 接続情報を構築しました")

# COMMAND ----------

# MAGIC %md
# MAGIC ## PostgreSQLドライバのインストール

# COMMAND ----------

# psycopg2のインストール
%pip install psycopg2-binary

# COMMAND ----------

# MAGIC %md
# MAGIC ## northwind.sql のダウンロードと実行
# MAGIC
# MAGIC GitHubから直接ダウンロードしてRDSに投入します。
# MAGIC ソース: [pthom/northwind_psql](https://github.com/pthom/northwind_psql)

# COMMAND ----------

import urllib.request
import psycopg2

# northwind.sql をダウンロード
NORTHWIND_SQL_URL = "https://raw.githubusercontent.com/pthom/northwind_psql/master/northwind.sql"
print(f"📥 ダウンロード中: {NORTHWIND_SQL_URL}")

response = urllib.request.urlopen(NORTHWIND_SQL_URL)
northwind_sql = response.read().decode('utf-8')
print(f"✅ ダウンロード完了: {len(northwind_sql)} bytes")

# COMMAND ----------

# MAGIC %md
# MAGIC ## DDL + データ投入の実行

# COMMAND ----------

# RDSに接続してnorthwind.sqlを実行
try:
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        sslmode='require'
    )
    conn.autocommit = True
    cursor = conn.cursor()

    # northwind.sql を実行（DDL + INSERT + PRIMARY KEY + FK 全て含む）
    cursor.execute(northwind_sql)
    print("✅ northwind.sql 実行完了: 全テーブルとデータが作成されました")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"❌ エラー: {str(e)}")
    print("\n確認事項:")
    print("1. Secret Scope の接続情報が正しいか")
    print("2. Databricks Compute と RDS が同じ VPC 内にあるか")
    print("3. Security Group で Databricks Compute SG からの 5432 が許可されているか")
    raise e

# COMMAND ----------

# MAGIC %md
# MAGIC ## データ確認

# COMMAND ----------

# 全14テーブルの件数を確認
tables = [
    'categories',
    'customers',
    'employees',
    'suppliers',
    'shippers',
    'products',
    'orders',
    'order_details',
    'region',
    'territories',
    'us_states',
    'employee_territories',
    'customer_demographics',
    'customer_customer_demo'
]

print("📊 各テーブルの件数:")
for table in tables:
    try:
        df = spark.read.jdbc(
            url=jdbc_url,
            table=table,
            properties=connection_properties
        )
        count = df.count()
        print(f"  ✅ {table}: {count} 件")
    except Exception as e:
        print(f"  ⚠️ {table}: テーブルが存在しないか読み取りエラー ({str(e)[:50]})")

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ 完了チェックリスト
# MAGIC
# MAGIC - [ ] northwind.sql がダウンロードされた
# MAGIC - [ ] DDL + データ投入が正常に完了した
# MAGIC - [ ] 全14テーブルの件数が確認できた
# MAGIC
# MAGIC ### 期待されるデータ件数
# MAGIC
# MAGIC | テーブル | 件数 |
# MAGIC |---------|------|
# MAGIC | categories | 8 |
# MAGIC | customers | 91 |
# MAGIC | employees | 9 |
# MAGIC | suppliers | 29 |
# MAGIC | shippers | 3 |
# MAGIC | products | 77 |
# MAGIC | orders | 830 |
# MAGIC | order_details | 2,155 |
# MAGIC | region | 4 |
# MAGIC | territories | 53 |
# MAGIC | us_states | 51 |
# MAGIC | employee_territories | 49 |
# MAGIC | customer_demographics | 0 |
# MAGIC | customer_customer_demo | 0 |
# MAGIC
# MAGIC **次のステップ**: `02_etl_bronze_ingest.py`
