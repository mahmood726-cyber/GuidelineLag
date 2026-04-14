import yaml
from pathlib import Path

PATH = Path(__file__).resolve().parents[2] / "protocol" / "thresholds.yaml"
CLASSES = Path(__file__).resolve().parents[2] / "protocol" / "classes.yaml"


def test_all_ten_classes_have_threshold():
    thresholds = yaml.safe_load(PATH.read_text())["thresholds"]
    classes = yaml.safe_load(CLASSES.read_text())["classes"]
    class_ids = {c["id"] for c in classes}
    threshold_ids = {t["class_id"] for t in thresholds}
    assert class_ids == threshold_ids


def test_uniform_rule_enforced():
    thresholds = yaml.safe_load(PATH.read_text())["thresholds"]
    for t in thresholds:
        assert t["metric"] == "HR"
        assert t["direction"] == "upper_ci_less_than"
        assert t["uci_bound"] == 0.90


def test_every_threshold_has_outcome_description():
    thresholds = yaml.safe_load(PATH.read_text())["thresholds"]
    for t in thresholds:
        assert t["outcome"]
        assert len(t["outcome"]) > 5
