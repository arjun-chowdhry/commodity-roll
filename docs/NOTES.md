# Plain-English notes

Anything marked **(general knowledge)** comes from how markets work or market history, not from this project's data. Everything else is a number we measured.

---

## Futures in one minute (general knowledge)
A WTI crude oil futures contract is an agreement to buy 1,000 barrels of oil, delivered at Cushing, Oklahoma, in a specific month. There is a separate contract for every month: December 2026, January 2027, and so on. Each one stops trading around the 20th of the month before delivery.

The list of prices across those months is the **futures curve**. In this project:
- **Contract 1** (c1, the "front month") is the one expiring next.
- **Contract 2** (c2) is the one after that, and so on.

Nobody who wants oil "exposure" actually wants 1,000 barrels in their driveway. So investors hold a contract for a while and sell it before it expires. They then buy the next one. That switch is the **roll**.

## Contango
**Later months cost more than nearer months** (c2 > c1). The curve slopes up.

- **Why it happens (general knowledge):** oil is plentiful today. Someone could buy oil now, store it, and sell it later at the higher futures price. Storage and financing cost money, so the later price sits above today's price by roughly those costs. In a glut, when storage is filling up, contango gets very steep.
- **In our data:** WTI was in contango on **53.6% of days** from 1985 to April 2024. It was almost always in contango from 2005 to 2017. The longest unbroken stretch, counting whole months, ran from October 2008 to June 2013 (57 months).

## Backwardation
**Later months cost less than nearer months** (c2 < c1). The curve slopes down.

- **Why it happens (general knowledge):** oil is scarce *now*. Refiners and other users pay up to get barrels immediately. Holding physical oil has a benefit, sometimes called the *convenience yield*, because you can keep a refinery running.
- **In our data:** **45.7% of days.** It was common before 2004, again in 2021–22, and in the live curve on 2026-11-03. On that day, December 2026 was $96.96 and November 2027 was $80.05.

## Roll yield
When you roll, you sell the contract you hold and buy the next one.

- **Backwardation:** you sell the dearer contract and buy the cheaper one. With the same money you now hold slightly *more* oil, and as time passes the cheaper contract tends to drift up toward the spot price. **Positive roll yield.**
- **Contango:** you sell cheap and buy dear, so every month you hold slightly less oil. **Negative roll yield, meaning you pay to roll.**

A simple example: c2 is $80 and c3 is $82, which is contango. Rolling turns 1 contract into 80/82 = 0.976 of a contract, a 2.4% "cost" that happens whether or not oil prices move.

**In our data**, for a position that holds contract 2 and rolls monthly:
- **Contango months:** roll yield averaged **−0.95% a month**. **Backwardation months:** **+1.31% a month.**
- **By era:** about **+8.6% a year** in 1985–2003, about **−8.0% a year** in 2004–2017, and about **+1.9% a year** in 2018–2024.
- **The single worst roll was 22 April 2020.** The position sold the June contract at $11.57 and bought July at $18.69, losing 38% in one day (−48% in log terms).

## How the return splits up
Holding futures pays you three things (general knowledge):
1. **Price change:** what the oil price did.
2. **Roll yield:** what rolling added or cost.
3. **Interest on the cash you don't use:** a futures contract only needs a small margin deposit, so the rest of the cash earns T-bill interest. *We leave this out.*

This project measures 1 and 2. We use **log returns** because they add up neatly: total = price + roll, exactly. Rough translation: +100% in log terms means the value went up about 2.7×.

## Why USO lags oil
USO (United States Oil Fund) is an ETF that holds WTI futures, not barrels (general knowledge). It launched in 2006, just as WTI moved into a decade of mostly contango. It held the front month and rolled every month, so it kept paying the contango roll cost. Over the years, USO fell far behind the oil price that people saw on TV. Our data shows the same pattern: in 2010–2019 the rolled position lost **−64% (log) from roll yield alone**.

In April 2020, contango became extreme and the front month went negative (general knowledge). USO moved its holdings into later months, spreading its money across contracts up to a year out. That was partly to avoid the expiring contract and partly because exchanges limited its positions. It also did a 1-for-8 reverse split after its price collapsed.

The lesson people quote in interviews: **an oil ETF is not oil.** Its return is price change plus roll yield, and in contango the roll yield is a steady drag.

## "Spot-like" front month price
We don't have a true spot (physical) price series in this project. The front-month futures price is the usual stand-in: close to expiry, it should be close to the physical price at Cushing (general knowledge). The 2020-04-20 −$37.63 print shows that "close to expiry" can also mean "very strange".

## Reading the charts
- `share_by_year.png`: each bar is a year. Red is the share of days in contango and blue the share in backwardation. Long red runs (2005–2017) mean a long stretch of roll costs.
- `spread.png`: contract 2 minus contract 1, in dollars. Above zero is contango, below zero is backwardation. The axis is cut at ±$4, so April 2020 (+$58) runs off the chart.
- `monthly_roll_yield.png`: the estimated roll yield for each month, (c2 − c3) / c3. Blue means rolling paid, red means it cost.
- `spot_vs_rolled.png`: the top panel compares the front-month price with the rolled position, on a log scale. The bottom panel shows what roll yield *alone* did to $100. It peaked around 650 in 2005, then lost most of that over 2005–2020.
- `roll_yield_by_year.png`: the roll yield actually earned in each calendar year.
- `latest_curve.png`: the curve across the next 12 delivery months on the latest date available.

## Interview soundbites (from our numbers)
- "Over 1985 to April 2024, a rolled WTI position returned about +145% in log terms. Roughly +120 of that came from price and +24 from roll yield. But roll yield was +73 in just the late 1980s and −64 in the 2010s, so the long-run total hides two very different eras."
- "Roll yield is about the *shape* of the curve, not the *level* of the price. In contango you pay to roll even if oil goes nowhere."
- "One roll day in April 2020 cost 38%. That's why serious oil products avoid holding the expiring month."
