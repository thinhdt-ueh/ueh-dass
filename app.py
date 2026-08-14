import os
import tempfile

import numpy as np
import pandas as pd
import streamlit as st

from utils.state import get_df, set_df, has_data, init_state, show_log
from utils.i18n import t, get_lang, set_lang, LANGUAGES
from utils.export import df_to_csv_bytes, df_to_excel_bytes
from utils.footer import render_footer
from utils.project import serialize_project, deserialize_project
from utils.report import init_report_state, report_count, build_docx_bytes, clear_report

APP_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(APP_DIR, "assets", "logo-ueh.png")

st.set_page_config(page_title="DASS", page_icon="📊", layout="wide")
init_state()

# Streamlit's default .block-container padding leaves a large gap at the top/sides
# of the main content area; tighten it so pages start closer to the top-left corner.
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2rem;
        padding-left: 2rem;
        padding-right: 2rem;
        padding-bottom: 2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if os.path.exists(LOGO_PATH):
    st.logo(LOGO_PATH, size="large")


def generate_demo_data(lang: str = "vi", n: int = 200, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    if lang == "en":
        col_gender, col_age, col_income, col_edu = "Gender", "AgeGroup", "Income", "Education"
        gender_vals = ["Male", "Female"]
        income_vals = ["<$1,000", "$1,000-2,000", "$2,000-3,000", ">$3,000"]
        edu_vals = ["High School", "College", "Bachelor's", "Graduate"]
        prefix_ba, prefix_pi, col_guilt = "BA", "PI", "Guilt"
    else:
        col_gender, col_age, col_income, col_edu = "GioiTinh", "NhomTuoi", "ThuNhap", "TrinhDo"
        gender_vals = ["Nam", "Nữ"]
        income_vals = ["<10 triệu", "10-20 triệu", "20-30 triệu", ">30 triệu"]
        edu_vals = ["THPT", "Cao đẳng", "Đại học", "Sau đại học"]
        prefix_ba, prefix_pi, col_guilt = "XT", "YD", "ToiLoi"

    age_labels = ["18-24", "25-34", "35-44", "45-54", "55+"]

    df = pd.DataFrame({
        "ID": range(1, n + 1),
        col_gender: rng.choice(gender_vals, size=n),
        col_age: rng.choice(age_labels, size=n, p=[0.35, 0.30, 0.15, 0.12, 0.08]),
        col_income: rng.choice(income_vals, size=n),
        col_edu: rng.choice(edu_vals, size=n),
    })

    # Construct: Brand Authenticity - 4 items, 7-point Likert
    for i in range(1, 5):
        df[f"{prefix_ba}{i}"] = rng.integers(1, 8, size=n)

    # Construct: (Green) Purchase Intention - 4 items, 7-point Likert
    for i in range(1, 5):
        df[f"{prefix_pi}{i}"] = rng.integers(1, 8, size=n)

    # Reverse-worded item example (matches the guilt-statement example in the brief)
    df[col_guilt] = rng.integers(1, 8, size=n)

    # Sprinkle some missing values to exercise the Missing Data module
    for col in [f"{prefix_ba}2", f"{prefix_pi}3", col_income]:
        idx = rng.choice(n, size=int(n * 0.05), replace=False)
        df.loc[idx, col] = np.nan

    return df


def read_uploaded_file(uploaded) -> pd.DataFrame:
    name = uploaded.name.lower()
    if name.endswith(".csv"):
        try:
            return pd.read_csv(uploaded, encoding="utf-8-sig")
        except UnicodeDecodeError:
            uploaded.seek(0)
            return pd.read_csv(uploaded, encoding="latin1")
    elif name.endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded)
    elif name.endswith(".sav"):
        try:
            import pyreadstat
        except ImportError:
            st.error(t("common.need_pyreadstat"))
            st.stop()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".sav") as tmp:
            tmp.write(uploaded.getvalue())
            tmp_path = tmp.name
        try:
            df_sav, meta = pyreadstat.read_sav(tmp_path)
        finally:
            os.unlink(tmp_path)
        labels = dict(zip(meta.column_names, meta.column_labels or meta.column_names))
        st.session_state.var_labels.update({k: (v or k) for k, v in labels.items()})
        return df_sav
    else:
        st.error(t("common.unsupported_format"))
        st.stop()


