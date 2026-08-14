import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from scipy.stats import chi2_contingency, chisquare

from utils.state import get_df, require_data, numeric_columns, all_columns, categorical_columns
from utils.i18n import t
from utils.footer import render_footer
from utils.report import add_report_entry

st.title(f"📊 {t('nav.desc')}")
require_data()
df = get_df()

tab_freq, tab_desc, tab_cross, tab_gof = st.tabs(
    [f"🔢 {t('ds.freq.tab')}", f"📈 {t('ds.desc.tab')}", f"🔀 {t('ds.cross.tab')}", f"🎯 {t('ds.gof.tab')}"]
)

# ----------------------------------------------------------------------------
# FREQUENCIES
# ----------------------------------------------------------------------------
with tab_freq:
    st.caption(t("ds.freq.caption"))
    freq_vars = st.multiselect(t("common.select_vars"), all_columns(df), key="freq_vars")
    for v in freq_vars:
        st.markdown(f"##### {v}")
        s = df[v]
        vc = s.value_counts(dropna=True).sort_index()
        n_total = len(s)
        n_valid = int(vc.sum())
        n_missing = n_total - n_valid

        c_val, c_freq, c_pct, c_vpct, c_cum = (
            t("ds.freq.col_value"), t("ds.freq.col_freq"), t("ds.freq.col_pct"),
            t("ds.freq.col_valid_pct"), t("ds.freq.col_cum_pct"),
        )
        rows = []
        cum = 0.0
        for val, cnt in vc.items():
            pct = cnt / n_total * 100
            valid_pct = cnt / n_valid * 100 if n_valid > 0 else 0
            cum += valid_pct
            rows.append({
                c_val: val, c_freq: int(cnt),
                c_pct: round(pct, 1), c_vpct: round(valid_pct, 1), c_cum: round(cum, 1),
            })
        if n_missing > 0:
            rows.append({
                c_val: t("ds.freq.missing_row"), c_freq: int(n_missing),
                c_pct: round(n_missing / n_total * 100, 1), c_vpct: "-", c_cum: "-",
            })
        rows.append({
            c_val: t("common.total"), c_freq: n_total, c_pct: 100.0, c_vpct: "-", c_cum: "-",
        })
        freq_table = pd.DataFrame(rows)
        c1, c2 = st.columns([2, 3])
        c1.dataframe(freq_table, width="stretch", hide_index=True)
        chart_df = vc.reset_index()
        chart_df.columns = [v, c_freq]
        fig = px.bar(chart_df, x=v, y=c_freq, title=t("ds.freq.chart_title", var=v))
        c2.plotly_chart(fig, width="stretch")

        if st.button(t("report.add_btn"), key=f"report_freq_{v}"):
            add_report_entry(f"{t('ds.freq.tab')} — {v}", [("table", freq_table)])
            st.toast(t("report.added_toast"))

# ----------------------------------------------------------------------------
# DESCRIPTIVES
# ----------------------------------------------------------------------------
with tab_desc:
    st.caption(t("ds.desc.caption"))
    num_cols = numeric_columns(df)
    desc_vars = st.multiselect(t("common.select_vars"), num_cols, default=num_cols[: min(5, len(num_cols))], key="desc_vars")
    if desc_vars:
        rows = []
        for v in desc_vars:
            s = df[v].dropna()
            rows.append({
                t("home.var_name"): v, "N": int(s.count()),
                t("ds.desc.min"): s.min(), t("ds.desc.max"): s.max(),
                t("ds.desc.mean"): round(s.mean(), 3),
                t("ds.desc.std"): round(s.std(), 3),
                t("ds.desc.var"): round(s.var(), 3),
                t("ds.desc.skew"): round(s.skew(), 3),
                t("ds.desc.kurt"): round(s.kurt(), 3),
            })
        desc_table = pd.DataFrame(rows)
        st.dataframe(desc_table, width="stretch", hide_index=True)

        if st.button(t("report.add_btn"), key="report_desc"):
            add_report_entry(t("ds.desc.tab"), [("table", desc_table)])
            st.toast(t("report.added_toast"))

