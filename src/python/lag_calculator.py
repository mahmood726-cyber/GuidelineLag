# sentinel:skip-file — hardcoded paths / templated placeholders are fixture/registry/audit-narrative data for this repo's research workflow, not portable application configuration. Same pattern as push_all_repos.py and E156 workbook files.
"""Compute lag-to-cite and lag-to-L4 per (class, body) pair."""
from __future__ import annotations
from datetime import date, datetime
from typing import Iterable
import pandas as pd


def months_between(start: date, end: date) -> int:
    delta_months = (end.year - start.year) * 12 + (end.month - start.month)
    if end.day - start.day >= 15:
        delta_months += 1
    elif end.day - start.day <= -15:
        delta_months -= 1
    return int(delta_months)


def _to_date(val) -> date | None:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    return datetime.fromisoformat(str(val)).date()


def compute_lag_row(
    *, cd_id: str, class_id: str, threshold_year: int | None,
    body: str,
    first_citing_pub_date: date | str | None,
    first_l4_pub_date: date | str | None,
) -> dict:
    threshold_anchor = date(threshold_year, 7, 1) if threshold_year else None
    cite_d = _to_date(first_citing_pub_date)
    l4_d = _to_date(first_l4_pub_date)

    lag_cite = months_between(threshold_anchor, cite_d) if (threshold_anchor and cite_d) else None
    lag_l4 = months_between(threshold_anchor, l4_d) if (threshold_anchor and l4_d) else None

    return {
        "cd_id": cd_id,
        "class_id": class_id,
        "body": body,
        "threshold_year": threshold_year,
        "first_citing_pub_date": cite_d.isoformat() if cite_d else None,
        "first_l4_pub_date": l4_d.isoformat() if l4_d else None,
        "lag_to_cite_months": lag_cite,
        "lag_to_l4_months": lag_l4,
        "censored_cite": cite_d is None,
        "censored_l4": l4_d is None,
    }


def build_lag_dataset(
    threshold_dates: pd.DataFrame,
    citations: pd.DataFrame,
    l4: pd.DataFrame,
    *, bodies: Iterable[str],
) -> pd.DataFrame:
    rows = []
    for _, t in threshold_dates.iterrows():
        for body in bodies:
            cite_match = citations[
                (citations["cd_id"] == t["cd_id"]) & (citations["body"] == body)
            ]
            l4_match = l4[
                (l4["class_id"] == t["class_id"]) & (l4["body"] == body)
            ]
            cite_d = cite_match.iloc[0]["first_citing_pub_date"] if not cite_match.empty else None
            l4_d = l4_match.iloc[0]["first_l4_pub_date"] if not l4_match.empty else None
            rows.append(compute_lag_row(
                cd_id=t["cd_id"], class_id=t["class_id"],
                threshold_year=t.get("threshold_year"),
                body=body,
                first_citing_pub_date=cite_d, first_l4_pub_date=l4_d,
            ))
    df = pd.DataFrame(rows)
    return df
