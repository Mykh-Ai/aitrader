# SHI RESET 40C Own Signal Frozen Proxy Run

Date: 2026-10-14

Verdict: `NO_NET_PROFITABLE_FAMILY_ESTABLISHED_UNDER_FROZEN_COST_ASSUMPTIONS`.

The user authorized the full run after 40B1 preparation. The frozen v1 experiment has now generated AiTrader's own-feed signals, replayed entries/exits and produced a complete financial journal. Demand sweep/reclaim is positive before costs but negative after both assumed cost scenarios. Seller retest has one losing trade; supply sweep/reclaim has no admitted signals. No family can be called a profitable strategy from this run.

Run root: `market_monitor_runs/SHI_RESET_40C_own_signal_frozen_proxy_run_v0/`.

Source preparation: `market_monitor_runs/SHI_RESET_40B_own_signal_run_preparation_v1/`.

## Frozen scope and chronology

- Active contract: `SHI_RESET_40B_OWN_SIGNAL_RESEARCH_V1_SINGLE_MINUTE_SKIP` from `research/own_signal_run/contract_v1.json`. Trading hypotheses, exits, costs, periods, exclusions and code were not changed after viewing returns.
- Source: 310,213 selected minute-close observations, 230 frozen source files, March 11 13:45 through October 12 23:59 UTC. October 13 and later are outside the experiment. The final completed nominal H1 closes at October 12 23:00.
- The 40C folder retains the preparation contract, inventory, gaps, degradation and pre-run verification records. Their earlier preparation-only status is historical; `run_verification.json` is the completed-run status. `run_provenance.json` records the preparation source and copied artifact hashes.
- One `CausalSignalEngine` instance processed 5,170 H1 updates across weekly technical progress checkpoints. Market state, structural inventory, liquidity context, pending qualified sequences and setup context remained carried. Every reset flag is false. The source interval is processed from the beginning, including warm-up, exclusion, purge and exit-tail context.
- 37E pressure/state and 38M qualified sequence primitives supply the frozen research hypotheses. No Scout seeds, old Analyzer candidates, 38S rows, saved 38V/38W1 candidates or outcome-selected shortlist enter the run.
- Candidate evidence clocks are checked against the decision; planned entry follows one minute later. Actual entry uses the chronologically selected minute open, with geometry checked again.
- Exit remains full frozen structural target, initial stop or 48-hour expiry. Stop-first collision and adverse stop-gap rules apply. No TP1 partial, BE, trailing, live order, account sizing or legacy Backtester promotion gate is enabled.

## Candidate and entry accounting

Candidate decisions are event/reference records, not independent trades. Several reference levels or overlapping signals can concern the same market episode. The frozen one-position-per-family policy determines the financial sample.

| Family | Candidate decisions | Pass signal gates | Entered trades | Resolved | Censored |
| --- | ---: | ---: | ---: | ---: | ---: |
| Seller-dominance retest down | 1,211 | 1 | 1 | 1 | 0 |
| Supply sweep/reclaim down | 1,168 | 0 | 0 | 0 | 0 |
| Demand sweep/reclaim up | 1,362 | 62 | 20 | 20 | 0 |
| Total counts | 3,741 | 63 | 21 | 21 | 0 |

Forty-two gate-passing demand signals do not become trades: 34 encounter an already open family position and eight fail geometry at the actual entry open. This accounts for all 63 accepted signals. The ledger contains 63 rows because each of the 21 trades is priced under three cost scenarios; it does not contain 63 distinct trades.

All 27 family/period/cost combinations are present, including zero-trade results. No unresolved return is invented and no unfavorable completed trade is removed.

## Family results

R is raw entry-to-initial-stop price risk. Fees, adverse slippage and assumed carry are deducted in that same unit. Family books are independent: adding their R is not account equity or a portfolio result.

| Family | Trades | Zero-cost R | Assumed base net R | Assumed stress net R |
| --- | ---: | ---: | ---: | ---: |
| Seller-dominance retest down | 1 | -1.000000 | -2.033209 | -3.211737 |
| Supply sweep/reclaim down | 0 | No trades | No trades | No trades |
| Demand sweep/reclaim up | 20 | +4.378150 | -2.414304 | -10.124236 |

Base assumptions: 5 bps fee and 2 bps adverse slippage per fill, plus 0.1 bps adverse carry per elapsed hour. Stress: 10/5/0.2. Both fills are charged. These are frozen assumptions, not verified account tariffs or reconstructed actual funding/borrowing. The price market is `BTCUSDT_FEED_PRICE_PROXY`; this is not executable BTC/USDC Spot Margin evidence.

Demand has six target exits, thirteen stop exits and one positive expiry. Its base net win rate is 35%, mean is -0.120715 R/trade, profit factor is 0.862092 and cumulative trade-R drawdown is 11.235127 R. Mean holding time is 10.726667 hours. Base costs consume 6.792454 R: fee 4.587393, slippage 1.834957 and assumed carry 0.370104 R. Gross mean +0.218907 R/trade cannot cover that cost load.

