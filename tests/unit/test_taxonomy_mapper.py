import pytest
from src.python.taxonomy_mapper import map_to_canonical, TaxonomyError


def test_esc_class_i_maps_to_L4():
    assert map_to_canonical("esc", "Class I") == "L4"


def test_nice_offer_maps_to_L4():
    assert map_to_canonical("nice", "Offer") == "L4"


def test_nice_l2_returns_none():
    assert map_to_canonical("nice", "__any_l2_input__", probe_level="L2") is None


def test_acc_aha_class_iii_harm_maps_to_L0():
    assert map_to_canonical("acc_aha", "Class III: Harm") == "L0"


def test_case_insensitive():
    assert map_to_canonical("esc", "class i") == "L4"
    assert map_to_canonical("esc", "CLASS IIa") == "L3"


def test_unknown_raises_with_diff():
    with pytest.raises(TaxonomyError, match="unknown"):
        map_to_canonical("esc", "Class IV (invented)")


def test_unknown_body_raises():
    with pytest.raises(TaxonomyError, match="body"):
        map_to_canonical("who", "Class I")
