# タグ分類体系（Epic 3 / Story 3-2）

Unity Catalog のテーブルタグ・カラムタグの設計定義。
`ALTER TABLE ... SET TAGS` / `ALTER TABLE ... ALTER COLUMN ... SET TAGS` で適用する。

---

## 1. タグキー定義（タクソノミー）

| タグキー | 説明 | 許容値 |
|---------|------|--------|
| `domain` | 業務ドメイン | `sales`, `product`, `customer`, `employee`, `logistics`, `operations`, `reference` |
| `layer` | メダリオン層 | `bronze`, `silver`, `gold`, `ops` |
| `pii` | 個人情報を含むか | `true`, `false` |
| `update_frequency` | 更新頻度 | `daily`, `one_time`, `append` |
| `data_type` | データ種別 | `master`, `transaction`, `aggregate`, `log`, `reference` |

### タグキーの設計思想

- **domain**: ビジネスユーザーが「売上に関するテーブル」「従業員に関するテーブル」のようにドメイン単位で検索するためのキー
- **layer**: メダリオンアーキテクチャのどの層に属するかを明示。Catalog Explorer での絞り込みに使用
- **pii**: GDPR/個人情報保護の観点でPIIを含むテーブルを即座に特定するためのキー
- **update_frequency**: データの鮮度や更新タイミングを把握するためのキー
- **data_type**: マスタ/トランザクション/集計/ログの区別を明示するためのキー

---

## 2. テーブル別タグマッピング

### 2-1. Bronze 層（14テーブル）

| テーブル | domain | layer | pii | update_frequency | data_type |
|---------|--------|-------|-----|-----------------|-----------|
| `categories` | `product` | `bronze` | `false` | `daily` | `master` |
| `customers` | `customer` | `bronze` | `true` | `daily` | `master` |
| `employees` | `employee` | `bronze` | `true` | `daily` | `master` |
| `suppliers` | `logistics` | `bronze` | `false` | `daily` | `master` |
| `shippers` | `logistics` | `bronze` | `false` | `daily` | `master` |
| `products` | `product` | `bronze` | `false` | `daily` | `master` |
| `region` | `reference` | `bronze` | `false` | `daily` | `reference` |
| `orders` | `sales` | `bronze` | `false` | `daily` | `transaction` |
| `order_details` | `sales` | `bronze` | `false` | `daily` | `transaction` |
| `territories` | `reference` | `bronze` | `false` | `daily` | `reference` |
| `us_states` | `reference` | `bronze` | `false` | `daily` | `reference` |
| `employee_territories` | `employee` | `bronze` | `false` | `daily` | `reference` |
| `customer_demographics` | `customer` | `bronze` | `false` | `daily` | `reference` |
| `customer_customer_demo` | `customer` | `bronze` | `false` | `daily` | `reference` |

### 2-2. Silver 層（4テーブル）

| テーブル | domain | layer | pii | update_frequency | data_type |
|---------|--------|-------|-----|-----------------|-----------|
| `customers` | `customer` | `silver` | `true` | `daily` | `master` |
| `orders` | `sales` | `silver` | `false` | `daily` | `transaction` |
| `order_details` | `sales` | `silver` | `false` | `daily` | `transaction` |
| `products` | `product` | `silver` | `false` | `daily` | `master` |

### 2-3. Gold 層（4テーブル）

| テーブル | domain | layer | pii | update_frequency | data_type |
|---------|--------|-------|-----|-----------------|-----------|
| `sales_by_product` | `sales` | `gold` | `false` | `daily` | `aggregate` |
| `sales_by_customer` | `sales` | `gold` | `false` | `daily` | `aggregate` |
| `sales_by_category` | `sales` | `gold` | `false` | `daily` | `aggregate` |
| `order_summary` | `sales` | `gold` | `false` | `daily` | `aggregate` |

### 2-4. Ops 層（3テーブル）

| テーブル | domain | layer | pii | update_frequency | data_type |
|---------|--------|-------|-----|-----------------|-----------|
| `job_runs` | `operations` | `ops` | `false` | `append` | `log` |
| `ingestion_log` | `operations` | `ops` | `false` | `append` | `log` |
| `dq_results` | `operations` | `ops` | `false` | `append` | `log` |

---

## 3. PII カラムタグ

個人情報を含むカラムに対して、カラムレベルで PII タグを付与する。
テーブルタグの `pii:true` は「このテーブルに PII が含まれる」の目印、カラムタグの `pii:true` は「このカラムが PII そのもの」の目印として使い分ける。
`domain`/`layer` 等の他のタグキーはテーブルレベルのみ（テーブル内の全カラムで値が同じため、カラムレベルに付けても情報が増えない）。

### 3-1. `bronze.customers` のPIIカラム

| カラム名 | pii | pii_type |
|---------|-----|----------|
| `contact_name` | `true` | `name` |
| `address` | `true` | `address` |
| `phone` | `true` | `phone` |
| `fax` | `true` | `phone` |

### 3-2. `bronze.employees` のPIIカラム

| カラム名 | pii | pii_type |
|---------|-----|----------|
| `birth_date` | `true` | `birth_date` |
| `address` | `true` | `address` |
| `home_phone` | `true` | `phone` |
| `photo` | `true` | `photo` |

### 3-3. `silver.customers` のPIIカラム

Bronze から引き継いだ PII カラム（クレンジング済み）。

| カラム名 | pii | pii_type |
|---------|-----|----------|
| `contact_name` | `true` | `name` |
| `address` | `true` | `address` |
| `phone` | `true` | `phone` |
| `fax` | `true` | `phone` |

### pii_type の定義

| pii_type | 説明 |
|----------|------|
| `name` | 個人氏名 |
| `birth_date` | 生年月日 |
| `address` | 住所 |
| `phone` | 電話番号・FAX番号 |
| `photo` | 顔写真等の画像データ |

---

## 4. タグ検索の想定ユースケース

| ユースケース | 検索条件 | 期待ヒット数 |
|------------|---------|------------|
| 売上に関するテーブルを探す | `domain = 'sales'` | 8テーブル |
| 個人情報を含むテーブルを探す | `pii = 'true'` | 3テーブル |
| PIIカラムを特定する | カラムタグ `pii = 'true'` | 12カラム |
| Gold層の集計テーブルを探す | `data_type = 'aggregate'` | 4テーブル |
| 運用ログを探す | `domain = 'operations'` | 3テーブル |
| Gold層 × 売上ドメイン | `layer = 'gold' AND domain = 'sales'` | 4テーブル |

---

## 5. 拡張計画（Sprint 4 / Story 3-6〜3-8 で追加予定）

Sprint 4 で以下のタグ拡張を予定:

- MLflow 実験テーブル・推論結果テーブルへのタグ付与（Story 3-6）
- `domain: ml` タグの追加
- BI ダッシュボード関連テーブルへのタグ付与
- カタログ全体の網羅性チェックと補完（Story 3-8）
