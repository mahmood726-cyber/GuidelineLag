import pandas as pd
from pathlib import Path
import pytest
from src.python.cd_topic_enricher import enrich, _extract_cd_id, EnrichmentError

FIX = Path(__file__).resolve().parents[1] / "fixtures" / "sample_pairwise70_listing.txt"
OVERRIDE = Path(__file__).resolve().parents[2] / "protocol" / "cd_manual_cardio.csv"


def test_extract_cd_id():
    assert _extract_cd_id("CD003177_pub3_data.rda") == "CD003177"
    assert _extract_cd_id("CD013650_pub1_data.rda") == "CD013650"


def test_extract_cd_id_bad_filename():
    with pytest.raises(EnrichmentError):
        _extract_cd_id("not_a_cochrane.rda")


def test_enrich_merges_manual_override(tmp_path):
    out = tmp_path / "cd_topics.csv"
    listing = FIX.read_text().splitlines()
    enrich(listing, manual_override=OVERRIDE, out_csv=out, api_fetcher=lambda cd: None)
    df = pd.read_csv(out)
    assert set(df.columns) >= {"cd_id", "title", "mesh_terms", "is_cardio", "cardio_class", "source"}
    assert set(df[df["is_cardio"]]["cd_id"]) >= {"CD003177", "CD013650"}


def test_non_cardio_cd_marked_false(tmp_path):
    out = tmp_path / "cd_topics.csv"
    listing = FIX.read_text().splitlines()
    enrich(listing, manual_override=OVERRIDE, out_csv=out, api_fetcher=lambda cd: None)
    df = pd.read_csv(out)
    assert not df[df["cd_id"] == "CD000028"]["is_cardio"].iloc[0]
