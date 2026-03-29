-- タイトル: 商品カテゴリ別の売上
-- 説明: 商品カテゴリごとの売上金額と販売数量を集計する
-- 用途: Genie Space のサンプル SQL クエリとして登録する

SELECT
  cat.category_name                                                            AS category_name,
  ROUND(SUM(od.unit_price * od.quantity * (1 - od.discount)), 2)               AS total_sales,
  SUM(od.quantity)                                                             AS total_quantity
FROM silver.order_details AS od
JOIN silver.products      AS p   ON od.product_id  = p.product_id
JOIN silver.categories    AS cat ON p.category_id   = cat.category_id
GROUP BY cat.category_name
ORDER BY total_sales DESC;
