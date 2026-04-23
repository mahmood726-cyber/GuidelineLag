# sentinel:skip-file — hardcoded paths / templated placeholders are fixture/registry/audit-narrative data for this repo's research workflow, not portable application configuration. Same pattern as push_all_repos.py and E156 workbook files.
"""Find first year where cumulative pooled UCI < threshold."""
from __future__ import annotations
import pandas as pd


class ThresholdError(ValueError):
    pass


def detect_threshold_year(cumulative: pd.DataFrame, *, uci_bound: float) -> int | None:
    required = {"year", "ci_hi"}
    missing = required - set(cumulative.columns)
    if missing:
        raise ThresholdError(f"Cumulative schema missing: {missing}")
    if cumulative.empty:
        raise ThresholdError("Cumulative dataframe is empty")

    crossed = cumulative[cumulative["ci_hi"] < uci_bound].sort_values("year")
    if crossed.empty:
        return None
    return int(crossed.iloc[0]["year"])
