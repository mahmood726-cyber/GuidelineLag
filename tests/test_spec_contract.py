from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "docs" / "superpowers" / "specs" / "2026-04-14-guideline-lag-design.md"


def test_guideline_lag_spec_declares_core_cohort_and_endpoints():
    text = SPEC.read_text(encoding="utf-8")
    required = [
        "Cochrane CDSR",
        "ESC / ACC-AHA / NICE",
        "Primary endpoint B",
        "Secondary endpoint C",
        "Right-censoring",
        "endpoint_b_months",
        "endpoint_c_months",
    ]
    missing = [marker for marker in required if marker not in text]
    assert missing == []


def test_guideline_lag_spec_has_fail_closed_stats_plan():
    text = SPEC.read_text(encoding="utf-8")
    required = [
        "Schoenfeld residuals",
        "RMST",
        "Cox",
        "Kaplan-Meier",
        "tolerance 1e-6",
        "fail-closed",
        "OA",
    ]
    missing = [marker for marker in required if marker not in text]
    assert missing == []
