"""ダッシュボード画面"""

import streamlit as st
from common.db import fetch_all, fetch_one


def render():
    st.header("ダッシュボード")

    # --- KPI カード ---
    col1, col2, col3 = st.columns(3)

    product_count = fetch_one(
        "SELECT COUNT(*) as cnt FROM products WHERE discontinued = 0"
    )
    order_count = fetch_one("SELECT COUNT(*) as cnt FROM orders")
    alert_count = fetch_one(
        "SELECT COUNT(*) as cnt FROM products "
        "WHERE discontinued = 0 AND units_in_stock <= reorder_level"
    )

    col1.metric("有効商品数", product_count["cnt"])
    col2.metric("総注文数", order_count["cnt"])
    col3.metric("在庫アラート", alert_count["cnt"])

    # --- 最近の注文 ---
    st.subheader("最近の注文")
    recent_orders = fetch_all(
        "SELECT o.order_id, c.company_name, o.order_date, "
        "  COALESCE(SUM(od.unit_price * od.quantity * (1 - od.discount)), 0) as total "
        "FROM orders o "
        "LEFT JOIN customers c ON o.customer_id = c.customer_id "
        "LEFT JOIN order_details od ON o.order_id = od.order_id "
        "GROUP BY o.order_id, c.company_name, o.order_date "
        "ORDER BY o.order_id DESC LIMIT 10"
    )
    if recent_orders:
        st.dataframe(
            recent_orders,
            column_config={
                "order_id": st.column_config.NumberColumn("注文#"),
                "company_name": "顧客",
                "order_date": st.column_config.DateColumn("注文日"),
                "total": st.column_config.NumberColumn("合計", format="$%.2f"),
            },
            use_container_width=True,
            hide_index=True,
        )

    # --- 在庫アラート ---
    st.subheader("在庫アラート")
    alerts = fetch_all(
        "SELECT p.product_id, p.product_name, p.units_in_stock, p.reorder_level, "
        "  c.category_name "
        "FROM products p "
        "LEFT JOIN categories c ON p.category_id = c.category_id "
        "WHERE p.discontinued = 0 AND p.units_in_stock <= p.reorder_level "
        "ORDER BY p.units_in_stock ASC"
    )
    if alerts:
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
