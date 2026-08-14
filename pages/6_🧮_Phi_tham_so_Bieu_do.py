import pandas as pd
import plotly.express as px
import streamlit as st
from scipy import stats

from utils.state import get_df, require_data, numeric_columns, all_columns, categorical_columns
from utils.i18n import t
from utils.footer import render_footer
from utils.report import add_report_entry

st.title(f"🧮 {t('nav.np')}")
require_data()
df = get_df()

tab_normal, tab_mw, tab_kw, tab_wilcoxon, tab_graph = st.tabs(
    [f"🔔 {t('np.normal.tab')}", f"👥 {t('np.mw.tab')}", f"📐 {t('np.kw.tab')}",
     f"🔗 {t('np.wilcoxon.tab')}", f"📉 {t('np.graph.tab')}"]
)

# ----------------------------------------------------------------------------
# NORMALITY CHECK
# ----------------------------------------------------------------------------
with tab_normal:
    st.caption(t("np.normal.caption"))
    var_n = st.selectbox(t("common.select_vars"), numeric_columns(df), key="normal_var")
    if st.button(t("np.normal.run_btn"), key="btn_shapiro"):
        s = df[var_n].dropna()
        if len(s) < 3:
            st.warning(t("ht.warn_not_enough_valid"))
        else:
            stat, p = stats.shapiro(s)
            st.write(f"**Shapiro-Wilk**: W = {stat:.4f}, p-value = {p:.4f}")
            if p < 0.05:
                st.warning(t("np.normal.nonnormal", p=f"{p:.4f}", var=var_n))
            else:
                st.success(t("np.normal.normal_ok", p=f"{p:.4f}"))
            fig = px.histogram(df, x=var_n, marginal="box", title=t("np.normal.chart_title", var=var_n))
            st.plotly_chart(fig, width="stretch")

# ----------------------------------------------------------------------------
# MANN-WHITNEY U
# ----------------------------------------------------------------------------
with tab_mw:
    st.caption(t("np.mw.caption"))
    group_var = st.selectbox(t("ht.group_var"), categorical_columns(df), key="mw_group_var")
    all_groups = df[group_var].dropna().unique().tolist()
    chosen_groups = st.multiselect(t("ht.choose_2_groups"), all_groups, default=all_groups[:2], key="mw_groups")
    test_vars = st.multiselect(t("ht.test_vars"), numeric_columns(df), key="mw_vars")
    mw_add_report = st.checkbox(t("report.add_checkbox"), key="mw_add_report")

    if len(chosen_groups) != 2:
        st.info(t("ht.info_choose_2"))
    elif st.button(t("np.mw.run_btn"), key="btn_mw"):
        g1_label, g2_label = chosen_groups
        for v in test_vars:
            g1 = df[df[group_var] == g1_label][v].dropna()
            g2 = df[df[group_var] == g2_label][v].dropna()
            if len(g1) < 1 or len(g2) < 1:
                st.warning(t("ht.warn_not_enough_data", var=v))
                continue
            u_stat, p_val = stats.mannwhitneyu(g1, g2, alternative="two-sided")
            st.markdown(f"##### {v}")
            rank_stats = pd.DataFrame({
                t("ht.col_group"): [str(g1_label), str(g2_label)],
                "N": [len(g1), len(g2)],
                t("np.mw.median"): [g1.median(), g2.median()],
                t("np.mw.mean_rank"): [
                    stats.rankdata(pd.concat([g1, g2]))[: len(g1)].mean(),
                    stats.rankdata(pd.concat([g1, g2]))[len(g1):].mean(),
                ],
            })
            st.dataframe(rank_stats, width="stretch", hide_index=True)
            st.write(f"**Mann-Whitney U** = {u_stat:.3f}, p-value = {p_val:.4f}")
            if p_val < 0.05:
                st.success(t("np.sig_diff_groups", p=f"{p_val:.4f}"))
            else:
                st.info(t("np.nonsig_diff_groups", p=f"{p_val:.4f}"))

            if mw_add_report:
                add_report_entry(
                    f"{t('np.mw.tab')} — {v} ({g1_label} vs {g2_label})",
                    [("table", rank_stats), ("text", f"Mann-Whitney U={u_stat:.3f}, p={p_val:.4f}")],
                )
        if mw_add_report and test_vars:
            st.toast(t("report.added_toast"))

# ----------------------------------------------------------------------------
# KRUSKAL-WALLIS
# ----------------------------------------------------------------------------
with tab_kw:
    st.caption(t("np.kw.caption"))
    factor_var = st.selectbox(t("ht.anova.factor_var"), categorical_columns(df), key="kw_factor")
    dep_var = st.selectbox(t("ht.anova.dep_var"), numeric_columns(df), key="kw_dep")
    kw_add_report = st.checkbox(t("report.add_checkbox"), key="kw_add_report")

    if st.button(t("np.kw.run_btn"), key="btn_kw"):
        sub = df[[factor_var, dep_var]].dropna()
        groups_data = [g[dep_var].values for _, g in sub.groupby(factor_var)]
        if len(groups_data) < 2:
            st.warning(t("ht.anova.warn_min_groups"))
        else:
            desc = sub.groupby(factor_var)[dep_var].agg(N="count", **{t("np.mw.median"): "median"}).round(3)
            st.dataframe(desc, width="stretch")
            h_stat, p_val = stats.kruskal(*groups_data)
            st.write(f"**Kruskal-Wallis H** = {h_stat:.3f}, p-value = {p_val:.4f}")
            if p_val < 0.05:
                st.success(t("np.kw.sig", p=f"{p_val:.4f}", var=factor_var))
            else:
                st.info(t("np.nonsig_diff_groups", p=f"{p_val:.4f}"))
            fig = px.box(sub, x=factor_var, y=dep_var, title=t("ht.anova.dep_var") + f" — {dep_var} / {factor_var}")
            st.plotly_chart(fig, width="stretch")

            if kw_add_report:
                add_report_entry(
                    f"{t('np.kw.tab')} — {dep_var} ~ {factor_var}",
                    [("table", desc.reset_index()), ("text", f"Kruskal-Wallis H={h_stat:.3f}, p={p_val:.4f}")],
                )
                st.toast(t("report.added_toast"))

