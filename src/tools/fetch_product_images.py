"""商品画像をローカルに取得するユーティリティ

各商品 (product_id) に対し、商品名から導いた「実在する食品キーワード」で
ライセンスがクリーンな画像 (Openverse / Wikimedia Commons) を検索・ダウンロードし、
src/web/img/products/{product_id}.jpg として 480x320 (3:2) で保存する。

使い方:
    python src/tools/fetch_product_images.py            # 未取得の商品だけ取得
    python src/tools/fetch_product_images.py --force     # 既存ファイルも上書き
    python src/tools/fetch_product_images.py --only 1 9 38   # 指定IDだけ取得

画像を手動で差し替えたい場合:
    src/web/img/products/{product_id}.jpg を好きな画像に置き換えるだけ。
    （--force を付けずに再実行すれば、既存ファイルは上書きされない）

ライセンス: Openverse は CC / パブリックドメイン画像のみ、Wikimedia Commons も
同様にフリーライセンス。商用デモでも安全に使える画像のみを取得する。
"""

import io
import sys
import time
import argparse
from pathlib import Path

import requests
from PIL import Image

# src/ を import パスに追加して api.db を使えるようにする
SRC_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SRC_DIR))
from api.db import fetch_all  # noqa: E402

OUT_DIR = SRC_DIR / "web" / "img" / "products"
TARGET_SIZE = (480, 320)  # 商品カード画像 (3:2)
USER_AGENT = "NorthwindStore-ImageFetcher/1.0 (educational demo)"

# 商品名 → 検索キーワード。架空ブランド名・多言語名を実在の食品語に翻訳する。
KEYWORDS = {
    1:  "chai tea",
    2:  "beer bottle",
    3:  "anise syrup bottle",
    4:  "cajun seasoning spice",
    5:  "gumbo soup",
    6:  "boysenberry jam",
    7:  "dried pears",
    8:  "cranberry sauce",
    9:  "wagyu kobe beef",
    10: "salmon roe ikura",
    11: "blue cheese",
    12: "manchego cheese",
    13: "kombu seaweed",
    14: "tofu",
    15: "soy sauce bottle",
    16: "pavlova dessert",
    17: "lamb mutton meat",
    18: "tiger prawns",
    19: "chocolate biscuits",
    20: "orange marmalade jar",
    21: "scones",
    22: "crispbread knackebrod",
    23: "swedish flatbread",
    24: "guarana soda drink",
    25: "chocolate hazelnut spread",
    26: "gummy bears",
    27: "chocolate bar",
    28: "sauerkraut",
    29: "bratwurst sausage",
    30: "pickled herring matjes",
    31: "gorgonzola cheese",
    32: "mascarpone cheese",
    33: "norwegian brown cheese",
    34: "ale beer glass",
    35: "stout beer",
    36: "pickled herring",
    37: "gravlax cured salmon",
    38: "red wine bottle",
    39: "green chartreuse liqueur",
    40: "crab meat",
    41: "clam chowder",
    42: "fried noodles hokkien",
    43: "coffee cup beans",
    44: "palm sugar gula melaka",
    45: "smoked herring",
    46: "salted herring",
    47: "dutch spiced cookies",
    48: "chocolate",
    49: "licorice candy",
    50: "white chocolate",
    51: "dried apples",
    52: "filo pastry",
    53: "meat pasty pie",
    54: "tourtiere meat pie",
    55: "shepherds pie",
    56: "gnocchi",
    57: "ravioli pasta",
    58: "escargot snails",
    59: "raclette cheese",
    60: "camembert cheese",
    61: "maple syrup",
    62: "sugar pie tart",
    63: "yeast vegetable spread",
    64: "bread dumplings",
    65: "hot pepper sauce bottle",
    66: "pickled okra",
    67: "lager beer",
    68: "shortbread cookies",
    69: "norwegian brown cheese",
    70: "lager beer glass",
    71: "brown cheese",
    72: "mozzarella cheese",
    73: "red caviar",
    74: "tofu block",
    75: "dark monastery beer",
    76: "cloudberry liqueur",
    77: "green herb sauce",
}


