-- タイトル: 売上上位10社の顧客
-- 説明: 売上金額が多い順に上位10社の顧客を表示する
-- 用途: Genie Space のサンプル SQL クエリとして登録する

SELECT
  c.company_name                                                               AS company_name,
  c.country                                                                    AS country,
  ROUND(SUM(od.unit_price * od.quantity * (1 - od.discount)), 2)               AS total_sales
FROM silver.orders        AS o
JOIN silver.customers     AS c  ON o.customer_id = c.customer_id
JOIN silver.order_details AS od ON o.order_id    = od.order_id
GROUP BY c.company_name, c.country
ORDER BY total_sales DESC
LIMIT 10;
