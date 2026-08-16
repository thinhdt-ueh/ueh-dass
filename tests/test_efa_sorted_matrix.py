"""Regression tests for the sorted & suppressed EFA component matrix
(pages/3, EFA tab) - the SPSS "sort by size, suppress small coefficients"
style table added alongside the existing raw loadings matrix."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from tests.conftest import seed_session_state

SCALE_PAGE = str(Path(__file__).resolve().parent.parent / "pages" / "3_✅_Danh_gia_thang_do.py")


@pytest.fixture
def two_factor_df():
    rng = np.random.default_rng(21)
    n = 300
    f1 = rng.normal(0, 1, n)
    f2 = rng.normal(0, 1, n)
    return pd.DataFrame({
        "A1": 0.85 * f1 + rng.normal(0, 0.5, n),
        "A2": 0.80 * f1 + rng.normal(0, 0.5, n),
        "A3": 0.75 * f1 + rng.normal(0, 0.5, n),
        "B1": 0.80 * f2 + rng.normal(0, 0.5, n),
        "B2": 0.75 * f2 + rng.normal(0, 0.5, n),
        "B3": 0.70 * f2 + rng.normal(0, 0.5, n),
    })


def test_efa_sorted_matrix_runs_and_reports(two_factor_df):
    at = AppTest.from_file(SCALE_PAGE)
    seed_session_state(at, two_factor_df)
    at.run(timeout=60)

    at.multiselect(key="efa_items").set_value(list(two_factor_df.columns))
    at.run(timeout=60)
    at.checkbox(key="efa_add_report").set_value(True)
    at.run(timeout=60)
    at.button(key="btn_efa").click().run(timeout=60)

    assert not at.exception
    report = at.session_state["report"]
    assert len(report) == 1
    # blocks: text summary, raw loadings, sorted+suppressed, communalities, variance
    tables = [b[1] for b in report[0]["blocks"] if b[0] == "table"]
    assert len(tables) == 4

    sorted_table = tables[1]
    # every non-blank cell must be >= the default suppression threshold (0.4)
    numeric_cells = sorted_table.drop(columns=[sorted_table.columns[0]]).to_numpy().ravel()
    for v in numeric_cells:
        if v != "":
            assert abs(float(v)) >= 0.4 - 1e-9

    # each item should appear in the sorted table exactly once
    var_col = sorted_table.columns[0]
    assert sorted(sorted_table[var_col].tolist()) == sorted(two_factor_df.columns.tolist())


def test_efa_suppress_threshold_is_configurable(two_factor_df):
    at = AppTest.from_file(SCALE_PAGE)
    seed_session_state(at, two_factor_df)
    at.run(timeout=60)

    at.multiselect(key="efa_items").set_value(list(two_factor_df.columns))
    at.run(timeout=60)
    at.number_input(key="efa_suppress_threshold").set_value(0.9)
    at.run(timeout=60)
    at.button(key="btn_efa").click().run(timeout=60)

    assert not at.exception
    # with a 0.9 threshold, essentially everything should be suppressed
    caption_texts = " ".join(el.value for el in at.caption)
    assert "0.90" in caption_texts
