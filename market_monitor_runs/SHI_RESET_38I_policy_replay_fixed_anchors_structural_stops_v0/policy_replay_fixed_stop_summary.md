# SHI RESET 38I Policy Replay Fixed Anchors Structural Stops Summary

Research-only policy replay on the five existing 38G focus setup rows using 38F fixed entry anchors and 38H selected research stops.

- Total focus setup rows: 5
- Result rows: 10
- Rows by setup_type: {"SELLER_DOMINANCE_RETEST_DOWN_SETUP": 2, "SUPPLY_SWEEP_RECLAIM_DOWN_SETUP": 3}
- Rows by sequence_role: {"CONFIRMATION_SETUP": 1, "CORRECTION_END_ENTRY_SETUP": 1, "HIGH_QUALITY_CONTINUATION_SETUP": 1, "INITIAL_IDEAL_SETUP": 1, "POST_IMPULSE_CORRECTION_PRECURSOR": 1}
- Rows by selected_research_stop_type: {"local_swing_stop": 4, "structural_zone_stop": 1}
- Outcomes by policy_name: {"SELECTED_STOP_TARGET_POLICY": {"SELECTED_STOP_BEFORE_TARGET": 1, "TARGET_BEFORE_SELECTED_STOP": 4}, "TP1_BE_WITH_SELECTED_STOP_POLICY": {"TP1_THEN_TARGET": 5}}
- Target-before-stop count: 4
- Stop-before-target count: 1
- TP1 touched count: 10
- TP1 then target count: 5
- TP1 then BE count: 0
- Rejected/unresolved count: 1

## Policy-Positive Setups

- `2026-03-26T01:59:00Z` `SUPPLY_SWEEP_RECLAIM_DOWN_SETUP` `SELECTED_STOP_TARGET_POLICY` -> `TARGET_BEFORE_SELECTED_STOP`
- `2026-03-26T01:59:00Z` `SUPPLY_SWEEP_RECLAIM_DOWN_SETUP` `TP1_BE_WITH_SELECTED_STOP_POLICY` -> `TP1_THEN_TARGET`
- `2026-03-26T07:59:00Z` `SELLER_DOMINANCE_RETEST_DOWN_SETUP` `SELECTED_STOP_TARGET_POLICY` -> `TARGET_BEFORE_SELECTED_STOP`
- `2026-03-26T07:59:00Z` `SELLER_DOMINANCE_RETEST_DOWN_SETUP` `TP1_BE_WITH_SELECTED_STOP_POLICY` -> `TP1_THEN_TARGET`
- `2026-06-23T08:59:00Z` `SUPPLY_SWEEP_RECLAIM_DOWN_SETUP` `SELECTED_STOP_TARGET_POLICY` -> `TARGET_BEFORE_SELECTED_STOP`
- `2026-06-23T08:59:00Z` `SUPPLY_SWEEP_RECLAIM_DOWN_SETUP` `TP1_BE_WITH_SELECTED_STOP_POLICY` -> `TP1_THEN_TARGET`
- `2026-06-23T18:59:00Z` `SELLER_DOMINANCE_RETEST_DOWN_SETUP` `TP1_BE_WITH_SELECTED_STOP_POLICY` -> `TP1_THEN_TARGET`
- `2026-06-25T11:59:00Z` `SUPPLY_SWEEP_RECLAIM_DOWN_SETUP` `SELECTED_STOP_TARGET_POLICY` -> `TARGET_BEFORE_SELECTED_STOP`
- `2026-06-25T11:59:00Z` `SUPPLY_SWEEP_RECLAIM_DOWN_SETUP` `TP1_BE_WITH_SELECTED_STOP_POLICY` -> `TP1_THEN_TARGET`

## Setups That Remain Weak After Fixed-Anchor / Structural-Stop Replay

- `2026-06-23T18:59:00Z` `SELLER_DOMINANCE_RETEST_DOWN_SETUP` `SELECTED_STOP_TARGET_POLICY` -> `SELECTED_STOP_BEFORE_TARGET`

## Governance

- `setup_reference_level` was not used as entry.
- No setup rows were created.
- WATCH rows were not evaluated.
- Forward data was used only after `setup_formed_at` for outcome evaluation.
- No Backtester, Executor, orders, entries/exits, PnL, position sizing, live-readiness, or strategy promotion.
