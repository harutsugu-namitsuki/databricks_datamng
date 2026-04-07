-- カテゴリ別月次売上推移
-- データソース: gold.sales_by_category
SELECT
    category_name,
    MAKE_DATE(order_year, order_month, 1)  AS order_month,
    total_sales,
    total_quantity,
    order_count
FROM northwind_catalog.gold.sales_by_category
ORDER BY order_month, category_name
