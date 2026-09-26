# SHI RESET 38P TP1/BE Directional Activation Fix Audit

Verdict: TP1_BE_DIRECTIONAL_ACTIVATION_CONTRACT_FIXED

Scope: research-only policy replay fix. No Executor, orders, live trading, position sizing, PnL, live-readiness, strategy promotion, setup detection changes, Setup Builder changes, or 38M/38O stage-gate changes.

## Bug Explanation

`TP1_BE_WITH_SELECTED_STOP_POLICY` must not treat BE as active at entry. BE becomes active only after TP1 is touched in the correct direction. The fix adds explicit same-candle TP1/BE ambiguity handling and regression tests for short and long direction-aware TP1 activation.

Policy contract now covered:
- SHORT TP1 requires price at or below `tp1_price`.
- LONG TP1 requires price at or above `tp1_price`.
- SHORT BE after TP1 requires price back at or above entry.
- LONG BE after TP1 requires price back at or below entry.
- Selected stop before TP1 remains terminal as `NO_TP1_SELECTED_STOP`.
- TP1 and BE in the same candle is `AMBIGUOUS_SAME_BAR`.

## Old 38P Outcome For setup_000002

- setup_id: `setup_000002`
- setup_review_ts: `2026-05-26T16:59:00+00:00`
- entry_candidate_ts: `2026-05-26T15:59:00Z`
- entry_candidate_price: `76476.8`
- policy: `TP1_BE_WITH_SELECTED_STOP_POLICY`
- old outcome: `TP1_THEN_BE`
- old first_event: `BE`
- old first_event_ts: `2026-05-26T16:23:00Z`

## Corrected Outcome

Corrected/verified outcome remains `TP1_THEN_BE` for `setup_000002`, because the feed shows a valid short TP1 touch before BE.

Exact timestamps:
- `tp1_touched_at`: `2026-05-26T16:13:00Z`
- `be_touched_at`: `2026-05-26T16:23:00Z`
- `selected_stop_touched_at`: empty
- `target_touched_at`: `2026-05-28T04:03:00Z`

Directional feed evidence:
- Entry candidate price: `76476.8`
- Short TP1 price: `76236.56065`
- At `2026-05-26 16:13:00`, low was `76171.00`, so short TP1 was touched first.
- At `2026-05-26 16:23:00`, high was `76485.00`, so BE was touched after TP1.
- Therefore this row is not evidence of BE being active at entry.

## New Fix Output Root

`market_monitor_runs/SHI_RESET_38P_tp1_be_directional_activation_fix_v0/`

Files:
- `tp1_be_directional_fix_policy_results.csv`
- `tp1_be_directional_fix_summary.md`
- `tp1_be_directional_fix_manifest.json`
- `stage_gate_setup_rows.csv`
- `stage_gate_sequence_links.csv`
- `stage_gate_policy_replay_results.csv`
- `stage_gate_failures.csv`
- `stage_gate_summary.md`
- `stage_gate_manifest.json`

## Verification

- `python -m pytest -q tests/test_policy_replay_fixed_stops.py tests/test_stage_gate_replay.py` -> `11 passed`
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q` -> `715 passed, 11 warnings`
- `python -m compileall -q market_monitor\policy_replay_fixed_stops.py market_monitor\run_stage_gate_replay.py` -> passed
- `git diff --check` -> clean
- `git status --short` -> modified `market_monitor/policy_replay_fixed_stops.py`, `tests/test_policy_replay_fixed_stops.py`; untracked 38P runner/audits/tests remain for staging

## Conclusion

The policy path now explicitly prevents BE from triggering before TP1 and marks same-candle TP1/BE ordering as ambiguous. The 2026-05-26 `setup_000002` result remains `TP1_THEN_BE` only because TP1 was directionally touched before BE in the source feed.