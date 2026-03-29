-- タイトル: 在庫切れの商品一覧
-- 説明: 在庫数がゼロで、かつ販売終了していない商品を表示する
-- 用途: Genie Space のサンプル SQL クエリとして登録する

SELECT
  p.product_name                                                               AS product_name,
  cat.category_name                                                            AS category_name,
  s.company_name                                                               AS supplier_name
FROM silver.products   AS p
JOIN silver.categories AS cat ON p.category_id  = cat.category_id
JOIN silver.suppliers  AS s   ON p.supplier_id  = s.supplier_id
WHERE p.units_in_stock = 0
  AND p.discontinued   = 0;
