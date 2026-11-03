# Data quality note

Source: `data/raw/futures_eia_c1_c4_sample.csv` (U.S. EIA daily NYMEX WTI settlement prices for contracts 1–4).
Clean output: `data/clean/wti_c1_c4.csv`, produced by `python src/m1_clean.py`.

## Coverage
- **9,861 trading days, 1985-01-02 to 2024-04-05.** Contracts 1 and 3 begin in 1983, but contracts 2 and 4 only begin in 1985, so 1985 is our start date.
- **The data stops in April 2024.** There are no contract 1–4 data after that in this sample, so all the history-based results end on 2024-04-05. The "today's curve" chart uses a different source (Yahoo).
- Natural gas columns (`RNGC*`) are in the raw file and get dropped.

## Checks and results

| Check | Result | What we do |
|---|---|---|
| Weekdays with no row | 382 in total, about 9.7 per year | Normal. Exchange holidays account for ~9 per year. Nothing to fix. |
| Gaps longer than 5 calendar days | 0 | None. |
| Blank cells | c1: 108, c2: 267, c3: 77, c4: 310 (703 rows have at least one blank) | **Kept blank, not filled.** Most are in 1986–2006, and contract 2 is missing about 20 days a year from 1994 to 2003. The blanks are spread through the month, not bunched around expiry. When a calculation needs a contract, it skips the days where that contract is blank. |
| Prices ≤ 0 | 1 row: **2020-04-20, c1 = −37.63** (c2 = 20.43) | **Kept** and flagged in `flag_nonpositive`. The price is real (see below). The rolled position holds contract 2, so it never touches this price. |
| Daily moves > 20% | 12 days: 1991-01-17 (start of the Gulf War air campaign, −33%) and 11 days in March–May 2020 (COVID demand collapse, price war, storage squeeze) | **Kept** and flagged in `flag_big_move`. All of them match known market events. |
| Stale prices (5+ identical closes) | 0 | None. |
| Neighbouring contracts > 20% apart | 21 cases, all in Dec 2008–Feb 2009 or April 2020 | **Kept.** These are periods of extreme contango (an oversupplied market with full storage), not bad prints. |

## Why the negative price is real (general knowledge)
On 20 April 2020, the May 2020 contract was one day from expiry. A futures contract left open at expiry means taking physical delivery of oil at Cushing, Oklahoma, and storage there was nearly full. Holders who couldn't take delivery paid other traders to take the contracts off their hands, so the price settled at −$37.63. The next contract (June) still traded at about +$20. This is the clearest real-world example of why you don't hold the front month into expiry.

## Known approximations
- **Roll dates are calculated, not taken from the data.** The EIA file doesn't say which contract month each column refers to on a given day. We use the CME rule instead: trading ends 3 business days before the 25th (general knowledge). We count weekdays only and ignore holidays, so a few roll dates may be off by a day. Milestone 3 checks the calculated dates against the price data (next section).

## Roll-date check (Milestone 3)
On the day the contracts roll, today's c1 and c2 should continue *yesterday's c2 and c3*. On any other day they should continue *yesterday's c1 and c2*. For each day, we test which story fits the prices better. Only days where the two stories differ by more than 10 cents count. We then shift our calculated roll dates earlier or later and rerun the test (`results/roll_date_check.csv`):

| Shift from our date | −3 | −2 | −1 | **0** | +1 | +2 | +3 |
|---|---|---|---|---|---|---|---|
| Days whose prices fit a roll | 10% | 15% | 33% | **90%** | 9% | 6% | 8% |

Ordinary (non-roll) days fit a roll about 10% of the time, which is the noise level. Our calculated date wins clearly. The higher reading at −1 is what you'd expect from occasional holiday errors and from prices converging on the expiry day itself.

A simpler first check asked only "is today's c1 closer to yesterday's c2 than to yesterday's c1?". It passed only 61% of roll days, because when the curve is flat, the spread between contracts is smaller than a normal day's move. That check was weak, not wrong, so we replaced it.

## The April 2020 roll
The rolled position holds contract 2, so it avoided the −$37.63 day. It still had to roll on 22 April 2020: it sold June at $11.57 and bought July at $18.69, losing 38% in one day. That is a real cost from the steepest contango in the data, not an error, so we keep it. It explains most of the gap between Milestone 2's smoothed estimate (+1.6% a year) and the roll yield actually earned (+0.6% a year). Without April–May 2020, the earned figure is +1.9% a year.
