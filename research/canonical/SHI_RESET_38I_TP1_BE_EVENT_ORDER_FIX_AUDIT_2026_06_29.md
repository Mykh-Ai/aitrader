# SHI_RESET_38I_TP1_BE_EVENT_ORDER_FIX_AUDIT_2026_06_29

## Scope

- Research-only fix for 38I TP1/BE policy event ordering.
- No sample expansion.
- No setup detection changes.
- No Setup Builder changes.
- No Backtester execution logic.
- No Executor.
- No orders.
- No entries/exits.
- No PnL.
- No position sizing.
- No live-readiness.
- No strategy promotion.

## Bug

For `2026-06-23T18:59:00Z` / `SELLER_DOMINANCE_RETEST_DOWN_SETUP`:

- `tradable_entry_anchor`: `62219.4`
- `selected_research_stop_reference`: `62837.1`
- `stop_distance_usd`: `617.7`
- `tp1_price`: `61601.7`
- `selected_stop_touched_at`: `2026-06-24T00:10:00Z`
- `tp1_touched_at`: `2026-06-24T13:42:00Z`
- `target_touched_at`: `2026-06-24T16:52:00Z`

The previous 38I artifact incorrectly allowed the later TP1/target sequence to override the earlier selected stop and returned:

- `first_event`: `TARGET`
- `policy_outcome_label`: `TP1_THEN_TARGET`

## Fix

`TP1_BE_WITH_SELECTED_STOP_POLICY` now evaluates the first event after setup among `selected_stop` and `TP1` before considering later target/BE events:

- If selected stop occurs before TP1, the TP1 policy outcome is terminal:
  - `first_event=SELECTED_STOP`
  - `policy_outcome_label=NO_TP1_SELECTED_STOP`
- If TP1 occurs before selected stop, target/BE/selected stop are evaluated after TP1.
- If selected stop and TP1 occur in the same candle, the result is marked `AMBIGUOUS_SAME_BAR`.

## Regenerated 38I Outputs

- `market_monitor_runs/SHI_RESET_38I_policy_replay_fixed_anchors_structural_stops_v0/policy_replay_fixed_stop_results.csv`
- `market_monitor_runs/SHI_RESET_38I_policy_replay_fixed_anchors_structural_stops_v0/policy_replay_fixed_stop_summary.md`
- `market_monitor_runs/SHI_RESET_38I_policy_replay_fixed_anchors_structural_stops_v0/policy_replay_fixed_stop_manifest.json`

## Corrected Regression Result

For `2026-06-23T18:59:00Z` / `TP1_BE_WITH_SELECTED_STOP_POLICY`:

- `first_event`: `SELECTED_STOP`
- `policy_outcome_label`: `NO_TP1_SELECTED_STOP`
- `evidence_summary` includes:
  - `selected_stop_touched_at=2026-06-24T00:10:00Z occurred before tp1_touched_at=2026-06-24T13:42:00Z`

## Updated Summary Counts

- `SELECTED_STOP_TARGET_POLICY`:
  - `TARGET_BEFORE_SELECTED_STOP`: 4
  - `SELECTED_STOP_BEFORE_TARGET`: 1
- `TP1_BE_WITH_SELECTED_STOP_POLICY`:
  - `TP1_THEN_TARGET`: 4
  - `NO_TP1_SELECTED_STOP`: 1
- TP1 then target count: 4
- TP1 then BE count: 0
- Rejected/unresolved count: 2

## Verification

- Focused 38I policy tests: `4 passed`
- Full suite: `696 passed, 11 warnings`

## Conclusion

The corrected 38I replay no longer counts a later TP1/target sequence as valid when the selected research stop was touched first. This remains a research-only replay fix and does not introduce setup detection, execution, orders, PnL, or live-readiness.
