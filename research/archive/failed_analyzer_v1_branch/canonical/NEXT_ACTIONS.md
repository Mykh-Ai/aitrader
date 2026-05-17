# NEXT_ACTIONS

Last updated: 2026-05-16

## 1. Immediate Hygiene Tasks

1. Treat `research/canonical/PROJECT_STATE_CURRENT.md` as the first state file for future agents.
2. Keep `research/canonical/CANDIDATE_REGISTRY.csv` updated after every material replay/watch update.
3. Do not physically move existing `research/findings/` or `research/results/` files until a separate traceability manifest is prepared.
4. Use `research/archive/` for future archived diagnostics or index files; current sprint created the directory but did not move legacy artifacts.

## 2. Data Repair Tasks

1. Preserve `analyzer_runs/recovered_gap_2026-04-23_2026-05-06/` as the official recovered Analyzer rerun.
2. Preserve `backtest_runs/recovered_gap_2026-04-23_2026-05-06/` as the official recovered aggregate Backtester rerun.
3. Keep recovered run lineage explicit in summaries and candidate reports.
4. Keep all primary-feed gap outputs marked contaminated/audit-only in future summaries.
5. Do not use funding/liquidation conclusions from recovered gap rows unless marked degraded.

## 3. Analyzer Tasks

1. Do not change baseline Analyzer contract for current candidates.
2. Keep `ReclaimDepthToImpulseRange` and long/short selector features in sidecar research until they are materialized by a formal candidate replay contract.
3. If recovered-window Analyzer outputs are rerun again, do not overwrite the Sprint 02 official directory without a new dated suffix.
4. If H4 is reopened, implement explicit H4 Candle A/B/C detector instead of patching current EXTENDED_V1.
5. Keep `H2_Post12Label_v1` as diagnostic outcome label only, never entry predicate.

## 4. Backtester Tasks

1. Add a formal fee/slippage/spread stress model for official candidate validation; current Sprint 02 cost stress is sidecar return-basis evidence.
2. Add per-candidate same-bar ambiguity summaries to validation output, not just canonical notes.
3. Add source concentration and single-day dominance summaries to official candidate-level replay reports.
4. Keep `COST_MODEL_ZERO_SKELETON_ONLY` clearly labeled as non-production.
5. Do not mutate risk logic to make a candidate pass.

## 5. Candidate Validation Tasks

1. Run true forward holdout for `CAND_SHORT_CTX_SPIKE_GE2_ENTRY_DELAY_1` with no parameter changes after the Sprint 03 freeze timestamp.
2. Keep `CAND_SHORT_IMPULSE_FADE_DEEP_RECLAIM_GT_0_6` rejected under Sprint 03 formal mapping; do not retune threshold.
3. If deep reclaim is ever reopened, treat it as a new pre-declared candidate with a new holdout clock.
4. Continue `CAND_LONG_IMPULSE_FADE_LATE_US_STRUCTURAL` with the frozen watch selector only.
5. Keep current `CAND_H4_FAILED_BREAK_RECLAIM_EXTENDED_V1` quarantined; rebuild detector before any replay.
6. For every candidate, report raw and cluster-first results at 30m/60m/120m/240m/480m/1440m.
7. For every candidate, report top 1/2/3 winner and loser concentration.

## 6. Documentation / Context Tasks

1. Keep `DATA_INVENTORY.md` aligned with any recovered rerun.
2. Add a short note to new findings when they exclude or replace `2026-04-23 17:05..2026-05-06 22:51`.
3. Keep `AGENT_HANDOFF.md` current after major research-cycle changes.
4. If server runs are performed, update `research/run_log.csv` without duplicating run IDs.

## 7. Stop-Doing List

1. Do not run Executor.
2. Do not call any candidate live-ready.
3. Do not continue broad H1 daily replay as the main strategy search loop.
4. Do not use synthetic-gap FE=0 as market evidence.
5. Do not add more filters to `entry_delay_1` before true holdout.
6. Do not reuse current H4 EXTENDED_V1 as H4 candle setup evidence.
7. Do not hide negative or `REJECT` results.
