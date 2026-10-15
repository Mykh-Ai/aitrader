# SHI RESET 38W1 Chronological TP1/Stop Label Fix

Research-only correction of 38W outcome labels on canonical 38V setup_builder candidates only.

## Governance

- This is not live trading.
- This does not prove edge.
- This does not use old Analyzer v1.
- This does not use old Backtester.
- This evaluates canonical setup_builder candidates only.
- 38S rows remain rejected as source candidates.
- No Executor, orders, PnL, position sizing, live-readiness, or strategy promotion.
- MFE/R after selected stop is not counted as trade-quality evidence.
- Manual shortlist excludes rows where selected_stop_touched_at <= tp1_touched_at.

## Corrected Counts

- Canonical setup_builder candidates replayed: 51
- Valid TP1-before-stop reactions: 34
- Target-before-stop / full target continuation: 2
- TP1 then target: 2
- STOP_BEFORE_TP1 rows: 17
- Unresolved / insufficient: 0
- Manual monitor shortlist rows: 30
- Manual monitor reject rows: 21
- ARMED/HIGH valid reaction: 20 of 31
- Non-specimen ARMED/HIGH valid reaction: 19 of 30
- 2026-05-26 specimen remains strong: true

## Splits

- By setup_type: {"DEMAND_SWEEP_RECLAIM_UP_SETUP": 9, "SELLER_DOMINANCE_RETEST_DOWN_SETUP": 28, "SUPPLY_SWEEP_RECLAIM_DOWN_SETUP": 14}
- By direction_context: {"DOWN": 42, "UP": 9}
- By trigger_status: {"ARMED": 43, "WATCH": 8}
- By candidate_strength: {"HIGH": 33, "LOW": 1, "MEDIUM": 17}
- By ARMED/HIGH bucket: {"false": 20, "true": 31}
- By outcome_label: {"STOP_BEFORE_TP1": 17, "TP1_ONLY_NO_FOLLOWUP": 1, "TP1_THEN_BE": 31, "TP1_THEN_TARGET": 2}
- By manual_monitor_verdict: {"DATA_COVERAGE_REVIEW": 4, "MANUAL_REVIEW_PRIMARY": 20, "MANUAL_REVIEW_SECONDARY": 10, "WEAK_REACTION_REJECT": 17}
- Policy outcomes: {"SELECTED_STOP_TARGET_POLICY": {"NO_DECISIVE_OUTCOME": 1, "SELECTED_STOP_BEFORE_TARGET": 48, "TARGET_BEFORE_SELECTED_STOP": 2}, "TP1_BE_WITH_SELECTED_STOP_POLICY": {"STOP_BEFORE_TP1": 17, "TP1_ONLY_NO_FOLLOWUP": 1, "TP1_THEN_BE": 31, "TP1_THEN_TARGET": 2}}

## Verdict

38W was positive as proof that the monitor sees reactions, but 38W1 rejects the earlier 51/51 quality reading. The corrected valid reaction set is based on chronological TP1-before-stop only, with full target continuation remaining limited to the target-before-stop rows.

## Manual Monitor Shortlist

