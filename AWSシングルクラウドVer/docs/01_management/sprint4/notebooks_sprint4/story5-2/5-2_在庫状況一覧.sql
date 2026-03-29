-- 在庫状況一覧（全商品のリスク判定付き）
-- データソース: silver.products + silver.categories
SELECT
    p.product_id,
    p.product_name,
    c.category_name,
    p.unit_price,
    p.units_in_stock,
    p.reorder_level,
    p.units_on_order,
    p.discontinued,
    CASE
        WHEN p.discontinued = 1 THEN '廃止'
        WHEN p.units_in_stock = 0 THEN '在庫切れ'
        WHEN p.units_in_stock <= p.reorder_level AND p.units_on_order = 0 THEN '発注点割れ（未発注）'
        WHEN p.units_in_stock <= p.reorder_level AND p.units_on_order > 0 THEN '発注点割れ（発注済）'
        ELSE '正常'
    END AS stock_status
FROM northwind_catalog.silver.products p
LEFT JOIN northwind_catalog.bronze.categories c
    ON p.category_id = c.category_id
ORDER BY
    CASE
        WHEN p.discontinued = 1 THEN 4
        WHEN p.units_in_stock = 0 THEN 1
        WHEN p.units_in_stock <= p.reorder_level AND p.units_on_order = 0 THEN 2
        WHEN p.units_in_stock <= p.reorder_level AND p.units_on_order > 0 THEN 3
        ELSE 5
    END,
    p.product_name
