"""商品一覧画面"""

import streamlit as st
from common.db import fetch_all


def render():
    # --- カテゴリフィルタ ---
    categories = fetch_all("SELECT category_id, category_name FROM categories ORDER BY category_name")
    cat_names = ["全て"] + [c["category_name"] for c in categories]
    cat_map = {c["category_name"]: c["category_id"] for c in categories}

    col_filter, col_search = st.columns([1, 2])
    with col_filter:
        selected_cat = st.selectbox("カテゴリ", cat_names, key="catalog_cat")
    with col_search:
        search = st.text_input("検索", placeholder="商品名で検索...", key="catalog_search")

    # --- クエリ ---
    query = (
        "SELECT p.product_id, p.product_name, p.unit_price, p.units_in_stock, "
        "  p.quantity_per_unit, c.category_name, s.company_name as supplier_name "
        "FROM products p "
        "LEFT JOIN categories c ON p.category_id = c.category_id "
        "LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id "
        "WHERE p.discontinued = 0"
    )
    params = []
    if selected_cat != "全て":
        query += " AND c.category_name = %s"
        params.append(selected_cat)
    if search:
        query += " AND p.product_name ILIKE %s"
        params.append(f"%{search}%")
    query += " ORDER BY c.category_name, p.product_name"

    products = fetch_all(query, params or None)

    if not products:
        st.info("該当する商品がありません")
        return

    # --- カード表示 (3列) ---
    cols = st.columns(3)
    for i, p in enumerate(products):
        with cols[i % 3]:
            with st.container(border=True):
                st.subheader(p["product_name"])
                st.caption(f"{p['category_name']} | {p['supplier_name']}")
                st.write(f"**${p['unit_price']:.2f}**")
                st.write(f"在庫: {p['units_in_stock']} | {p['quantity_per_unit'] or ''}")

                if p["units_in_stock"] > 0:
                    qty = st.number_input(
                        "数量", min_value=1, max_value=p["units_in_stock"],
                        value=1, key=f"qty_{p['product_id']}"
                    )
                    if st.button("カートに追加", key=f"add_{p['product_id']}"):
                        _add_to_cart(p, qty)
                        st.success(f"{p['product_name']} x{qty} をカートに追加しました")
                        st.rerun()
                else:
                    st.error("在庫切れ")


def _add_to_cart(product, quantity):
    """セッションのカートに商品を追加する。"""
    cart = st.session_state.setdefault("cart", [])
    # 既存の商品があれば数量を加算
    for item in cart:
        if item["product_id"] == product["product_id"]:
            item["quantity"] += quantity
            return
    cart.append({
        "product_id": product["product_id"],
        "product_name": product["product_name"],
        "unit_price": product["unit_price"],
        "quantity": quantity,
        "max_stock": product["units_in_stock"],
    })
