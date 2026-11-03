"""Milestone 1: build a clean daily table of WTI contracts 1-4 and run quality checks.

Run: python src/m1_clean.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "futures_eia_c1_c4_sample.csv"
CLEAN = ROOT / "data" / "clean" / "wti_c1_c4.csv"
COLS = ["c1", "c2", "c3", "c4"]

# 1. Load, keep WTI only, rename, start when all four contracts exist (1985).
raw = pd.read_csv(RAW, parse_dates=["date"])
df = raw[["date", "RCLC1", "RCLC2", "RCLC3", "RCLC4"]].copy()
df.columns = ["date"] + COLS
df = df[df["date"] >= "1985-01-02"].dropna(how="all", subset=COLS)
df = df.sort_values("date").reset_index(drop=True)

print(f"Rows: {len(df)}  from {df.date.min().date()} to {df.date.max().date()}")

# 2. Missing values.
print("\nMissing values per contract:")
print(df[COLS].isna().sum().to_string())

# 3. Gaps: business days (Mon-Fri) with no row. Exchange holidays count here,
#    so roughly 9 per year are expected.
all_bdays = pd.bdate_range(df.date.min(), df.date.max())
missing = all_bdays.difference(df["date"])
per_year = len(missing) / (len(all_bdays) / 261)
print(f"\nWeekdays with no row: {len(missing)} ({per_year:.1f} per year, holidays ~9/yr)")
gaps = df["date"].diff().dt.days
big = df.loc[gaps > 5, "date"]
print(f"Gaps longer than 5 calendar days: {len(big)}")
for d in big:
    i = df.index[df.date == d][0]
    print(f"  {df.date[i-1].date()} -> {d.date()} ({gaps[i]:.0f} days)")

# 4. Negative or zero prices.
bad = df[(df[COLS] <= 0).any(axis=1)]
print(f"\nRows with a price <= 0: {len(bad)}")
print(bad.to_string(index=False))

# 5. Outliers: daily moves bigger than 20% (absolute). Flag, do not remove.
#    Use price differences divided by |previous price| so negative prices don't break it.
moves = df[COLS].diff() / df[COLS].shift().abs()
outliers = df.loc[(moves.abs() > 0.20).any(axis=1), "date"]
print(f"\nDays with a >20% move in any contract: {len(outliers)}")
for d in outliers:
    i = df.index[df.date == d][0]
    print(f"  {d.date()}  " + "  ".join(f"{c}:{moves.loc[i, c]:+.0%}" for c in COLS))

# 6. Stale prices: same value 5+ days in a row (sign of a frozen feed).
stale = {c: int((df[c].diff() == 0).rolling(4).sum().eq(4).sum()) for c in COLS}
print(f"\nStale runs (5+ identical closes): {stale}")

# 7. Neighbouring contracts far apart (> 20% of the nearer price): possible bad print.
far = []
for a, b in [("c1", "c2"), ("c2", "c3"), ("c3", "c4")]:
    gap = (df[b] - df[a]).abs() / df[a].abs()
    far += list(df.loc[gap > 0.20, "date"].dt.date.astype(str) + f" {a}/{b}")
print(f"\nNeighbour contracts >20% apart: {len(far)} -> {far}")

# 8. Save. Keep every row, including 2020-04-20 (it is a real price).
df["flag_nonpositive"] = (df[COLS] <= 0).any(axis=1)
df["flag_big_move"] = df["date"].isin(outliers)
CLEAN.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(CLEAN, index=False)
print(f"\nSaved {CLEAN.relative_to(ROOT)}")
