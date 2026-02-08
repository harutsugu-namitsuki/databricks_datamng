# Unity Catalog 設計書

## 1. 概要

Unity Catalog を使用してデータガバナンスを実現します。

---

## 2. 名前空間構造

```
Unity Catalog
└── northwind_catalog (カタログ)
    ├── bronze (スキーマ)
    │   ├── customers
    │   ├── orders
    │   └── ...
    ├── silver (スキーマ)
    │   ├── customers
    │   ├── orders
    │   └── ...
    └── gold (スキーマ)
        ├── sales_by_product
        ├── sales_by_customer
        └── ...
```

---

## 3. Storage Credential

| 項目 | 値 |
|------|-----|
| 名前 | `azure_adls_credential` |
| タイプ | Azure Managed Identity |
| Access Connector | `/subscriptions/.../accessConnectors/<name>` |

---

## 4. External Location

| 名前 | URL | Credential |
|------|-----|------------|
| `ext_bronze` | `abfss://bronze@<account>.dfs.core.windows.net/` | azure_adls_credential |
| `ext_silver` | `abfss://silver@<account>.dfs.core.windows.net/` | azure_adls_credential |
| `ext_gold` | `abfss://gold@<account>.dfs.core.windows.net/` | azure_adls_credential |

---

## 5. アクセス制御

### 5.1 ロール設計

| ロール | 権限 |
|--------|------|
| data_engineer | Bronze/Silver/Gold の読み書き |
| data_analyst | Silver/Gold の読み取りのみ |
| admin | 全権限 |

### 5.2 権限付与例

```sql
-- Analystにgoldスキーマの読み取り権限を付与
GRANT SELECT ON SCHEMA northwind_catalog.gold TO analyst_group;
```

---

## 変更履歴

| 日付 | 変更内容 |
|------|----------|
| 2026-02-09 | 初版作成 |
