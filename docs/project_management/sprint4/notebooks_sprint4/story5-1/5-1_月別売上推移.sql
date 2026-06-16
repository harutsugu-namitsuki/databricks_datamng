-- 月別売上推移
-- データソース: gold.order_summary（日次注文サマリ）を月単位に集計
SELECT
    DATE_TRUNC('month', order_date)  AS order_month,
    SUM(total_sales)                 AS monthly_sales,
    SUM(line_count)                  AS monthly_orders,
    ROUND(AVG(avg_line_value), 2)    AS avg_order_value
FROM northwind_catalog.gold.order_summary
GROUP BY DATE_TRUNC('month', order_date)
ORDER BY order_month
