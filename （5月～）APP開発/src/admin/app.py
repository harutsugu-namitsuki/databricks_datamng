"""Northwind 業務管理アプリ — メインエントリポイント"""

import sys
from pathlib import Path

# src/ を PYTHONPATH に追加
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

st.set_page_config(page_title="Northwind 業務管理", page_icon="📊", layout="wide")

from common.auth import admin_login, admin_logout

if not admin_login():
    st.stop()

# --- サイドバー ---
user = st.session_state["admin_user"]
st.sidebar.title(f"👤 {user['name']}")
st.sidebar.caption(f"ロール: {user['role']}")

page = st.sidebar.radio(
    "メニュー",
    ["ダッシュボード", "商品管理", "在庫管理", "従業員管理"],
)
st.sidebar.divider()
if st.sidebar.button("ログアウト"):
    admin_logout()

# --- ページルーティング ---
if page == "ダッシュボード":
    from admin.pages import dashboard
    dashboard.render()
elif page == "商品管理":
    from admin.pages import products
    products.render()
elif page == "在庫管理":
    from admin.pages import inventory
    inventory.render()
elif page == "従業員管理":
    from admin.pages import employees
    employees.render()
