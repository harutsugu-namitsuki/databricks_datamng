# -*- coding: utf-8 -*-
"""Build src/api/trace_map.json by transcribing the UI mockup's JS objects.

Source of truth:
  docs/design/app_development/操作トレース可視化システム_UIモックアップ.html

This is a faithful transcription: COLS / N / DETAIL copied verbatim; edges
derived from ACTIONS exactly as the mockup's allEdges construction does.
"""
import json
import pathlib

COLS = ["画面", "fetch", "CORS", "認証", "ハンドラ関数", "db.py", "psycopg2", "テーブル"]

N = {
    "catalog": {"c": 0, "l": "catalog.html", "s": "商品一覧画面"},
    "checkout": {"c": 0, "l": "checkout.html", "s": "注文確定画面"},
    "inventory": {"c": 0, "l": "inventory.html", "s": "在庫管理(admin)"},
    "dashPage": {"c": 0, "l": "dashboard.html", "s": "ダッシュボード(admin)"},
    "login": {"c": 0, "l": "login.html", "s": "ログイン画面"},
    "fetch": {"c": 1, "l": "fetch()", "s": "web/js/api.js"},
    "cors": {"c": 2, "l": "CORS MW", "s": "main.py:29"},
    "auth": {"c": 3, "l": "_require_token", "s": "Bearer照合"},
    "h_list": {"c": 4, "l": "list_products", "s": "GET /api/products"},
    "h_adj": {"c": 4, "l": "adjust_stock", "s": "POST /inventory/adjust"},
    "h_order": {"c": 4, "l": "create_order", "s": "POST /api/orders"},
    "h_dash": {"c": 4, "l": "dashboard", "s": "GET /api/dashboard"},
    "h_slogin": {"c": 4, "l": "store_login", "s": "POST /auth/store"},
    "db": {"c": 5, "l": "db.py", "s": "fetch_all/execute"},
    "pg": {"c": 6, "l": "psycopg2", "s": "PG ドライバ"},
    "t_products": {"c": 7, "l": "products", "s": "商品"},
    "t_categories": {"c": 7, "l": "categories", "s": "カテゴリ"},
    "t_suppliers": {"c": 7, "l": "suppliers", "s": "仕入先"},
    "t_orders": {"c": 7, "l": "orders", "s": "注文"},
    "t_details": {"c": 7, "l": "order_details", "s": "注文明細"},
    "t_customers": {"c": 7, "l": "customers", "s": "顧客"},
}