def render_sidebar():
    with st.sidebar:
        lang_codes = list(LANGUAGES.keys())
        lang_names = list(LANGUAGES.values())
        current_idx = lang_codes.index(get_lang())
        chosen_name = st.selectbox(f"🌐 {t('sidebar.language')}", lang_names, index=current_idx, key="lang_selector")
        chosen_code = lang_codes[lang_names.index(chosen_name)]
        if chosen_code != get_lang():
            set_lang(chosen_code)
            st.rerun()

        st.divider()
        st.header(t("sidebar.import_header"))
        uploaded = st.file_uploader(t("sidebar.upload_label"), type=["csv", "xlsx", "xls", "sav"])
        # st.file_uploader keeps returning the same file on every rerun (any click
        # anywhere in the app re-runs this sidebar), so guard on file_id to avoid
        # silently re-importing and wiping out later edits.
        if uploaded is not None and st.session_state.get("_last_data_file_id") != uploaded.file_id:
            try:
                new_df = read_uploaded_file(uploaded)
                set_df(new_df, f"{t('common.import_success', rows=new_df.shape[0], cols=new_df.shape[1])} ('{uploaded.name}')")
                st.session_state["_last_data_file_id"] = uploaded.file_id
                st.success(t("common.import_success", rows=new_df.shape[0], cols=new_df.shape[1]))
            except Exception as e:
                st.error(t("common.import_error", error=e))

        st.divider()
        if st.button(t("sidebar.demo_btn")):
            demo = generate_demo_data(lang=get_lang())
            set_df(demo, t("sidebar.demo_success"))
            st.success(t("sidebar.demo_success"))

        if has_data() and st.button(t("sidebar.clear_btn")):
            set_df(None)
            st.rerun()

        st.divider()
        st.subheader(t("sidebar.export_header"))
        if has_data():
            export_df = get_df()
            st.download_button(
                t("sidebar.export_csv"), data=df_to_csv_bytes(export_df),
                file_name="ueh_dass_data.csv", mime="text/csv", width="stretch",
            )
            st.download_button(
                t("sidebar.export_excel"), data=df_to_excel_bytes(export_df),
                file_name="ueh_dass_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width="stretch",
            )
            st.caption(t("sidebar.export_hint"))
        else:
            st.caption(t("sidebar.no_data_export"))

        st.divider()
        st.subheader(t("sidebar.project_header"))
        if has_data():
            project_df = get_df()
            st.download_button(
                t("sidebar.project_save"),
                data=serialize_project(project_df, st.session_state.var_labels, st.session_state.log, get_lang()),
                file_name="dass_project.json", mime="application/json", width="stretch",
            )
        uploaded_project = st.file_uploader(t("sidebar.project_load_label"), type=["json"], key="project_uploader")
        if uploaded_project is not None and st.session_state.get("_last_project_file_id") != uploaded_project.file_id:
            try:
                new_df, var_labels, log, lang = deserialize_project(uploaded_project.getvalue())
                st.session_state.var_labels = var_labels
                st.session_state.log = log
                set_lang(lang)
                set_df(new_df, t("sidebar.project_load_success"))
                st.session_state["_last_project_file_id"] = uploaded_project.file_id
                st.success(t("sidebar.project_load_success"))
            except Exception as e:
                st.error(t("sidebar.project_load_error", error=e))
        st.caption(t("sidebar.project_hint"))

        st.divider()
        init_report_state()
        n_report = report_count()
        st.subheader(f"{t('sidebar.report_header')} ({n_report})")
        if n_report:
            st.download_button(
                t("sidebar.report_download"), data=build_docx_bytes(),
                file_name="DASS_Report.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                width="stretch",
            )
            if st.button(t("sidebar.report_clear")):
                clear_report()
                st.rerun()
        else:
            st.caption(t("sidebar.report_empty"))

        st.divider()
        st.markdown(t("sidebar.modules_hint"))


