# SHI RESET 38S Live-Like Full-Feed Stage-Gate Scan Audit

Verdict: PASS / LIVE_LIKE_FULL_FEED_STAGE_GATE_SCAN_CREATED

## Scope

Research-only full-feed continuous stage-gate scan using current 38M/38O/38Q rules. No Executor, orders, live trading, Backtester campaign, PnL, position sizing, live-readiness, or strategy promotion.

## Input Files Used

- `market_monitor_runs\SHI_RESET_38J_wider_research_window_2026_05_23_to_2026_06_10_v0\wider_setup_classification_corrected.csv`
- `feed/*.csv`
- `feed_recovered/2026-04-23.csv through feed_recovered/2026-05-06.csv where present`
- `market_monitor/run_stage_gate_replay.py`
- `market_monitor/run_sequence_window_h1_replay.py`
- `market_monitor/qualified_h1_sweep_reclaim.py`
- `market_monitor/policy_replay_fixed_stops.py`

## Exact Commands Run

- `python market_monitor_runs\SHI_RESET_38S_live_like_full_feed_stage_gate_scan_v0\_build_live_like_full_feed_stage_gate_scan.py`
- `python -m compileall -q market_monitor`
- `python -m pytest -q tests/test_stage_gate_replay.py tests/test_policy_replay_fixed_stops.py`
- `git diff --check`
- `git status --short`

## Files Generated

- `market_monitor_runs/SHI_RESET_38S_live_like_full_feed_stage_gate_scan_v0/live_like_stage_gate_events.csv`
- `market_monitor_runs/SHI_RESET_38S_live_like_full_feed_stage_gate_scan_v0/live_like_sequence_candidates.csv`
- `market_monitor_runs/SHI_RESET_38S_live_like_full_feed_stage_gate_scan_v0/live_like_policy_allowed_candidates.csv`
- `market_monitor_runs/SHI_RESET_38S_live_like_full_feed_stage_gate_scan_v0/live_like_rejected_rows.csv`
- `market_monitor_runs/SHI_RESET_38S_live_like_full_feed_stage_gate_scan_v0/live_like_state_carry_forward_audit.csv`
- `market_monitor_runs/SHI_RESET_38S_live_like_full_feed_stage_gate_scan_v0/live_like_summary.md`
- `market_monitor_runs/SHI_RESET_38S_live_like_full_feed_stage_gate_scan_v0/live_like_manifest.json`
- `research/canonical/SHI_RESET_38S_LIVE_LIKE_FULL_FEED_STAGE_GATE_SCAN_AUDIT_2026_06_30.md`

## Summary

# SHI RESET 38S Live-Like Full-Feed Stage-Gate Scan

Research-only continuous scan. This is not a Backtester campaign and does not use Executor, orders, live trading, PnL, position sizing, live-readiness, or strategy promotion.

## Feed And Processing Scope

- Feed start: `2026-03-11T13:45:00Z`
- Feed end: `2026-06-28T23:59:00Z`
- Total bars processed: `157573`
- Technical day/file chunks: `110`
- Recovered degraded days used: `["2026-04-23", "2026-04-24", "2026-04-25", "2026-04-26", "2026-04-27", "2026-04-28", "2026-04-29", "2026-04-30", "2026-05-01", "2026-05-02", "2026-05-03", "2026-05-04", "2026-05-05", "2026-05-06"]`
- Setup/context source artifact: `market_monitor_runs\SHI_RESET_38J_wider_research_window_2026_05_23_to_2026_06_10_v0\wider_setup_classification_corrected.csv`
- Setup/context source coverage: `2026-05-24T05:59:00Z` -> `2026-06-09T17:59:00Z`
- Full M1/H1 feed state was loaded once and processed cumulatively; setup-source coverage is not overclaimed as full-feed setup discovery.

## Stage-Gate Counts

- Total setup/context rows: `9`
- Raw sweeps: `56`
- Qualified H1 sweeps: `3`
- Qualified H1 failed reclaims: `3`
- Sequence-linked candidates: `1`
- Policy replay allowed candidates: `1`
- Rejected rows by failed stage: `{"STAGE_2_QUALIFIED_H1_SWEEP": 8}`

## Specimen-Like Candidates

| setup_id | setup_formed_at | entry_candidate_ts | entry_candidate_price | qualified_h1_sweep_ts | stage_gate_status |
| --- | --- | --- | --- | --- | --- |
| setup_000002 | 2026-05-26T16:59:00+00:00 | 2026-05-26T15:59:00Z | 76476.8 | 2026-05-26T14:59:00Z | POLICY_REPLAY_ALLOWED |

- 2026-05-26 specimen reproduced: `true`

## State Carry-Forward Proof

- `live_like_state_carry_forward_audit.csv` records cumulative M1 bars, H1 bars, setup rows, raw sweeps, qualified sweeps, and qualified failed reclaims by processing day.
- Every day row has `market_state_reset=false`, `structure_levels_reset=false`, `liquidity_zones_reset=false`, `qualified_h1_state_reset=false`, and `setup_context_reset=false`.
- Day/file boundaries are marked `technical_chunk_only=true`; they are not market logic windows.

## Boundary Verdict

- RAW_SWEEP remains observation-only.
- Entry candidate timestamp remains reclaim/rejection close.
- `setup_formed_at` remains review time.
- Policy replay is allowed only for `sequence_valid_for_setup=true` rows.
- No Executor/orders/live/PnL/position sizing/live-readiness/strategy promotion was added.

## Test Results

- `python -m compileall -q market_monitor` -> passed.
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q` -> `716 passed, 11 warnings in 57.38s`.

## git diff --check Result

Clean; no whitespace errors reported.

## Final Git Status

`?? research/canonical/SHI_RESET_38S_LIVE_LIKE_FULL_FEED_STAGE_GATE_SCAN_AUDIT_2026_06_30.md`

Generated 38S run-output files are under ignored `market_monitor_runs/` storage and do not appear in `git status --short`.

## Verdict

PASS / LIVE_LIKE_FULL_FEED_STAGE_GATE_SCAN_CREATED
