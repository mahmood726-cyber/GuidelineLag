import json
import pandas as pd
from src.python.e156_compose import compose_article, validate_e156


def _sample_lag():
    rows = []
    bodies = ["esc", "acc_aha", "nice", "ccs"]
    lags = {"esc": 18, "acc_aha": 24, "nice": 48, "ccs": 30}
    for body in bodies:
        rows.append({"class_id": "sglt2i_hfref", "body": body,
                     "lag_to_l4_months": lags[body], "censored_l4": False})
        rows.append({"class_id": "pcsk9i", "body": body,
                     "lag_to_l4_months": lags[body] + 6, "censored_l4": False})
    return pd.DataFrame(rows)


def test_compose_returns_seven_sentences():
    article = compose_article(_sample_lag())
    assert len(article["sentences"]) == 7
    assert set(article["sentences"]) == {f"S{i}" for i in range(1, 8)}


def test_word_count_leq_156():
    article = compose_article(_sample_lag())
    body_words = article["body"].split()
    assert len(body_words) <= 156, f"got {len(body_words)} words"


def test_validate_rejects_wrong_sentence_count():
    bad = {"body": "One. Two. Three.", "sentences": {"S1": "One.", "S2": "Two.", "S3": "Three."}, "word_count": 3}
    errors = validate_e156(bad)
    assert any("7 sentences" in e for e in errors)
