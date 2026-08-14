"""Session-state helpers shared across all pages of UEH-DASS."""
import numpy as np
import pandas as pd
import streamlit as st

from utils.i18n import t, DEFAULT_LANG
from utils.footer import render_footer


def init_state():
    if "df" not in st.session_state:
        st.session_state.df = None
    if "var_labels" not in st.session_state:
        st.session_state.var_labels = {}
    if "log" not in st.session_state:
        st.session_state.log = []
    if "lang" not in st.session_state:
        st.session_state.lang = DEFAULT_LANG


def get_df():
    init_state()
    return st.session_state.df


def set_df(df: pd.DataFrame, message: str = None):
    init_state()
    st.session_state.df = df
    if message:
        log_action(message)


def has_data() -> bool:
    init_state()
    return st.session_state.df is not None and len(st.session_state.df) > 0


def require_data():
    """Call at the top of every analysis page. Stops the page if no data is loaded."""
    init_state()
    if not has_data():
        st.warning(t("common.require_data", home=t("nav.home")))
        render_footer()
        st.stop()


def log_action(message: str):
    init_state()
    st.session_state.log.append(message)


def numeric_columns(df: pd.DataFrame):
    return df.select_dtypes(include=[np.number]).columns.tolist()


def all_columns(df: pd.DataFrame):
    return df.columns.tolist()


def categorical_columns(df: pd.DataFrame, max_unique: int = 30):
    """Heuristic: text columns, or numeric columns with few distinct values (Likert/group codes)."""
    cols = []
    for c in df.columns:
        if df[c].dtype == object or str(df[c].dtype) == "category":
            cols.append(c)
        elif df[c].nunique(dropna=True) <= max_unique:
            cols.append(c)
    return cols


def show_log():
    init_state()
    if st.session_state.log:
        with st.expander(t("common.log_header", n=len(st.session_state.log))):
            for i, msg in enumerate(reversed(st.session_state.log), 1):
                st.write(f"{len(st.session_state.log) - i + 1}. {msg}")
