"""商品管理画面"""

import streamlit as st
from common.db import fetch_all, execute


def render():
    st.header("商品管理")

    # --- カテゴリ・仕入先の選択肢をロード ---
    categories = fetch_all("SELECT category_id, category_name FROM categories ORDER BY category_name")
    suppliers = fetch_all("SELECT supplier_id, company_name FROM suppliers ORDER BY company_name")

    cat_options = {c["category_name"]: c["category_id"] for c in categories}
    sup_options = {s["company_name"]: s["supplier_id"] for s in suppliers}

    # --- 新規登録フォーム ---
    with st.expander("＋ 新規商品登録", expanded=False):
        _product_form(
            key="new",
            categories=cat_options,
            suppliers=sup_options,
            defaults={},
            on_submit=_insert_product,
        )

    st.divider()

    # --- フィルタ ---
    col1, col2 = st.columns([1, 2])
    with col1:
        filter_cat = st.selectbox("カテゴリ", ["全て"] + list(cat_options.keys()))
    with col2:
        search = st.text_input("検索", placeholder="商品名で検索...")

    # --- 商品一覧 ---
    query = (
        "SELECT p.product_id, p.product_name, c.category_name, s.company_name as supplier_name, "
        "  p.unit_price, p.units_in_stock, p.units_on_order, p.reorder_level, "
        "  p.quantity_per_unit, p.discontinued, p.category_id, p.supplier_id "
        "FROM products p "
        "LEFT JOIN categories c ON p.category_id = c.category_id "
        "LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id "
        "WHERE 1=1"
    )
    params = []

    if filter_cat != "全て":
        query += " AND c.category_name = %s"
        params.append(filter_cat)
    if search:
        query += " AND p.product_name ILIKE %s"
        params.append(f"%{search}%")

    query += " ORDER BY p.product_id"
    products = fetch_all(query, params or None)

    if not products:
        st.info("該当する商品がありません")
        return

    # テーブル表示
    st.dataframe(
        [{
            "ID": p["product_id"],
            "商品名": p["product_name"],
            "カテゴリ": p["category_name"],
            "仕入先": p["supplier_name"],
            "単価": p["unit_price"],
            "在庫": p["units_in_stock"],
            "廃止": "Yes" if p["discontinued"] else "",
        } for p in products],
        column_config={
            "単価": st.column_config.NumberColumn(format="$%.2f"),
        },
        use_container_width=True,
        hide_index=True,
    )

    # --- 編集フォーム ---
    st.subheader("商品編集")
    product_names = {f"{p['product_id']}: {p['product_name']}": p for p in products}
    selected = st.selectbox("編集する商品を選択", list(product_names.keys()))

    if selected:
        p = product_names[selected]
        with st.expander(f"#{p['product_id']} {p['product_name']} を編集", expanded=True):
            _product_form(
                key=f"edit_{p['product_id']}",
                categories=cat_options,
                suppliers=sup_options,
                defaults=p,
                on_submit=lambda data, pid=p["product_id"]: _update_product(pid, data),
            )


def _product_form(key, categories, suppliers, defaults, on_submit):
    """商品の入力フォーム (新規・編集共通)。"""
    with st.form(key):
        name = st.text_input("商品名", value=defaults.get("product_name", ""))
        col1, col2 = st.columns(2)
        with col1:
            cat_names = list(categories.keys())
            cat_default = next(
                (i for i, c in enumerate(cat_names) if categories[c] == defaults.get("category_id")),
                0,
            )
            category = st.selectbox("カテゴリ", cat_names, index=cat_default)
        with col2:
            sup_names = list(suppliers.keys())
            sup_default = next(
                (i for i, s in enumerate(sup_names) if suppliers[s] == defaults.get("supplier_id")),
                0,
            )
            supplier = st.selectbox("仕入先", sup_names, index=sup_default)

        col3, col4 = st.columns(2)
        with col3:
            price = st.number_input("単価", min_value=0.0, value=float(defaults.get("unit_price") or 0), step=0.01)
        with col4:
            qty_per_unit = st.text_input("数量/単位", value=defaults.get("quantity_per_unit", ""))

        discontinued = st.checkbox("廃止", value=bool(defaults.get("discontinued", False)))
        submitted = st.form_submit_button("保存")

    if submitted:
        if not name:
            st.error("商品名は必須です")
            return
        data = {
            "product_name": name,
            "category_id": categories[category],
            "supplier_id": suppliers[supplier],
            "unit_price": price,
            "quantity_per_unit": qty_per_unit,
            "discontinued": 1 if discontinued else 0,
        }
        on_submit(data)


def _insert_product(data):
    execute(
        "INSERT INTO products (product_name, category_id, supplier_id, unit_price, "
        "  quantity_per_unit, discontinued, units_in_stock, units_on_order, reorder_level) "
        "VALUES (%(product_name)s, %(category_id)s, %(supplier_id)s, %(unit_price)s, "
        "  %(quantity_per_unit)s, %(discontinued)s, 0, 0, 0)",
        data,
    )
    st.success(f"商品「{data['product_name']}」を登録しました")


def _update_product(product_id, data):
    execute(
        "UPDATE products SET product_name=%(product_name)s, category_id=%(category_id)s, "
        "  supplier_id=%(supplier_id)s, unit_price=%(unit_price)s, "
        "  quantity_per_unit=%(quantity_per_unit)s, discontinued=%(discontinued)s "
        "WHERE product_id=%(product_id)s",
        {**data, "product_id": product_id},
    )
    st.success(f"商品 #{product_id} を更新しました")
