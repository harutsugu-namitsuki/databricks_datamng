"""Northwind FastAPI バックエンド

ブラウザ (HTML/JS) からの API リクエストを受け取り、
RDS PostgreSQL を操作して JSON で返す。
"""

import secrets
import datetime
from pathlib import Path
from typing import Optional

import psycopg2
import psycopg2.extras
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from api.db import fetch_all, fetch_one, execute

# ---------------------------------------------------------------------------
# アプリ初期化
# ---------------------------------------------------------------------------

app = FastAPI(title="Northwind API")

# CORS: 開発中はすべて許可 (本番では Origin を絞る)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静的ファイル (HTML/CSS/JS) を /static で配信
WEB_DIR = Path(__file__).resolve().parent.parent / "web"
app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")

# ---------------------------------------------------------------------------
# 簡易認証 (トークン → ユーザー情報 のメモリキャッシュ)
# ---------------------------------------------------------------------------

_sessions: dict[str, dict] = {}

ADMIN_USERS = {
    "admin": {"password": "admin123", "name": "管理者", "role": "admin"},
    "staff": {"password": "staff123", "name": "スタッフ", "role": "staff"},
}


def _require_token(authorization: str = Header(...)) -> dict:
    """Authorization: Bearer <token> からセッション情報を取り出す。"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="認証が必要です")
    token = authorization[7:]
    session = _sessions.get(token)
    if not session:
        raise HTTPException(status_code=401, detail="トークンが無効または期限切れです")
    return session


# ---------------------------------------------------------------------------
# ルート → 静的 HTML へリダイレクト
# ---------------------------------------------------------------------------

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/static/store/catalog.html")


# ---------------------------------------------------------------------------
# 認証エンドポイント
# ---------------------------------------------------------------------------

class AdminLoginRequest(BaseModel):
    username: str
    password: str

class StoreLoginRequest(BaseModel):
    customer_id: str
    password: str


@app.post("/api/auth/admin")
def admin_login(req: AdminLoginRequest):
    user = ADMIN_USERS.get(req.username)
    if not user or user["password"] != req.password:
        raise HTTPException(status_code=401, detail="ユーザー名またはパスワードが正しくありません")
    token = secrets.token_urlsafe(32)
    _sessions[token] = {"type": "admin", "username": req.username, **user}
    return {"token": token, "name": user["name"], "role": user["role"]}


@app.post("/api/auth/store")
def store_login(req: StoreLoginRequest):
    cid = req.customer_id.upper()
    customer = fetch_one(
        "SELECT customer_id, company_name, contact_name, address, city, region, "
        "postal_code, country FROM customers WHERE customer_id = %s",
        (cid,),
    )
    if not customer or req.password != cid:
        raise HTTPException(status_code=401, detail="顧客IDまたはパスワードが正しくありません")
    token = secrets.token_urlsafe(32)
    _sessions[token] = {"type": "store", "customer": dict(customer)}
    return {"token": token, "customer": dict(customer)}


# ---------------------------------------------------------------------------
# 商品 API
# ---------------------------------------------------------------------------

class ProductUpdate(BaseModel):
    product_name: str
    category_id: int
    supplier_id: int
    unit_price: float
    quantity_per_unit: Optional[str] = None
    discontinued: int = 0


@app.get("/api/products")
def list_products(category: Optional[str] = None, search: Optional[str] = None):
    query = (
        "SELECT p.product_id, p.product_name, p.unit_price, p.units_in_stock, "
        "  p.units_on_order, p.reorder_level, p.quantity_per_unit, p.discontinued, "
        "  p.category_id, p.supplier_id, "
        "  c.category_name, s.company_name as supplier_name "
        "FROM products p "
        "LEFT JOIN categories c ON p.category_id = c.category_id "
        "LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id WHERE 1=1"
    )
    params = []
    if category:
        query += " AND c.category_name = %s"
        params.append(category)
    if search:
        query += " AND p.product_name ILIKE %s"
        params.append(f"%{search}%")
    query += " ORDER BY c.category_name, p.product_name"
    return fetch_all(query, params or None)


@app.post("/api/products")
def create_product(body: ProductUpdate, session=Depends(_require_token)):
    execute(
        "INSERT INTO products (product_name, category_id, supplier_id, unit_price, "
        "quantity_per_unit, discontinued, units_in_stock, units_on_order, reorder_level) "
        "VALUES (%(product_name)s, %(category_id)s, %(supplier_id)s, %(unit_price)s, "
        "%(quantity_per_unit)s, %(discontinued)s, 0, 0, 0)",
        body.model_dump(),
    )
    return {"ok": True}


@app.put("/api/products/{product_id}")
def update_product(product_id: int, body: ProductUpdate, session=Depends(_require_token)):
    execute(
        "UPDATE products SET product_name=%(product_name)s, category_id=%(category_id)s, "
        "supplier_id=%(supplier_id)s, unit_price=%(unit_price)s, "
        "quantity_per_unit=%(quantity_per_unit)s, discontinued=%(discontinued)s "
        "WHERE product_id=%(product_id)s",
        {**body.model_dump(), "product_id": product_id},
    )
    return {"ok": True}


# ---------------------------------------------------------------------------
# カテゴリ / 仕入先 / 配送業者 API
# ---------------------------------------------------------------------------

@app.get("/api/categories")
def list_categories():
    return fetch_all("SELECT category_id, category_name FROM categories ORDER BY category_name")


@app.get("/api/suppliers")
def list_suppliers():
    return fetch_all("SELECT supplier_id, company_name FROM suppliers ORDER BY company_name")


@app.get("/api/shippers")
def list_shippers():
    return fetch_all("SELECT shipper_id, company_name FROM shippers ORDER BY shipper_id")


# ---------------------------------------------------------------------------
# 在庫調整 API
# ---------------------------------------------------------------------------

class StockAdjust(BaseModel):
    product_id: int
    adjustment: int


@app.post("/api/inventory/adjust")
def adjust_stock(body: StockAdjust, session=Depends(_require_token)):
    product = fetch_one(
        "SELECT units_in_stock FROM products WHERE product_id = %s", (body.product_id,)
    )
    if not product:
        raise HTTPException(status_code=404, detail="商品が見つかりません")
    new_stock = product["units_in_stock"] + body.adjustment
    if new_stock < 0:
        raise HTTPException(status_code=400, detail="在庫数が負の値になります")
    execute(
        "UPDATE products SET units_in_stock = %s WHERE product_id = %s",
        (new_stock, body.product_id),
    )
    return {"ok": True, "units_in_stock": new_stock}


# ---------------------------------------------------------------------------
# 従業員 API
# ---------------------------------------------------------------------------

class EmployeeUpdate(BaseModel):
    first_name: str
    last_name: str
    title: Optional[str] = None
    title_of_courtesy: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None


@app.get("/api/employees")
def list_employees(session=Depends(_require_token)):
    return fetch_all(
        "SELECT employee_id, last_name, first_name, title, title_of_courtesy, "
        "hire_date, city, country FROM employees ORDER BY employee_id"
    )


@app.get("/api/employees/{employee_id}")
def get_employee(employee_id: int, session=Depends(_require_token)):
    emp = fetch_one(
        "SELECT employee_id, last_name, first_name, title, title_of_courtesy, "
        "birth_date, hire_date, address, city, region, postal_code, country, "
        "home_phone, extension, notes FROM employees WHERE employee_id = %s",
        (employee_id,),
    )
    if not emp:
        raise HTTPException(status_code=404, detail="従業員が見つかりません")
    role = session.get("role", "staff")
    result = dict(emp)
    if role != "admin":
        result["birth_date"] = "****-**-**"
        result["home_phone"] = "****"
    return result


@app.put("/api/employees/{employee_id}")
def update_employee(employee_id: int, body: EmployeeUpdate, session=Depends(_require_token)):
    execute(
        "UPDATE employees SET first_name=%s, last_name=%s, title=%s, "
        "title_of_courtesy=%s, address=%s, city=%s, country=%s, postal_code=%s "
        "WHERE employee_id=%s",
        (body.first_name, body.last_name, body.title, body.title_of_courtesy,
         body.address, body.city, body.country, body.postal_code, employee_id),
    )
    return {"ok": True}


# ---------------------------------------------------------------------------
# 注文 API
# ---------------------------------------------------------------------------

class OrderItem(BaseModel):
    product_id: int
    unit_price: float
    quantity: int


class OrderCreate(BaseModel):
    ship_name: str
    ship_address: str
    ship_city: str
    ship_region: Optional[str] = None
    ship_postal_code: Optional[str] = None
    ship_country: str
    ship_via: int
    items: list[OrderItem]


@app.post("/api/orders")
def create_order(body: OrderCreate, session=Depends(_require_token)):
    if session.get("type") != "store":
        raise HTTPException(status_code=403, detail="顧客ログインが必要です")
    customer_id = session["customer"]["customer_id"]

    max_row = fetch_one("SELECT COALESCE(MAX(order_id), 10000) + 1 AS next_id FROM orders")
    next_id = max_row["next_id"]

    execute(
        "INSERT INTO orders (order_id, customer_id, employee_id, order_date, required_date, "
        "ship_via, freight, ship_name, ship_address, ship_city, ship_region, "
        "ship_postal_code, ship_country) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (next_id, customer_id, 1,
         datetime.date.today(),
         datetime.date.today() + datetime.timedelta(days=14),
         body.ship_via, 0.0,
         body.ship_name, body.ship_address, body.ship_city, body.ship_region,
         body.ship_postal_code, body.ship_country),
    )
    for item in body.items:
        execute(
            "INSERT INTO order_details (order_id, product_id, unit_price, quantity, discount) "
            "VALUES (%s, %s, %s, %s, %s)",
            (next_id, item.product_id, item.unit_price, item.quantity, 0.0),
        )
        execute(
            "UPDATE products SET units_in_stock = units_in_stock - %s WHERE product_id = %s",
            (item.quantity, item.product_id),
        )
    return {"ok": True, "order_id": next_id}


@app.get("/api/orders")
def list_orders(session=Depends(_require_token)):
    if session.get("type") != "store":
        raise HTTPException(status_code=403)
    customer_id = session["customer"]["customer_id"]
    return fetch_all(
        "SELECT o.order_id, o.order_date, o.shipped_date, o.ship_name, "
        "  sh.company_name as shipper_name, "
        "  COALESCE(SUM(od.unit_price * od.quantity * (1 - od.discount)), 0) as total "
        "FROM orders o "
        "LEFT JOIN order_details od ON o.order_id = od.order_id "
        "LEFT JOIN shippers sh ON o.ship_via = sh.shipper_id "
        "WHERE o.customer_id = %s "
        "GROUP BY o.order_id, o.order_date, o.shipped_date, o.ship_name, sh.company_name "
        "ORDER BY o.order_id DESC",
        (customer_id,),
    )


@app.get("/api/orders/{order_id}/details")
def order_details(order_id: int, session=Depends(_require_token)):
    return fetch_all(
        "SELECT p.product_name, od.unit_price, od.quantity, od.discount, "
        "  (od.unit_price * od.quantity * (1 - od.discount)) as subtotal "
        "FROM order_details od "
        "LEFT JOIN products p ON od.product_id = p.product_id "
        "WHERE od.order_id = %s",
        (order_id,),
    )


# ---------------------------------------------------------------------------
# ダッシュボード API
# ---------------------------------------------------------------------------

@app.get("/api/dashboard")
def dashboard(session=Depends(_require_token)):
    return {
        "product_count": fetch_one("SELECT COUNT(*) as cnt FROM products WHERE discontinued=0")["cnt"],
        "order_count": fetch_one("SELECT COUNT(*) as cnt FROM orders")["cnt"],
        "alert_count": fetch_one(
            "SELECT COUNT(*) as cnt FROM products WHERE discontinued=0 AND units_in_stock <= reorder_level"
        )["cnt"],
        "recent_orders": fetch_all(
            "SELECT o.order_id, c.company_name, o.order_date, "
            "  COALESCE(SUM(od.unit_price * od.quantity * (1-od.discount)), 0) as total "
            "FROM orders o LEFT JOIN customers c ON o.customer_id=c.customer_id "
            "LEFT JOIN order_details od ON o.order_id=od.order_id "
            "GROUP BY o.order_id, c.company_name, o.order_date "
            "ORDER BY o.order_id DESC LIMIT 10"
        ),
        "alerts": fetch_all(
            "SELECT p.product_id, p.product_name, p.units_in_stock, p.reorder_level, "
            "  c.category_name FROM products p "
            "LEFT JOIN categories c ON p.category_id=c.category_id "
            "WHERE p.discontinued=0 AND p.units_in_stock <= p.reorder_level "
            "ORDER BY p.units_in_stock"
        ),
    }
