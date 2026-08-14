import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from utils.state import get_df, set_df, require_data, numeric_columns, all_columns, show_log
from utils.i18n import t
from utils.footer import render_footer

st.title(f"🔧 {t('nav.data_mgmt')}")
require_data()
df = get_df()

tab_recode, tab_missing, tab_compute = st.tabs(
    [f"🔁 {t('dm.recode.tab')}", f"❓ {t('dm.missing.tab')}", f"➕ {t('dm.compute.tab')}"]
)

# ----------------------------------------------------------------------------
# RECODE
# ----------------------------------------------------------------------------
with tab_recode:
    st.markdown(f"#### {t('dm.recode.reverse_title')}")
    st.caption(t("dm.recode.reverse_caption"))
    num_cols = numeric_columns(df)
    rc1, rc2, rc3 = st.columns([3, 1, 1])
    rev_vars = rc1.multiselect(t("dm.recode.reverse_select"), num_cols, key="rev_vars")
    scale_min = rc2.number_input(t("dm.recode.scale_min"), value=1, step=1, key="scale_min")
    scale_max = rc3.number_input(t("dm.recode.scale_max"), value=7, step=1, key="scale_max")
    rev_mode = st.radio(
        t("dm.recode.apply_as"), [t("dm.recode.mode_new"), t("dm.recode.mode_overwrite")],
        horizontal=True, key="rev_mode",
    )
    if st.button(t("dm.recode.reverse_btn"), key="btn_reverse"):
        if not rev_vars:
            st.warning(t("dm.recode.warn_select_var"))
        else:
            preview_cols = []
            for v in rev_vars:
                target = v if rev_mode == t("dm.recode.mode_overwrite") else f"{v}_R"
                df[target] = (scale_min + scale_max) - df[v]
                preview_cols.append(target)
            set_df(df, t("dm.recode.reverse_log", min=scale_min, max=scale_max, vars=", ".join(rev_vars)))
            st.success(t("dm.recode.reverse_success", n=len(rev_vars)))
            st.dataframe(df[rev_vars + preview_cols].head(10), width="stretch")

    st.divider()
    st.markdown(f"#### {t('dm.recode.custom_title')}")
    st.caption(t("dm.recode.custom_caption"))
    var_rc = st.selectbox(t("dm.recode.custom_select"), all_columns(df), key="custom_recode_var")
    if var_rc:
        uniques = sorted(df[var_rc].dropna().unique().tolist(), key=lambda x: str(x))
        map_df = pd.DataFrame({t("dm.recode.old_value"): uniques, t("dm.recode.new_value"): uniques})
        edited_map = st.data_editor(
            map_df, num_rows="fixed", width="stretch", key="recode_map_editor",
            disabled=[t("dm.recode.old_value")],
        )
        new_name = st.text_input(t("dm.recode.result_name"), value=f"{var_rc}_MH", key="recode_new_name")
        if st.button(t("dm.recode.custom_btn"), key="btn_custom_recode"):
            mapping = dict(zip(edited_map[t("dm.recode.old_value")], edited_map[t("dm.recode.new_value")]))
            df[new_name] = df[var_rc].map(mapping)
            set_df(df, t("dm.recode.custom_log", var=var_rc, new=new_name))
            st.success(t("dm.recode.custom_success", new=new_name))
            st.dataframe(df[[var_rc, new_name]].head(10), width="stretch")