def _session():
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT})
    return s


def fetch_openverse(sess, query):
    """Openverse から画像バイト列を取得 (失敗時 None)。"""
    try:
        r = sess.get(
            "https://api.openverse.org/v1/images/",
            params={"q": query, "page_size": 8, "mature": "false"},
            timeout=20,
        )
        if r.status_code != 200:
            return None
        for item in r.json().get("results", []):
            for url in (item.get("thumbnail"), item.get("url")):
                if not url:
                    continue
                data = _download_image(sess, url)
                if data:
                    return data
    except requests.RequestException:
        return None
    return None


def fetch_commons(sess, query):
    """Wikimedia Commons から画像バイト列を取得 (失敗時 None)。"""
    try:
        r = sess.get(
            "https://commons.wikimedia.org/w/api.php",
            params={
                "action": "query", "format": "json",
                "generator": "search",
                "gsrsearch": f"{query} filetype:bitmap",
                "gsrnamespace": 6, "gsrlimit": 8,
                "prop": "imageinfo", "iiprop": "url", "iiurlwidth": 600,
            },
            timeout=20,
        )
        if r.status_code != 200:
            return None
        pages = r.json().get("query", {}).get("pages", {})
        for page in pages.values():
            for info in page.get("imageinfo", []):
                url = info.get("thumburl") or info.get("url")
                data = _download_image(sess, url) if url else None
                if data:
                    return data
    except requests.RequestException:
        return None
    return None


def _download_image(sess, url):
    try:
        r = sess.get(url, timeout=20)
        if r.status_code == 200 and r.content and len(r.content) > 1000:
            return r.content
    except requests.RequestException:
        pass
    return None


def _save_cover(data, dest):
    """480x320 にカバー配置 (中央クロップ) して JPEG 保存。"""
    img = Image.open(io.BytesIO(data)).convert("RGB")
    tw, th = TARGET_SIZE
    sw, sh = img.size
    scale = max(tw / sw, th / sh)
    img = img.resize((round(sw * scale), round(sh * scale)), Image.LANCZOS)
    nw, nh = img.size
    left, top = (nw - tw) // 2, (nh - th) // 2
    img = img.crop((left, top, left + tw, top + th))
    img.save(dest, "JPEG", quality=85)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="既存ファイルも上書き")
    ap.add_argument("--only", nargs="*", type=int, help="指定 product_id だけ取得")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    products = fetch_all(
        "SELECT product_id, product_name FROM products ORDER BY product_id"
    )
    sess = _session()

    ok, skip, fail = 0, 0, []
    for p in products:
        pid, name = p["product_id"], p["product_name"]
        if args.only and pid not in args.only:
            continue
        dest = OUT_DIR / f"{pid}.jpg"
        if dest.exists() and not args.force:
            skip += 1
            continue

        query = KEYWORDS.get(pid) or name
        data = fetch_openverse(sess, query)
        source = "openverse"
        if not data:
            data = fetch_commons(sess, query)
            source = "commons"
        if not data:
            print(f"  [FAIL] {pid:>2} {name!r}  q={query!r}")
            fail.append(pid)
            time.sleep(0.5)
            continue
        try:
            _save_cover(data, dest)
            ok += 1
            print(f"  [ OK ] {pid:>2} {name!r}  <- {source}  q={query!r}")
        except Exception as e:  # 画像デコード失敗など
            print(f"  [FAIL] {pid:>2} {name!r}  decode error: {e}")
            fail.append(pid)
        time.sleep(0.4)  # API への配慮

    print(f"\n完了: OK={ok} SKIP={skip} FAIL={len(fail)}")
    if fail:
        print("失敗した product_id:", fail)
        print("→ 再実行 (--only でID指定) するか、手動で {ID}.jpg を配置してください。")


if __name__ == "__main__":
    main()
