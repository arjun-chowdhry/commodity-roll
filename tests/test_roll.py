import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from roll import expiry_date, roll_dates  # noqa: E402


def test_expiry_when_25th_is_weekend():
    # May 2020 contract: 25 April 2020 was a Saturday -> expired Tue 21 April 2020
    assert expiry_date(2020, 4) == pd.Timestamp("2020-04-21")


def test_expiry_when_25th_is_weekday():
    # May 2024 contract: 25 March 2024 was a Monday -> expired Wed 20 March 2024
    assert expiry_date(2024, 3) == pd.Timestamp("2024-03-20")


def test_roll_dates_one_per_month():
    dates = roll_dates("2023-01-01", "2023-12-31")
    assert len(dates) == 12
    assert all(d.day < 25 for d in dates)
