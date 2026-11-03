"""Milestone 3: front-month price vs a monthly rolled position, and today's curve.

Run: python src/m3_rolled.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

import charts
from roll import expiry_date, rolled_returns

ROOT = Path(__file__).resolve().parents[1]
CHARTS = ROOT / "charts"
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)
charts.setup()
plt = charts.plt

df = pd.read_csv(ROOT / "data" / "clean" / "wti_c1_c4.csv", parse_dates=["date"])

# 1. Rolled position (holds contract 2, rolls monthly) - see roll.py.
r = rolled_returns(df)
r.to_csv(RESULTS / "rolled_daily.csv", index=False)
print(f"Days: {len(r)}, roll days: {r.is_roll.sum()} "
      f"({r.is_roll.sum() / ((r.date.iloc[-1] - r.date.iloc[0]).days / 365.25):.1f} per year)")

# 2. Check our calculated roll dates against the prices.
#    Neighbouring contracts move almost together. So on a real roll day, today's c1 and c2
#    should continue yesterday's c2 and c3; on a normal day, yesterday's c1 and c2.
#    For each day, see which story fits better. Only judge days where the two stories differ
#    by more than 10 cents. Then shift our dates by -3..+3 days: the right date should win.
v = df.dropna(subset=["c1", "c2", "c3"]).reset_index(drop=True)
p = v.shift()
misfit_roll = ((v.c1 - p.c2) - (v.c2 - p.c3)).abs()
misfit_none = ((v.c1 - p.c1) - (v.c2 - p.c2)).abs()
fits_roll = misfit_roll < misfit_none
clear = (misfit_roll - misfit_none).abs() > 0.10
our_rows = v.index[v.date.isin(r.date[r.is_roll])]
check = []
for shift in range(-3, 4):
    rows = [i + shift for i in our_rows if 0 < i + shift < len(v)]
    rows = [i for i in rows if clear[i]]
    check.append({"shift_days": shift, "share_fit_roll": fits_roll[rows].mean(), "days": len(rows)})
check = pd.DataFrame(check)
check.round(3).to_csv(RESULTS / "roll_date_check.csv", index=False)
others = clear & ~v.index.isin(our_rows)
print("Roll-date check (share of days whose prices fit a roll):")
print(check.to_string(index=False, formatters={"share_fit_roll": "{:.0%}".format}))
print(f"Ordinary days that fit a roll anyway (noise): {fits_roll[others].mean():.0%}")

# 3. Headline split: total = price + roll (log returns, so they add up).
def split(x):
    years = (x.date.iloc[-1] - x.date.iloc[0]).days / 365.25
    total, price, roll = x.total_ret.sum(), x.price_ret.sum(), x.roll_ret.sum()
    return pd.Series({"years": round(years, 1), "total_log": total, "price_log": price,
                      "roll_log": roll, "roll_per_year": roll / years,
                      "total_simple": np.exp(total) - 1})

periods = {"1985-2024 (all)": r}
for start, end in [(1985, 1989), (1990, 1999), (2000, 2009), (2010, 2019), (2020, 2024)]:
    periods[f"{start}-{end}"] = r[r.date.dt.year.between(start, end)]
table = pd.DataFrame({k: split(v) for k, v in periods.items()}).T
table.round(4).to_csv(RESULTS / "return_split.csv")
fmt = table.copy()
for c in ["total_log", "price_log", "roll_log", "roll_per_year", "total_simple"]:
    fmt[c] = table[c].map("{:+.0%}".format)
print("\nReturn split (log returns: total = price + roll)")
print(fmt.to_string())

c1_change = np.log(df.c1.dropna().iloc[-1] / df.c1.dropna().iloc[0])
print(f"\nFor comparison, front-month (c1) price change: {c1_change:+.0%} log "
      f"({df.c1.dropna().iloc[0]:.2f} -> {df.c1.dropna().iloc[-1]:.2f})")

# 4. Chart: spot-like front month vs rolled position, both = 100 at the start,
#    plus a second panel with the part that comes only from rolling.
first = df.dropna(subset=["c1"]).iloc[0]
spot = df.dropna(subset=["c1"]).set_index("date")["c1"] / first.c1 * 100
rolled = 100 * np.exp(r.set_index("date")["total_ret"].cumsum())
roll_only = 100 * np.exp(r.set_index("date")["roll_ret"].cumsum())

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7.5), sharex=True,
                               gridspec_kw={"height_ratios": [3, 2]})
# Log scale: equal vertical distance = equal % change, fair over 40 years.
# A log scale can't show a negative price, so 2020-04-20 is left out of the line and labelled.
ax1.set_yscale("log")
ax1.plot(spot.index, spot.where(spot > 0), color=charts.SERIES[1], linewidth=1.3,
         label="Front-month price (spot-like)")
ax1.plot(rolled.index, rolled, color=charts.SERIES[0], linewidth=1.3, label="Rolled futures position")
ax1.axhline(100, color=charts.FLAT, linewidth=1)
ax1.set_ylabel("Index (Jan 1985 = 100, log scale)")
ax1.yaxis.set_major_formatter(charts.matplotlib.ticker.FuncFormatter(lambda y, _: f"{y:g}"))
neg = df.loc[df.c1 <= 0].iloc[0]
ax1.annotate(f"{neg.date:%d %b %Y}: front month hit -${abs(neg.c1):.2f}"
             "\n(negative, can't be drawn on a log scale)",
             xy=(neg.date, spot[spot > 0].min()), xytext=(-12, 0), textcoords="offset points",
             ha="right", va="bottom", fontsize=8, color=charts.INK_2)
ax1.set_title("Holding WTI futures vs watching the front-month price")
for s, name in [(spot, "Front month"), (rolled, "Rolled")]:
    ax1.annotate(f"{name}: {s.iloc[-1]:.0f}", xy=(s.index[-1], s.iloc[-1]), xytext=(6, 0),
                 textcoords="offset points", va="center", fontsize=8, color=charts.INK_2)
ax1.legend(loc="upper left")

ax2.fill_between(roll_only.index, 100, roll_only, where=roll_only >= 100,
                 color=charts.BACKWARDATION, linewidth=0, alpha=0.85, label="Roll has added value")
ax2.fill_between(roll_only.index, 100, roll_only, where=roll_only < 100,
                 color=charts.CONTANGO, linewidth=0, alpha=0.85, label="Roll has cost value")
ax2.plot(roll_only.index, roll_only, color=charts.INK_2, linewidth=1)
ax2.axhline(100, color=charts.FLAT, linewidth=1)
ax2.set_ylabel("Roll yield only ($100 start)")
ax2.set_title("The gap: what rolling alone did to $100", fontsize=11)
ax2.legend(loc="upper left")
ax2.text(0, -0.2, "Rolled position holds contract 2 and rolls when contract 1 expires. "
         "No costs or cash interest. Source: EIA, Jan 1985 to Apr 2024.",
         transform=ax2.transAxes, color=charts.MUTED, fontsize=8)
charts.save(fig, CHARTS / "spot_vs_rolled.png")

# 5. Chart: roll yield by year.
by_year = r.groupby(r.date.dt.year)["roll_ret"].sum()
by_year.to_frame("roll_log_return").round(4).to_csv(RESULTS / "roll_yield_by_year.csv")
fig, ax = plt.subplots(figsize=(11, 4.2))
ax.bar(by_year.index, by_year * 100, width=0.8, linewidth=0,
       color=[charts.BACKWARDATION if v > 0 else charts.CONTANGO for v in by_year])
ax.axhline(0, color=charts.FLAT, linewidth=1)
ax.set_ylabel("% (log) per year")
low = by_year.idxmin()
ax.annotate(f"{low}: {by_year[low]:+.0%}", xy=(low, by_year[low] * 100), xytext=(6, 4),
            textcoords="offset points", fontsize=8, color=charts.INK_2)
ax.set_title("Roll yield earned by the rolled position, each year")
from matplotlib.patches import Patch  # noqa: E402
ax.legend(handles=[Patch(color=charts.BACKWARDATION, label="Backwardation: roll gain"),
                   Patch(color=charts.CONTANGO, label="Contango: roll cost")], loc="lower left")
ax.text(0, -0.16, "Sum of roll-day gains/losses. 2024 is a partial year (to Apr 5). Source: EIA.",
        transform=ax.transAxes, color=charts.MUTED, fontsize=8)
ax.margins(x=0.01)
charts.save(fig, CHARTS / "roll_yield_by_year.png")


# 6. Today's curve: try live Yahoo prices, otherwise use the saved sample.
MONTH_CODES = "FGHJKMNQUVXZ"


def next_contracts(today, n=12):
    """Tickers for the next n CL contracts still trading on `today`."""
    out, p = [], pd.Period(today, "M")
    while len(out) < n:
        p += 1   # candidate delivery month; it stops trading in the month before
        if expiry_date((p - 1).year, (p - 1).month) >= pd.Timestamp(today).normalize():
            out.append((f"CL{MONTH_CODES[p.month - 1]}{p.year % 100:02d}.NYM", p))
    return out


def live_curve():
    import warnings
    warnings.filterwarnings("ignore")   # yfinance prints pandas deprecation noise
    import yfinance as yf
    contracts = next_contracts(pd.Timestamp.today())
    px = yf.download([t for t, _ in contracts], period="10d", progress=False,
                     auto_adjust=False)["Close"]
    last = px.ffill().iloc[-1]
    curve = pd.DataFrame({"contract": [p.strftime("%b %Y") for _, p in contracts],
                          "ticker": [t for t, _ in contracts],
                          "price": [last.get(t, np.nan) for t, _ in contracts]}).dropna()
    if len(curve) < 6:
        raise ValueError(f"only {len(curve)} contracts came back")
    return curve, px.index[-1].date(), "live Yahoo Finance"


def sample_curve():
    s = pd.read_csv(ROOT / "data" / "raw" / "futures_yahoo_curve_sample.csv", parse_dates=["Date"])
    cl = [c for c in s.columns if c.startswith("CL")]
    row = s.dropna(subset=cl, how="all").iloc[-1]
    months = {c: MONTH_CODES.index(c[2]) + 1 for c in cl}
    curve = pd.DataFrame({"contract": [pd.Period(f"20{c[3:5]}-{months[c]:02d}", "M").strftime("%b %Y")
                                       for c in cl],
                          "ticker": cl, "price": [row[c] for c in cl]}).dropna()
    return curve, row["Date"].date(), "saved Yahoo sample (live download failed)"


try:
    curve, asof, source = live_curve()
except Exception as e:  # no internet, Yahoo changed, etc.
    print(f"\nLive curve failed ({type(e).__name__}: {e}); using the saved sample.")
    curve, asof, source = sample_curve()
curve.to_csv(RESULTS / "latest_curve.csv", index=False)
shape = "backwardation" if curve.price.iloc[1] < curve.price.iloc[0] else "contango"
print(f"\nLatest curve ({source}, {asof}): {shape}. "
      f"Front {curve.price.iloc[0]:.2f}, 12th {curve.price.iloc[-1]:.2f}")
print(curve.to_string(index=False))

fig, ax = plt.subplots(figsize=(9, 4.2))
ax.plot(range(len(curve)), curve.price, color=charts.SERIES[0], marker="o", markersize=5)
ax.set_xticks(range(len(curve)), curve.contract, rotation=45, ha="right")
ax.set_ylabel("$ per barrel")
ax.set_title(f"WTI futures curve on {asof}: {shape}")
ax.margins(y=0.15)
for i in [0, len(curve) - 1]:
    ax.annotate(f"${curve.price.iloc[i]:.2f}", xy=(i, curve.price.iloc[i]), xytext=(0, 8),
                textcoords="offset points", ha="center", fontsize=8, color=charts.INK_2)
ax.text(0, -0.32, f"Latest close of each delivery month. Source: {source}.",
        transform=ax.transAxes, color=charts.MUTED, fontsize=8)
charts.save(fig, CHARTS / "latest_curve.png")
