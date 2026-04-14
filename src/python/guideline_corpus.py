"""Load and filter the guideline corpus manifest."""
from __future__ import annotations
from pathlib import Path
import pandas as pd

REQUIRED = ["body", "topic", "edition_year", "pub_date", "pdf_path", "status", "parse_mode"]


class CorpusError(RuntimeError):
    pass


def load_manifest(path: Path) -> pd.DataFrame:
    if not Path(path).exists():
        raise CorpusError(f"Manifest not found: {path}")
    df = pd.read_csv(path)
    missing = set(REQUIRED) - set(df.columns)
    if missing:
        raise CorpusError(f"Manifest missing columns: {missing}")
    return df


def filter_ready(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["status"] == "sourced"].reset_index(drop=True)
