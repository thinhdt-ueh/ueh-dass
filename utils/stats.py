"""Statistical helper functions shared across pages."""
import numpy as np
import pandas as pd
from scipy import stats as _stats


def cronbach_alpha(df_items: pd.DataFrame):
    """Return (alpha, item_stats_df, n_obs) for a set of Likert-type items."""
    data = df_items.dropna()
    k = data.shape[1]
    item_vars = data.var(axis=0, ddof=1)
    total_var = data.sum(axis=1).var(ddof=1)
    alpha = (k / (k - 1)) * (1 - item_vars.sum() / total_var)

    total_score = data.sum(axis=1)
    rows = []
    for col in data.columns:
        rest = total_score - data[col]
        corr = data[col].corr(rest)

        remaining = data.drop(columns=[col])
        k2 = remaining.shape[1]
        if k2 > 1:
            r_vars = remaining.var(axis=0, ddof=1)
            r_total_var = remaining.sum(axis=1).var(ddof=1)
            alpha_deleted = (k2 / (k2 - 1)) * (1 - r_vars.sum() / r_total_var)
        else:
            alpha_deleted = np.nan

        rows.append({
            "Biến": col,
            "Tương quan biến-tổng hiệu chỉnh": corr,
            "Alpha nếu loại biến": alpha_deleted,
        })

    item_stats = pd.DataFrame(rows)
    return alpha, item_stats, data.shape[0]


def independent_ttest_effects(g1: pd.Series, g2: pd.Series, equal_var: bool, alpha: float = 0.05):
    """Cohen's d and CI for the mean difference of an independent-samples t-test."""
    n1, n2 = len(g1), len(g2)
    m1, m2 = g1.mean(), g2.mean()
    s1, s2 = g1.std(ddof=1), g2.std(ddof=1)
    mean_diff = m1 - m2

    pooled_sd = np.sqrt(((n1 - 1) * s1 ** 2 + (n2 - 1) * s2 ** 2) / (n1 + n2 - 2))
    cohen_d = mean_diff / pooled_sd if pooled_sd > 0 else np.nan

    if equal_var:
        df = n1 + n2 - 2
        se = pooled_sd * np.sqrt(1 / n1 + 1 / n2)
    else:
        se = np.sqrt(s1 ** 2 / n1 + s2 ** 2 / n2)
        df = (s1 ** 2 / n1 + s2 ** 2 / n2) ** 2 / (
            (s1 ** 2 / n1) ** 2 / (n1 - 1) + (s2 ** 2 / n2) ** 2 / (n2 - 1)
        )

    t_crit = _stats.t.ppf(1 - alpha / 2, df)
    ci_low = mean_diff - t_crit * se
    ci_high = mean_diff + t_crit * se
    return {"cohen_d": cohen_d, "se": se, "df": df, "ci_low": ci_low, "ci_high": ci_high}


def paired_ttest_effects(diff: pd.Series, alpha: float = 0.05):
    """Cohen's dz and CI for the mean difference of a paired-samples t-test."""
    n = len(diff)
    mean_diff = diff.mean()
    sd_diff = diff.std(ddof=1)
    cohen_dz = mean_diff / sd_diff if sd_diff > 0 else np.nan
    se = sd_diff / np.sqrt(n)
    df = n - 1
    t_crit = _stats.t.ppf(1 - alpha / 2, df)
    ci_low = mean_diff - t_crit * se
    ci_high = mean_diff + t_crit * se
    return {"cohen_dz": cohen_dz, "se": se, "df": df, "ci_low": ci_low, "ci_high": ci_high}


def anova_effect_sizes(groups_data):
    """Eta-squared and omega-squared for a one-way ANOVA given a list of group arrays."""
    all_vals = np.concatenate(groups_data)
    grand_mean = all_vals.mean()
    k = len(groups_data)
    n_total = len(all_vals)

    ss_between = sum(len(g) * (np.mean(g) - grand_mean) ** 2 for g in groups_data)
    ss_total = sum((all_vals - grand_mean) ** 2)
    ss_within = ss_total - ss_between

    eta_sq = ss_between / ss_total if ss_total > 0 else np.nan
    ms_within = ss_within / (n_total - k) if n_total > k else np.nan
    omega_sq = (
        (ss_between - (k - 1) * ms_within) / (ss_total + ms_within)
        if ss_total + ms_within > 0 else np.nan
    )
    return {"eta_sq": eta_sq, "omega_sq": omega_sq}


def cohen_d_interpretation_key(d: float) -> str:
    d = abs(d)
    if d < 0.2:
        return "effect.d.negligible"
    if d < 0.5:
        return "effect.d.small"
    if d < 0.8:
        return "effect.d.medium"
    return "effect.d.large"


def eta_sq_interpretation_key(eta_sq: float) -> str:
    if eta_sq < 0.01:
        return "effect.eta.negligible"
    if eta_sq < 0.06:
        return "effect.eta.small"
    if eta_sq < 0.14:
        return "effect.eta.medium"
    return "effect.eta.large"


def alpha_interpretation_key(alpha: float) -> str:
    """Return an i18n key suffix describing the Cronbach's Alpha quality band."""
    if alpha >= 0.9:
        return "sc.alpha.interp.excellent"
    if alpha >= 0.8:
        return "sc.alpha.interp.good"
    if alpha >= 0.7:
        return "sc.alpha.interp.acceptable"
    if alpha >= 0.6:
        return "sc.alpha.interp.questionable"
    return "sc.alpha.interp.poor"
