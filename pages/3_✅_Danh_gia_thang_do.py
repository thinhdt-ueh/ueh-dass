import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.state import get_df, require_data, numeric_columns
from utils.stats import cronbach_alpha, alpha_interpretation_key
from utils.i18n import t
from utils.footer import render_footer
from utils.report import add_report_entry

st.title(f"✅ {t('nav.scale')}")
require_data()
df = get_df()

tab_alpha, tab_efa = st.tabs([f"🎯 {t('sc.alpha.tab')}", f"🧩 {t('sc.efa.tab')}"])

# ----------------------------------------------------------------------------
# CRONBACH'S ALPHA
# ----------------------------------------------------------------------------
with tab_alpha:
    st.caption(t("sc.alpha.caption"))
    items = st.multiselect(t("sc.alpha.items_select"), numeric_columns(df), key="alpha_items")
    alpha_add_report = st.checkbox(t("report.add_checkbox"), key="alpha_add_report")

    if len(items) < 2:
        st.info(t("sc.alpha.warn_min_items"))
    elif st.button(t("sc.alpha.run_btn"), key="btn_alpha"):
        alpha, item_stats, n_obs = cronbach_alpha(df[items])
        item_stats = item_stats.rename(columns={
            "Biến": t("home.var_name"),
            "Tương quan biến-tổng hiệu chỉnh": t("sc.alpha.col_item_total_corr"),
            "Alpha nếu loại biến": t("sc.alpha.col_alpha_if_deleted"),
        })
        c1, c2 = st.columns([1, 3])
        c1.metric("Cronbach's Alpha", f"{alpha:.3f}")
        c1.caption(t("sc.alpha.n_caption", n=n_obs, k=len(items)))
        c1.info(t(alpha_interpretation_key(alpha)))

        st.markdown(f"##### {t('sc.alpha.item_stats_title')}")
        st.dataframe(item_stats.round(3), width="stretch", hide_index=True)

        weak_items = item_stats[item_stats[t("sc.alpha.col_item_total_corr")] < 0.3][t("home.var_name")].tolist()
        if weak_items:
            st.warning(t("sc.alpha.weak_items_warn", vars=", ".join(weak_items)))
        else:
            st.success(t("sc.alpha.all_good"))

        if alpha_add_report:
            add_report_entry(
                f"{t('sc.alpha.tab')} — {', '.join(items)}",
                [
                    ("text", f"Cronbach's Alpha = {alpha:.3f} (N={n_obs}, k={len(items)})"),
                    ("table", item_stats.round(3)),
                ],
            )
            st.toast(t("report.added_toast"))

