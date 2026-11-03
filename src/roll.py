"""Roll math for WTI futures. Small, pure functions so they are easy to test."""
import numpy as np
import pandas as pd

BDAY = pd.offsets.BDay(1)


def expiry_date(year, month):
    """Last trading day of the WTI contract that trades out in `month` of `year`.

    Rule (general knowledge, CME): trading ends 3 business days before the 25th.
    If the 25th is not a business day, it ends 3 business days before the
    business day just before the 25th. Weekends only - exchange holidays are ignored,
    so a handful of dates can be off by one day.
    """
    d = pd.Timestamp(year, month, 25)
    if d.weekday() >= 5:          # Saturday or Sunday
        d = d - BDAY              # step back to Friday
    return d - 3 * BDAY


def roll_dates(start, end):
    """All contract-1 expiry dates between start and end (inclusive)."""
    months = pd.period_range(pd.Timestamp(start), pd.Timestamp(end), freq="M")
    dates = [expiry_date(p.year, p.month) for p in months]
    return [d for d in dates if pd.Timestamp(start) <= d <= pd.Timestamp(end)]


def label_curve(near, far):
    """Label each day's curve shape from a near and a far contract price.

    far > near -> "contango"       (later oil costs more)
    far < near -> "backwardation"  (later oil costs less)
    equal      -> "flat"; a missing price -> None
    """
    near, far = pd.Series(near, dtype=float), pd.Series(far, dtype=float)
    spread = far - near
    labels = pd.Series(None, index=spread.index, dtype=object)
    labels[spread > 0] = "contango"
    labels[spread < 0] = "backwardation"
    labels[spread == 0] = "flat"
    return labels


def rolled_returns(df):
    """Daily log returns of a position that always holds contract 2.

    df needs columns date, c2, c3. When contract 1 expires, yesterday's c3 becomes
    today's c2, so on that day we 'roll' and measure against yesterday's c3:
        normal day: total = log(c2_t / c2_{t-1})
        roll day:   total = log(c2_t / c3_{t-1})
    Split (exact, because logs add up):
        price = log(c2_t / c2_{t-1})          what the c2 price series did
        roll  = log(c2_{t-1} / c3_{t-1})      only on roll days; > 0 backwardation, < 0 contango
        total = price + roll
    """
    d = df.dropna(subset=["c2", "c3"]).sort_values("date").reset_index(drop=True)
    expiries = pd.DatetimeIndex(roll_dates(d["date"].min(), d["date"].max()))
    prev = d["date"].shift()
    # Roll day = first row after an expiry date (expiry day itself still has the old contract 1).
    d["is_roll"] = [bool(((p <= expiries) & (expiries < t)).any()) if pd.notna(p) else False
                    for p, t in zip(prev, d["date"])]
    d["price_ret"] = np.log(d["c2"] / d["c2"].shift())
    d["roll_ret"] = np.where(d["is_roll"], np.log(d["c2"].shift() / d["c3"].shift()), 0.0)
    d["total_ret"] = d["price_ret"] + d["roll_ret"]
    return d.iloc[1:].reset_index(drop=True)