# ----------------------------------------------------------------------------
# WILCOXON SIGNED-RANK
# ----------------------------------------------------------------------------
with tab_wilcoxon:
    st.caption(t("np.wilcoxon.caption"))
    num_cols = numeric_columns(df)
    c1, c2 = st.columns(2)
    var1 = c1.selectbox(t("ht.paired.var1"), num_cols, key="wil_var1")
    idx2 = 1 if len(num_cols) > 1 else 0
    var2 = c2.selectbox(t("ht.paired.var2"), num_cols, index=idx2, key="wil_var2")
    wil_add_report = st.checkbox(t("report.add_checkbox"), key="wil_add_report")

    if st.button(t("np.wilcoxon.run_btn"), key="btn_wilcoxon"):
        if var1 == var2:
            st.warning(t("ds.cross.warn_same_var"))
        else:
            paired = df[[var1, var2]].dropna()
            stat, p_val = stats.wilcoxon(paired[var1], paired[var2])
            st.write(f"N = {len(paired)}, Median({var1}) = {paired[var1].median():.3f}, Median({var2}) = {paired[var2].median():.3f}")
            st.write(f"**Wilcoxon Signed-Rank** statistic = {stat:.3f}, p-value = {p_val:.4f}")
            if p_val < 0.05:
                st.success(t("ht.sig_diff_2vars", p=f"{p_val:.4f}", var1=var1, var2=var2))
            else:
                st.info(t("ht.nonsig_diff_2vars", p=f"{p_val:.4f}", var1=var1, var2=var2))

            if wil_add_report:
                add_report_entry(
                    f"{t('np.wilcoxon.tab')} — {var1} vs {var2}",
                    [("text", f"N={len(paired)}, statistic={stat:.3f}, p={p_val:.4f}")],
                )
                st.toast(t("report.added_toast"))

# ----------------------------------------------------------------------------
# GRAPHS
# ----------------------------------------------------------------------------
with tab_graph:
    chart_options = [t("np.graph.hist"), t("np.graph.scatter"), t("np.graph.box"), t("np.graph.bar")]
    chart_type = st.selectbox(t("np.graph.type_label"), chart_options, key="graph_type")

    if chart_type == t("np.graph.hist"):
        var = st.selectbox(t("common.select_vars"), numeric_columns(df), key="hist_var")
        bins = st.slider(t("np.graph.bins"), 5, 50, 20, key="hist_bins")
        fig = px.histogram(df, x=var, nbins=bins, marginal="box", title=t("np.graph.hist_title", var=var))
        st.plotly_chart(fig, width="stretch")

    elif chart_type == t("np.graph.scatter"):
        num_cols = numeric_columns(df)
        c1, c2, c3 = st.columns(3)
        x = c1.selectbox(t("np.graph.x_axis"), num_cols, key="scatter_x")
        idx_y = 1 if len(num_cols) > 1 else 0
        y = c2.selectbox(t("np.graph.y_axis"), num_cols, index=idx_y, key="scatter_y")
        color_opt = c3.selectbox(t("np.graph.color_by"), [t("ds.cross.pct_none")] + all_columns(df), key="scatter_color")
        trendline = st.checkbox(t("np.graph.trendline"), key="scatter_trend")
        fig = px.scatter(
            df, x=x, y=y,
            color=None if color_opt == t("ds.cross.pct_none") else color_opt,
            trendline="ols" if trendline else None,
            title=t("np.graph.scatter_title", y=y, x=x),
        )
        st.plotly_chart(fig, width="stretch")

    elif chart_type == t("np.graph.box"):
        y = st.selectbox(t("common.select_vars"), numeric_columns(df), key="box_y")
        x_opt = st.selectbox(t("np.graph.group_by_optional"), [t("ds.cross.pct_none")] + categorical_columns(df), key="box_x")
        fig = px.box(df, x=None if x_opt == t("ds.cross.pct_none") else x_opt, y=y, points="outliers", title=t("np.graph.box_title", var=y))
        st.plotly_chart(fig, width="stretch")

    elif chart_type == t("np.graph.bar"):
        var = st.selectbox(t("common.select_vars"), categorical_columns(df), key="bar_var")
        vc = df[var].value_counts(dropna=True).reset_index()
        vc.columns = [var, t("ds.freq.col_freq")]
        fig = px.bar(vc, x=var, y=t("ds.freq.col_freq"), title=t("np.graph.bar_title", var=var))
        st.plotly_chart(fig, width="stretch")

render_footer()
