-- 発注点割れアラート（発注が必要な商品の詳細）
SELECT
    p.product_name,
    c.category_name,
    s.company_name                                        AS supplier_name,
    p.units_in_stock,
    p.reorder_level,
    (p.reorder_level - p.units_in_stock)                  AS shortage_qty,
    p.units_on_order,
    p.unit_price,
    ROUND((p.reorder_level - p.units_in_stock) * p.unit_price, 2) AS estimated_order_cost,
    CASE
        WHEN p.units_on_order > 0 THEN '発注済'
        ELSE '未発注 - 要アクション'
    END AS order_status
FROM northwind_catalog.silver.products p
LEFT JOIN northwind_catalog.bronze.categories c
    ON p.category_id = c.category_id
LEFT JOIN northwind_catalog.bronze.suppliers s
    ON p.supplier_id = s.supplier_id
WHERE p.discontinued = 0
  AND p.units_in_stock < p.reorder_level
ORDER BY shortage_qty DESC
