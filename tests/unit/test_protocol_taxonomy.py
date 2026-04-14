import yaml
from pathlib import Path

PATH = Path(__file__).resolve().parents[2] / "protocol" / "taxonomy.yaml"


def test_five_levels_defined():
    data = yaml.safe_load(PATH.read_text())
    assert set(data["levels"].keys()) == {"L0", "L1", "L2", "L3", "L4"}


def test_four_bodies_mapped():
    data = yaml.safe_load(PATH.read_text())
    assert set(data["body_mappings"].keys()) == {"esc", "acc_aha", "nice", "ccs"}


def test_l4_exists_for_all_bodies():
    data = yaml.safe_load(PATH.read_text())
    for body, mapping in data["body_mappings"].items():
        assert mapping.get("L4"), f"{body} missing L4"


def test_nice_l2_is_null():
    data = yaml.safe_load(PATH.read_text())
    assert data["body_mappings"]["nice"]["L2"] is None
