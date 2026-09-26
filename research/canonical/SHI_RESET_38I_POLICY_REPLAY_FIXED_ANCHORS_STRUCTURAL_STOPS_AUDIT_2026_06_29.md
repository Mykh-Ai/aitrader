# SHI_RESET_38I_POLICY_REPLAY_FIXED_ANCHORS_STRUCTURAL_STOPS_AUDIT_2026_06_29

## Scope

- Research-only policy replay using 38F fixed price-reference semantics and 38H selected structural stop candidates.
- Focus setup rows only.
- No sample expansion.
- No setup detection rule changes.
- No Setup Builder rule changes.
- No Backtester execution logic.
- No Executor.
- No orders.
- No live trading.
- No entries/exits.
- No PnL.
- No position sizing.
- No live-readiness.
- No strategy promotion.

## Inputs

- `market_monitor_runs/SHI_RESET_38G_live_like_bar_by_bar_state_replay_v0/focus_setup_alignment_check.csv`
- `market_monitor_runs/SHI_RESET_38H_structural_swing_stop_resolver_v0/structural_stop_reference_candidates.csv`
- `market_monitor_runs/SHI_RESET_38C_armed_manual_verdict_and_sequence_audit_v0/armed_setup_manual_verdicts.csv`
- `feed/`

## Outputs

- `market_monitor_runs/SHI_RESET_38I_policy_replay_fixed_anchors_structural_stops_v0/policy_replay_fixed_stop_results.csv`
- `market_monitor_runs/SHI_RESET_38I_policy_replay_fixed_anchors_structural_stops_v0/policy_replay_fixed_stop_summary.md`
- `market_monitor_runs/SHI_RESET_38I_policy_replay_fixed_anchors_structural_stops_v0/policy_replay_fixed_stop_manifest.json`

## Contract

38I uses:

- entry anchor = `tradable_entry_anchor`
- stop = `selected_research_stop_reference`
- target = `target_reference`

It does not use `setup_reference_level` as entry. `setup_reference_level` remains a structural/reference field.

## Result Summary

- Focus setup rows: 5
- Result rows: 10
- Rows by setup type:
  - `SUPPLY_SWEEP_RECLAIM_DOWN_SETUP`: 3
  - `SELLER_DOMINANCE_RETEST_DOWN_SETUP`: 2
- Rows by selected research stop type:
  - `local_swing_stop`: 4
  - `structural_zone_stop`: 1
- `SELECTED_STOP_TARGET_POLICY` outcomes:
  - `TARGET_BEFORE_SELECTED_STOP`: 4
  - `SELECTED_STOP_BEFORE_TARGET`: 1
- `TP1_BE_WITH_SELECTED_STOP_POLICY` outcomes:
  - `TP1_THEN_TARGET`: 5
- TP1 touched count: 10 result rows
- TP1 then target count: 5
- TP1 then BE count: 0
- Rejected/unresolved count: 1

## Primary Fixed Case

For `2026-06-25T11:59:00Z` / `SUPPLY_SWEEP_RECLAIM_DOWN_SETUP`:

- `setup_reference_level`: `59628.3709`
- `tradable_entry_anchor`: `61244.7`
- `setup_reference_used_as_entry`: `false`
- `selected_research_stop_reference`: `62200.0`
- `selected_research_stop_type`: `structural_zone_stop`
- `target_reference`: `zone_000102:SELL_SIDE:59500.93465-59560.46535`
- `target_zone_lower`: `59500.93465`
- `target_zone_upper`: `59560.46535`
- `stop_distance_usd`: `955.3`
- `target_distance_usd`: `1684.23465`
- `potential_r_to_target`: `1.763043`
- `tp1_price`: `60289.4`
- `target_touched_at`: `2026-06-25T13:49:00Z`
- `tp1_touched_at`: `2026-06-25T13:43:00Z`
- `SELECTED_STOP_TARGET_POLICY`: `TARGET_BEFORE_SELECTED_STOP`
- `TP1_BE_WITH_SELECTED_STOP_POLICY`: `TP1_THEN_TARGET`

The source-window high `61395.3` was not used as selected structural stop for this setup.

## Policy-Positive Setups

- `2026-03-26T01:59:00Z` / `SUPPLY_SWEEP_RECLAIM_DOWN_SETUP`
- `2026-03-26T07:59:00Z` / `SELLER_DOMINANCE_RETEST_DOWN_SETUP`
- `2026-06-23T08:59:00Z` / `SUPPLY_SWEEP_RECLAIM_DOWN_SETUP`
- `2026-06-25T11:59:00Z` / `SUPPLY_SWEEP_RECLAIM_DOWN_SETUP`

`2026-06-23T18:59:00Z` is policy-positive only under `TP1_BE_WITH_SELECTED_STOP_POLICY`; under full selected-stop-to-target replay it remains `SELECTED_STOP_BEFORE_TARGET`.

## Setups That Remain Weak

- `2026-06-23T18:59:00Z` / `SELLER_DOMINANCE_RETEST_DOWN_SETUP` under `SELECTED_STOP_TARGET_POLICY`

## Governance

The 38I manifest records:

- `sample_expanded=false`
- `focus_setup_rows_only=true`
- `watch_rows_evaluated=false`
- `changes_setup_detection_logic=false`
- `changes_setup_builder=false`
- `setup_reference_level_used_as_entry=false`
- `uses_tradable_entry_anchor=true`
- `uses_selected_research_stop_reference=true`
- `uses_backtester=false`
- `uses_executor=false`
- `uses_orders=false`
- `uses_entries_exits=false`
- `uses_pnl=false`
- `uses_position_sizing=false`
- `live_readiness_claim=false`
- `strategy_promotion=false`

## Verification

- Focused tests: `2 passed`
- Full suite: `694 passed, 11 warnings`

## Conclusion

38I corrects the invalid 38D-style interpretation by replaying policies from actual `tradable_entry_anchor` and selected 38H stop references. It is still research replay only. It does not prove edge, live-readiness, or executable strategy behavior.

