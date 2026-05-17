# DATA_INVENTORY

Last updated: 2026-05-16

## Verdict

Primary `feed/` is valid before the outage and after recovery, but the window `2026-04-23 17:05:00` through `2026-05-06 22:51:00` UTC is contaminated in primary feed and must be treated as audit-only.

`feed_recovered/` exists for `2026-04-23` through `2026-05-06` and is usable for Analyzer/Backtester research with degraded provenance notes: funding is untrusted during the WS gap, historical liquidation quantities are missing/degraded, and funding/liquidation conclusions are unsupported unless explicitly marked degraded.

Official recovered Analyzer rerun was run in `analyzer_runs/recovered_gap_2026-04-23_2026-05-06/` on 2026-05-16. It produced successful Analyzer artifacts for all 14 recovered days: 405 setup rows, 203 shortlist/research summary rows, and 13 `FormalizationEligible=True` rows.

## Primary Gap Evidence Invalidation

Primary feed gap conclusions are invalid as market evidence.

FE=0 / no setup / no event inside the contaminated window must be treated as data outage, not market behavior.

## Data Windows

| Window | Source | Status | Research Use |
|---|---|---|---|
| 2026-03-10..2026-04-22 | `feed/` | Clean enough for current research, subject to normal feed caveats | Allowed |
| 2026-04-23 00:00..17:04 UTC | `feed/` | Partially valid primary day before outage | Allowed only with intraday cutoff awareness |
| 2026-04-23 17:05..2026-05-06 22:51 UTC | `feed/` | Contaminated synthetic/flat outage window | Audit-only; do not use for market conclusions |
| 2026-04-23..2026-05-06 | `feed_recovered/` | Recovered SHI-compatible feed | Allowed for research reruns with degraded funding/liquidation caveat |
| 2026-05-07..2026-05-14 | `feed/` | Clean post-gap local archive, 0 synthetic rows in checked files | Allowed |
| 2026-05-15..2026-05-16 | `feed/` from server sync | Complete 1440-row days with Analyzer runs copied locally after Sprint 03 | Backfill/audit only; not true holdout because timestamps are before Sprint 03 freeze |
| 2026-05-17 | `feed/` | Original zip state contains a single synthetic zero row after Sprint 03 freeze; server has only partial in-progress current-day data until UTC rotation | Not valid holdout evidence; wait for completed UTC day and feed audit PASS |

## Problem Days

| Date | Primary Rows | Primary Synthetic | Primary Verdict | Recovered Rows | Recovered Synthetic | Recovered Verdict | Analyzer/Backtester Use |
|---|---:|---:|---|---:|---:|---|---|
| 2026-04-23 | 1440 | 415 (28.82%) | Partially contaminated after 17:05 UTC | 1440 | 0 | Usable recovered mirror | Primary allowed only before outage; recovered preferred for full-day rerun |
| 2026-04-24 | 1440 | 1440 (100%) | Fully contaminated flat synthetic day | 1440 | 0 | Usable recovered mirror | Primary invalid; recovered allowed |
| 2026-04-25 | 1440 | 1440 (100%) | Fully contaminated flat synthetic day | 1440 | 0 | Usable recovered mirror | Primary invalid; recovered allowed |
| 2026-04-26 | 1440 | 1440 (100%) | Fully contaminated flat synthetic day | 1440 | 0 | Usable recovered mirror | Primary invalid; recovered allowed |
| 2026-04-27 | 1440 | 1440 (100%) | Fully contaminated flat synthetic day | 1440 | 0 | Usable recovered mirror | Primary invalid; recovered allowed |
| 2026-04-28 | 1440 | 1440 (100%) | Fully contaminated flat synthetic day | 1440 | 0 | Usable recovered mirror | Primary invalid; recovered allowed |
| 2026-04-29 | 1440 | 1440 (100%) | Fully contaminated flat synthetic day | 1440 | 0 | Usable recovered mirror | Primary invalid; recovered allowed |
| 2026-04-30 | 1440 | 1440 (100%) | Fully contaminated flat synthetic day | 1440 | 0 | Usable recovered mirror | Primary invalid; recovered allowed |
| 2026-05-01 | 1440 | 1440 (100%) | Fully contaminated flat synthetic day | 1440 | 0 | Usable recovered mirror | Primary invalid; recovered allowed |
| 2026-05-02 | 1440 | 1440 (100%) | Fully contaminated flat synthetic day | 1440 | 0 | Usable recovered mirror | Primary invalid; recovered allowed |
| 2026-05-03 | 1440 | 1440 (100%) | Fully contaminated flat synthetic day | 1440 | 0 | Usable recovered mirror | Primary invalid; recovered allowed |
| 2026-05-04 | 1440 | 1440 (100%) | Fully contaminated flat synthetic day | 1440 | 0 | Usable recovered mirror | Primary invalid; recovered allowed |
| 2026-05-05 | 1440 | 1440 (100%) | Fully contaminated flat synthetic day | 1440 | 0 | Usable recovered mirror | Primary invalid; recovered allowed |
| 2026-05-06 | 1389 | 1321 (95.10%) | Mostly contaminated; partial broken day | 1440 | 0 | Usable recovered mirror | Primary invalid; recovered allowed |

## Invalidated / Audit-Only Runs

Treat these as contaminated or audit-only unless rerun from `feed_recovered/`:

- `research/run_log.csv` rows for `2026-04-23_to_2026-04-23_run_001` through `2026-05-02_to_2026-05-02_run_001`.
- Local `analyzer_runs/2026-05-01_to_2026-05-01_run_001` through `analyzer_runs/2026-05-06_to_2026-05-06_run_001`.
- Any backtest/research artifact that reads primary `feed/` over `2026-04-23 17:05..2026-05-06 22:51` without an explicit clean cutoff.
- `FAILED_BREAK_RECLAIM_EXTENDED` artifacts with broad window names including `2026-03-30_to_2026-05-02` are audit-only as whole-window artifacts, even when a specific selected subset ends before the outage.

The official recovered rerun directories are the canonical replacement evidence for this gap window:

- Analyzer: `analyzer_runs/recovered_gap_2026-04-23_2026-05-06/`
- Backtester: `backtest_runs/recovered_gap_2026-04-23_2026-05-06/`

## Recovered Analyzer Audit

Official recovered rerun outcome:

- Output root: `analyzer_runs/recovered_gap_2026-04-23_2026-05-06/`
- Days: 14/14 successful.
- Total recovered Analyzer events: 269.
- Total recovered Analyzer setups: 405.
- Total recovered shortlist/research summary rows: 203.
- Total recovered `FormalizationEligible=True` rows: 13.
- Only `2026-04-24` had zero formalizable recovered rows in this rerun.

This confirms recovered feed restores Analyzer surface, but it does not create a promotable strategy.

## Recovered Backtester Rerun

Official recovered Backtester rerun outcome:

- Output root: `backtest_runs/recovered_gap_2026-04-23_2026-05-06/`
- Analyzer artifact days replayed: 14.
- Replay run dirs with `backtest_trades.csv`: 27.
- Trades: 154.
- Validation rows: 67, all `FAIL`.
- Promotion rows: 67, all `REJECT`.
- `PROMOTE`: 0.
- Cost model: `COST_MODEL_ZERO_SKELETON_ONLY`.
- Same-bar policy: `SAME_BAR_CONSERVATIVE_V0_1`.

This is clean recovered replay evidence, not an execution-ready result.
