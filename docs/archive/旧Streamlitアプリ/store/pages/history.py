"""注文履歴画面"""

import streamlit as st
from common.db import fetch_all


def render():
    customer = st.session_state.get("store_customer", {})
    customer_id = customer.get("customer_id")

    if not customer_id:
        st.warning("ログインしてください")
        return

    st.subheader("注文履歴")

    orders = fetch_all(
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

    if not orders:
        st.info("注文履歴がありません")
        return

    for order in orders:
        status = "出荷済" if order["shipped_date"] else "処理中"
        with st.expander(
            f"注文 #{order['order_id']} | {order['order_date']} | "
            f"${order['total']:.2f} | {status}"
        ):
            st.write(f"**注文日:** {order['order_date']}")
            st.write(f"**出荷日:** {order['shipped_date'] or '未出荷'}")
            st.write(f"**配送先:** {order['ship_name']}")
            st.write(f"**配送業者:** {order['shipper_name']}")

            # 明細
            details = fetch_all(
                "SELECT p.product_name, od.unit_price, od.quantity, od.discount, "
                "  (od.unit_price * od.quantity * (1 - od.discount)) as subtotal "
                "FROM order_details od "
                "LEFT JOIN products p ON od.product_id = p.product_id "
                "WHERE od.order_id = %s",
                (order["order_id"],),
            )
            if details:
                st.dataframe(
                    details,
                    column_config={
                        "product_name": "商品名",
                        "unit_price": st.column_config.NumberColumn("単価", format="$%.2f"),
                        "quantity": "数量",
                        "discount": st.column_config.NumberColumn("割引", format="%.0f%%"),
                        "subtotal": st.column_config.NumberColumn("小計", format="$%.2f"),
                    },
                    use_container_width=True,
                    hide_index=True,
                )
