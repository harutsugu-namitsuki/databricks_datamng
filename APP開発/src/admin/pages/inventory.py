"""在庫管理画面"""

import streamlit as st
from common.db import fetch_all, execute


def render():
    st.header("在庫管理")

    # --- 在庫アラート ---
    alerts = fetch_all(
        "SELECT p.product_id, p.product_name, p.units_in_stock, p.reorder_level, "
        "  c.category_name "
        "FROM products p "
        "LEFT JOIN categories c ON p.category_id = c.category_id "
        "WHERE p.discontinued = 0 AND p.units_in_stock <= p.reorder_level "
        "ORDER BY p.units_in_stock ASC"
    )
    if alerts:
        st.warning(f"在庫アラート: {len(alerts)} 件")
        st.dataframe(
            alerts,
            column_config={
                "product_id": "ID",
                "product_name": "商品名",
                "units_in_stock": st.column_config.NumberColumn("在庫数"),
                "reorder_level": st.column_config.NumberColumn("発注点"),
                "category_name": "カテゴリ",
            },
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.success("在庫アラートはありません")

    st.divider()

    # --- 在庫調整 ---
    st.subheader("在庫調整")

    products = fetch_all(
        "SELECT product_id, product_name, units_in_stock "
        "FROM products WHERE discontinued = 0 ORDER BY product_name"
    )
    product_map = {f"{p['product_name']} (現在庫: {p['units_in_stock']})": p for p in products}

    with st.form("adjust_stock"):
        selected = st.selectbox("商品", list(product_map.keys()))
        col1, col2 = st.columns(2)
        with col1:
            adjustment = st.number_input("調整数量", value=0, step=1, help="正の値で入荷、負の値で出庫")
        with col2:
            reason = st.selectbox("理由", ["入荷", "出庫", "棚卸調整", "破損・廃棄", "その他"])
        submitted = st.form_submit_button("調整実行")

    if submitted and selected:
        p = product_map[selected]
        new_stock = p["units_in_stock"] + adjustment
        if new_stock < 0:
            st.error(f"在庫数が負の値になります (現在: {p['units_in_stock']}, 調整: {adjustment})")
        elif adjustment == 0:
            st.warning("調整数量を入力してください")
        else:
            execute(
                "UPDATE products SET units_in_stock = %s WHERE product_id = %s",
                (new_stock, p["product_id"]),
            )
            st.success(
                f"「{p['product_name']}」の在庫を調整しました: "
                f"{p['units_in_stock']} → {new_stock} ({reason})"
            )
            st.rerun()

    st.divider()

    # --- 全商品在庫一覧 ---
    st.subheader("全商品在庫一覧")
    all_products = fetch_all(
        "SELECT p.product_id, p.product_name, c.category_name, "
        "  p.units_in_stock, p.units_on_order, p.reorder_level, p.discontinued "
        "FROM products p "
        "LEFT JOIN categories c ON p.category_id = c.category_id "
        "ORDER BY c.category_name, p.product_name"
    )
    st.dataframe(
        [{
            "ID": p["product_id"],
            "商品名": p["product_name"],
            "カテゴリ": p["category_name"],
            "在庫数": p["units_in_stock"],
            "発注中": p["units_on_order"],
            "発注点": p["reorder_level"],
            "廃止": "Yes" if p["discontinued"] else "",
        } for p in all_products],
        column_config={
            "在庫数": st.column_config.ProgressColumn(
                min_value=0, max_value=150, format="%d",
            ),
        },
        use_container_width=True,
        hide_index=True,
    )
