# AGENT_HANDOFF

Last updated: 2026-05-17

## 1. What This Project Is

AiTrader / Strategy Shi is a research and deterministic backtesting stack:

Aggregator -> Analyzer -> Backtester -> Phase 4 Bridge -> Executor

Only Aggregator, Analyzer, and Backtester research flow are active. Executor is planned and must not be run.

## 2. Current Phase

Phase 2 / Phase 3 overlap.

The project is searching for edge through Analyzer artifacts, deterministic replay, sidecar diagnostics, and candidate validation.

## 3. What Is Locked

- No live trading.
- No Executor.
- No cross margin.
- Execution target remains isolated margin only as a design constraint.
- Broad H1 remains a control family, not the main edge path.
- `entry_delay_1` is frozen for holdout; do not tune it.
- Sprint 03 freeze point is commit `23d1cc3`.
- Primary-feed outage window is contaminated.

## 4. Where Raw / Recovered Data Lives

- Primary feed: `feed/YYYY-MM-DD.csv`
- Recovered gap feed: `feed_recovered/YYYY-MM-DD.csv`
- Confirmed primary outage: `2026-04-23 17:05:00` through `2026-05-06 22:51:00` UTC.

Use `research/canonical/DATA_INVENTORY.md` before any data-window claim.

## 5. Where Analyzer Outputs Live

- Official/local copied runs: `analyzer_runs/`
- Official Sprint 02 recovered gap rerun: `analyzer_runs/recovered_gap_2026-04-23_2026-05-06/`

`analyzer_runs/2026-05-01..2026-05-06` are primary-feed contaminated/audit-only.

## 6. Where Backtester Outputs Live

- Routine/local copied backtests: `backtest_runs/`
- Official Sprint 02 recovered aggregate rerun: `backtest_runs/recovered_gap_2026-04-23_2026-05-06/`
- Sprint 03 formal candidate replay: `backtest_runs/sprint_03_candidate_rulesets/`
- Research sidecar backtester artifacts may also exist under `research/results/**/backtester_*`

Do not aggregate sibling derived runs into a promotion claim.

## 7. Current Active Candidates

- `CAND_SHORT_CTX_SPIKE_GE2_ENTRY_DELAY_1`: main validation candidate; formal replayable ruleset exists; `ACTIVE_VALIDATION / WAIT` pending true holdout and cost/same-bar review.
- `CAND_LONG_IMPULSE_FADE_LATE_US_STRUCTURAL`: passive watch only; sample too small; no formal ruleset mapping yet.

Read `research/canonical/CANDIDATE_REGISTRY.csv` and `research/canonical/ACTIVE_WATCHLIST.md`.

## 8. What Is Rejected

- Broad H1 reclaim as main edge path.
- Daily broad replay as primary research loop.
- `CAND_SHORT_IMPULSE_FADE_DEEP_RECLAIM_GT_0_6` as current formal ruleset.
- Current H4 EXTENDED_V1 as intended H4 evidence.
- Local H1 duplicate cluster family.
- Primary-feed gap FE=0 conclusions.
- Broad long filters outside late-US structural watch.

Read `research/canonical/REJECTED_FAMILIES.md`.

## 9. What Is Contaminated

Primary `feed/` from `2026-04-23 17:05` through `2026-05-06 22:51` UTC.

Do not use primary-feed outputs over that window as market evidence. Use recovered reruns.

Primary feed gap conclusions are invalid as market evidence. FE=0 / no setup / no event inside the contaminated window must be treated as data outage, not market behavior.

## 10. What Must Not Be Done

- Do not start live trading.
- Do not present any candidate as execution-ready.
- Do not mutate risk/exit logic to improve backtest.
- Do not use `H2_Post12Label_v1` as an entry input.
- Do not hide `REJECT` or negative findings.
- Do not physically delete research artifacts without an inventory.

## 11. First Commands / Files To Inspect

1. `Get-Content README.md -TotalCount 220`
2. `Get-Content research/OPS.md -TotalCount 220`
3. `Get-Content research/canonical/PROJECT_STATE_CURRENT.md`
4. `Get-Content research/canonical/DATA_INVENTORY.md`
5. `Import-Csv research/canonical/CANDIDATE_REGISTRY.csv`
6. `python -m pytest -q`
7. `Import-Csv research/run_log.csv | Group-Object routine_status`
8. `Get-ChildItem backtest_runs -Recurse -Filter backtest_promotion_decisions.csv`

## 12. Current Strategic Direction

Stop broad search loops. Move to controlled candidate validation:

Data repair -> canonical recovered reruns -> candidate registry -> frozen contracts -> pooled replay -> true forward holdout -> cost stress -> robustness -> promotion verdict -> only then Phase 4 Bridge.

Sprint 03 narrowed the active short path to `CAND_SHORT_CTX_SPIKE_GE2_ENTRY_DELAY_1`. It is WAIT, not PROMOTE.

True holdout starts only after Sprint 03 commit `23d1cc3`; everything before that commit is already-seen evidence.