# ----------------------------------------------------------------------------
# MISSING DATA
# ----------------------------------------------------------------------------
with tab_missing:
    miss = df.isna().sum()
    miss_pct = (miss / len(df) * 100).round(2)
    miss_df = pd.DataFrame({
        t("home.var_name"): df.columns,
        t("dm.missing.count"): miss.values,
        t("dm.missing.pct"): miss_pct.values,
    })
    miss_df = miss_df[miss_df[t("dm.missing.count")] > 0].sort_values(t("dm.missing.count"), ascending=False)

    if miss_df.empty:
        st.success(t("dm.missing.none_found"))
    else:
        st.dataframe(miss_df, width="stretch")
        fig = px.bar(miss_df, x=t("home.var_name"), y=t("dm.missing.count"), title=t("dm.missing.chart_title"))
        st.plotly_chart(fig, width="stretch")

        st.markdown(f"#### {t('dm.missing.handle_title')}")
        method_options = [
            t("dm.missing.method_mean"),
            t("dm.missing.method_median"),
            t("dm.missing.method_mode"),
            t("dm.missing.method_listwise"),
        ]
        method = st.radio(t("dm.missing.method_label"), method_options)
        target_vars = st.multiselect(
            t("dm.missing.target_vars"), miss_df[t("home.var_name")].tolist(),
            default=miss_df[t("home.var_name")].tolist(),
        )
        if st.button(t("dm.missing.handle_btn"), key="btn_missing"):
            if not target_vars:
                st.warning(t("dm.missing.warn_select_var"))
            else:
                n_before = len(df)
                if method == t("dm.missing.method_mean"):
                    skipped = []
                    for v in target_vars:
                        if pd.api.types.is_numeric_dtype(df[v]):
                            df[v] = df[v].fillna(df[v].mean())
                        else:
                            skipped.append(v)
                    applied = [v for v in target_vars if v not in skipped]
                    msg = t("dm.missing.log_mean", vars=", ".join(applied))
                    if skipped:
                        st.warning(t("dm.missing.warn_skip_categorical", vars=", ".join(skipped)))
                elif method == t("dm.missing.method_median"):
                    skipped = []
                    for v in target_vars:
                        if pd.api.types.is_numeric_dtype(df[v]):
                            df[v] = df[v].fillna(df[v].median())
                        else:
                            skipped.append(v)
                    applied = [v for v in target_vars if v not in skipped]
                    msg = t("dm.missing.log_median", vars=", ".join(applied))
                    if skipped:
                        st.warning(t("dm.missing.warn_skip_categorical", vars=", ".join(skipped)))
                elif method == t("dm.missing.method_mode"):
                    for v in target_vars:
                        mode_val = df[v].mode(dropna=True)
                        if not mode_val.empty:
                            df[v] = df[v].fillna(mode_val.iloc[0])
                    msg = t("dm.missing.log_mode", vars=", ".join(target_vars))
                else:  # listwise deletion
                    df = df.dropna(subset=target_vars)
                    msg = t("dm.missing.log_listwise", vars=", ".join(target_vars), before=n_before, after=len(df))
                set_df(df, msg)
                st.success(t("dm.missing.handled_success"))
                st.rerun()

# ----------------------------------------------------------------------------
# COMPUTE VARIABLE
# ----------------------------------------------------------------------------
with tab_compute:
    st.caption(t("dm.compute.caption"))
    items = st.multiselect(t("dm.compute.items"), numeric_columns(df), key="compute_items")
    new_name = st.text_input(t("dm.compute.new_name"), value=t("dm.compute.default_name"), key="compute_new_name")
    agg_options = [t("dm.compute.agg_mean"), t("dm.compute.agg_sum")]
    agg = st.radio(t("dm.compute.agg_label"), agg_options, horizontal=True, key="compute_agg")
    if st.button(t("dm.compute.btn"), key="btn_compute"):
        if not items:
            st.warning(t("dm.compute.warn_select_items"))
        elif not new_name:
            st.warning(t("dm.compute.warn_name"))
        else:
            if agg == t("dm.compute.agg_mean"):
                df[new_name] = df[items].mean(axis=1)
            else:
                df[new_name] = df[items].sum(axis=1)
            set_df(df, t("dm.compute.log", new=new_name, agg=agg, items=", ".join(items)))
            st.success(t("dm.compute.success", new=new_name))
            st.dataframe(df[items + [new_name]].head(10), width="stretch")

show_log()
render_footer()
