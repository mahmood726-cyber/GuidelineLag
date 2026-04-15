import pandas as pd
import pytest
from pathlib import Path
from src.python.guideline_parser import parse_edition_manual, ParserError

FIX = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.mark.integration
def test_manual_mode_returns_typed_dict():
    out = parse_edition_manual(
        refs_csv=FIX / "sample_refs.csv",
        recs_csv=FIX / "sample_recs.csv",
        body="esc", topic="heart_failure", edition_year=2021,
    )
    assert set(out.keys()) == {"refs", "recs"}
    assert isinstance(out["refs"], pd.DataFrame)
    assert isinstance(out["recs"], pd.DataFrame)
    assert "doi" in out["refs"].columns
    assert "rec_class_raw" in out["recs"].columns


def test_schema_mismatch_raises_with_diff(tmp_path):
    bad = tmp_path / "bad_refs.csv"
    bad.write_text("wrong,columns\nfoo,bar\n")
    with pytest.raises(ParserError, match="schema"):
        parse_edition_manual(
            refs_csv=bad, recs_csv=FIX / "sample_recs.csv",
            body="esc", topic="heart_failure", edition_year=2021,
        )


def test_empty_refs_raises(tmp_path):
    empty = tmp_path / "empty.csv"
    empty.write_text("body,topic,edition_year,ref_number,authors,title,journal,year,doi\n")
    with pytest.raises(ParserError, match="empty"):
        parse_edition_manual(
            refs_csv=empty, recs_csv=FIX / "sample_recs.csv",
            body="esc", topic="heart_failure", edition_year=2021,
        )
