# SHI RESET 40D Own Signal Strategy Search

Date: 2026-10-14.

Verdict: `HISTORICALLY_SELECTED_CANDIDATE_MEETS_USER_MONETARY_BENCHMARK`.

The user explicitly authorized iterative research after the negative 40C baseline, accepted the lightweight research replay, and specified $3,000 per position, $5 total commission per completed trade and at least $500 net on roughly six months of history. This is distinct from 40B's frozen three-hypothesis experiment. No old preparation, source data or completed baseline result was rewritten.

Implementation: `research/strategy_search/`. Run root: `market_monitor_runs/SHI_RESET_40D_own_signal_strategy_search_v0/`. Current rules: `selected_strategy.json`.

## What changed and why

40C's nearest opposite H1 blocker produced very small structural reward distances, while broad pressure-score gates almost eliminated short entries. The 37E/37F audits document pressure/classifier asymmetry and missed downward context. The 39A audit identifies accepted-break versus reclaim, maturity and structural-risk gaps. These findings informed research variants; they did not promote new production Monitor policy.

The search compares direct causal own-feed structure/price/volume/delta context: two-close accepted breaks, breakouts, trend retests and sweep/reclaim hypotheses. It tests broader structural stops, predeclared reward multiples and holding horizons. A maturity filter rejects chasing excessive distance from EMA24 and unusually large H1 displacement bars. Batch grids and code identities precede their evaluations. The hybrid's inputs were declared before its seed evaluation, and its code was frozen for subsequent exact reproduction. Further batches are explicitly adaptive and use previously observed history; they are not pristine holdout tests.

Recorded batches: 4,608 initial variants; 335 expanded minute replays from that same grid; 7,776 maturity/context variants; 1,728 retest refinements; 1,152 long-horizon variants; one declared directional hybrid. These are 15,264 grid configurations plus the hybrid, not independent statistical trials. Exact grids, results and rejected variants remain in the run root. A separate short-gap stop-debit scenario produced a positive modeled result but is **not** used in the selected candidate. Original source for batches 01-03 was saved before the later gap-sensitivity/source additions.

## Frozen selected rule

Common: full prior history; closed right-labeled UTC H1; one global position; three-minute post-exit cooldown; one-minute entry latency; next observed eligible minute open; one isolated missing/synthetic minute is skipped with actual clock retained. Trading references require usable prior bars. Recovery/post-outage exclusion and seven-day context-only period purges remain explicit. Entry end is October 1; later source is an exit tail.

LONG: price EMA24 > EMA72, close > EMA168; H1 low touches EMA24 and completed green close returns above it; signed delta >=0.04; volume >=1.3 of prior 24-H1 median; displacement from EMA24 <=1.5 ATR(24); H1 range <=2 ATR(24). Prior 96 H1 bars must be usable. Initial stop is the farther of the buffered prior-six-H1 low and entry minus 2 ATR. Full target is 10 initial price-risk distances above actual entry.

SHORT: a known prior 48-H1 lower reference is frozen before two successive completed closes below it; 24-hour downward price/negative-delta alignment (price change <0, aggregate delta <0); current signed delta <=0; volume ratio >=1.3. Initial stop is the farther of buffered prior-six-H1 high and entry plus 1.5 ATR. Full target is 6 initial price-risk distances below entry.

Stop buffer: 5 bps. Initial price risk must be 0.4%-4% of entry. Both sides expire after 168 elapsed hours. Conflicting LONG/SHORT families skip rather than choose by outcome. Minute replay uses stop-first collisions, adverse opening stop gaps, fixed targets and actual elapsed expiry. There are no partial/BE/trailing exits in this selected rule.

Position notional is $3,000 per independent sequential trade, not $3,000 risk. Quantity is 3000/raw entry. Commission is $5 total per resolved trade; adverse slippage is 2 bps per fill. No compounding, leverage allocation, live sizing or borrowing behavior is introduced.

## Monetary result

| Entry cohort | Trades | Gross USD | Commission USD | Slippage USD | Net USD |
| --- | ---: | ---: | ---: | ---: | ---: |
| Full source's eligible entries, March 18-September 30 | 26 | +673.553044 | 130.000000 | 31.277029 | **+512.276015** |
| Predeclared six months, April 1-September 30 | 23 | +721.704434 | 115.000000 | 27.685442 | **+579.018992** |

Cash is summed across one global book, unlike 40C's independent family R books. Positions opened before the cohort start can occupy the book; cohort results are attributed by entry and include the subsequent exit tail. This is not a compounded account balance or an intratrade floating-equity curve.

Full sample: 14 longs, 12 shorts; 26 observed outcomes; zero censored or conservative gap marks. Long/retest net +442.443309 USD; short/accepted-break net +69.832705 USD. There are 16 stops, six expiries and four targets. Mean net +19.702924 USD / +0.767263R; total normalized net +19.948835R. April-September mean +25.174739 USD / +0.924612R; total +21.266072R. Profit factor 1.578414; closed-trade cash drawdown 459.172245 USD; mean hold 70.767308 hours.

Initial risk mean 48.777537 USD, range 18.268634-74.387704 USD. Planned target mean 380.174589 USD /8.153846R. Four attained targets average +238.283234 USD net, planned multiple 8R and 55.870833 hours to touch. Planned reward is not confused with realized return.

## Verification

- 762 tests passed, 11 existing warnings, in 56.75s with a fresh neutral workspace basetemp. Ten new meaningful cases cover monetary accounting, dynamic risk, true minute target/stop order, skipped entry/trade minutes, expiry, recovered data separation, causal features, conflicts and one global book.
- Source/code identity matches the original v1 preparation before/after. All 230 selected source hashes remain frozen; selected feed has 310,213 rows. Protected primary/recovered files were not modified.
- `_verify_selected_candidate.py` reproduces the original hybrid seed ledger, validates code identity, compares a nontrivial real June 20 prefix against the same chronology with future feed appended, and independently checks first terminal touches, entry prices, structural stop formulas, target multiples and every dollar cost/PnL.
- The same verifier checks global concurrency/cooldown, observed RAW execution paths, actual clocks, no conservative missing-data marks and both user monetary thresholds. Four isolated omitted minutes remain in the selected journal without interrupting trades. Actual extended/recovered paths remain censored and fail qualification.
- CSV/JSON selected artifacts have recorded SHA-256 identities. `git diff --check` is recorded in the project log.

## Limits and scope

This fulfills the requested historical monetary benchmark under the stated fee/slippage model. It does not establish a statistically validated profitable live strategy. The rules were selected after an extensive adaptive search of already researched history; period tables are descriptive and cannot be relabeled independent holdout. The 26-trade sample is small and concentrated: without the best three trades its full result is -326.621333 USD. This negative sensitivity is preserved rather than concealed.

Prices are `BTCUSDT_FEED_PRICE_PROXY_USD_REPORTING` with USDT/USD parity assumed. Actual BTC/USDC execution, borrowing interest, account tariffs and exchange-fill microstructure are unverified/unmodeled. The user's $5 commission is an input. Reported net means after that commission and explicit 2-bps slippage, not all possible real account costs.

No production Monitor/Executor source, legacy Backtester gate, source feed, server, network, dependency, commit or remote branch was changed by this task. The 39A architecture remains canonical, and no edge/live/production governance is promoted. The selected rule and its full journal are ready for subsequent fixed-rule confirmation; no untouched-data confirmation has been performed.
