# SHI RESET 38H Structural Swing Stop Resolver Summary

Research-only stop reference comparison for existing 38G focus setups.

- Focus setup rows: 5
- Rows by selected_research_stop_type: {"local_swing_stop": 4, "structural_zone_stop": 1}
- Rows by setup_type: {"SELLER_DOMINANCE_RETEST_DOWN_SETUP": 2, "SUPPLY_SWEEP_RECLAIM_DOWN_SETUP": 3}
- Rows by sequence_role: {"CONFIRMATION_SETUP": 1, "CORRECTION_END_ENTRY_SETUP": 1, "HIGH_QUALITY_CONTINUATION_SETUP": 1, "INITIAL_IDEAL_SETUP": 1, "POST_IMPULSE_CORRECTION_PRECURSOR": 1}

## Required Conclusions

- Setup detection was not changed.
- Setup Builder rules were not changed.
- Stop references are classified and compared only; no entries/exits, orders, PnL, position sizing, Backtester, Executor, live-readiness, or strategy promotion are introduced.
- `setup_reference_level` remains a structural/reference level and is not treated as a tradable entry.
- Source-window high/low are context candidates and are not automatically selected as structural swing stops.
- For `2026-06-25T11:59:00Z`, the resolver compares original stop `61286.628`, source-window high `61395.3`, broader local swing high `61897.6`, and the manual `62000-62200` support-resistance flip review zone.

## 2026-06-25T11:59Z Check

- actual_setup_price: 61244.7
- tradable_entry_anchor: 61244.7
- setup_reference_level: 59628.3709
- source_window_high: 61395.3
- local_swing_high_candidate: 61897.6
- structural_zone: 62000.0 -> 62200.0 `support_resistance_flip_review_zone`
- selected_research_stop_reference: 62200.0 `structural_zone_stop`
- potential_r_from_selected_stop: 1.763043
