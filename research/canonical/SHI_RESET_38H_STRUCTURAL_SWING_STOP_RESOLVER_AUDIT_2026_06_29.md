# SHI_RESET_38H_STRUCTURAL_SWING_STOP_RESOLVER_AUDIT_2026_06_29

## Scope

- Research-only structural swing-stop resolver.
- No sample expansion.
- No setup detection rule changes.
- No Setup Builder rule changes.
- No Backtester execution logic.
- No Executor.
- No orders.
- No entries/exits.
- No PnL.
- No position sizing.
- No live-readiness.
- No strategy promotion.

## Inputs

- `market_monitor_runs/SHI_RESET_38G_live_like_bar_by_bar_state_replay_v0/live_like_bar_by_bar_state_replay.csv`
- `market_monitor_runs/SHI_RESET_38G_live_like_bar_by_bar_state_replay_v0/focus_setup_alignment_check.csv`
- `market_monitor_runs/SHI_RESET_38C_armed_manual_verdict_and_sequence_audit_v0/armed_setup_manual_verdicts.csv`

## Outputs

- `market_monitor_runs/SHI_RESET_38H_structural_swing_stop_resolver_v0/structural_stop_reference_candidates.csv`
- `market_monitor_runs/SHI_RESET_38H_structural_swing_stop_resolver_v0/structural_stop_resolver_summary.md`
- `market_monitor_runs/SHI_RESET_38H_structural_swing_stop_resolver_v0/structural_stop_resolver_manifest.json`

## Behavior

38H classifies and compares available stop reference candidates for the existing 38G focus setup rows:

- `source_window_stop`
- `local_swing_stop`
- `structural_zone_stop`
- `original_invalidation_stop`

It does not create new setups, change setup detection, or decide entries. It only records a selected research stop reference for manual comparison and future audit.

## Result Summary

- Focus setup rows: 5
- Selected research stop types:
  - `local_swing_stop`: 4
  - `structural_zone_stop`: 1
- Setup types:
  - `SUPPLY_SWEEP_RECLAIM_DOWN_SETUP`: 3
  - `SELLER_DOMINANCE_RETEST_DOWN_SETUP`: 2
- Sequence roles:
  - `INITIAL_IDEAL_SETUP`: 1
  - `CONFIRMATION_SETUP`: 1
  - `POST_IMPULSE_CORRECTION_PRECURSOR`: 1
  - `HIGH_QUALITY_CONTINUATION_SETUP`: 1
  - `CORRECTION_END_ENTRY_SETUP`: 1

## Primary Fixed Case

For `2026-06-25T11:59:00Z` / `SUPPLY_SWEEP_RECLAIM_DOWN_SETUP`:

- `actual_setup_price`: `61244.7`
- `tradable_entry_anchor`: `61244.7`
- `setup_reference_level`: `59628.3709`
- `target_reference`: `zone_000102:SELL_SIDE:59500.93465-59560.46535`
- `original_stop_reference`: `61286.628`
- `source_window_high`: `61395.3`
- `source_window_stop_reference`: `61395.3`
- `local_swing_high_candidate`: `61897.6`
- `local_swing_stop_reference`: `61897.6`
- `structural_zone_lower`: `62000.0`
- `structural_zone_upper`: `62200.0`
- `structural_zone_role`: `support_resistance_flip_review_zone`
- `structural_zone_stop_reference`: `62200.0`
- `selected_research_stop_reference`: `62200.0`
- `selected_research_stop_type`: `structural_zone_stop`
- `stop_distance_usd`: `955.3`
- `target_distance_usd`: `1684.23465`
- `potential_r_from_selected_stop`: `1.763043`

This confirms that `59628.3709` remains a setup/reference level and is not treated as a tradable entry. It also confirms that `61395.3` is preserved as source-window context and is not automatically selected as the structural stop.

## Governance

The 38H manifest records:

- `sample_expanded=false`
- `changes_setup_detection_logic=false`
- `changes_setup_builder=false`
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
- Full suite: `692 passed, 11 warnings`

## Conclusion

38H is a stop-reference semantics layer, not a trading layer. It resolves the specific weakness found in 38F/38G research: source-window high/low must not be blindly treated as structural swing stops. The 2026-06-25 focus setup now has separate original, source-window, local-swing, and structural-zone stop candidates available for manual review.
