"""従業員管理画面"""

import streamlit as st
from common.db import fetch_all, execute


def render():
    st.header("従業員管理")

    user_role = st.session_state.get("admin_user", {}).get("role", "staff")

    employees = fetch_all(
        "SELECT employee_id, last_name, first_name, title, title_of_courtesy, "
        "  birth_date, hire_date, address, city, region, postal_code, country, "
        "  home_phone, extension, notes, reports_to "
        "FROM employees ORDER BY employee_id"
    )

    if not employees:
        st.info("従業員データがありません")
        return

    # --- 一覧テーブル ---
    st.dataframe(
        [{
            "ID": e["employee_id"],
            "氏名": f"{e['title_of_courtesy'] or ''} {e['first_name']} {e['last_name']}",
            "役職": e["title"],
            "入社日": e["hire_date"],
            "市区町村": e["city"],
            "国": e["country"],
        } for e in employees],
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    # --- 詳細編集 ---
    st.subheader("従業員詳細")
    emp_options = {f"{e['employee_id']}: {e['first_name']} {e['last_name']}": e for e in employees}
    selected = st.selectbox("従業員を選択", list(emp_options.keys()))

    if selected:
        e = emp_options[selected]
        can_see_private = user_role == "admin"

        with st.form(f"emp_{e['employee_id']}"):
            col1, col2 = st.columns(2)
            with col1:
                first_name = st.text_input("名前", value=e["first_name"])
                last_name = st.text_input("姓", value=e["last_name"])
                title = st.text_input("役職", value=e["title"] or "")
                courtesy = st.text_input("敬称", value=e["title_of_courtesy"] or "")
            with col2:
                address = st.text_input("住所", value=e["address"] or "")
                city = st.text_input("市区町村", value=e["city"] or "")
                country = st.text_input("国", value=e["country"] or "")
                postal_code = st.text_input("郵便番号", value=e["postal_code"] or "")

            # 個人情報 (権限に応じてマスキング)
            st.caption("個人情報")
            if can_see_private:
                birth_date = st.text_input("生年月日", value=str(e["birth_date"] or ""))
                home_phone = st.text_input("自宅電話番号", value=e["home_phone"] or "")
            else:
                st.text_input("生年月日", value="****-**-**", disabled=True)
                st.text_input("自宅電話番号", value="****", disabled=True)
                st.info("個人情報の閲覧には管理者権限が必要です")

            submitted = st.form_submit_button("保存")

        if submitted:
            execute(
                "UPDATE employees SET first_name=%s, last_name=%s, title=%s, "
                "  title_of_courtesy=%s, address=%s, city=%s, country=%s, postal_code=%s "
                "WHERE employee_id=%s",
                (first_name, last_name, title, courtesy, address, city, country, postal_code, e["employee_id"]),
            )
            st.success(f"従業員 #{e['employee_id']} を更新しました")
            st.rerun()
