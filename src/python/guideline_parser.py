"""Parse a guideline edition into refs + recs tables. Manual mode is the default."""
from __future__ import annotations
from pathlib import Path
import pandas as pd

REFS_REQUIRED = ["body", "topic", "edition_year", "ref_number", "authors", "title", "journal", "year", "doi"]
RECS_REQUIRED = ["body", "topic", "edition_year", "rec_id", "topic_tag", "rec_class_raw", "rec_text"]


class ParserError(RuntimeError):
    pass


def _load_csv(path: Path, required: list[str]) -> pd.DataFrame:
    if not path.exists():
        raise ParserError(f"File not found: {path}")
    df = pd.read_csv(path)
    missing = set(required) - set(df.columns)
    if missing:
        raise ParserError(f"schema missing: {missing} in {path.name}")
    if df.empty:
        raise ParserError(f"empty: {path.name}")
    return df


def parse_edition_manual(
    *,
    refs_csv: Path, recs_csv: Path,
    body: str, topic: str, edition_year: int,
) -> dict[str, pd.DataFrame]:
    refs = _load_csv(refs_csv, REFS_REQUIRED)
    recs = _load_csv(recs_csv, RECS_REQUIRED)

    refs = refs[
        (refs["body"] == body) & (refs["topic"] == topic) & (refs["edition_year"] == edition_year)
    ].reset_index(drop=True)
    recs = recs[
        (recs["body"] == body) & (recs["topic"] == topic) & (recs["edition_year"] == edition_year)
    ].reset_index(drop=True)

    # Normalize DOIs: lowercase, strip trailing dots, strip .pubN
    refs["doi_normalized"] = (
        refs["doi"].astype(str).str.lower()
        .str.rstrip(". ")
        .str.replace(r"\.pub\d+$", "", regex=True)
    )
    return {"refs": refs, "recs": recs}
