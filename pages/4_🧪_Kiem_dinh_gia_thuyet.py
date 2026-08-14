import pandas as pd
import streamlit as st
from scipy import stats
import statsmodels.formula.api as smf
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multicomp import pairwise_tukeyhsd

from utils.state import get_df, require_data, numeric_columns, categorical_columns
from utils.i18n import t
from utils.footer import render_footer
from utils.report import add_report_entry
from utils.stats import (
    independent_ttest_effects, paired_ttest_effects, anova_effect_sizes,
    cohen_d_interpretation_key, eta_sq_interpretation_key,
)

st.title(f"🧪 {t('nav.hyp')}")
require_data()
df = get_df()

tab_ind, tab_paired, tab_anova, tab_twoway = st.tabs(
    [f"👥 {t('ht.ind.tab')}", f"🔗 {t('ht.paired.tab')}", f"📐 {t('ht.anova.tab')}", f"📊 {t('ht.twoway.tab')}"]
)

# ----------------------------------------------------------------------------
# INDEPENDENT T-TEST
# ----------------------------------------------------------------------------
with tab_ind:
    st.caption(t("ht.ind.caption"))
    group_var = st.selectbox(t("ht.group_var"), categorical_columns(df), key="ind_group_var")
    all_groups = df[group_var].dropna().unique().tolist()

    if len(all_groups) < 2:
        st.warning(t("ht.warn_min_groups", var=group_var, n=len(all_groups)))
    else:
        chosen_groups = st.multiselect(t("ht.choose_2_groups"), all_groups, default=all_groups[:2], key="ind_chosen_groups")
        test_vars = st.multiselect(t("ht.test_vars"), numeric_columns(df), key="ind_test_vars")
        ind_add_report = st.checkbox(t("report.add_checkbox"), key="ind_add_report")

        if len(chosen_groups) != 2:
            st.info(t("ht.info_choose_2"))
        elif st.button(t("ht.ind.run_btn"), key="btn_ind_ttest"):
            g1_label, g2_label = chosen_groups
            for v in test_vars:
                g1 = df[df[group_var] == g1_label][v].dropna()
                g2 = df[df[group_var] == g2_label][v].dropna()
                if len(g1) < 2 or len(g2) < 2:
                    st.warning(t("ht.warn_not_enough_data", var=v))
                    continue

                levene_stat, levene_p = stats.levene(g1, g2)
                equal_var = levene_p > 0.05
                t_stat, p_val = stats.ttest_ind(g1, g2, equal_var=equal_var)
                mean_diff = g1.mean() - g2.mean()
                eff = independent_ttest_effects(g1, g2, equal_var)

                st.markdown(f"##### {v}")
                grp_stats = pd.DataFrame({
                    t("ht.col_group"): [str(g1_label), str(g2_label)],
                    "N": [len(g1), len(g2)],
                    "Mean": [round(g1.mean(), 3), round(g2.mean(), 3)],
                    t("ds.desc.std"): [round(g1.std(), 3), round(g2.std(), 3)],
                })
                c1, c2 = st.columns([1, 2])
                c1.dataframe(grp_stats, width="stretch", hide_index=True)

                with c2:
                    equal_note = t("ht.equal_var_yes") if equal_var else t("ht.equal_var_no")
                    st.write(f"**{t('ht.levene_label')}**: F = {levene_stat:.3f}, p = {levene_p:.4f} → {equal_note}")
                    st.write(f"**{t('ht.ttest_label')}**: t = {t_stat:.3f}, {t('ht.p_2tailed')} = {p_val:.4f}, {t('ht.mean_diff')} = {mean_diff:.3f}")
                    st.write(f"**{t('effect.cohen_d')}** = {eff['cohen_d']:.3f} ({t(cohen_d_interpretation_key(eff['cohen_d']))})")
                    st.write(f"**{t('effect.ci_mean_diff')}**: [{eff['ci_low']:.3f}, {eff['ci_high']:.3f}]")
                    if p_val < 0.05:
                        st.success(t("ht.sig_diff_2groups", p=f"{p_val:.4f}", var=v))
                    else:
                        st.info(t("ht.nonsig_diff_2groups", p=f"{p_val:.4f}", var=v))

                if ind_add_report:
                    add_report_entry(
                        f"{t('ht.ind.tab')} — {v} ({g1_label} vs {g2_label})",
                        [
                            ("table", grp_stats),
                            ("text", f"Levene F={levene_stat:.3f}, p={levene_p:.4f}; t={t_stat:.3f}, p={p_val:.4f}, "
                                     f"mean diff={mean_diff:.3f}; Cohen's d={eff['cohen_d']:.3f}; "
                                     f"95% CI=[{eff['ci_low']:.3f}, {eff['ci_high']:.3f}]"),
                        ],
                    )
            if ind_add_report and test_vars:
                st.toast(t("report.added_toast"))

