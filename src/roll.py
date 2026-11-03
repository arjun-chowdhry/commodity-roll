"""Roll math for WTI futures. Small, pure functions so they are easy to test."""
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
