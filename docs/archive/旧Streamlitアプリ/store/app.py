"""Northwind 購買アプリ — メインエントリポイント"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

st.set_page_config(page_title="Northwind Store", page_icon="🛒", layout="wide")

from common.auth import store_login, store_logout

if not store_login():
    st.stop()

# --- ヘッダー ---
customer = st.session_state["store_customer"]
cart = st.session_state.setdefault("cart", [])

header_col1, header_col2, header_col3 = st.columns([4, 1, 1])
with header_col1:
    st.title("Northwind Store")
    st.caption(f"ようこそ、{customer['company_name']} 様")
with header_col2:
    cart_count = sum(item["quantity"] for item in cart)
    st.metric("カート", f"{cart_count} 点")
with header_col3:
    if st.button("ログアウト"):
        store_logout()

# --- タブナビゲーション ---
tab_catalog, tab_cart, tab_checkout, tab_history = st.tabs(
    ["商品一覧", f"カート ({cart_count})", "注文確定", "注文履歴"]
)

with tab_catalog:
    from store.pages import catalog
    catalog.render()

with tab_cart:
    from store.pages import cart_page
    cart_page.render()

with tab_checkout:
    from store.pages import checkout
    checkout.render()

with tab_history:
    from store.pages import history
    history.render()
