import pandas as pd
from pathlib import Path
from src.python.guideline_corpus import load_manifest, filter_ready, CorpusError
import pytest

TEMPLATE = Path(__file__).resolve().parents[2] / "protocol" / "guideline_manifest_template.csv"


def test_load_manifest_schema():
    df = load_manifest(TEMPLATE)
    required = {"body", "topic", "edition_year", "pub_date", "pdf_path", "status", "parse_mode"}
    missing = required - set(df.columns)
    assert not missing


def test_filter_ready_drops_non_sourced(tmp_path):
    df = pd.DataFrame({
        "body": ["esc", "esc"], "topic": ["hf", "hf"],
        "edition_year": [2021, 2023], "pub_date": ["2021-08-27", "2023-08-25"],
        "pdf_path": ["a.pdf", "b.pdf"],
        "status": ["sourced", "needed"],
        "parse_mode": ["manual", "manual"], "notes": ["", ""],
    })
    ready = filter_ready(df)
    assert len(ready) == 1
    assert ready.iloc[0]["edition_year"] == 2021


def test_missing_file_raises():
    with pytest.raises(CorpusError):
        load_manifest(Path("does_not_exist.csv"))
