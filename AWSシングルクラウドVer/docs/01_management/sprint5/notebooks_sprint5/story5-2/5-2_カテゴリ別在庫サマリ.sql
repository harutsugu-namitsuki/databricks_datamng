-- カテゴリ別在庫サマリ
SELECT
    c.category_name,
    COUNT(*)                                                                       AS product_count,
    SUM(CASE WHEN p.units_in_stock = 0 AND p.discontinued = 0 THEN 1 ELSE 0 END)  AS out_of_stock_count,
    SUM(CASE WHEN p.units_in_stock <= p.reorder_level
              AND p.units_in_stock > 0
              AND p.discontinued = 0 THEN 1 ELSE 0 END)                           AS below_reorder_count,
    SUM(p.units_in_stock)                                                          AS total_stock,
    ROUND(SUM(p.units_in_stock * p.unit_price), 2)                                 AS stock_value
FROM northwind_catalog.silver.products p
LEFT JOIN northwind_catalog.silver.categories c
    ON p.category_id = c.category_id
GROUP BY c.category_name
ORDER BY out_of_stock_count DESC, below_reorder_count DESC