# ----------------------------------------------------------------------------
# PAIRED T-TEST
# ----------------------------------------------------------------------------
with tab_paired:
    st.caption(t("ht.paired.caption"))
    num_cols = numeric_columns(df)
    c1, c2 = st.columns(2)
    var1 = c1.selectbox(t("ht.paired.var1"), num_cols, key="paired_var1")
    idx2 = 1 if len(num_cols) > 1 else 0
    var2 = c2.selectbox(t("ht.paired.var2"), num_cols, index=idx2, key="paired_var2")
    paired_add_report = st.checkbox(t("report.add_checkbox"), key="paired_add_report")

    if st.button(t("ht.paired.run_btn"), key="btn_paired_ttest"):
        if var1 == var2:
            st.warning(t("ds.cross.warn_same_var"))
        else:
            paired = df[[var1, var2]].dropna()
            if len(paired) < 2:
                st.warning(t("ht.warn_not_enough_valid"))
            else:
                t_stat, p_val = stats.ttest_rel(paired[var1], paired[var2])
                diff = paired[var1] - paired[var2]
                eff = paired_ttest_effects(diff)

                summary = pd.DataFrame({
                    t("home.var_name"): [var1, var2, t("ht.paired.diff_row")],
                    "N": [len(paired)] * 3,
                    "Mean": [round(paired[var1].mean(), 3), round(paired[var2].mean(), 3), round(diff.mean(), 3)],
                    t("ds.desc.std"): [round(paired[var1].std(), 3), round(paired[var2].std(), 3), round(diff.std(), 3)],
                })
                st.dataframe(summary, width="stretch", hide_index=True)
                st.write(f"**{t('ht.paired.result_label')}**: t = {t_stat:.3f}, df = {len(paired) - 1}, {t('ht.p_2tailed')} = {p_val:.4f}")
                st.write(f"**{t('effect.cohen_dz')}** = {eff['cohen_dz']:.3f} ({t(cohen_d_interpretation_key(eff['cohen_dz']))})")
                st.write(f"**{t('effect.ci_mean_diff')}**: [{eff['ci_low']:.3f}, {eff['ci_high']:.3f}]")
                if p_val < 0.05:
                    st.success(t("ht.sig_diff_2vars", p=f"{p_val:.4f}", var1=var1, var2=var2))
                else:
                    st.info(t("ht.nonsig_diff_2vars", p=f"{p_val:.4f}", var1=var1, var2=var2))

                if paired_add_report:
                    add_report_entry(
                        f"{t('ht.paired.tab')} — {var1} vs {var2}",
                        [
                            ("table", summary),
                            ("text", f"t={t_stat:.3f}, df={len(paired)-1}, p={p_val:.4f}; Cohen's dz={eff['cohen_dz']:.3f}; "
                                     f"95% CI=[{eff['ci_low']:.3f}, {eff['ci_high']:.3f}]"),
                        ],
                    )
                    st.toast(t("report.added_toast"))

