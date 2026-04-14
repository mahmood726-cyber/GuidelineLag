import pandas as pd
from src.python.build_manuscript import build_bmj_draft


def test_draft_contains_every_lag_value(tmp_path):
    lag = pd.DataFrame([
        {"class_id": "sglt2i_hfref", "body": "esc", "lag_to_l4_months": 18, "censored_l4": False},
        {"class_id": "sglt2i_hfref", "body": "nice", "lag_to_l4_months": 48, "censored_l4": False},
    ])
    out = tmp_path / "bmj.md"
    build_bmj_draft(lag, out)
    md = out.read_text()
    assert "18" in md and "48" in md
    assert "NICE" in md or "nice" in md.lower()
    assert "TBD" not in md and "TODO" not in md
