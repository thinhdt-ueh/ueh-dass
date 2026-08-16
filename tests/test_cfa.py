"""Regression tests for the CFA tab (pages/3, third tab). Covers the two real
bugs found during development (Arrow serialization on mixed-dtype loadings
table; the semopy/scipy/numpy incompatibilities in the DWLS+polychoric path)
plus the core good-fit / single-factor / validation-error paths."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from tests.conftest import seed_session_state

CFA_PAGE = str(Path(__file__).resolve().parent.parent / "pages" / "3_✅_Danh_gia_thang_do.py")


@pytest.fixture
def two_factor_correlated_df():
    rng = np.random.default_rng(7)
    n = 300
    f1 = rng.normal(0, 1, n)
    f2 = rng.normal(0, 1, n)
    return pd.DataFrame({
        "X1": 0.85 * f1 + rng.normal(0, 0.5, n),
        "X2": 0.80 * f1 + rng.normal(0, 0.5, n),
        "X3": 0.75 * f1 + rng.normal(0, 0.5, n),
        "X4": 0.80 * f2 + rng.normal(0, 0.5, n),
        "X5": 0.75 * f2 + rng.normal(0, 0.5, n),
        "X6": 0.70 * f2 + rng.normal(0, 0.5, n),
    })


@pytest.fixture
def two_factor_likert_df():
    rng = np.random.default_rng(11)
    n = 350
    f1 = rng.normal(0, 1, n)
    f2 = rng.normal(0, 1, n)

    def to_likert(cont, levels=5):
        q = pd.qcut(cont, levels, labels=False, duplicates="drop") + 1
        return q.astype(int)

    return pd.DataFrame({
        "X1": to_likert(0.85 * f1 + rng.normal(0, 0.5, n)),
        "X2": to_likert(0.80 * f1 + rng.normal(0, 0.5, n)),
        "X3": to_likert(0.75 * f1 + rng.normal(0, 0.5, n)),
        "X4": to_likert(0.80 * f2 + rng.normal(0, 0.5, n)),
        "X5": to_likert(0.75 * f2 + rng.normal(0, 0.5, n)),
        "X6": to_likert(0.70 * f2 + rng.normal(0, 0.5, n)),
    })


def _run_two_factor_cfa(at, add_to_report=True):
    at.multiselect(key="cfa_items_0").set_value(["X1", "X2", "X3"])
    at.run(timeout=60)
    at.multiselect(key="cfa_items_1").set_value(["X4", "X5", "X6"])
    at.run(timeout=60)
    if add_to_report:
        at.checkbox(key="cfa_add_report").set_value(True)
        at.run(timeout=60)
    at.button(key="btn_cfa").click().run(timeout=90)
    return at


def test_cfa_good_fit_ml(two_factor_correlated_df):
    at = AppTest.from_file(CFA_PAGE)
    seed_session_state(at, two_factor_correlated_df)
    at.run(timeout=60)
    _run_two_factor_cfa(at)
    assert not at.exception

    successes = " ".join(el.value for el in at.success)
    assert "CFI" in successes and "Excellent" in successes
    report = at.session_state["report"]
    assert len(report) == 1
    block_types = [b[0] for b in report[0]["blocks"]]
    assert "table" in block_types and "image" in block_types


def test_cfa_single_factor_no_crash(two_factor_correlated_df):
    """1-factor CFA must skip the correlation-matrix/discriminant-validity
    path (needs >=2 factors) without raising."""
    at = AppTest.from_file(CFA_PAGE)
    seed_session_state(at, two_factor_correlated_df)
    at.run(timeout=60)
    at.number_input(key="cfa_n_factors").set_value(1)
    at.run(timeout=60)
    at.multiselect(key="cfa_items_0").set_value(["X1", "X2", "X3"])
    at.run(timeout=60)
    at.button(key="btn_cfa").click().run(timeout=90)
    assert not at.exception


def test_cfa_validation_blocks_factor_with_one_item(two_factor_correlated_df):
    at = AppTest.from_file(CFA_PAGE)
    seed_session_state(at, two_factor_correlated_df)
    at.run(timeout=60)
    at.multiselect(key="cfa_items_0").set_value(["X1"])
    at.run(timeout=60)
    at.multiselect(key="cfa_items_1").set_value(["X4", "X5"])
    at.run(timeout=60)
    at.button(key="btn_cfa").click().run(timeout=60)
    assert not at.exception
    errors = [el.value for el in at.error]
    assert any("F1" in e for e in errors)
    assert at.session_state["report"] == []


def test_cfa_loadings_table_is_arrow_safe(two_factor_correlated_df):
    """Regression test: semopy.inspect() mixes floats with the literal '-'
    marker on fixed reference-indicator rows in Std.Err/z/p, which broke
    Streamlit's Arrow serialization when passed straight to st.dataframe()."""
    at = AppTest.from_file(CFA_PAGE)
    seed_session_state(at, two_factor_correlated_df)
    at.run(timeout=60)
    _run_two_factor_cfa(at, add_to_report=False)
    assert not at.exception
    # if serialization had broken, at.exception would be non-empty above;
    # this just also confirms a loadings dataframe element was rendered
    assert len(at.dataframe) >= 1


def test_cfa_dwls_polychoric_estimator(two_factor_likert_df):
    """Regression test: semopy 2.3.11's polychoric/DWLS path is broken under
    the numpy/scipy versions this project installs (np.ma.corrcoef lost its
    'bias' kwarg; scipy.stats.mvn.mvnun was removed). The app works around
    both via its own polychoric_cov() helper + a bivariate_cdf monkeypatch -
    this exercises that whole path end to end."""
    at = AppTest.from_file(CFA_PAGE)
    seed_session_state(at, two_factor_likert_df)
    at.run(timeout=60)

    at.multiselect(key="cfa_items_0").set_value(["X1", "X2", "X3"])
    at.run(timeout=60)
    at.multiselect(key="cfa_items_1").set_value(["X4", "X5", "X6"])
    at.run(timeout=60)
    at.radio(key="cfa_estimator").set_value(at.radio(key="cfa_estimator").options[1])
    at.run(timeout=60)
    at.checkbox(key="cfa_add_report").set_value(True)
    at.run(timeout=60)
    at.button(key="btn_cfa").click().run(timeout=120)

    assert not at.exception
    report = at.session_state["report"]
    assert len(report) == 1
    text_blocks = [b[1] for b in report[0]["blocks"] if b[0] == "text"]
    assert any("DWLS" in t for t in text_blocks)


def test_cfa_report_builds_valid_docx(two_factor_correlated_df):
    at = AppTest.from_file(CFA_PAGE)
    seed_session_state(at, two_factor_correlated_df)
    at.run(timeout=60)
    _run_two_factor_cfa(at, add_to_report=True)
    assert not at.exception

    st.session_state.report = at.session_state["report"]
    from utils.report import build_docx_bytes
    docx_bytes = build_docx_bytes()
    assert len(docx_bytes) > 1000

    from docx import Document
    import io
    doc = Document(io.BytesIO(docx_bytes))
    assert len(doc.tables) >= 4
    assert len(doc.inline_shapes) >= 1  # the path diagram image
