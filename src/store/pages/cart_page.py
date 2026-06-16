"""カート画面"""

import streamlit as st


def render():
    cart = st.session_state.get("cart", [])

    if not cart:
        st.info("カートは空です。商品一覧から商品を追加してください。")
        return

    st.subheader("ショッピングカート")

    total = 0.0
    items_to_remove = []

    for i, item in enumerate(cart):
        col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 0.5])
        with col1:
            st.write(f"**{item['product_name']}**")
        with col2:
            st.write(f"${item['unit_price']:.2f}")
        with col3:
            new_qty = st.number_input(
                "数量", min_value=1, max_value=item["max_stock"],
                value=item["quantity"], key=f"cart_qty_{i}",
                label_visibility="collapsed",
            )
            item["quantity"] = new_qty
        with col4:
            subtotal = item["unit_price"] * item["quantity"]
            total += subtotal
            st.write(f"${subtotal:.2f}")
        with col5:
            if st.button("×", key=f"cart_rm_{i}"):
                items_to_remove.append(i)

    if items_to_remove:
        for idx in sorted(items_to_remove, reverse=True):
            cart.pop(idx)
        st.rerun()

    st.divider()
    st.markdown(f"### 合計: ${total:.2f}")