- setup_000001 2026-03-12T16:59:00Z UP DEMAND_SWEEP_RECLAIM_UP_SETUP TP1_THEN_BE quality_mfe_before_stop_r=1.480914 verdict=MANUAL_REVIEW_SECONDARY
- setup_000002 2026-03-14T07:59:00Z UP DEMAND_SWEEP_RECLAIM_UP_SETUP TP1_THEN_BE quality_mfe_before_stop_r=1.205658 verdict=MANUAL_REVIEW_SECONDARY
- setup_000003 2026-03-17T04:59:00Z DOWN SELLER_DOMINANCE_RETEST_DOWN_SETUP TP1_THEN_BE quality_mfe_before_stop_r=2.0249 verdict=MANUAL_REVIEW_PRIMARY
- setup_000005 2026-03-19T07:59:00Z DOWN SELLER_DOMINANCE_RETEST_DOWN_SETUP TP1_THEN_BE quality_mfe_before_stop_r=2.200912 verdict=MANUAL_REVIEW_PRIMARY
- setup_000006 2026-03-21T21:59:00Z DOWN SELLER_DOMINANCE_RETEST_DOWN_SETUP TP1_THEN_BE quality_mfe_before_stop_r=15.930238 verdict=MANUAL_REVIEW_PRIMARY
- setup_000007 2026-03-22T21:59:00Z DOWN SELLER_DOMINANCE_RETEST_DOWN_SETUP TP1_THEN_BE quality_mfe_before_stop_r=1.694733 verdict=MANUAL_REVIEW_PRIMARY
- setup_000008 2026-03-26T07:59:00Z DOWN SELLER_DOMINANCE_RETEST_DOWN_SETUP TP1_THEN_BE quality_mfe_before_stop_r=47.033036 verdict=MANUAL_REVIEW_SECONDARY
- setup_000009 2026-03-27T03:59:00Z DOWN SELLER_DOMINANCE_RETEST_DOWN_SETUP TP1_THEN_BE quality_mfe_before_stop_r=3.875068 verdict=MANUAL_REVIEW_PRIMARY
- setup_000010 2026-04-02T01:59:00Z DOWN SELLER_DOMINANCE_RETEST_DOWN_SETUP TP1_THEN_BE quality_mfe_before_stop_r=17.170524 verdict=MANUAL_REVIEW_PRIMARY
- setup_000011 2026-04-02T14:59:00Z DOWN SUPPLY_SWEEP_RECLAIM_DOWN_SETUP TP1_THEN_BE quality_mfe_before_stop_r=4.058894 verdict=MANUAL_REVIEW_PRIMARY
- setup_000014 2026-04-18T06:59:00Z DOWN SUPPLY_SWEEP_RECLAIM_DOWN_SETUP TP1_THEN_BE quality_mfe_before_stop_r=21.287188 verdict=MANUAL_REVIEW_SECONDARY
- setup_000015 2026-04-19T14:59:00Z DOWN SELLER_DOMINANCE_RETEST_DOWN_SETUP TP1_THEN_BE quality_mfe_before_stop_r=10.571076 verdict=MANUAL_REVIEW_PRIMARY
- setup_000016 2026-04-20T20:59:00Z UP DEMAND_SWEEP_RECLAIM_UP_SETUP TP1_THEN_BE quality_mfe_before_stop_r=1.001203 verdict=MANUAL_REVIEW_SECONDARY
- setup_000018 2026-04-22T00:59:00Z UP DEMAND_SWEEP_RECLAIM_UP_SETUP TP1_THEN_BE quality_mfe_before_stop_r=1.25941 verdict=MANUAL_REVIEW_SECONDARY
- setup_000023 2026-05-07T02:59:00Z DOWN SELLER_DOMINANCE_RETEST_DOWN_SETUP TP1_THEN_BE quality_mfe_before_stop_r=2.984487 verdict=MANUAL_REVIEW_PRIMARY
- setup_000024 2026-05-13T11:59:00Z DOWN SELLER_DOMINANCE_RETEST_DOWN_SETUP TP1_THEN_BE quality_mfe_before_stop_r=8.831368 verdict=MANUAL_REVIEW_PRIMARY
- setup_000026 2026-05-17T23:59:00Z DOWN SUPPLY_SWEEP_RECLAIM_DOWN_SETUP TP1_THEN_BE quality_mfe_before_stop_r=4.804673 verdict=MANUAL_REVIEW_SECONDARY
- setup_000028 2026-05-22T14:59:00Z DOWN SELLER_DOMINANCE_RETEST_DOWN_SETUP TP1_THEN_BE quality_mfe_before_stop_r=7.442026 verdict=MANUAL_REVIEW_PRIMARY
- setup_000030 2026-05-24T05:59:00Z UP DEMAND_SWEEP_RECLAIM_UP_SETUP TP1_THEN_BE quality_mfe_before_stop_r=2.584928 verdict=MANUAL_REVIEW_SECONDARY
- setup_000031 2026-05-26T16:59:00Z DOWN SELLER_DOMINANCE_RETEST_DOWN_SETUP TP1_THEN_TARGET quality_mfe_before_stop_r=102.585427 verdict=MANUAL_REVIEW_PRIMARY
- setup_000032 2026-05-26T11:59:00Z DOWN SUPPLY_SWEEP_RECLAIM_DOWN_SETUP TP1_THEN_BE quality_mfe_before_stop_r=3.305689 verdict=MANUAL_REVIEW_PRIMARY
- setup_000034 2026-06-01T12:59:00Z DOWN SELLER_DOMINANCE_RETEST_DOWN_SETUP TP1_THEN_TARGET quality_mfe_before_stop_r=60.602933 verdict=MANUAL_REVIEW_PRIMARY
- setup_000035 2026-06-02T18:59:00Z DOWN SELLER_DOMINANCE_RETEST_DOWN_SETUP TP1_THEN_BE quality_mfe_before_stop_r=8.319964 verdict=MANUAL_REVIEW_PRIMARY
- setup_000037 2026-06-03T05:59:00Z DOWN SELLER_DOMINANCE_RETEST_DOWN_SETUP TP1_THEN_BE quality_mfe_before_stop_r=2.025405 verdict=MANUAL_REVIEW_PRIMARY
- setup_000039 2026-06-05T15:59:00Z DOWN SELLER_DOMINANCE_RETEST_DOWN_SETUP TP1_THEN_BE quality_mfe_before_stop_r=5.869934 verdict=MANUAL_REVIEW_PRIMARY
- setup_000040 2026-06-05T19:59:00Z DOWN SUPPLY_SWEEP_RECLAIM_DOWN_SETUP TP1_THEN_BE quality_mfe_before_stop_r=2.442476 verdict=MANUAL_REVIEW_PRIMARY
- setup_000042 2026-06-17T20:59:00Z DOWN SELLER_DOMINANCE_RETEST_DOWN_SETUP TP1_THEN_BE quality_mfe_before_stop_r=6.75507 verdict=MANUAL_REVIEW_PRIMARY
- setup_000045 2026-06-18T09:59:00Z DOWN SUPPLY_SWEEP_RECLAIM_DOWN_SETUP TP1_THEN_BE quality_mfe_before_stop_r=1.989745 verdict=MANUAL_REVIEW_PRIMARY
- setup_000048 2026-06-23T01:59:00Z DOWN SELLER_DOMINANCE_RETEST_DOWN_SETUP TP1_THEN_BE quality_mfe_before_stop_r=1.382823 verdict=MANUAL_REVIEW_SECONDARY
- setup_000049 2026-06-23T02:59:00Z DOWN SUPPLY_SWEEP_RECLAIM_DOWN_SETUP TP1_ONLY_NO_FOLLOWUP quality_mfe_before_stop_r=41.873277 verdict=MANUAL_REVIEW_SECONDARY