# ----------------------------------------------------------------------------
# CROSSTABS
# ----------------------------------------------------------------------------
with tab_cross:
    st.caption(t("ds.cross.caption"))
    cat_cols = all_columns(df)
    c1, c2 = st.columns(2)
    row_var = c1.selectbox(t("ds.cross.row_var"), cat_cols, key="cross_row")
    default_col_idx = 1 if len(cat_cols) > 1 else 0
    col_var = c2.selectbox(t("ds.cross.col_var"), cat_cols, index=default_col_idx, key="cross_col")
    pct_options = [t("ds.cross.pct_none"), t("ds.cross.pct_row"), t("ds.cross.pct_col"), t("ds.cross.pct_total")]
    pct_option = st.radio(t("ds.cross.pct_label"), pct_options, horizontal=True)
    cross_add_report = st.checkbox(t("report.add_checkbox"), key="cross_add_report")
    if st.button(t("ds.cross.run_btn"), key="btn_crosstab"):
        if row_var == col_var:
            st.warning(t("ds.cross.warn_same_var"))
        else:
            sub = df[[row_var, col_var]].dropna()
            ct = pd.crosstab(sub[row_var], sub[col_var])
            st.markdown(f"##### {t('ds.cross.counts_title')}")
            st.dataframe(ct, width="stretch")

            ct_pct = None
            if pct_option != t("ds.cross.pct_none"):
                normalize = {
                    t("ds.cross.pct_row"): "index",
                    t("ds.cross.pct_col"): "columns",
                    t("ds.cross.pct_total"): "all",
                }[pct_option]
                ct_pct = pd.crosstab(sub[row_var], sub[col_var], normalize=normalize) * 100
                st.markdown(f"##### {t('ds.cross.pct_title', option=pct_option)}")
                st.dataframe(ct_pct.round(1), width="stretch")

            chi2, p, dof, expected = chi2_contingency(ct)
            st.markdown(f"##### {t('ds.cross.chi2_title')}")
            st.write(f"χ² = {chi2:.3f}, df = {dof}, p-value = {p:.4f}")
            if p < 0.05:
                st.success(t("ds.cross.chi2_sig", p=f"{p:.4f}", row=row_var, col=col_var))
            else:
                st.info(t("ds.cross.chi2_nonsig", p=f"{p:.4f}", row=row_var, col=col_var))

            n = ct.to_numpy().sum()
            r, k = ct.shape
            phi2 = chi2 / n
            cramers_v = float(np.sqrt(phi2 / (min(r - 1, k - 1)))) if min(r - 1, k - 1) > 0 else np.nan
            st.markdown(f"##### {t('ds.cross.assoc_title')}")
            assoc_rows = [{"": t("ds.cross.cramers_v"), "Value": round(cramers_v, 3)}]
            if r == 2 and k == 2:
                phi = float(np.sqrt(phi2))
                assoc_rows.insert(0, {"": t("ds.cross.phi"), "Value": round(phi, 3)})
            assoc_table = pd.DataFrame(assoc_rows)
            st.dataframe(assoc_table, width="stretch", hide_index=True)

            fig = px.bar(
                ct.reset_index(), x=row_var, y=ct.columns.tolist(), barmode="group",
                title=t("ds.cross.chart_title", row=row_var, col=col_var),
            )
            st.plotly_chart(fig, width="stretch")

            if cross_add_report:
                blocks = [("table", ct.reset_index())]
                if ct_pct is not None:
                    blocks.append(("table", ct_pct.round(1).reset_index()))
                blocks.append(("text", f"Chi-square: χ²={chi2:.3f}, df={dof}, p={p:.4f}"))
                blocks.append(("table", assoc_table))
                add_report_entry(f"{t('ds.cross.tab')} — {row_var} × {col_var}", blocks)
                st.toast(t("report.added_toast"))

# ----------------------------------------------------------------------------
# CHI-SQUARE GOODNESS-OF-FIT
# ----------------------------------------------------------------------------
with tab_gof:
    st.caption(t("ds.gof.caption"))
    gof_var = st.selectbox(t("ds.gof.var_select"), categorical_columns(df), key="gof_var")
    expected_mode = st.radio(
        t("ds.gof.expected_mode"), [t("ds.gof.expected_equal"), t("ds.gof.expected_custom")], horizontal=True
    )

    vc = df[gof_var].dropna().value_counts().sort_index()
    categories = vc.index.tolist()
    observed = vc.values

    custom_props = None
    if expected_mode == t("ds.gof.expected_custom"):
        st.caption(t("ds.gof.custom_hint"))
        default_props = pd.DataFrame({
            t("ds.gof.col_category"): categories,
            t("ds.gof.col_expected_pct"): [round(100 / len(categories), 2)] * len(categories),
        })
        edited_props = st.data_editor(default_props, num_rows="fixed", width="stretch", key="gof_props_editor")
        custom_props = edited_props[t("ds.gof.col_expected_pct")].astype(float).values

    gof_add_report = st.checkbox(t("report.add_checkbox"), key="gof_add_report")
    if st.button(t("ds.gof.run_btn"), key="btn_gof"):
        n_total = observed.sum()
        if custom_props is not None:
            weights = custom_props / custom_props.sum()
        else:
            weights = np.ones(len(categories)) / len(categories)
        expected_counts = weights * n_total

        chi2_stat, p_val = chisquare(f_obs=observed, f_exp=expected_counts)

        gof_table = pd.DataFrame({
            t("ds.gof.col_category"): categories,
            t("ds.gof.col_observed"): observed,
            t("ds.gof.col_expected"): np.round(expected_counts, 2),
        })
        st.markdown(f"##### {t('ds.gof.result_title')}")
        st.dataframe(gof_table, width="stretch", hide_index=True)
        st.write(f"χ² = {chi2_stat:.3f}, df = {len(categories) - 1}, p-value = {p_val:.4f}")
        if p_val < 0.05:
            st.success(t("ds.gof.sig", p=f"{p_val:.4f}"))
        else:
            st.info(t("ds.gof.nonsig", p=f"{p_val:.4f}"))

        fig = px.bar(gof_table, x=t("ds.gof.col_category"), y=[t("ds.gof.col_observed"), t("ds.gof.col_expected")], barmode="group")
        st.plotly_chart(fig, width="stretch")

        if gof_add_report:
            add_report_entry(
                f"{t('ds.gof.tab')} — {gof_var}",
                [("table", gof_table), ("text", f"χ²={chi2_stat:.3f}, df={len(categories)-1}, p={p_val:.4f}")],
            )
            st.toast(t("report.added_toast"))

render_footer()
