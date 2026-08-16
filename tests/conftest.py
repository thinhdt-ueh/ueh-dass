import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def demo_df() -> pd.DataFrame:
    """Same shape/columns as app.py's generate_demo_data(lang='en'), so page
    smoke tests exercise the same code paths a real user would hit."""
    rng = np.random.default_rng(42)
    n = 200
    df = pd.DataFrame({
        "ID": range(1, n + 1),
        "Gender": rng.choice(["Male", "Female"], size=n),
        "AgeGroup": rng.choice(["18-24", "25-34", "35-44", "45-54", "55+"], size=n),
        "Income": rng.choice(["<$1,000", "$1,000-2,000", "$2,000-3,000", ">$3,000"], size=n),
        "Education": rng.choice(["High School", "College", "Bachelor's", "Graduate"], size=n),
    })
    for i in range(1, 5):
        df[f"BA{i}"] = rng.integers(1, 8, size=n)
    for i in range(1, 5):
        df[f"PI{i}"] = rng.integers(1, 8, size=n)
    df["Guilt"] = rng.integers(1, 8, size=n)
    return df


def seed_session_state(at, df: pd.DataFrame, lang: str = "en"):
    """Populate an AppTest instance's session_state the way app.py's
    init_state() would after data has been loaded, before the first at.run()."""
    at.session_state["df"] = df
    at.session_state["var_labels"] = {}
    at.session_state["log"] = []
    at.session_state["lang"] = lang
    at.session_state["report"] = []