DETAIL = {
    "catalog": {"k": "画面 (HTML)", "f": "src/web/store/catalog.html",
        "one": "あなたが今“見ている”画面そのもの。商品が並ぶWebページです。",
        "easy": "<span class='term' title='Webページの見た目・構造を書くための言語'>HTML</span>は“ページの設計図”で、文字やボタンの置き場所を決めます。ただしHTMLだけでは中身のデータ（実際の商品名や価格）は持っていません。<b>空っぽの棚を並べた“ガワ”</b>だと思ってください。棚に商品を並べるのは後ろにいるサーバーの仕事です。ボタンを押すと、ページに仕込まれた<span class='term' title='ブラウザの中で動く小さなプログラム。操作に反応する'>JavaScript</span>が動き、サーバーへ「商品データちょうだい」と問い合わせます。",
        "terms": [["HTML", "エイチティーエムエル", "Webページの構造・見た目を書く言語。"], ["JavaScript", "ジャバスクリプト", "ブラウザ内で動くプログラム言語。ボタン操作などに反応する。"], ["ブラウザ", "―", "Chrome等、Webページを表示するソフト。"]]},
    "checkout": {"k": "画面 (HTML)", "f": "src/web/store/checkout.html",
        "one": "カートの中身を確定して“注文”をサーバーへ送る画面。",
        "easy": "ここで「注文する」を押すと、カートに入れた商品リストがまとめてサーバーへ送られます。今までは「データをもらう」方向でしたが、ここは逆に<b>ブラウザからサーバーへデータを“預ける”</b>操作で、これを<span class='term' title='サーバーへデータを送って新規作成・登録するHTTPの操作'>POST</span>と呼びます。",
        "terms": [["POST", "ポスト", "サーバーへデータを送って登録・作成する通信の種類。逆に“もらう”のはGET。"], ["カート", "―", "購入予定の商品を一時的にためる仕組み。ここではブラウザ側で保持。"]]},
    "inventory": {"k": "画面 (HTML)", "f": "src/web/admin/inventory.html",
        "one": "社内担当者が在庫数を増減させる“管理用”画面。",
        "easy": "お客様用ではなく<b>“中の人”用</b>の画面です。誰でも勝手に在庫を変えられては困るので、この操作には<span class='term' title='「あなたは誰か」を確認する仕組み'>認証</span>（ログイン）が必要です。ログイン済みであることを示す“通行証”を通信に添えて送ります。",
        "terms": [["認証", "にんしょう", "「あなたは誰か」を確認する仕組み。ログインがこれ。"], ["admin", "アドミン", "管理者・運営側のこと。お客様(顧客)と区別される。"]]},
    "dashPage": {"k": "画面 (HTML)", "f": "src/web/admin/dashboard.html",
        "one": "商品数・注文数・在庫アラートなどを“まとめて”見る集計画面。",
        "easy": "この画面は開いた瞬間に複数の情報を一気に取りに行きます。<b>1回のクリックでも、裏では「在庫が少ない商品は？」「最近の注文は？」など複数の問い合わせが同時に飛ぶ</b>良い例です。だから本システムは「1クリック＝1まとまり」で束ねて見せます。",
        "terms": [["集計", "しゅうけい", "たくさんのデータを数えたり合計して要約すること。"], ["ダッシュボード", "―", "車のメーターのように重要数値を一望できる画面。"]]},
    "login": {"k": "画面 (HTML)", "f": "src/web/store/login.html",
        "one": "顧客IDを入れてログインする“入口”の画面。",
        "easy": "入力したIDが正しいかをサーバーが確かめ、OKなら<span class='term' title='ログイン成功の証となるランダムな文字列の通行証'>トークン</span>（通行証）を発行します。以降の操作ではこの通行証を見せることで「ログイン済み」と認識されます。",
        "terms": [["トークン", "―", "ログイン成功の証として発行されるランダムな文字列の通行証。毎回の通信に添える。"], ["ID", "アイディー", "利用者を一意に識別する番号や記号。"]]},
    "fetch": {"k": "通信の出発点 (JavaScript)", "f": "src/web/js/api.js",
        "one": "ブラウザからサーバーへ“電話をかける”係。すべての通信の出発点。",
        "easy": "<span class='term' title='ブラウザからサーバーへ通信するJavaScriptの命令'>fetch</span>は「このデータちょうだい」「これ登録して」とサーバーにお願いする命令です。本システムでは<b>ここに細工をして、毎回の通信に“この通信はあなたのどのクリックから始まったか”という荷札（<span class='term' title='一連の処理を追跡するための共通の番号'>trace_id</span>）を付けます</b>。荷札を全工程で持ち回ることで、後から「このクリック→この通信→このSQL」と1本の線でつなげられます。これが<b>トレース（追跡）の肝</b>です。",
        "terms": [["fetch", "フェッチ", "ブラウザからサーバーへ通信するJavaScriptの命令。"], ["HTTP", "エイチティーティーピー", "ブラウザとサーバーが会話するための“共通語”の取り決め。"], ["API", "エーピーアイ", "プログラム同士がやり取りする“窓口”の決まりごと。"], ["trace_id", "トレースアイディー", "一連の処理に付ける追跡用の荷札番号。"]]},
    "cors": {"k": "ミドルウェア（門番）", "f": "src/api/main.py:29 CORSMiddleware",
        "one": "サーバーの“受付・門番”。届いた通信を最初に検査する共通処理。",
        "easy": "<span class='term' title='本来の処理に届く前に必ず通る共通の“関所”'>ミドルウェア</span>は、依頼が担当者に届く前に必ず通る“通路の関所”です。<span class='term' title='違うWebサイト間の通信を許可/制限するブラウザの安全ルール'>CORS</span>は「どのWebサイトからのアクセスならOKか」を判断する安全装置で、<b>悪意あるサイトから勝手にデータを抜かれるのを防ぎます</b>。開発中は全部許可していますが、本番では絞ります。",
        "terms": [["ミドルウェア", "―", "処理の前後に共通で挟み込む“関所”のような部品。"], ["CORS", "コルス", "違うドメイン間の通信を許可・制限するブラウザの安全ルール。"], ["リクエスト", "―", "ブラウザからサーバーへの“お願い”1件。"], ["オリジン", "―", "通信元のWebサイトの住所（ドメイン）。"]]},
    "auth": {"k": "認証（改札）", "f": "src/api/main.py:52 _require_token",
        "one": "通行証（トークン）を確認する“改札”。",
        "easy": "在庫変更や注文など<b>“誰がやったか”が重要な操作の前に立つ改札</b>です。通信に添えられたトークンが、サーバーが覚えているログイン情報（<span class='term' title='ログイン中という状態をサーバー側で記憶していること'>セッション</span>）と一致するか照合します。不一致なら門前払い（<span class='term' title='「認証が必要・失敗」を表すHTTPの番号'>401エラー</span>）。逆に商品一覧のような“誰でも見てよい”<span class='term' title='ログイン無しで誰でも呼べる窓口'>公開API</span>はこの改札を通りません。モックで🛒や🔑が認証ノードを飛ばすのはこのためです。",
        "terms": [["トークン", "―", "通行証となるランダムな文字列。"], ["401", "よんまるいち", "「認証が必要・失敗」を表すHTTPの番号（エラーコード）。"], ["セッション", "―", "ログイン中という状態をサーバーが覚えていること。"], ["公開API", "こうかいエーピーアイ", "ログイン無しで誰でも呼べる窓口。"]]},
    "h_list": {"k": "APIハンドラ（担当プログラム）", "f": "src/api/main.py:125 list_products()",
        "one": "「商品一覧ください」に応える担当プログラム（関数）。",
        "easy": "<span class='term' title='“この住所に頼めばこの仕事をする”という窓口。例 /api/products'>エンドポイント</span> /api/products に来た依頼を受け、データベースへ「商品＋カテゴリ＋仕入先をひとまとめにして」と問い合わせる<span class='term' title='データベースに命令する専用の言語'>SQL</span>を組み立てます。複数の表を“のりづけ”して1つの結果にすることを<span class='term' title='複数の表を共通項目でつなげる操作'>JOIN（結合）</span>と言います。",
        "terms": [["関数", "かんすう", "ひとまとまりの処理に名前を付けたプログラムの単位。"], ["エンドポイント", "―", "API窓口の住所。例 /api/products。"], ["SQL", "エスキューエル", "データベースに命令するための言語。"], ["JOIN", "ジョイン", "複数の表を共通項目でつなげて1つにする操作。"]],
        "sql": "SELECT p.*, c.category_name, s.company_name\nFROM products p\nLEFT JOIN categories c ON p.category_id=c.category_id\nLEFT JOIN suppliers s ON p.supplier_id=s.supplier_id"},
    "h_adj": {"k": "APIハンドラ（担当プログラム）", "f": "src/api/main.py:199 adjust_stock()",
        "one": "在庫数を増やす/減らす担当プログラム（要ログイン）。",
        "easy": "まず現在の在庫を<span class='term' title='データを読み出すSQL命令'>SELECT</span>で読み、増減後の値を計算し、<b>マイナスにならないか確認(<span class='term' title='入力や結果が正しいか検査すること'>バリデーション</span>)してから</b><span class='term' title='既存データを書き換えるSQL命令'>UPDATE</span>で書き換えます。“読んでから書く”の2段構えです。",
        "terms": [["SELECT", "セレクト", "データを“読み出す”SQL命令。"], ["UPDATE", "アップデート", "既存データを“書き換える”SQL命令。"], ["バリデーション", "―", "入力や結果が妥当か検査すること。ここでは在庫が負にならないか。"]],
        "sql": "SELECT units_in_stock FROM products WHERE product_id=%s;\nUPDATE products SET units_in_stock=%s WHERE product_id=%s"},
    "h_order": {"k": "APIハンドラ（担当プログラム）", "f": "src/api/main.py:290 create_order()",
        "one": "注文を確定し、在庫を減らす担当プログラム（システムで一番“重い”処理）。",
        "easy": "1回の注文で複数のことが連鎖します：注文ヘッダを作り(<span class='term' title='新しいデータを追加するSQL命令'>INSERT</span> orders)、商品ごとに<span class='term' title='注文内の商品1行ごとの内訳'>明細</span>を作り(INSERT order_details)、その分だけ在庫を減らす(UPDATE products)。本来はこれらが<b>全部成功するか・全部取り消すか</b>をまとめる<span class='term' title='一連の書き込みを“全部成功 or 全部なかったこと”にする仕組み'>トランザクション</span>が重要になります。",
        "terms": [["INSERT", "インサート", "新しいデータを“追加する”SQL命令。"], ["トランザクション", "―", "一連の書き込みを“全部成功 or 全部なかったこと”にまとめる仕組み。"], ["明細", "めいさい", "注文の中の商品1行ごとの内訳（数量・単価）。"]],
        "sql": "INSERT INTO orders (...) VALUES (...);\nINSERT INTO order_details (...) VALUES (...);  -- 明細数ぶん繰り返す\nUPDATE products SET units_in_stock = units_in_stock - %s ..."},
    "h_dash": {"k": "APIハンドラ（担当プログラム）", "f": "src/api/main.py:358 dashboard()",
        "one": "ダッシュボード1画面分の数字をまとめて作る担当プログラム。",
        "easy": "商品数・注文数・在庫アラート・最近の注文…を、<b>複数のSQLを連続実行</b>して1つのまとまり(<span class='term' title='プログラム間でデータを受け渡す軽量な書式'>JSON</span>)にして返します。1クリックが多数の問い合わせを生む典型で、「1操作＝1トレース」で束ねる意味がよく分かる箇所です。",
        "terms": [["JSON", "ジェイソン", "プログラム間でデータを受け渡す軽量な書式。{名前:値}の形。"], ["COUNT", "カウント", "件数を数えるSQLの関数。"], ["集約", "しゅうやく", "合計・件数などにまとめる計算。"]],
        "sql": "SELECT COUNT(*) FROM products WHERE discontinued=0;\nSELECT COUNT(*) FROM orders;\nSELECT ... FROM orders JOIN customers JOIN order_details ...;\nSELECT ... FROM products WHERE units_in_stock <= reorder_level"},
    "h_slogin": {"k": "APIハンドラ（担当プログラム）", "f": "src/api/main.py:96 store_login()",
        "one": "ログインの可否を判定し、通行証を“発行”する担当プログラム。",
        "easy": "送られた顧客IDが customers 表にあるか<span class='term' title='入力が登録内容と一致するか突き合わせること'>照合</span>し、合っていればトークンを作って返します。<b>“改札(認証)”が通行証を『確認』する側なのに対し、ここは通行証を『発行』する側</b>。役割が逆なので、認証ノードを通らずに認証情報を作ります。",
        "terms": [["照合", "しょうごう", "入力が登録内容と一致するか突き合わせること。"], ["トークン", "―", "発行される通行証文字列。"], ["認証情報", "にんしょうじょうほう", "ログインの証となるデータ。"]],
        "sql": "SELECT customer_id, company_name, contact_name, ...\nFROM customers WHERE customer_id = %s"},
    "db": {"k": "DBアクセス層（橋渡し）", "f": "src/api/db.py",
        "one": "サーバーとデータベースの“通訳・橋渡し”をする共通部品。",
        "easy": "各担当プログラムはSQLの文字列を作るだけ。それを実際に<span class='term' title='データを整理して保管・検索する専用ソフト'>データベース</span>へ送り結果を受け取る泥仕事を、この db.py が肩代わりします。<b>fetch_all=複数行取得／fetch_one=1行取得／execute=書き込み実行</b>、と役割が分かれています。",
        "terms": [["データベース", "でーたべーす", "データを整理して保管・検索する専用ソフト。略してDB。"], ["モジュール", "―", "機能ごとにまとめたプログラムの部品。"], ["コネクション", "―", "アプリとDBの間に張る通信の“線”。"]]},
    "pg": {"k": "ドライバ（翻訳機）", "f": "psycopg2",
        "one": "PythonからPostgreSQLへ実際に話しかける“専用翻訳機”。",
        "easy": "ブラウザがDBと直接話せないのは、DBの言葉(<span class='term' title='通信の手順・約束事'>プロトコル</span>)を喋れないからです。psycopg2はPythonにその言葉を教える<span class='term' title='特定のソフト/機器と通信するための専用変換プログラム'>ドライバ</span>。<span class='term' title='1台のPC内で通信窓口を区別する番号'>ポート</span>5432の<span class='term' title='高機能な無料のデータベースソフト'>PostgreSQL</span>に接続し、SQLを送って結果を持ち帰ります。",
        "terms": [["ドライバ", "―", "特定のソフト/機器と通信するための専用変換プログラム。"], ["PostgreSQL", "ポストグレスキューエル", "高機能な無料のデータベースソフト。"], ["プロトコル", "―", "通信の手順・約束事。"], ["ポート", "―", "5432など、1台のPC内で通信窓口を区別する番号。"]]},
    "t_products": {"k": "テーブル（表）", "f": "northwind.products",
        "one": "商品マスタ。名前・価格・在庫数などの“商品台帳”。",
        "easy": "<span class='term' title='行と列でデータを格納するDBの基本単位'>テーブル</span>は表のこと。<span class='term' title='滅多に増減しない基準データ。商品・顧客など'>マスタ</span>とは“台帳”データで、注文のたびに在庫数の<span class='term' title='表の縦の項目'>カラム（列）</span>が書き換わります。",
        "terms": [["テーブル", "―", "行と列でデータを格納するDBの基本単位＝表。"], ["マスタ", "―", "基準となる台帳データ。商品・顧客など滅多に増減しない。"], ["カラム", "―", "表の縦＝1項目（列）。"]]},
    "t_categories": {"k": "テーブル（表）", "f": "northwind.categories",
        "one": "商品の分類（飲料・菓子など）の台帳。",
        "easy": "商品を“どのジャンルか”で束ねる小さなマスタです。products 表が category_id という番号でこの表を指し示し、JOINで分類名を引いてきます。",
        "terms": [["マスタ", "―", "基準となる台帳データ。"], ["JOIN", "ジョイン", "複数の表を共通項目でつなげる操作。"]]},
    "t_suppliers": {"k": "テーブル（表）", "f": "northwind.suppliers",
        "one": "商品の仕入先企業の台帳。",
        "easy": "「この商品はどの会社から仕入れているか」を管理するマスタ。products が supplier_id でこの表とつながります。",
        "terms": [["マスタ", "―", "基準となる台帳データ。"]]},
    "t_orders": {"k": "テーブル（表）", "f": "northwind.orders",
        "one": "注文1件ごとのヘッダ情報（誰が・いつ・どこへ）。",
        "easy": "日々増えていく<span class='term' title='取引のたびに増える記録データ'>トランザクションデータ</span>です。各行は order_id という<span class='term' title='各行をひとつに識別する列'>主キー</span>で区別されます。",
        "terms": [["トランザクションデータ", "―", "取引のたびに増えていく記録（注文・明細など）。マスタの対義。"], ["主キー", "しゅキー", "各行を一意に識別する列。orders なら order_id。"]]},
    "t_details": {"k": "テーブル（表）", "f": "northwind.order_details",
        "one": "注文の中の商品1行ごとの明細（数量・単価・割引）。",
        "easy": "1つの注文に複数商品があるので、ヘッダ(orders)と分けて“1商品＝1行”で持ちます。order_id という<span class='term' title='他の表の行を指し示す列'>外部キー</span>で orders とつながります。",
        "terms": [["外部キー", "がいぶキー", "他の表の行を指し示す列。order_id で orders とつながる。"], ["明細", "めいさい", "注文内の商品1行ごとの内訳。"]]},
    "t_customers": {"k": "テーブル（表）", "f": "northwind.customers",
        "one": "顧客企業の台帳。ECではこれがログインアカウントを兼ねる。",
        "easy": "91社の顧客マスタ。このシステムでは<b>顧客ID＝ログインID</b>として使われ、store_login がここを照合します。",
        "terms": [["マスタ", "―", "基準となる台帳データ。"]]},
}

