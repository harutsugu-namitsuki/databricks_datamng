-- 商品別売上ランキング TOP 20
-- データソース: gold.sales_by_product（全期間を集計）
SELECT
    product_name,
    SUM(total_sales)     AS total_sales,
    SUM(total_quantity)  AS total_quantity,
    SUM(order_count)     AS order_count
FROM northwind_catalog.gold.sales_by_product
GROUP BY product_name
ORDER BY total_sales DESC
LIMIT 20
