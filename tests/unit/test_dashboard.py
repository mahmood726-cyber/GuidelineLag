import pandas as pd
from pathlib import Path
from src.python.build_dashboard import render_dashboard


def test_dashboard_renders_with_no_cdn_and_no_placeholders(tmp_path):
    lag = pd.DataFrame([
        {"class_id": "sglt2i_hfref", "body": "esc", "lag_to_l4_months": 18, "censored_l4": False},
        {"class_id": "sglt2i_hfref", "body": "nice", "lag_to_l4_months": 48, "censored_l4": False},
        {"class_id": "sglt2i_hfref", "body": "acc_aha", "lag_to_l4_months": 24, "censored_l4": False},
        {"class_id": "sglt2i_hfref", "body": "ccs", "lag_to_l4_months": 30, "censored_l4": False},
    ])
    out = tmp_path / "index.html"
    render_dashboard(lag, out)
    html = out.read_text(encoding="utf-8")
    assert "<html" in html.lower()
    assert "http://" not in html
    assert "https://cdn" not in html
    for placeholder in ["{{", "}}", "TBD", "TODO", "REPLACE_ME", "__PLACEHOLDER__"]:
        assert placeholder not in html, f"placeholder leaked: {placeholder}"
    # No hardcoded local paths
    assert "C:\\\\Users" not in html
    assert "C:/Users" not in html
    # Data present
    assert "sglt2i_hfref" in html
    assert "NICE" in html or "nice" in html