ACTIONS = [
    {"id": "a1", "spine": ["catalog", "fetch", "cors", "h_list", "db", "pg"],
     "tables": ["t_products", "t_categories", "t_suppliers"]},
    {"id": "a4", "spine": ["dashPage", "fetch", "cors", "auth", "h_dash", "db", "pg"],
     "tables": ["t_products", "t_orders", "t_details", "t_customers", "t_categories"]},
    {"id": "a5", "spine": ["login", "fetch", "cors", "h_slogin", "db", "pg"],
     "tables": ["t_customers"]},
    {"id": "a2", "spine": ["inventory", "fetch", "cors", "auth", "h_adj", "db", "pg"],
     "tables": ["t_products"]},
    {"id": "a3", "spine": ["checkout", "fetch", "cors", "auth", "h_order", "db", "pg"],
     "tables": ["t_orders", "t_details", "t_products"]},
]


def build_edges():
    edges = []
    seen = set()
    for a in ACTIONS:
        spine = a["spine"]
        pairs = []
        for i in range(len(spine) - 1):
            pairs.append((spine[i], spine[i + 1]))
        last = spine[-1]
        for t in a["tables"]:
            pairs.append((last, t))
        for u, v in pairs:
            key = u + ">" + v
            if key not in seen:
                seen.add(key)
                edges.append([u, v])
    return edges


def build_nodes():
    nodes = {}
    missing = []
    for nid, n in N.items():
        d = DETAIL.get(nid)
        if d is None:
            missing.append(nid)
            detail = {"k": "", "f": "", "one": "", "easy": "", "terms": []}
        else:
            detail = {"k": d["k"], "f": d["f"], "one": d["one"],
                      "easy": d["easy"], "terms": d["terms"]}
            if "sql" in d:
                detail["sql"] = d["sql"]
        nodes[nid] = {"col": n["c"], "label": n["l"], "sub": n["s"], "detail": detail}
    return nodes, missing


def main():
    nodes, missing = build_nodes()
    out = {"columns": COLS, "nodes": nodes, "edges": build_edges()}
    target = pathlib.Path("src/api/trace_map.json")
    target.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    print("cols", len(out["columns"]), "nodes", len(out["nodes"]),
          "edges", len(out["edges"]))
    if missing:
        print("MISSING DETAIL:", missing)
    else:
        print("all nodes have DETAIL")


if __name__ == "__main__":
    main()
