# 商品画像

商品カタログ ([catalog.html](../../store/catalog.html)) に表示される商品画像。

- ファイル名 = `{product_id}.jpg`（例: `1.jpg` は Chai）
- 配信URL = `/static/img/products/{product_id}.jpg`
- 推奨サイズ = 480×320 (3:2)。違うサイズでも CSS の `object-fit: cover` で表示される。

## 画像を差し替えたいとき

該当の `{product_id}.jpg` を好きな画像に置き換えるだけ。
（ファイルが無い商品は、画面側で自動的に picsum.photos のランダム画像にフォールバックする）

## 一括取得・再取得

```bash
python src/tools/fetch_product_images.py            # 未取得の商品だけ取得（既存は上書きしない）
python src/tools/fetch_product_images.py --force     # 全件再取得
python src/tools/fetch_product_images.py --only 1 9   # 指定IDだけ
```

検索キーワードは `src/tools/fetch_product_images.py` の `KEYWORDS` で商品ごとに定義。
画像は Openverse / Wikimedia Commons（CC・パブリックドメイン）から取得している。
