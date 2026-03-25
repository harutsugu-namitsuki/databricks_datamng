# Northwind アプリケーション

Northwind DB を操作する Web アプリ。2種類の実装がある。

---

## 🌐 HTML/CSS/JS + FastAPI 版（推奨）

### アーキテクチャ

```
ブラウザ (HTML + CSS + JavaScript)
        ↕ HTTP (fetch API)
FastAPI バックエンド (Python)
        ↕ psycopg2
RDS PostgreSQL (Northwind DB)
```

### 起動方法

```bash
# 依存インストール
pip install -r requirements.txt

# .env を作成
cp .env.example .env
# RDS 接続情報を書き込む

# FastAPI サーバーを起動 (ポート 8000)
cd src
uvicorn api.main:app --reload --port 8000
```

### 開き方

ブラウザで以下のURLを開く:

| アプリ | URL |
|--------|-----|
| 購買アプリ (ストア) | http://localhost:8000/static/store/login.html |
| 業務管理アプリ | http://localhost:8000/static/admin/login.html |
| API ドキュメント | http://localhost:8000/docs |

### ログイン情報

**業務管理アプリ:**
| ユーザー | パスワード | 権限 |
|----------|-----------|------|
| admin | admin123 | 管理者 (個人情報閲覧可) |
| staff | staff123 | スタッフ (個人情報マスキング) |

**購買アプリ (ストア):**
- 顧客ID で認証。パスワードは顧客IDと同じ
- 例: `ALFKI` / `ALFKI`、`ANATR` / `ANATR`

---

## 🐍 Streamlit 版（旧実装 / 参考）

Python だけで完結するシンプルな実装。

```bash
cd src && streamlit run admin/app.py --server.port 8501   # 業務管理
cd src && streamlit run store/app.py --server.port 8502   # 購買
```

---

## ファイル構成

```
APP開発/
├── requirements.txt
├── .env.example
├── docs/
│   └── design/
│       ├── システム設計.md
│       └── 画面設計.md
└── src/
    ├── api/              ← FastAPI バックエンド
    │   ├── main.py       ← API エンドポイント全部
    │   └── db.py         ← DB 接続
    ├── web/              ← HTML/CSS/JS フロントエンド
    │   ├── css/style.css ← 共通スタイル
    │   ├── js/api.js     ← fetch ユーティリティ / カート
    │   ├── admin/        ← 業務管理アプリ画面
    │   │   ├── login.html
    │   │   ├── dashboard.html
    │   │   ├── products.html
    │   │   ├── inventory.html
    │   │   └── employees.html
    │   └── store/        ← 購買アプリ画面
    │       ├── login.html
    │       ├── catalog.html
    │       ├── cart.html
    │       ├── checkout.html
    │       └── history.html
    ├── admin/            ← Streamlit 業務管理アプリ
    └── store/            ← Streamlit 購買アプリ
```
