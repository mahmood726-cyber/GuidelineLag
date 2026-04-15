import pandas as pd
from src.python.citation_matcher import normalize_doi, find_first_citation


def test_normalize_strips_pub_version():
    assert normalize_doi("10.1002/14651858.CD013650.pub3") == "10.1002/14651858.cd013650"


def test_normalize_strips_trailing_dot():
    assert normalize_doi("10.1056/NEJMoa1911303.") == "10.1056/nejmoa1911303"


def test_find_first_citation_earliest_year_wins():
    refs = pd.DataFrame({
        "body": ["esc", "esc", "nice"],
        "topic": ["heart_failure", "heart_failure", "chronic_heart_failure"],
        "edition_year": [2023, 2021, 2023],
        "pub_date": ["2023-08-25", "2021-08-27", "2023-11-15"],
        "doi_normalized": [
            "10.1002/14651858.cd013650",
            "10.1002/14651858.cd013650",
            "10.1002/14651858.cd013650",
        ],
    })
    target_doi = "10.1002/14651858.CD013650.pub1"
    hits = find_first_citation(target_doi, refs)
    assert len(hits) == 2
    esc_hit = hits[hits["body"] == "esc"].iloc[0]
    assert esc_hit["edition_year"] == 2021
    nice_hit = hits[hits["body"] == "nice"].iloc[0]
    assert nice_hit["edition_year"] == 2023


def test_no_citation_returns_empty():
    refs = pd.DataFrame({
        "body": ["esc"], "topic": ["hf"], "edition_year": [2021],
        "pub_date": ["2021-08-27"],
        "doi_normalized": ["10.1056/nejmoa1911303"],
    })
    hits = find_first_citation("10.9999/does.not.exist", refs)
    assert hits.empty
