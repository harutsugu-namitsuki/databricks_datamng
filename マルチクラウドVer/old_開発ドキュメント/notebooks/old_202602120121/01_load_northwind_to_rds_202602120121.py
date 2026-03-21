# Databricks notebook source
# MAGIC %md
# MAGIC # 01. Northwindデータ → RDS PostgreSQL 投入
# MAGIC 
# MAGIC このノートブックでは、NorthwindサンプルデータをRDS PostgreSQLにロードします。
# MAGIC 
# MAGIC **前提条件**:
# MAGIC - RDS PostgreSQLが起動している（CloudFormationデプロイ済み）
# MAGIC - セキュリティグループでDatabricksからの接続が許可されている

# COMMAND ----------

# MAGIC %md
# MAGIC ## ⚠️ 設定値を入力してください
# MAGIC 
# MAGIC CloudFormationの出力やAWSコンソールから以下の値を取得して入力してください

# COMMAND ----------

# ============================================
# 👇 ここに実際の値を入力してください 👇
# ============================================

# RDS接続情報（CloudFormation出力から取得）
DB_HOST = "premigration-northwind-db.cb0as2s6sr83.ap-southeast-2.rds.amazonaws.com"  # RDSEndpoint
DB_USER = "dbadmin"        # パラメータで設定したDBUsername
DB_PASSWORD = "Yi2345678"  # パラメータで設定したDBPassword
DB_NAME = "northwind"
DB_PORT = 5432

