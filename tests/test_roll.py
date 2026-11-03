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


def test_label_curve():
    from roll import label_curve
    near = [50.0, 50.0, 50.0, None]
    far = [51.0, 49.0, 50.0, 50.0]
    labels = label_curve(near, far)
    assert list(labels[:3]) == ["contango", "backwardation", "flat"]
    assert pd.isna(labels[3])  # missing price -> no label


def test_rolled_returns_toy_example():
    import numpy as np
    from roll import rolled_returns
    # Contract 1 expires Wed 2024-03-20, so the roll happens on Thu 2024-03-21.
    # Curve is in backwardation: c3 is below c2, so rolling should earn money.
    toy = pd.DataFrame({
        "date": pd.to_datetime(["2024-03-18", "2024-03-19", "2024-03-20",
                                "2024-03-21", "2024-03-22", "2024-03-25"]),
        "c2": [80.0, 81.0, 82.0, 80.0, 81.0, 82.0],
        "c3": [79.0, 80.0, 79.0, 78.0, 79.0, 80.0],
    })
    r = rolled_returns(toy)

    assert list(r["is_roll"]) == [False, False, True, False, False]
    roll_day = r[r["is_roll"]].iloc[0]
    # On the roll day we held yesterday's c3 (79), which is today's c2 (80).
    assert np.isclose(roll_day["total_ret"], np.log(80 / 79))
    assert np.isclose(roll_day["roll_ret"], np.log(82 / 79))   # positive = backwardation pays
    assert np.isclose(roll_day["price_ret"], np.log(80 / 82))
    # Normal day: just the c2 price change, no roll part.
    assert np.isclose(r["total_ret"].iloc[0], np.log(81 / 80))
    assert r["roll_ret"].iloc[0] == 0
    # The split always adds up.
    assert np.allclose(r["price_ret"] + r["roll_ret"], r["total_ret"])


def test_contango_roll_costs_money():
    from roll import rolled_returns
    toy = pd.DataFrame({
        "date": pd.to_datetime(["2024-03-20", "2024-03-21"]),
        "c2": [80.0, 81.0],
        "c3": [82.0, 83.0],   # later contract dearer = contango
    })
    assert rolled_returns(toy)["roll_ret"].iloc[0] < 0
