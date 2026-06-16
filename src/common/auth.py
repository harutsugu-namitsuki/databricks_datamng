"""簡易認証モジュール"""

import streamlit as st


# 業務管理アプリ用ユーザー (初期実装: ハードコード → 将来は YAML or DB)
ADMIN_USERS = {
    "admin": {"password": "admin123", "name": "管理者", "role": "admin"},
    "staff": {"password": "staff123", "name": "スタッフ", "role": "staff"},
}


def admin_login() -> bool:
    """業務管理アプリのログイン。成功で True を返す。"""
    if st.session_state.get("admin_authenticated"):
        return True

    st.title("Northwind 業務管理")
    with st.form("login_form"):
        username = st.text_input("ユーザー名")
        password = st.text_input("パスワード", type="password")
        submitted = st.form_submit_button("ログイン")

    if submitted:
        user = ADMIN_USERS.get(username)
        if user and user["password"] == password:
            st.session_state["admin_authenticated"] = True
            st.session_state["admin_user"] = {
                "username": username,
                "name": user["name"],
                "role": user["role"],
            }
            st.rerun()
        else:
            st.error("ユーザー名またはパスワードが正しくありません")
    return False


def store_login() -> bool:
    """購買アプリのログイン (顧客IDベース)。成功で True を返す。"""
    if st.session_state.get("store_authenticated"):
        return True

    st.title("Northwind Store")
    with st.form("login_form"):
        customer_id = st.text_input("顧客ID (例: ALFKI)")
        password = st.text_input("パスワード", type="password")
        submitted = st.form_submit_button("ログイン")

    if submitted:
        # 初期実装: 顧客IDが存在すればログイン成功 (パスワードは customer_id と同じ)
        from common.db import fetch_one

        customer = fetch_one(
            "SELECT customer_id, company_name, contact_name, address, city, region, postal_code, country "
            "FROM customers WHERE customer_id = %s",
            (customer_id.upper(),),
        )
        if customer and password == customer_id.upper():
            st.session_state["store_authenticated"] = True
            st.session_state["store_customer"] = dict(customer)
            st.rerun()
        else:
            st.error("顧客IDまたはパスワードが正しくありません")
    return False


def admin_logout():
    """業務管理アプリのログアウト。"""
    for key in ["admin_authenticated", "admin_user"]:
        st.session_state.pop(key, None)
    st.rerun()


def store_logout():
    """購買アプリのログアウト。"""
    for key in ["store_authenticated", "store_customer", "cart"]:
        st.session_state.pop(key, None)
    st.rerun()
