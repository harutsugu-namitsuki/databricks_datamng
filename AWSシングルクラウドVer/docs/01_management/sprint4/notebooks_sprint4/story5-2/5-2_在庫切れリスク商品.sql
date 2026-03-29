-- 在庫切れリスク商品（在庫ゼロ or 発注点以下、かつ非廃止）
SELECT
    p.product_name,
    c.category_name,
    p.units_in_stock,
    p.reorder_level,
    p.units_on_order,
    p.unit_price,
    CASE
        WHEN p.units_in_stock = 0 THEN '在庫切れ'
        WHEN p.units_on_order = 0 THEN '要発注'
        ELSE '発注済（入荷待ち）'
    END AS alert_level
FROM northwind_catalog.silver.products p
LEFT JOIN northwind_catalog.bronze.categories c
    ON p.category_id = c.category_id
WHERE p.discontinued = 0
  AND p.units_in_stock <= p.reorder_level
ORDER BY p.units_in_stock ASC, p.reorder_level DESC