print(f"✅ 設定値")
print(f"   DB Host: {DB_HOST}")
print(f"   DB User: {DB_USER}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## JDBC接続情報の構築

# COMMAND ----------

# JDBC URL構築
jdbc_url = f"jdbc:postgresql://{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"

# 接続プロパティ
connection_properties = {
    "user": DB_USER,
    "password": DB_PASSWORD,
    "driver": "org.postgresql.Driver"
}

print(f"JDBC URL: {jdbc_url}")
print(f"✅ 接続情報を構築しました")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Northwind DDL準備
# MAGIC 
# MAGIC RDSに直接接続してテーブルを作成します

# COMMAND ----------

# Northwind DDL（簡易版 - 主要テーブルのみ）
northwind_ddl = """
-- 既存テーブルを削除（外部キー制約も含めて）
DROP TABLE IF EXISTS order_details CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS employees CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS suppliers CASCADE;
DROP TABLE IF EXISTS categories CASCADE;

-- Categories（カテゴリ）
CREATE TABLE categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(50) NOT NULL,
    description TEXT
);

-- Suppliers（仕入先）
CREATE TABLE suppliers (
    supplier_id SERIAL PRIMARY KEY,
    company_name VARCHAR(100) NOT NULL,
    contact_name VARCHAR(50),
    contact_title VARCHAR(50),
    address VARCHAR(100),
    city VARCHAR(50),
    region VARCHAR(50),
    postal_code VARCHAR(20),
    country VARCHAR(50),
    phone VARCHAR(30),
    fax VARCHAR(30)
);

-- Products（製品）
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    supplier_id INTEGER REFERENCES suppliers(supplier_id),
    category_id INTEGER REFERENCES categories(category_id),
    quantity_per_unit VARCHAR(50),
    unit_price DECIMAL(10,2),
    units_in_stock INTEGER DEFAULT 0,
    units_on_order INTEGER DEFAULT 0,
    reorder_level INTEGER DEFAULT 0,
    discontinued BOOLEAN DEFAULT FALSE
);

-- Customers（顧客）
CREATE TABLE customers (
    customer_id VARCHAR(10) PRIMARY KEY,
    company_name VARCHAR(100) NOT NULL,
    contact_name VARCHAR(50),
    contact_title VARCHAR(50),
    address VARCHAR(100),
    city VARCHAR(50),
    region VARCHAR(50),
    postal_code VARCHAR(20),
    country VARCHAR(50),
    phone VARCHAR(30),
    fax VARCHAR(30)
);

-- Employees（従業員）
CREATE TABLE employees (
    employee_id SERIAL PRIMARY KEY,
    last_name VARCHAR(50) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    title VARCHAR(50),
    birth_date DATE,
    hire_date DATE,
    address VARCHAR(100),
    city VARCHAR(50),
    region VARCHAR(50),
    postal_code VARCHAR(20),
    country VARCHAR(50),
    phone VARCHAR(30)
);

-- Orders（注文）
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id VARCHAR(10) REFERENCES customers(customer_id),
    employee_id INTEGER REFERENCES employees(employee_id),
    order_date DATE,
    required_date DATE,
    shipped_date DATE,
    ship_via INTEGER,
    freight DECIMAL(10,2),
    ship_name VARCHAR(100),
    ship_address VARCHAR(100),
    ship_city VARCHAR(50),
    ship_region VARCHAR(50),
    ship_postal_code VARCHAR(20),
    ship_country VARCHAR(50)
);

-- Order Details（注文明細）
CREATE TABLE order_details (
    order_id INTEGER REFERENCES orders(order_id),
    product_id INTEGER REFERENCES products(product_id),
    unit_price DECIMAL(10,2) NOT NULL,
    quantity INTEGER NOT NULL,
    discount DECIMAL(4,2) DEFAULT 0,
    PRIMARY KEY (order_id, product_id)
);
"""

print("✅ DDLを準備しました")
print("次のセルでRDSにDDLを実行します")

# COMMAND ----------

# MAGIC %md
# MAGIC ## PostgreSQLドライバのインストール

# COMMAND ----------

# psycopg2のインストール
%pip install psycopg2-binary

# COMMAND ----------

# MAGIC %md
# MAGIC ## DDLをRDSに実行

# COMMAND ----------

import psycopg2

# RDSに接続
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
    
    # DDL実行
    cursor.execute(northwind_ddl)
    print("✅ DDL実行完了: テーブルが作成されました")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ エラー: {str(e)}")
    print("\n確認事項:")
    print("1. DB_HOST, DB_USER, DB_PASSWORD が正しいか")
    print("2. RDSのセキュリティグループでDatabricks IPからの接続が許可されているか")
    print("3. RDSがパブリックアクセス可能になっているか")
    raise e

# COMMAND ----------

# MAGIC %md
# MAGIC ## サンプルデータ投入

# COMMAND ----------

# サンプルデータ
sample_data_sql = """
-- Categories
INSERT INTO categories (category_name, description) VALUES
('Beverages', 'Soft drinks, coffees, teas, beers, and ales'),
('Condiments', 'Sweet and savory sauces, relishes, spreads, and seasonings'),
('Confections', 'Desserts, candies, and sweet breads'),
('Dairy Products', 'Cheeses'),
('Grains/Cereals', 'Breads, crackers, pasta, and cereal'),
('Meat/Poultry', 'Prepared meats'),
('Produce', 'Dried fruit and bean curd'),
('Seafood', 'Seaweed and fish')
ON CONFLICT DO NOTHING;

-- Suppliers
INSERT INTO suppliers (company_name, contact_name, city, country, phone) VALUES
('Exotic Liquids', 'Charlotte Cooper', 'London', 'UK', '(171) 555-2222'),
('New Orleans Cajun Delights', 'Shelley Burke', 'New Orleans', 'USA', '(100) 555-4822'),
('Tokyo Traders', 'Yoshi Nagase', 'Tokyo', 'Japan', '(03) 3555-5011')
ON CONFLICT DO NOTHING;

-- Customers
INSERT INTO customers (customer_id, company_name, contact_name, city, country) VALUES
('ALFKI', 'Alfreds Futterkiste', 'Maria Anders', 'Berlin', 'Germany'),
('ANATR', 'Ana Trujillo Emparedados', 'Ana Trujillo', 'México D.F.', 'Mexico'),
('ANTON', 'Antonio Moreno Taquería', 'Antonio Moreno', 'México D.F.', 'Mexico'),
('AROUT', 'Around the Horn', 'Thomas Hardy', 'London', 'UK'),
('BERGS', 'Berglunds snabbköp', 'Christina Berglund', 'Luleå', 'Sweden')
ON CONFLICT DO NOTHING;

-- Employees
INSERT INTO employees (first_name, last_name, title, hire_date, city, country) VALUES
('Nancy', 'Davolio', 'Sales Representative', '1992-05-01', 'Seattle', 'USA'),
('Andrew', 'Fuller', 'Vice President, Sales', '1992-08-14', 'Tacoma', 'USA'),
('Janet', 'Leverling', 'Sales Representative', '1992-04-01', 'Kirkland', 'USA')
ON CONFLICT DO NOTHING;

-- Products
INSERT INTO products (product_name, supplier_id, category_id, unit_price, units_in_stock) VALUES
('Chai', 1, 1, 18.00, 39),
('Chang', 1, 1, 19.00, 17),
('Aniseed Syrup', 1, 2, 10.00, 13),
('Chef Anton''s Cajun Seasoning', 2, 2, 22.00, 53),
('Gumbo Mix', 2, 2, 21.35, 0),
('Ikura', 3, 8, 31.00, 31)
ON CONFLICT DO NOTHING;

-- Orders
INSERT INTO orders (customer_id, employee_id, order_date, ship_city, ship_country, freight) VALUES
('ALFKI', 1, '2024-01-15', 'Berlin', 'Germany', 29.46),
('ANATR', 2, '2024-01-16', 'México D.F.', 'Mexico', 1.61),
('ANTON', 3, '2024-01-17', 'México D.F.', 'Mexico', 13.97),
('AROUT', 1, '2024-01-18', 'London', 'UK', 81.91),
('BERGS', 2, '2024-01-19', 'Luleå', 'Sweden', 151.52)
ON CONFLICT DO NOTHING;

-- Order Details
INSERT INTO order_details (order_id, product_id, unit_price, quantity, discount) VALUES
(1, 1, 18.00, 10, 0),
(1, 2, 19.00, 5, 0.1),
(2, 3, 10.00, 20, 0),
(3, 4, 22.00, 15, 0.05),
(4, 5, 21.35, 8, 0),
(5, 6, 31.00, 12, 0.15)
ON CONFLICT DO NOTHING;
"""

# RDSに接続してデータ投入
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

cursor.execute(sample_data_sql)
print("✅ サンプルデータ投入完了")

cursor.close()
conn.close()

# COMMAND ----------

# MAGIC %md
# MAGIC ## データ確認

# COMMAND ----------

# 各テーブルの件数を確認
tables = ['categories', 'suppliers', 'customers', 'employees', 'products', 'orders', 'order_details']

print("📊 各テーブルの件数:")
for table in tables:
    df = spark.read.jdbc(
        url=jdbc_url,
        table=table,
        properties=connection_properties
    )
    count = df.count()
    print(f"  {table}: {count} 件")

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ 完了チェックリスト
# MAGIC 
# MAGIC - [ ] DDLが正常に実行された
# MAGIC - [ ] サンプルデータが投入された
# MAGIC - [ ] 各テーブルの件数が確認できた
# MAGIC 
# MAGIC 次のステップ: `02_etl_bronze_ingest.py` でRDSからBronzeレイヤーにデータを取り込みます
