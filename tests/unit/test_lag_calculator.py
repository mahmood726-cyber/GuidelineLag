from datetime import date
import pandas as pd
from src.python.lag_calculator import months_between, compute_lag_row, build_lag_dataset


def test_months_between_same_year():
    assert months_between(date(2021, 7, 1), date(2021, 10, 1)) == 3


def test_months_between_cross_years():
    assert months_between(date(2019, 7, 1), date(2021, 1, 1)) == 18


def test_months_rounded():
    assert months_between(date(2021, 7, 1), date(2021, 8, 14)) == 1
    assert months_between(date(2021, 7, 1), date(2021, 8, 20)) == 2


def test_lag_row_censored_when_never_reached():
    row = compute_lag_row(
        cd_id="CD013650", class_id="sglt2i_hfref", threshold_year=2020,
        body="nice", first_citing_pub_date=None, first_l4_pub_date=None,
    )
    assert row["lag_to_cite_months"] is None
    assert row["lag_to_l4_months"] is None
    assert row["censored_l4"] is True


def test_lag_row_both_reached():
    row = compute_lag_row(
        cd_id="CD013650", class_id="sglt2i_hfref", threshold_year=2019,
        body="esc",
        first_citing_pub_date=date(2021, 8, 27),
        first_l4_pub_date=date(2021, 8, 27),
    )
    assert row["lag_to_cite_months"] == months_between(date(2019, 7, 1), date(2021, 8, 27))
    assert row["lag_to_l4_months"] == row["lag_to_cite_months"]
    assert row["censored_l4"] is False


def test_build_lag_dataset_shape():
    threshold_dates = pd.DataFrame([
        {"cd_id": "CD013650", "class_id": "sglt2i_hfref", "threshold_year": 2019},
    ])
    citations = pd.DataFrame([
        {"cd_id": "CD013650", "body": "esc", "first_citing_pub_date": "2021-08-27"},
        {"cd_id": "CD013650", "body": "nice", "first_citing_pub_date": "2023-11-15"},
    ])
    l4 = pd.DataFrame([
        {"class_id": "sglt2i_hfref", "body": "esc", "first_l4_pub_date": "2021-08-27"},
        {"class_id": "sglt2i_hfref", "body": "nice", "first_l4_pub_date": "2023-11-15"},
    ])
    df = build_lag_dataset(threshold_dates, citations, l4, bodies=["esc", "acc_aha", "nice", "ccs"])
    assert len(df) == 4   # 1 class x 4 bodies
    assert set(df["body"]) == {"esc", "acc_aha", "nice", "ccs"}
    assert bool(df[df["body"] == "acc_aha"].iloc[0]["censored_l4"]) is True
