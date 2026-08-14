import numpy as np
import pandas as pd
import plotly.express as px
import statsmodels.api as sm
import streamlit as st
from scipy.stats import pearsonr, zscore
from statsmodels.stats.outliers_influence import variance_inflation_factor

from utils.state import get_df, require_data, numeric_columns
from utils.i18n import t
from utils.footer import render_footer
from utils.report import add_report_entry

st.title(f"📈 {t('nav.rel')}")
require_data()
df = get_df()

tab_corr, tab_reg = st.tabs([f"🔗 {t('ra.corr.tab')}", f"📐 {t('ra.reg.tab')}"])

# ----------------------------------------------------------------------------
# PEARSON CORRELATION
# ----------------------------------------------------------------------------
with tab_corr:
    st.caption(t("ra.corr.caption"))
    num_cols = numeric_columns(df)
    corr_vars = st.multiselect(t("common.select_vars"), num_cols, key="corr_vars")
    corr_add_report = st.checkbox(t("report.add_checkbox"), key="corr_add_report")

    if len(corr_vars) < 2:
        st.info(t("ra.corr.warn_min_vars"))
    elif st.button(t("ra.corr.run_btn"), key="btn_corr"):
        sub = df[corr_vars].dropna()
        corr = sub.corr(method="pearson")
        pvals = pd.DataFrame(np.zeros((len(corr_vars), len(corr_vars))), index=corr_vars, columns=corr_vars)
        for i in corr_vars:
            for j in corr_vars:
                if i != j:
                    _, p = pearsonr(sub[i], sub[j])
                    pvals.loc[i, j] = p

        st.markdown(f"##### {t('ra.corr.matrix_title')}")
        st.dataframe(
            corr.round(3).style.background_gradient(cmap="RdBu_r", vmin=-1, vmax=1),
            width="stretch",
        )
        st.markdown(f"##### {t('ra.corr.sig_title')}")
        st.dataframe(pvals.round(4), width="stretch")

        fig = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1, title=t("ra.corr.heatmap_title"))
        st.plotly_chart(fig, width="stretch")
        st.caption(t("ra.corr.convention"))

        if corr_add_report:
            add_report_entry(
                f"{t('ra.corr.tab')} — {', '.join(corr_vars)}",
                [("table", corr.round(3).reset_index().rename(columns={"index": ""})),
                 ("table", pvals.round(4).reset_index().rename(columns={"index": ""}))],
            )
            st.toast(t("report.added_toast"))

# ----------------------------------------------------------------------------
# LINEAR / MULTIPLE REGRESSION
# ----------------------------------------------------------------------------
with tab_reg:
    st.caption(t("ra.reg.caption"))
    num_cols = numeric_columns(df)
    dv = st.selectbox(t("ra.reg.dv"), num_cols, key="reg_dv")
    ivs = st.multiselect(t("ra.reg.ivs"), [c for c in num_cols if c != dv], key="reg_ivs")
    reg_add_report = st.checkbox(t("report.add_checkbox"), key="reg_add_report")

    if not ivs:
        st.info(t("ra.reg.warn_min_iv"))
    elif st.button(t("ra.reg.run_btn"), key="btn_reg"):
        sub = df[[dv] + ivs].dropna()
        if len(sub) < len(ivs) + 2:
            st.error(t("ra.reg.warn_too_few_obs"))
            st.stop()

        X = sm.add_constant(sub[ivs])
        y = sub[dv]
        model = sm.OLS(y, X).fit()

        st.markdown(f"##### {t('ra.reg.summary_title')}")
        summary_df = pd.DataFrame({
            "R": [np.sqrt(model.rsquared)],
            "R²": [model.rsquared],
            t("ra.reg.adj_r2"): [model.rsquared_adj],
            t("ra.reg.std_error"): [np.sqrt(model.mse_resid)],
        })
        st.dataframe(summary_df.round(3), width="stretch", hide_index=True)

        st.markdown(f"##### {t('ra.reg.anova_title')}")
        anova_df = pd.DataFrame({"F": [model.fvalue], "df1": [model.df_model], "df2": [model.df_resid], "Sig.": [model.f_pvalue]})
        st.dataframe(anova_df.round(4), width="stretch", hide_index=True)
        if model.f_pvalue < 0.05:
            st.success(t("ra.reg.model_fit_sig", p=f"{model.f_pvalue:.4f}"))
        else:
            st.warning(t("ra.reg.model_fit_nonsig", p=f"{model.f_pvalue:.4f}"))

        sub_z = sub.apply(zscore)
        Xz = sm.add_constant(sub_z[ivs])
        model_z = sm.OLS(sub_z[dv], Xz).fit()

        coef_df = pd.DataFrame({
            t("ra.reg.col_b"): model.params,
            t("ra.reg.col_std_err"): model.bse,
            t("ra.reg.col_beta"): model_z.params.reindex(model.params.index),
            "t": model.tvalues,
            "Sig.": model.pvalues,
        })

        vif_vals = pd.Series(
            [variance_inflation_factor(X.values, i) for i in range(X.shape[1])], index=X.columns
        )
        coef_df["VIF"] = vif_vals
        coef_df.loc["const", [t("ra.reg.col_beta"), "VIF"]] = np.nan
        coef_df = coef_df.rename(index={"const": t("ra.reg.constant")})

        st.markdown(f"##### {t('ra.reg.coef_title')}")
        st.dataframe(coef_df.round(3), width="stretch")

        sig_predictors = [i for i in ivs if model.pvalues[i] < 0.05]
        if sig_predictors:
            st.success(t("ra.reg.sig_predictors", dv=dv, vars=", ".join(sig_predictors)))
        else:
            st.info(t("ra.reg.no_sig_predictors"))

        high_vif = [i for i in ivs if vif_vals[i] > 10]
        if high_vif:
            st.warning(t("ra.reg.high_vif_warn", vars=", ".join(high_vif)))

        fig = px.scatter(
            x=model.fittedvalues, y=model.resid,
            labels={"x": t("ra.reg.fitted_axis"), "y": t("ra.reg.resid_axis")},
            title=t("ra.reg.resid_plot_title"),
        )
        fig.add_hline(y=0, line_dash="dash", line_color="red")
        st.plotly_chart(fig, width="stretch")

        if reg_add_report:
            add_report_entry(
                f"{t('ra.reg.tab')} — {dv} ~ {', '.join(ivs)}",
                [
                    ("table", summary_df.round(3)),
                    ("table", anova_df.round(4)),
                    ("table", coef_df.round(3).reset_index().rename(columns={"index": ""})),
                ],
            )
            st.toast(t("report.added_toast"))

render_footer()