# ----------------------------------------------------------------------------
# EFA
# ----------------------------------------------------------------------------
with tab_efa:
    st.caption(t("sc.efa.caption"))
    try:
        from factor_analyzer import FactorAnalyzer
        from factor_analyzer.factor_analyzer import calculate_kmo, calculate_bartlett_sphericity
    except ImportError:
        st.error(t("sc.efa.need_lib"))
        st.stop()

    items = st.multiselect(t("sc.efa.items_select"), numeric_columns(df), key="efa_items")

    c1, c2 = st.columns(2)
    rotation_options = ["varimax", "promax", "oblimin", "quartimax", t("sc.efa.no_rotation")]
    rotation_label = c1.selectbox(t("sc.efa.rotation_label"), rotation_options, key="efa_rotation")
    n_factor_mode_options = [t("sc.efa.mode_auto"), t("sc.efa.mode_manual")]
    n_factor_mode = c2.radio(t("sc.efa.n_factors_label"), n_factor_mode_options, key="efa_nfactor_mode")
    n_factor_manual = None
    if n_factor_mode == t("sc.efa.mode_manual"):
        n_factor_manual = st.number_input(t("sc.efa.n_factors_label"), min_value=1, max_value=max(len(items) - 1, 1), value=2, step=1)

    efa_add_report = st.checkbox(t("report.add_checkbox"), key="efa_add_report")

    if len(items) < 3:
        st.info(t("sc.efa.warn_min_items"))
    elif st.button(t("sc.efa.run_btn"), key="btn_efa"):
        data_efa = df[items].dropna()
        if len(data_efa) < len(items) + 2:
            st.error(t("sc.efa.warn_too_few_obs"))
            st.stop()

        kmo_all, kmo_model = calculate_kmo(data_efa)
        chi2_b, p_b = calculate_bartlett_sphericity(data_efa)

        st.markdown(f"##### {t('sc.efa.kmo_bartlett_title')}")
        k1, k2 = st.columns(2)
        k1.metric(t("sc.efa.kmo_metric"), f"{kmo_model:.3f}")
        k2.write(f"{t('sc.efa.bartlett_label')}: χ² = {chi2_b:.3f}, p-value = {p_b:.4f}")
        if kmo_model < 0.5:
            st.error(t("sc.efa.kmo_bad"))
        elif kmo_model < 0.6:
            st.warning(t("sc.efa.kmo_marginal"))
        else:
            st.success(t("sc.efa.kmo_good"))
        if p_b >= 0.05:
            st.warning(t("sc.efa.bartlett_nonsig"))

        fa_check = FactorAnalyzer(rotation=None)
        fa_check.fit(data_efa)
        ev, _ = fa_check.get_eigenvalues()

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=list(range(1, len(ev) + 1)), y=ev, mode="lines+markers", name="Eigenvalue"))
        fig.add_hline(y=1, line_dash="dash", line_color="red", annotation_text="Eigenvalue = 1")
        fig.update_layout(title=t("sc.efa.scree_title"), xaxis_title=t("sc.efa.factor_axis"), yaxis_title="Eigenvalue")
        st.plotly_chart(fig, width="stretch")

        if n_factor_mode == t("sc.efa.mode_auto"):
            n_factors = int((ev > 1).sum())
            n_factors = max(n_factors, 1)
            n_factors = min(n_factors, len(items) - 1)
        else:
            n_factors = int(n_factor_manual)

        rotation_param = None if rotation_label == t("sc.efa.no_rotation") else rotation_label
        fa = FactorAnalyzer(n_factors=n_factors, rotation=rotation_param)
        fa.fit(data_efa)

        factor_cols = [t("sc.efa.factor_col", i=i + 1) for i in range(n_factors)]
        loadings = pd.DataFrame(fa.loadings_, index=items, columns=factor_cols)
        st.markdown(f"##### {t('sc.efa.loadings_title', n=n_factors)}")

        def _highlight(v):
            return "font-weight: bold; color: #d62728" if abs(v) >= 0.5 else ""

        st.dataframe(loadings.style.format("{:.3f}").map(_highlight), width="stretch")

        communalities = pd.Series(fa.get_communalities(), index=items, name="Communality")
        st.markdown(f"##### {t('sc.efa.communalities_title')}")
        st.dataframe(communalities.round(3).to_frame(), width="stretch")

        var_expl = fa.get_factor_variance()
        var_df = pd.DataFrame(
            var_expl,
            index=[t("sc.efa.row_eigenvalue"), t("sc.efa.row_var_explained"), t("sc.efa.row_cum_var")],
            columns=factor_cols,
        )
        var_df.loc[[t("sc.efa.row_var_explained"), t("sc.efa.row_cum_var")]] *= 100
        st.markdown(f"##### {t('sc.efa.variance_title')}")
        st.dataframe(var_df.round(3), width="stretch")

        total_var = var_df.loc[t("sc.efa.row_cum_var")].iloc[-1]
        if total_var >= 50:
            st.success(t("sc.efa.variance_ok", pct=f"{total_var:.1f}"))
        else:
            st.warning(t("sc.efa.variance_low", pct=f"{total_var:.1f}"))

        if efa_add_report:
            add_report_entry(
                f"{t('sc.efa.tab')} — {', '.join(items)}",
                [
                    ("text", f"KMO = {kmo_model:.3f}; Bartlett's χ² = {chi2_b:.3f}, p = {p_b:.4f}; {n_factors} factor(s)"),
                    ("table", loadings.round(3).reset_index().rename(columns={"index": t("home.var_name")})),
                    ("table", communalities.round(3).to_frame().reset_index().rename(columns={"index": t("home.var_name")})),
                    ("table", var_df.round(3).reset_index().rename(columns={"index": ""})),
                ],
            )
            st.toast(t("report.added_toast"))

render_footer()
