"""Milestone 2: curve shape - contango vs backwardation, and a monthly roll yield estimate.

Run: python src/m2_curve.py
"""
from pathlib import Path

import pandas as pd

import charts
from roll import label_curve

ROOT = Path(__file__).resolve().parents[1]
CHARTS = ROOT / "charts"
RESULTS = ROOT / "results"
CHARTS.mkdir(exist_ok=True)
RESULTS.mkdir(exist_ok=True)
charts.setup()
plt = charts.plt

df = pd.read_csv(ROOT / "data" / "clean" / "wti_c1_c4.csv", parse_dates=["date"])

# 1. Daily curve shape from the c2 - c1 spread.
curve = df.dropna(subset=["c1", "c2"]).copy()
curve["spread"] = curve["c2"] - curve["c1"]
curve["state"] = label_curve(curve["c1"], curve["c2"])
curve["year"] = curve["date"].dt.year

overall = curve["state"].value_counts(normalize=True)
print("Share of all days:", (overall * 100).round(1).to_dict())

# 2. Share of days in each state, by year.
share = pd.crosstab(curve["year"], curve["state"], normalize="index")
share = share.reindex(columns=["contango", "backwardation", "flat"], fill_value=0)
share.round(3).to_csv(RESULTS / "share_by_year.csv")

fig, ax = plt.subplots(figsize=(11, 4.2))
bottom = 0
for state, color in [("backwardation", charts.BACKWARDATION), ("flat", charts.FLAT),
                     ("contango", charts.CONTANGO)]:
    ax.bar(share.index, share[state] * 100, bottom=bottom, color=color, width=0.8,
           edgecolor=charts.SURFACE, linewidth=1, label=state.capitalize())
    bottom = bottom + share[state] * 100
ax.set_ylim(0, 100)
ax.set_ylabel("% of trading days")
ax.set_title("WTI curve shape: share of days in contango vs backwardation, by year")
ax.text(0, -0.16, "Contract 2 minus contract 1. Source: EIA, 1985 to Apr 2024 (2024 is a partial year).",
        transform=ax.transAxes, color=charts.MUTED, fontsize=8)
ax.legend(loc="upper left", bbox_to_anchor=(1, 1))
ax.margins(x=0.01)
charts.save(fig, CHARTS / "share_by_year.png")

# 3. The spread over time, shaded by sign. Clip the axis so April 2020 doesn't hide everything.
LIM = 4
fig, ax = plt.subplots(figsize=(11, 4.2))
x, s = curve["date"], curve["spread"]
ax.fill_between(x, 0, s.clip(lower=0), color=charts.CONTANGO, linewidth=0, label="Contango (c2 > c1)")
ax.fill_between(x, 0, s.clip(upper=0), color=charts.BACKWARDATION, linewidth=0,
                label="Backwardation (c2 < c1)")
ax.axhline(0, color=charts.FLAT, linewidth=1)
ax.set_ylim(-LIM, LIM)
ax.set_ylabel("$ per barrel")
ax.set_title("WTI spread: contract 2 minus contract 1")
peak = curve.loc[s.idxmax()]
ax.annotate(f"{peak.date:%b %Y}: +${peak.spread:.0f} (off chart)", xy=(peak.date, LIM * 0.97),
            xytext=(-40, -6), textcoords="offset points", ha="right", va="top", fontsize=8,
            color=charts.INK_2, arrowprops=dict(arrowstyle="-", color=charts.MUTED, lw=0.8))
ax.legend(loc="lower left", ncol=2)
charts.save(fig, CHARTS / "spread.png")

# 4. Monthly roll yield estimate. Measured on c2 vs c3 - the pair the Milestone 3 position
#    actually rolls between - which also keeps the expiring contract (and -$37.63) out of it.
#    (c2 - c3) / c3 = what you'd gain in about a month if prices didn't move. Positive = backwardation.
ry = df.dropna(subset=["c2", "c3"]).copy()
ry["roll_yield_est"] = (ry["c2"] - ry["c3"]) / ry["c3"]
monthly = ry.set_index("date")["roll_yield_est"].resample("ME").mean().dropna()
monthly.to_frame().round(5).to_csv(RESULTS / "monthly_roll_yield_estimate.csv")
print(f"Average monthly roll yield estimate: {monthly.mean():+.2%} "
      f"(about {monthly.mean() * 12:+.1%} a year)")

fig, ax = plt.subplots(figsize=(11, 4.2))
colors = [charts.BACKWARDATION if v > 0 else charts.CONTANGO for v in monthly]
ax.bar(monthly.index, monthly * 100, width=25, color=colors, linewidth=0)
ax.axhline(0, color=charts.FLAT, linewidth=1)
ax.set_ylabel("% per month")
ax.set_title("Estimated monthly roll yield (positive = backwardation pays you)")
ax.text(0, -0.16, "Monthly average of (c2 - c3) / c3. Source: EIA, 1985 to Apr 2024.",
        transform=ax.transAxes, color=charts.MUTED, fontsize=8)
from matplotlib.patches import Patch  # noqa: E402
ax.legend(handles=[Patch(color=charts.BACKWARDATION, label="Backwardation: roll gain"),
                   Patch(color=charts.CONTANGO, label="Contango: roll cost")], loc="lower left")
charts.save(fig, CHARTS / "monthly_roll_yield.png")

# 5. When does it flip? Label each month by the sign of its average spread.
m = curve.set_index("date")["spread"].resample("ME").mean().dropna().to_frame("avg_spread")
m["state"] = label_curve(0 * m["avg_spread"], m["avg_spread"])
m["run_id"] = (m["state"] != m["state"].shift()).cumsum()
runs = (m.reset_index().groupby("run_id")
        .agg(state=("state", "first"), start=("date", "first"), end=("date", "last"),
             months=("state", "size"), avg_spread=("avg_spread", "mean")))
runs["start"] = runs["start"].dt.strftime("%Y-%m")
runs["end"] = runs["end"].dt.strftime("%Y-%m")
runs.round(3).to_csv(RESULTS / "curve_regimes.csv", index=False)

print(f"\nMonths: {len(m)}, flips: {len(runs) - 1}")
print("Months in each state:", m["state"].value_counts().to_dict())
print("\nLongest stretches (6+ months):")
print(runs[runs.months >= 6].sort_values("start").to_string(index=False))
print("\nYears mostly in contango (>50% of days):",
      list(share.index[share.contango > 0.5]))
