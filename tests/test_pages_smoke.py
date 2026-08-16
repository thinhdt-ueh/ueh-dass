"""Smoke tests: does every page load without raising, given demo data?
This is the regression net for the "nested button never fires" and
"file_uploader sticky value" classes of bugs found during development -
it won't catch everything, but it catches anything that breaks a page
outright."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from tests.conftest import seed_session_state

APP_DIR = Path(__file__).resolve().parent.parent
PAGE_FILES = sorted((APP_DIR / "pages").glob("*.py"))


def test_home_page_loads_with_data(demo_df):
    at = AppTest.from_file(str(APP_DIR / "app.py"))
    seed_session_state(at, demo_df)
    at.run(timeout=30)
    assert not at.exception


@pytest.mark.parametrize("page_path", PAGE_FILES, ids=lambda p: p.name)
def test_page_loads_with_data_vi(page_path, demo_df):
    at = AppTest.from_file(str(page_path))
    seed_session_state(at, demo_df, lang="vi")
    at.run(timeout=60)
    assert not at.exception, f"{page_path.name} (vi) raised: {at.exception}"


@pytest.mark.parametrize("page_path", PAGE_FILES, ids=lambda p: p.name)
def test_page_loads_with_data_en(page_path, demo_df):
    at = AppTest.from_file(str(page_path))
    seed_session_state(at, demo_df, lang="en")
    at.run(timeout=60)
    assert not at.exception, f"{page_path.name} (en) raised: {at.exception}"


def test_pages_without_data_show_warning_not_crash():
    """require_data() should stop the page cleanly with a warning, not raise."""
    for page_path in PAGE_FILES:
        if page_path.name.startswith("7_"):
            continue  # User Guide page has no require_data() gate
        at = AppTest.from_file(str(page_path))
        at.run(timeout=30)
        assert not at.exception, f"{page_path.name} raised with no data loaded: {at.exception}"
