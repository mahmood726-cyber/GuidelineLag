"""Match Cochrane DOI against guideline reference lists; return first-citation per body."""
from __future__ import annotations
import re
import pandas as pd


def normalize_doi(doi: str) -> str:
    if doi is None:
        return ""
    d = str(doi).strip().lower().rstrip(". ")
    d = re.sub(r"\.pub\d+$", "", d)
    return d


def find_first_citation(target_doi: str, refs: pd.DataFrame) -> pd.DataFrame:
    if "doi_normalized" not in refs.columns:
        raise KeyError("refs missing 'doi_normalized' column; call guideline_parser first")
    target = normalize_doi(target_doi)
    hits = refs[refs["doi_normalized"] == target].copy()
    if hits.empty:
        return hits
    hits = hits.sort_values(["body", "edition_year"]).groupby("body", as_index=False).first()
    return hits