# ----------------------------------------------------------------------------
# ONE-WAY ANOVA
# ----------------------------------------------------------------------------
with tab_anova:
    st.caption(t("ht.anova.caption"))
    factor_var = st.selectbox(t("ht.anova.factor_var"), categorical_columns(df), key="anova_factor")
    dep_var = st.selectbox(t("ht.anova.dep_var"), numeric_columns(df), key="anova_dep")
    run_posthoc = st.checkbox(t("ht.anova.posthoc_check"), value=True)
    anova_add_report = st.checkbox(t("report.add_checkbox"), key="anova_add_report")

    if st.button(t("ht.anova.run_btn"), key="btn_anova"):
        sub = df[[factor_var, dep_var]].dropna()
        n_groups = sub[factor_var].nunique()
        if n_groups < 2:
            st.warning(t("ht.anova.warn_min_groups"))
        else:
            groups_data = [g[dep_var].values for _, g in sub.groupby(factor_var)]
            desc = sub.groupby(factor_var)[dep_var].agg(N="count", Mean="mean", **{t("ds.desc.std"): "std"}).round(3)
            st.markdown(f"##### {t('ht.anova.desc_title')}")
            st.dataframe(desc, width="stretch")

            levene_stat, levene_p = stats.levene(*groups_data)
            st.write(f"**{t('ht.anova.homogeneity_label')}**: F = {levene_stat:.3f}, p = {levene_p:.4f}")

            f_stat, p_val = stats.f_oneway(*groups_data)
            eff = anova_effect_sizes(groups_data)
            st.write(f"**ANOVA**: F = {f_stat:.3f}, p-value = {p_val:.4f}")
            st.write(
                f"**{t('effect.eta_sq')}** = {eff['eta_sq']:.3f} ({t(eta_sq_interpretation_key(eff['eta_sq']))}) · "
                f"**{t('effect.omega_sq')}** = {eff['omega_sq']:.3f}"
            )
            if p_val < 0.05:
                st.success(t("ht.anova.sig", p=f"{p_val:.4f}", var=factor_var, dep=dep_var))
            else:
                st.info(t("ht.anova.nonsig", p=f"{p_val:.4f}"))

            tukey_df = None
            if run_posthoc and p_val < 0.05 and n_groups >= 3:
                st.markdown(f"##### {t('ht.anova.posthoc_title')}")
                tukey = pairwise_tukeyhsd(sub[dep_var], sub[factor_var])
                tukey_df = pd.DataFrame(tukey._results_table.data[1:], columns=tukey._results_table.data[0])
                st.dataframe(tukey_df, width="stretch", hide_index=True)

            if anova_add_report:
                blocks = [
                    ("table", desc.reset_index()),
                    ("text", f"Levene F={levene_stat:.3f}, p={levene_p:.4f}; ANOVA F={f_stat:.3f}, p={p_val:.4f}; "
                             f"eta²={eff['eta_sq']:.3f}, omega²={eff['omega_sq']:.3f}"),
                ]
                if tukey_df is not None:
                    blocks.append(("table", tukey_df))
                add_report_entry(f"{t('ht.anova.tab')} — {dep_var} ~ {factor_var}", blocks)
                st.toast(t("report.added_toast"))

# ----------------------------------------------------------------------------
# TWO-WAY ANOVA
# ----------------------------------------------------------------------------
with tab_twoway:
    st.caption(t("ht.twoway.caption"))
    cat_cols = categorical_columns(df)
    c1, c2, c3 = st.columns(3)
    tw_factor1 = c1.selectbox(t("ht.twoway.factor1"), cat_cols, key="tw_factor1")
    idx2 = 1 if len(cat_cols) > 1 else 0
    tw_factor2 = c2.selectbox(t("ht.twoway.factor2"), cat_cols, index=idx2, key="tw_factor2")
    tw_dep = c3.selectbox(t("ht.anova.dep_var"), numeric_columns(df), key="tw_dep")
    tw_add_report = st.checkbox(t("report.add_checkbox"), key="tw_add_report")

    if st.button(t("ht.twoway.run_btn"), key="btn_twoway"):
        if tw_factor1 == tw_factor2:
            st.warning(t("ht.twoway.warn_same_var"))
        else:
            sub = df[[tw_factor1, tw_factor2, tw_dep]].dropna().copy()
            sub.columns = ["F1", "F2", "DEP"]
            model = smf.ols("DEP ~ C(F1) * C(F2)", data=sub).fit()
            aov = anova_lm(model, typ=2)

            source_labels = {
                "C(F1)": tw_factor1,
                "C(F2)": tw_factor2,
                "C(F1):C(F2)": t("ht.twoway.row_interaction", f1=tw_factor1, f2=tw_factor2),
                "Residual": t("ht.twoway.row_residual"),
            }
            aov_display = aov.rename(index=source_labels).reset_index().rename(
                columns={"index": t("ht.twoway.col_source"), "sum_sq": "Sum Sq", "df": "df", "F": "F", "PR(>F)": "Sig."}
            )
            st.markdown(f"##### {t('ht.twoway.table_title')}")
            st.dataframe(aov_display.round(4), width="stretch", hide_index=True)

            for src, effect_label in [
                ("C(F1)", tw_factor1),
                ("C(F2)", tw_factor2),
                ("C(F1):C(F2)", t("ht.twoway.interaction_label", f1=tw_factor1, f2=tw_factor2)),
            ]:
                p_eff = aov.loc[src, "PR(>F)"]
                if p_eff < 0.05:
                    st.success(t("ht.twoway.effect_sig", effect=effect_label, dep=tw_dep, p=f"{p_eff:.4f}"))
                else:
                    st.info(t("ht.twoway.effect_nonsig", effect=effect_label, dep=tw_dep, p=f"{p_eff:.4f}"))

            if tw_add_report:
                add_report_entry(
                    f"{t('ht.twoway.tab')} — {tw_dep} ~ {tw_factor1} × {tw_factor2}",
                    [("table", aov_display.round(4))],
                )
                st.toast(t("report.added_toast"))

render_footer()
