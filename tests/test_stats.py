import numpy as np
import pandas as pd
import pytest

from utils.stats import (
    alpha_interpretation_key,
    anova_effect_sizes,
    cohen_d_interpretation_key,
    cr_ave,
    cronbach_alpha,
    eta_sq_interpretation_key,
    independent_ttest_effects,
    paired_ttest_effects,
)


def test_cronbach_alpha_high_for_near_identical_items():
    rng = np.random.default_rng(0)
    base = rng.normal(size=200)
    df = pd.DataFrame({f"item{i}": base + rng.normal(scale=0.01, size=200) for i in range(4)})
    alpha, item_stats, n = cronbach_alpha(df)
    assert alpha > 0.95
    assert n == 200
    assert set(item_stats["Biến"]) == set(df.columns)


def test_cronbach_alpha_low_for_uncorrelated_items():
    rng = np.random.default_rng(0)
    df = pd.DataFrame({f"item{i}": rng.integers(1, 8, size=200) for i in range(4)})
    alpha, _, _ = cronbach_alpha(df)
    assert alpha < 0.5


def test_cr_ave_known_values():
    # 3 equal standardized loadings of 0.8: AVE = mean(0.8^2) = 0.64
    # CR = (sum_loadings)^2 / [(sum_loadings)^2 + sum(1 - loadings^2)]
    cr, ave = cr_ave([0.8, 0.8, 0.8])
    assert ave == pytest.approx(0.64, abs=1e-9)
    assert cr == pytest.approx((2.4 ** 2) / (2.4 ** 2 + 3 * 0.36), abs=1e-9)


def test_cr_ave_higher_loadings_give_higher_cr_and_ave():
    cr_low, ave_low = cr_ave([0.5, 0.5, 0.5])
    cr_high, ave_high = cr_ave([0.9, 0.9, 0.9])
    assert ave_high > ave_low
    assert cr_high > cr_low


def test_independent_ttest_effects_shape():
    rng = np.random.default_rng(1)
    g1 = pd.Series(rng.normal(0, 1, 100))
    g2 = pd.Series(rng.normal(2, 1, 100))
    result = independent_ttest_effects(g1, g2, equal_var=True)
    assert result["cohen_d"] < -1.0  # g1 mean is well below g2 mean
    assert result["ci_low"] < result["ci_high"]


def test_paired_ttest_effects_positive_shift():
    rng = np.random.default_rng(2)
    diff = pd.Series(rng.normal(0.5, 1, 200))
    result = paired_ttest_effects(diff)
    assert result["cohen_dz"] > 0
    assert result["ci_low"] < result["ci_high"]


def test_anova_effect_sizes_near_zero_when_groups_equal():
    rng = np.random.default_rng(3)
    groups = [rng.normal(0, 1, 80) for _ in range(3)]
    result = anova_effect_sizes(groups)
    assert 0 <= result["eta_sq"] < 0.05


def test_anova_effect_sizes_large_when_groups_differ():
    groups = [np.full(50, 0.0), np.full(50, 5.0), np.full(50, 10.0)]
    result = anova_effect_sizes(groups)
    assert result["eta_sq"] > 0.9


@pytest.mark.parametrize("d,expected", [
    (0.1, "effect.d.negligible"),
    (0.3, "effect.d.small"),
    (0.6, "effect.d.medium"),
    (1.0, "effect.d.large"),
    (-1.0, "effect.d.large"),  # sign shouldn't matter
])
def test_cohen_d_interpretation_key(d, expected):
    assert cohen_d_interpretation_key(d) == expected


@pytest.mark.parametrize("eta,expected", [
    (0.005, "effect.eta.negligible"),
    (0.03, "effect.eta.small"),
    (0.10, "effect.eta.medium"),
    (0.20, "effect.eta.large"),
])
def test_eta_sq_interpretation_key(eta, expected):
    assert eta_sq_interpretation_key(eta) == expected


@pytest.mark.parametrize("alpha,expected", [
    (0.95, "sc.alpha.interp.excellent"),
    (0.85, "sc.alpha.interp.good"),
    (0.75, "sc.alpha.interp.acceptable"),
    (0.65, "sc.alpha.interp.questionable"),
    (0.3, "sc.alpha.interp.poor"),
])
def test_alpha_interpretation_key(alpha, expected):
    assert alpha_interpretation_key(alpha) == expected
