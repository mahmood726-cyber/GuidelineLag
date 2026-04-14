import pandas as pd
import pytest
from pathlib import Path
from src.python.threshold_detector import detect_threshold_year, ThresholdError


def df(rows):
    return pd.DataFrame(rows, columns=["year", "k", "effect", "se", "ci_lo", "ci_hi", "tau2", "method"])


def test_crosses_in_middle_year():
    cum = df([
        (2010, 2, 0.95, 0.1, 0.80, 1.10, 0.01, "PM"),
        (2012, 3, 0.85, 0.08, 0.75, 0.97, 0.01, "PM"),
        (2015, 5, 0.80, 0.05, 0.72, 0.89, 0.01, "REML"),   # crosses < 0.90
        (2018, 7, 0.78, 0.04, 0.72, 0.86, 0.01, "REML"),
    ])
    assert detect_threshold_year(cum, uci_bound=0.90) == 2015


def test_never_crosses():
    cum = df([
        (2010, 2, 0.95, 0.1, 0.80, 1.10, 0.01, "PM"),
        (2015, 4, 0.92, 0.05, 0.85, 0.99, 0.01, "PM"),
        (2020, 6, 0.90, 0.04, 0.83, 0.98, 0.01, "REML"),
    ])
    assert detect_threshold_year(cum, uci_bound=0.90) is None


def test_boundary_exactly_0_9_excluded_by_strict_lt():
    cum = df([(2015, 5, 0.85, 0.05, 0.72, 0.90, 0.01, "REML")])
    assert detect_threshold_year(cum, uci_bound=0.90) is None


def test_boundary_just_below_0_9_included():
    cum = df([(2015, 5, 0.85, 0.05, 0.72, 0.8999, 0.01, "REML")])
    assert detect_threshold_year(cum, uci_bound=0.90) == 2015


def test_empty_raises():
    cum = df([])
    with pytest.raises(ThresholdError):
        detect_threshold_year(cum, uci_bound=0.90)
