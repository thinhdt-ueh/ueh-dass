"""Save/restore a full DASS session (data + labels + log + language) as a single JSON file."""
import io
import json

import pandas as pd

PROJECT_VERSION = 1


def serialize_project(df: pd.DataFrame, var_labels: dict, log: list, lang: str) -> bytes:
    dtypes = {col: str(df[col].dtype) for col in df.columns}
    data_obj = json.loads(df.to_json(orient="split", date_format="iso"))
    payload = {
        "version": PROJECT_VERSION,
        "lang": lang,
        "var_labels": var_labels,
        "log": log,
        "dtypes": dtypes,
        "data": data_obj,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def deserialize_project(raw: bytes):
    payload = json.loads(raw.decode("utf-8"))
    data_json = json.dumps(payload["data"])
    df = pd.read_json(io.StringIO(data_json), orient="split")

    for col, dt in payload.get("dtypes", {}).items():
        if col not in df.columns:
            continue
        if dt.startswith("datetime"):
            df[col] = pd.to_datetime(df[col], errors="coerce")
        elif dt == "category":
            df[col] = df[col].astype("category")
        elif dt.startswith(("int", "float")):
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df, payload.get("var_labels", {}), payload.get("log", []), payload.get("lang", "en")
