"""Client for IRENA's IRENASTAT database (PxWeb v1 API).

PxWeb v1 quirk: for most variables (Technology, Grid connection, Year — but
NOT Country/area, which already uses real ISO3 codes) the query "values" are
positional index strings ("0", "1", ...) into a parallel "valueTexts" array,
not the real-world codes. This module hides that by letting callers filter
using human-readable labels (or raw codes) and returns a decoded DataFrame.
"""

import time

import pandas as pd
import requests

from extractors.shared import save_raw

API_ROOT = "https://pxweb.irena.org/api/v1/en/IRENASTAT"
TABLES = {
    "country_eleccap": "Country_ELECCAP_2026_H1_v-PX 1.px",
    "country_elecgen": "Country_ELECGEN_2025_H2_v-PX 1.px",
}
# The server rejects queries above roughly this many result cells (observed:
# ~300k cells -> 403 Forbidden from a WAF/proxy, not a PxWeb JSON error).
# Stay comfortably under it by chunking full-table fetches.
MAX_CELLS = 50_000


def get_metadata(table_url: str) -> dict:
    r = requests.get(table_url)
    r.raise_for_status()
    return r.json()


def _value_maps(metadata: dict) -> dict[str, dict[str, str]]:
    """code -> {value: valueText} for each variable."""
    return {
        var["code"]: dict(zip(var["values"], var["valueTexts"]))
        for var in metadata["variables"]
    }


def _resolve_filter_values(values: list[str], value_to_text: dict[str, str]) -> list[str]:
    """Translate human-readable labels to query codes; pass through raw codes."""
    text_to_value = {text: value for value, text in value_to_text.items()}
    return [text_to_value.get(v, v) for v in values]


def _post_with_retry(table_url: str, query: list[dict], max_retries: int = 5) -> dict:
    backoff = 5.0
    for attempt in range(max_retries):
        r = requests.post(table_url, json={"query": query, "response": {"format": "json"}})
        if r.status_code == 429:
            wait = float(r.headers.get("Retry-After", backoff))
            time.sleep(wait)
            backoff *= 2
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError(f"Gave up after {max_retries} retries (rate limited)")


def _query(table_url: str, metadata: dict, filters: dict[str, list[str]]) -> pd.DataFrame:
    value_maps = _value_maps(metadata)

    query = [
        {
            "code": code,
            "selection": {
                "filter": "item",
                "values": _resolve_filter_values(values, value_maps[code]),
            },
        }
        for code, values in filters.items()
    ]
    payload = _post_with_retry(table_url, query)

    columns = [c["code"] for c in payload["columns"] if c["type"] == "d"]
    rows = []
    for row in payload["data"]:
        decoded = {
            col: value_maps[col].get(key, key) for col, key in zip(columns, row["key"])
        }
        value = row["values"][0]
        decoded["value"] = None if value == "-" else float(value)
        rows.append(decoded)

    return pd.DataFrame(rows)


def fetch_table(table_url: str, filters: dict[str, list[str]]) -> pd.DataFrame:
    """Query a PxWeb v1 table and return a decoded DataFrame.

    filters: {variable_code: [label_or_code, ...]}, e.g.
        {"Country/area": ["Germany"], "Year": ["2023"]}
    Variables omitted from filters are returned unfiltered (all values).
    """
    metadata = get_metadata(table_url)
    return _query(table_url, metadata, filters)


def _latest_year_value(metadata: dict) -> tuple[str, str]:
    """Return (code, label) for the max year in the table's Year variable."""
    year_var = next(v for v in metadata["variables"] if v["code"] == "Year")
    pairs = zip(year_var["values"], year_var["valueTexts"])
    return max(pairs, key=lambda pair: int(pair[1]))


def fetch_latest_year(table_url: str, sleep: float = 1.0) -> pd.DataFrame:
    """Fetch every Country/area x Technology x Grid connection combo for the
    single most recent Year in the table (everything except Year unfiltered).

    A single unrestricted query across all variables is too large for the
    server (observed: ~300k result cells triggers a 403 from a WAF/proxy in
    front of PxWeb, not a PxWeb-level error), but restricting to one year
    usually brings the cell count low enough for one request. If it's still
    too large, this falls back to chunking along the largest remaining
    variable, same as a full fetch would.
    """
    metadata = get_metadata(table_url)
    variables = metadata["variables"]
    year_value, year_label = _latest_year_value(metadata)
    base_filters = {"Year": [year_value]}

    other_vars = [v for v in variables if v["code"] != "Year"]
    cells = 1
    for v in other_vars:
        cells *= len(v["values"])

    if cells <= MAX_CELLS:
        print(f"fetching Year={year_label} (all other variables unfiltered)...")
        return _query(table_url, metadata, filters=base_filters)

    chunk_var = max(other_vars, key=lambda v: len(v["values"]))
    remaining = [v for v in other_vars if v["code"] != chunk_var["code"]]
    cells_per_chunk = 1
    for v in remaining:
        cells_per_chunk *= len(v["values"])
    if cells_per_chunk > MAX_CELLS:
        raise ValueError(
            f"Even one slice of '{chunk_var['code']}' for Year={year_label} has "
            f"{cells_per_chunk} cells, over the {MAX_CELLS} limit — chunk along "
            "more than one variable."
        )

    dfs = []
    total = len(chunk_var["values"])
    for i, value in enumerate(chunk_var["values"]):
        label = chunk_var["valueTexts"][i]
        print(f"[{i + 1}/{total}] fetching {chunk_var['code']}={label}, Year={year_label}...")
        filters = {**base_filters, chunk_var["code"]: [value]}
        dfs.append(_query(table_url, metadata, filters=filters))
        if sleep and i < total - 1:
            time.sleep(sleep)

    return pd.concat(dfs, ignore_index=True)

if __name__ == "__main__":
    for file_name, table_file in TABLES.items():
        table_url = f"{API_ROOT}/Power Capacity and Generation/{table_file}"
        df = fetch_latest_year(table_url)
        print(f"{file_name}: {len(df)} rows")
        out_path = save_raw(df, source="irenastat", file_name=file_name)
        print(f"saved to {out_path}")