Without its best three trades, demand is -4.270823 R even at zero cost, -10.181259 R at base and -16.902064 R at stress. This is a concentration diagnostic, not a newly selected strategy rule. Seller's single stop loses more than 1R after costs because its raw stop distance is only 13.772279 bps; that single observation is not enough to assess its expectancy.

## Chronological periods

| Demand period | Trades | Base net R |
| --- | ---: | ---: |
| Development: March 18 14:00-June 27 00:00 | 13 | -9.405810 |
| Chronological validation: June 29-August 30 | 4 | +1.290620 |
| Later historical validation: September 1-October 11 | 3 | +5.700886 |

Period ends are exclusive UTC timestamps. Two 48-hour purges carry context without entries; the final context tail permits exits. Seller's one trade is in development; supply has none in any period.

The two later demand intervals are positive on seven trades in total. The later interval contains three winning trades, so its no-loss profit-factor field is undefined rather than a usable infinite estimate. These tiny samples do not overturn the full-period negative base/stress result. Existing history was previously examined; none of these intervals is pristine untouched holdout. Selecting September or altering thresholds because of this result would be retrospective selection.

## Rejections and data omissions

- Demand's main overlapping rejection flags are nearest blocker below 2R (866 rows), directional delta (698) and volume expansion (670).
- Seller context fails on 1,168 of 1,211 decisions. Supply context fails on 1,165 of 1,168; the other three still fail at least one remaining gate. Zero supply trades is a restrictive-contract/no-sample result, not proof that short sweep/reclaim can never work.
- Rejection flag counts are nonexclusive and must not be added as independent candidate counts. Full counts and individual rows remain in the run root.
- Thirty-five synthetic/invalid primary observations are skipped in memory. Protected feed assets are unchanged. Recovered observations retain degraded provenance; the outage/post-outage exclusion and extended-gap policy remain frozen.
- Three resolved demand trades each skip one synthetic minute during the trade. They continue to their actual target/stop with original UTC time and costs. None is censored or dropped because of that minute. Their base returns are +2.418685 R, -1.256993 R and +2.261960 R. No actual entry needed a single-minute delay and no accepted candidate has an omission in its decision context in this full run.

## Verification and reproducibility

`_run_signal_chronology.py` is a run artifact that calls the frozen engine and emits weekly progress without resetting it. Signal generation took approximately 103.6 seconds. Financial replay used the package CLI:

```powershell
python -m research.own_signal_run replay --output market_monitor_runs/SHI_RESET_40C_own_signal_frozen_proxy_run_v0
python market_monitor_runs/SHI_RESET_40C_own_signal_frozen_proxy_run_v0/_verify_and_summarize.py
```

Generation refuses to overwrite an existing signals folder; preserve this study when creating a later version. Replaying the current CLI overwrites its replay outputs, so preserve the recorded result identities and use a separate version for changed studies.

Verification passed:

- frozen contract/code and all source hashes before and after the run;
- candidate and continuity file hashes, every accepted evidence clock and every entry price against the selected raw observation;
- exact startup-prefix parity with the original 40B1 smoke, including its 164 decisions and ten accepted signals;
- ordered contiguous nominal H1 chronology, prefix availability, all five reset fields false;
- complete accepted-to-admission-to-ledger accounting, one row per trade/cost, all 27 result combinations and correct entry periods/exclusions;
- no overlapping positions within an independent family book;
- independently recomputed gross R, both-fill fees, adverse slippage, elapsed carry and net R for all resolved ledger rows;
- net returns monotonically decline from zero to base to stress on each identical trade.

The unchanged frozen code already passed 752 tests, including 31 research-contract cases, during 40B1. This task checks actual run artifacts; passing executable checks does not prove trading edge. `run_verification.json` records the completed checks and `result_identity.json` hashes generated CSV evidence. Documentation diff validation is recorded in the project log.

Primary outputs: `signals/candidate_decisions.csv`, `signals/state_continuity.csv`, `financial_proxy_replay/entry_admission.csv`, `financial_proxy_replay/trade_ledger.csv`, `financial_proxy_replay/family_period_results.csv`, `family_overall_results.csv`, `family_month_results.csv`, `resolved_trade_economics.csv`, and the candidate/entry rejection count files.

## Implication

This completes the first bounded causal own-feed financial proxy run, with a negative cost-aware overall result. It does not complete the user's intended profitable trading system. Demand remains a research hypothesis with some positive later observations, substantial cost sensitivity, concentration and too little validation evidence. The short families are insufficiently sampled.

The next bounded research task should diagnose the cost-to-structural-risk and short-context restrictions before declaring any changed finite hypothesis. Preserve the negative baseline, freeze new rules before their replay, label historical selection honestly, and obtain genuinely subsequent confirmation before an edge claim. This task makes no automatic threshold search, production lifecycle promotion, active Backtester gate, Executor change, dependency install, network action, push or live trade.
