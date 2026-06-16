-- タイトル: 国別の売上ランキング
-- 説明: 顧客の国別に売上金額を集計し、降順で表示する
-- 用途: Genie Space のサンプル SQL クエリとして登録する

SELECT
  c.country                                                                    AS country,
  ROUND(SUM(od.unit_price * od.quantity * (1 - od.discount)), 2)               AS total_sales,
  COUNT(DISTINCT o.order_id)                                                   AS order_count
FROM silver.orders       AS o
JOIN silver.customers    AS c  ON o.customer_id = c.customer_id
JOIN silver.order_details AS od ON o.order_id    = od.order_id
GROUP BY c.country
ORDER BY total_sales DESC;
