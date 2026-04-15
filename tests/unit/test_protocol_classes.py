import yaml
from pathlib import Path

CLASSES_YAML = Path(__file__).resolve().parents[2] / "protocol" / "classes.yaml"


def test_classes_yaml_has_ten_entries():
    data = yaml.safe_load(CLASSES_YAML.read_text())
    assert len(data["classes"]) == 10


def test_each_class_has_required_fields():
    data = yaml.safe_load(CLASSES_YAML.read_text())
    required = {"id", "display_name", "pivotal_trials", "bodies_in_scope"}
    for cls in data["classes"]:
        missing = required - cls.keys()
        assert not missing, f"{cls.get('id')} missing {missing}"


def test_bodies_are_canonical_four():
    data = yaml.safe_load(CLASSES_YAML.read_text())
    expected = {"esc", "acc_aha", "nice", "ccs"}
    for cls in data["classes"]:
        assert set(cls["bodies_in_scope"]) == expected
