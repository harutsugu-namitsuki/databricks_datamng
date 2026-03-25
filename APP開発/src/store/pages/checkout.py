"""注文確定画面"""

import datetime
import streamlit as st
from common.db import fetch_all, fetch_one, execute_returning, execute


def render():
    cart = st.session_state.get("cart", [])
    customer = st.session_state.get("store_customer", {})

    if not cart:
        st.info("カートに商品がありません。")
        return

    st.subheader("注文確定")

    # --- 注文内容 ---
    st.write("**注文内容:**")
    total = 0.0
    for item in cart:
        subtotal = item["unit_price"] * item["quantity"]
        total += subtotal
        st.write(f"- {item['product_name']} x{item['quantity']}　${subtotal:.2f}")
    st.markdown(f"**小計: ${total:.2f}**")

    st.divider()

    # --- 配送先 ---
    st.write("**配送先:**")
    with st.form("checkout_form"):
        ship_name = st.text_input("宛名", value=customer.get("company_name", ""))
        ship_address = st.text_input("住所", value=customer.get("address", ""))
        col1, col2 = st.columns(2)
        with col1:
            ship_city = st.text_input("市区町村", value=customer.get("city", ""))
            ship_region = st.text_input("地域", value=customer.get("region", ""))
        with col2:
            ship_postal = st.text_input("郵便番号", value=customer.get("postal_code", ""))
            ship_country = st.text_input("国", value=customer.get("country", ""))

        # 配送業者
        shippers = fetch_all("SELECT shipper_id, company_name FROM shippers ORDER BY shipper_id")
        shipper_map = {s["company_name"]: s["shipper_id"] for s in shippers}
        shipper = st.selectbox("配送業者", list(shipper_map.keys()))

        submitted = st.form_submit_button("注文を確定する")

    if submitted:
        _place_order(
            customer_id=customer["customer_id"],
            ship_via=shipper_map[shipper],
            ship_name=ship_name,
            ship_address=ship_address,
            ship_city=ship_city,
            ship_region=ship_region,
            ship_postal_code=ship_postal,
            ship_country=ship_country,
            cart=cart,
        )


def _place_order(customer_id, ship_via, ship_name, ship_address,
                 ship_city, ship_region, ship_postal_code, ship_country, cart):
    """orders + order_details を INSERT し、在庫を減算する。"""
    # 次の order_id を取得
    max_order = fetch_one("SELECT COALESCE(MAX(order_id), 0) + 1 as next_id FROM orders")
    next_order_id = max_order["next_id"]

    # orders INSERT
    execute(
        "INSERT INTO orders (order_id, customer_id, employee_id, order_date, required_date, "
        "  ship_via, freight, ship_name, ship_address, ship_city, ship_region, "
        "  ship_postal_code, ship_country) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (
            next_order_id, customer_id, 1,  # employee_id=1 (デフォルト)
            datetime.date.today(),
            datetime.date.today() + datetime.timedelta(days=14),
            ship_via, 0.0,
            ship_name, ship_address, ship_city, ship_region,
            ship_postal_code, ship_country,
        ),
    )

    # order_details INSERT + 在庫減算
    for item in cart:
        execute(
            "INSERT INTO order_details (order_id, product_id, unit_price, quantity, discount) "
            "VALUES (%s, %s, %s, %s, %s)",
            (next_order_id, item["product_id"], item["unit_price"], item["quantity"], 0.0),
        )
        execute(
            "UPDATE products SET units_in_stock = units_in_stock - %s WHERE product_id = %s",
            (item["quantity"], item["product_id"]),
        )

    # カートをクリア
    st.session_state["cart"] = []
    st.success(f"注文 #{next_order_id} を確定しました！")
    st.balloons()
