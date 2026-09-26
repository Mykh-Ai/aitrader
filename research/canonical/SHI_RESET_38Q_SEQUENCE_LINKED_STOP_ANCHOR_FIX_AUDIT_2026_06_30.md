# SHI RESET 38Q Sequence-Linked Stop Anchor Fix Audit

Verdict: SEQUENCE_LINKED_STOP_ANCHOR_FIXED

Scope: research-only policy replay stop-anchor fix. No Executor, orders, live trading, PnL, position sizing, live-readiness, strategy promotion, setup detection changes, Setup Builder changes, or qualified H1 sweep/reclaim gate changes.

## Problem

For `setup_000002`, the stage-gated replay used the corrected 38J structural stop as the policy stop:

- entry_candidate_ts: `2026-05-26T15:59:00Z`
- entry_candidate_price: `76476.8`
- old selected_stop_reference: `76717.03935`
- old selected_stop_type: `structural_zone_stop`
- sweep_h1_high: `78077.1`
- old stop_distance_usd: `240.23935`
- old tp1_price: `76236.56065`
- old TP1/BE outcome: `TP1_THEN_BE`

That stop is invalid for a bearish H1 sweep/reclaim sequence because it is below the sweep high and inside the sweep candle range. It created an artificial micro-TP1.

## Fix

For sequence-linked H1 sweep/reclaim policy replay, stop anchor selection now uses the sweep extreme unless a farther structural stop exists.

V0 buffer choice:
- `STOP_BUFFER_USD = 0.0`

SHORT rule:
- minimum valid stop = `sweep_h1_high + STOP_BUFFER_USD`
- structural stop is valid only if `structural_stop >= sweep_h1_high`
- structural stop below sweep high is rejected as `INVALID_STOP_INSIDE_SWEEP_RANGE`

LONG rule:
- maximum valid stop = `sweep_h1_low - STOP_BUFFER_USD`
- structural stop is valid only if `structural_stop <= sweep_h1_low`
- structural stop above sweep low is rejected as `INVALID_STOP_INSIDE_SWEEP_RANGE`

## setup_000002 Corrected Replay

- entry_candidate_ts remains: `2026-05-26T15:59:00Z`
- setup_formed_at remains review timestamp: `2026-05-26T16:59:00+00:00`
- rejected old stop: `76717.03935`
- rejected reason: `INVALID_STOP_INSIDE_SWEEP_RANGE`
- selected stop: `78077.1`
- selected_stop_type: `sweep_h1_high_stop`
- stop_distance_usd: `1600.3`
- tp1_price: `74876.5`

Policy outcomes after fix:
- `SELECTED_STOP_TARGET_POLICY` -> `TARGET_BEFORE_SELECTED_STOP`
- `TP1_BE_WITH_SELECTED_STOP_POLICY` -> `TP1_THEN_TARGET`

The old `TP1_THEN_BE` micro-stop outcome is invalidated.

## Required Outputs

Output root:
`market_monitor_runs/SHI_RESET_38Q_sequence_linked_stop_anchor_fix_v0/`

Files:
- `stop_anchor_fix_policy_results.csv`
- `stop_anchor_fix_summary.md`
- `stop_anchor_fix_manifest.json`
- `stage_gate_setup_rows.csv`
- `stage_gate_sequence_links.csv`
- `stage_gate_policy_replay_results.csv`
- `stage_gate_failures.csv`
- `stage_gate_summary.md`
- `stage_gate_manifest.json`

## Verification

- Focused stage-gate test includes invalid structural stop inside sweep range.
- `python -m pytest -q tests/test_stage_gate_replay.py` -> `3 passed`
- `python -m pytest -q tests/test_stage_gate_replay.py tests/test_policy_replay_fixed_stops.py` -> `12 passed`
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q` -> `716 passed, 11 warnings`
- `python -m compileall -q market_monitor\\run_stage_gate_replay.py market_monitor\\policy_replay_fixed_stops.py` -> passed
- Final `git diff --check` recorded in completion report.