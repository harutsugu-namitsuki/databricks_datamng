-- 顧客別売上集計
-- データソース: gold.sales_by_customer（全期間を集計）
SELECT
    company_name,
    country,
    SUM(total_sales)                AS total_sales,
    SUM(order_count)                AS order_count,
    ROUND(AVG(avg_order_value), 2)  AS avg_order_value
FROM northwind_catalog.gold.sales_by_customer
GROUP BY company_name, country
ORDER BY total_sales DESC
