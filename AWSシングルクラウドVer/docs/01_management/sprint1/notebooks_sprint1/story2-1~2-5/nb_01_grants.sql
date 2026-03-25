-- Epic 2 / Sprint 1 - Story 2-2: analyst_group 権限設定
-- ※ admin アカウント（metastore admin または catalog owner）で実行すること

-- Step 2-4-1: カタログへの USE 権限（配下スキーマへのアクセスに必須）
GRANT USE CATALOG ON CATALOG northwind_catalog TO analyst_group;

-- Step 2-4-2: Gold スキーマへの USE + SELECT 権限
-- bronze / silver / ops は意図的に付与しない（Unity Catalog はデフォルト拒否）
GRANT USE SCHEMA ON SCHEMA northwind_catalog.gold TO analyst_group;
GRANT SELECT ON SCHEMA northwind_catalog.gold TO analyst_group;

-- Step 2-5: 付与内容の確認
-- 期待結果: analyst_group に USE SCHEMA と SELECT が表示される
SHOW GRANTS ON SCHEMA northwind_catalog.gold;