def home_page():
    st.title(f"📊 {t('app.title')}")
    st.caption(t("app.caption"))

    if has_data():
        df = get_df()

        c1, c2, c3 = st.columns(3)
        c1.metric(t("common.rows_metric"), df.shape[0])
        c2.metric(t("common.cols_metric"), df.shape[1])
        c3.metric(t("common.missing_metric"), int(df.isna().sum().sum()))

        tab1, tab2 = st.tabs([f"🗂️ {t('home.data_view')}", f"🏷️ {t('home.var_view')}"])

        with tab1:
            st.caption(t("home.data_view_caption"))
            table_height = min(max(len(df) + 1, 8) * 35 + 3, 700)
            edited = st.data_editor(df, num_rows="dynamic", width="stretch", height=table_height, key="data_editor")
            if not edited.equals(df):
                set_df(edited, t("home.save_changes_log"))
                st.rerun()

        with tab2:
            info_rows = []
            for col in df.columns:
                info_rows.append({
                    t("home.var_name"): col,
                    t("home.var_dtype"): str(df[col].dtype),
                    t("home.var_label"): st.session_state.var_labels.get(col, ""),
                    t("home.var_valid"): int(df[col].notna().sum()),
                    t("home.var_missing"): int(df[col].isna().sum()),
                    t("home.var_unique"): int(df[col].nunique(dropna=True)),
                })
            st.dataframe(pd.DataFrame(info_rows), width="stretch")

            st.markdown(f"##### {t('home.assign_label')}")
            cc1, cc2, cc3 = st.columns([2, 3, 1])
            col_to_label = cc1.selectbox(t("home.var_name"), df.columns, label_visibility="collapsed", key="label_var_select")
            label_val = cc2.text_input(
                t("home.assign_label"), value=st.session_state.var_labels.get(col_to_label, ""),
                label_visibility="collapsed", placeholder=t("home.assign_label_placeholder"),
            )
            if cc3.button(t("home.save_label")):
                st.session_state.var_labels[col_to_label] = label_val
                st.success(t("home.saved"))
                st.rerun()

            st.divider()
            st.markdown(f"##### {t('home.change_dtype_title')}")
            st.caption(t("home.change_dtype_caption"))
            dc1, dc2, dc3 = st.columns([2, 2, 1])
            dtype_var = dc1.selectbox(t("home.var_name"), df.columns, label_visibility="collapsed", key="dtype_var_select")
            dtype_options = [
                t("home.dtype_numeric"), t("home.dtype_text"),
                t("home.dtype_date"), t("home.dtype_category"),
            ]
            target_dtype = dc2.selectbox(t("home.change_dtype_title"), dtype_options, label_visibility="collapsed", key="dtype_target_select")
            if dc3.button(t("home.apply_dtype_btn")):
                original = df[dtype_var]
                n_missing_before = int(original.isna().sum())
                if target_dtype == t("home.dtype_numeric"):
                    converted = pd.to_numeric(original, errors="coerce")
                elif target_dtype == t("home.dtype_text"):
                    converted = original.apply(lambda x: None if pd.isna(x) else str(x)).astype("object")
                elif target_dtype == t("home.dtype_date"):
                    converted = pd.to_datetime(original, errors="coerce")
                else:
                    converted = original.astype("category")
                n_missing_after = int(converted.isna().sum())
                df[dtype_var] = converted
                set_df(df, t("home.change_dtype_log", var=dtype_var, dtype=target_dtype))
                new_failures = n_missing_after - n_missing_before
                if new_failures > 0:
                    st.warning(t("home.dtype_coerce_warn", n=new_failures, var=dtype_var))
                else:
                    st.success(t("home.dtype_success", var=dtype_var, dtype=target_dtype))
                st.rerun()

        show_log()

    else:
        st.info(t("home.welcome_info"))
        st.markdown(t("home.modules_overview"))

    render_footer()


render_sidebar()

pages = [
    st.Page(home_page, title=t("nav.home"), icon="🏠", default=True),
    st.Page("pages/1_🔧_Bien_doi_du_lieu.py", title=t("nav.data_mgmt"), icon="🔧"),
    st.Page("pages/2_📊_Thong_ke_mo_ta.py", title=t("nav.desc"), icon="📊"),
    st.Page("pages/3_✅_Danh_gia_thang_do.py", title=t("nav.scale"), icon="✅"),
    st.Page("pages/4_🧪_Kiem_dinh_gia_thuyet.py", title=t("nav.hyp"), icon="🧪"),
    st.Page("pages/5_📈_Phan_tich_tuong_quan.py", title=t("nav.rel"), icon="📈"),
    st.Page("pages/6_🧮_Phi_tham_so_Bieu_do.py", title=t("nav.np"), icon="🧮"),
    st.Page("pages/7_❓_Huong_dan.py", title=t("nav.help"), icon="❓"),
]
pg = st.navigation(pages)
pg.run()
