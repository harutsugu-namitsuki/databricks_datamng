# src — アプリケーション層（ECストア / 業務管理）

Northwind 商社の **2つの Web アプリ**と、そのバックエンド API。

| アプリ | 役割 | 利用者 | 入口 URL |
|---|---|---|---|
| **EC ストア**（購買） | 商品閲覧・カート・注文 | 顧客（B2Bバイヤー） | `/static/store/login.html` |
| **業務管理**（admin） | 商品・在庫・従業員の管理 | 社内担当者 | `/static/admin/login.html` |

どちらも 1 つの FastAPI サーバー（[api/main.py](api/main.py)）が配信し、RDS PostgreSQL を読み書きします。

```
ブラウザ (HTML/CSS/JS)  ──fetch──▶  FastAPI (api/)  ──psycopg2──▶  RDS PostgreSQL
   web/store, web/admin                                              (Northwind)
```

---

## 起動（3 ステップ）

**Windows (cmd) — `src/` ディレクトリで実行:**

```bat
:: 1. 依存インストール（requirements.txt は infrastructure/ にある）
pip install -r ..\infrastructure\requirements.txt

:: 2. DB 接続情報を .env に記入（リポジトリ直下に置く。自動で読み込まれる）
::    ローカル PostgreSQL を使うなら既定値のままで可
copy ..\.env.example ..\.env
::    ↑のあと ..\.env を開いて RDS_HOST 等を書き換える

:: 3. サーバー起動（既に src/ にいるので cd は不要）
uvicorn api.main:app --reload --port 8000
```

**macOS / Linux (bash) — `src/` ディレクトリで実行:**

```bash
pip install -r ../infrastructure/requirements.txt
cp ../.env.example ../.env      # 中の RDS_HOST 等を編集
uvicorn api.main:app --reload --port 8000
```

> ⚠️ **必ず `src/` ディレクトリ内で起動**してください（`api.main:app` のパス解決のため）。
> 既に `src/` にいるなら `cd src` は不要です（二重で潜るとパスが見つからずエラーになります）。

### DB 接続情報について

[api/db.py](api/db.py) が起動時に **リポジトリ直下の `.env` を自動で読み込みます**
（`load_dotenv()` 実装済み）。`.env.example` をコピーして値を埋めるだけでOK。
`.env` が無い／値が空の場合は下表の既定値（ローカル PostgreSQL 向け）に落ちます。

| 環境変数 | 既定値 | 用途 |
|---|---|---|
| `RDS_HOST` | `localhost` | DB ホスト（RDS ならそのエンドポイント） |
| `RDS_PORT` | `5432` | ポート |
| `RDS_DBNAME` | `northwind` | DB 名 |
| `RDS_USER` | `postgres` | ユーザー |
| `RDS_PASSWORD` | `postgres` | パスワード |

> RDS は private subnet にあるため、ローカルから接続するには
> **RDS へ到達できるネットワーク経路**（VPN / 踏み台 / 同一 VPC 等）も別途必要です。

## 入口はこの 2 つだけ

| | URL |
|---|---|
| 🛒 EC ストア | http://localhost:8000/static/store/login.html |
| 🛠 業務管理 | http://localhost:8000/static/admin/login.html |
| 📖 API ドキュメント (Swagger) | http://localhost:8000/docs |

他の HTML（catalog/cart/checkout/dashboard…）は**ログイン後に画面遷移で開く**ので、直接押す必要はありません。

---

## なぜサーバーを立ち上げる必要があるのか（HTML を直接開いてはダメな理由）

> 「`uvicorn` を立てるのは面倒、HTML をダブルクリックで開けばいいのでは？」と思ったらここを読む。
> ちなみに `uvicorn` で立てるサーバーは **`localhost:8000`＝あなたの PC 上のローカルプロセス**です（クラウドに上げるわけではない）。

理由は2つあって、**RDS 通信が本質**ですが、正確にはこうです：

### ① ブラウザは DB（PostgreSQL）と直接喋れない

HTML の画面は「ガワ」で、中身のデータは持っていません。画面の JS は `fetch('/api/products')` のように
**HTTP で問い合わせている**だけです。

```
ブラウザ(HTML/JS) ──HTTP──▶ FastAPI(Python) ──psycopg2──▶ RDS PostgreSQL
   画面・ガワ                 翻訳・橋渡し役            データの実体
```

ブラウザには PostgreSQL ドライバが無く、セキュリティ上も DB に直接つなげません。**DB と喋れるのは
Python 側（psycopg2）だけ**。だから「ブラウザ ⇄ DB」の間に**通訳としてのサーバーが必須**になります。
これが立ち上げる理由です。

### ② file:// で開くとパスと CORS が壊れる

画面は `/api/...` や `/static/...` という相対パスでサーバーを前提に動きます。HTML ファイルを
ダブルクリック（file://）で開くと、これらの参照先が無くて即エラーになります。

## ログイン情報（開発用）

**業務管理:**

| ユーザー | パスワード | 権限 |
|---|---|---|
| `admin` | `admin123` | 管理者（個人情報を閲覧可） |
| `staff` | `staff123` | スタッフ（個人情報はマスキング） |

**EC ストア:** 顧客IDで認証（パスワード＝顧客ID）。例: `ALFKI` / `ALFKI`、`ANATR` / `ANATR`

---

## フォルダ構成

```
src/
├── api/                ← FastAPI バックエンド
│   ├── main.py         ← 全 API エンドポイント
│   └── db.py           ← RDS 接続（psycopg2）
└── web/                ← フロントエンド（静的配信）
    ├── css/style.css   ← 共通スタイル
    ├── js/api.js       ← fetch ユーティリティ / カート
    ├── store/          ← EC ストア画面（login → catalog → cart → checkout → history）
    └── admin/          ← 業務管理画面（login → dashboard / products / inventory / employees）
```

---

## 補足：Streamlit 版は退避済み

以前は同じ機能の **Streamlit 版**が `src/store`・`src/admin`・`src/common` に並存していて混乱の元でした。現在は
[`docs/archive/旧Streamlitアプリ/`](../docs/archive/旧Streamlitアプリ/) に退避しています。**現役の実装はこの FastAPI 版のみ**です。
