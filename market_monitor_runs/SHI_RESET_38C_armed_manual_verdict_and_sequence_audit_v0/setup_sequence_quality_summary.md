# SHI RESET 38C Setup Sequence Quality Summary

Research-only manual verdict and sequence-role audit for 38B ARMED setup rows.

- Source review pack: `market_monitor_runs/SHI_RESET_38B_armed_setup_manual_review_pack_v0/armed_setup_manual_review.csv`
- Source replay results: `market_monitor_runs/SHI_RESET_38A_setup_replay_validation_v0/setup_replay_results.csv`
- Included rows: 9 ARMED setups
- WATCH rows: excluded
- Detection logic changed: false
- Backtester / Executor / orders / entries / exits / PnL / position sizing / live-readiness / strategy promotion: false

## Counts

### By setup_type

- SELLER_DOMINANCE_RETEST_DOWN_SETUP: 5
- SUPPLY_SWEEP_RECLAIM_DOWN_SETUP: 4

### By replay_outcome

- TARGET: 5
- INVALIDATION: 3
- NO_EVENT: 1

### By sequence_role

- INITIAL_IDEAL_SETUP: 1
- CONFIRMATION_SETUP: 1
- LATE_LAST_WAGON: 1
- TP_BE_DEPENDENT_SETUP: 1
- POST_IMPULSE_CORRECTION_PRECURSOR: 1
- HIGH_QUALITY_CONTINUATION_SETUP: 1
- EARLY_CORRECTION_SETUP: 1
- CORRECTION_END_ENTRY_SETUP: 1
- LATE_CONFIRMATION_OR_LAST_WAGON: 1

### By research_action

- KEEP_FOR_WIDER_REPLAY: 3
- REJECT_OR_DOWNGRADE: 1
- KEEP_FOR_TP_BE_POLICY_REPLAY: 1
- KEEP_BUT_REVIEW_SETUP_NAMING_AND_DIRECTION_LOGIC: 1
- MODIFY_OR_REQUIRE_CORRECTION_COMPLETION_FILTER: 1
- KEEP_FOR_SWING_STOP_REPLAY: 1
- DOWNGRADE_OR_REJECT_FOR_ENTRY_MODEL: 1

## Kept For Wider Replay

- 2026-03-26T01:59:00Z `SUPPLY_SWEEP_RECLAIM_DOWN_SETUP` - INITIAL_IDEAL_SETUP
- 2026-03-26T07:59:00Z `SELLER_DOMINANCE_RETEST_DOWN_SETUP` - CONFIRMATION_SETUP
- 2026-06-23T18:59:00Z `SELLER_DOMINANCE_RETEST_DOWN_SETUP` - HIGH_QUALITY_CONTINUATION_SETUP

## Requiring TP/BE Replay

- 2026-06-21T02:59:00Z `SELLER_DOMINANCE_RETEST_DOWN_SETUP` - TP_BE_DEPENDENT_SETUP

## Requiring Swing-Stop Replay

- 2026-06-25T11:59:00Z `SUPPLY_SWEEP_RECLAIM_DOWN_SETUP` - CORRECTION_END_ENTRY_SETUP

## Late / Last-Wagon Setups To Downgrade Or Reject

- 2026-03-27T22:59:00Z `SELLER_DOMINANCE_RETEST_DOWN_SETUP` - LATE_LAST_WAGON
- 2026-06-25T15:59:00Z `SELLER_DOMINANCE_RETEST_DOWN_SETUP` - LATE_CONFIRMATION_OR_LAST_WAGON

## Modify / Review Logic

- 2026-06-23T08:59:00Z `SUPPLY_SWEEP_RECLAIM_DOWN_SETUP` - POST_IMPULSE_CORRECTION_PRECURSOR; keep, but review setup naming and direction logic.
- 2026-06-24T22:59:00Z `SUPPLY_SWEEP_RECLAIM_DOWN_SETUP` - EARLY_CORRECTION_SETUP; modify or require correction-completion filter.

## Required Conclusions

1. Replay outcome alone is insufficient.
2. ARMED setup quality depends on sequence role.
3. `SUPPLY_SWEEP_RECLAIM_DOWN_SETUP` is not automatically bad; it can be ideal when it appears at the right correction phase.
4. `SELLER_DOMINANCE_RETEST_DOWN_SETUP` can be strong as confirmation/continuation, but late instances must be downgraded.
5. Future replay must evaluate TP/BE and swing-stop variants.
6. Wider sample expansion should be split by sequence role, not only setup_type.

## Verdict

SHI_RESET_38C_ARMED_MANUAL_VERDICT_AND_SEQUENCE_AUDIT_V0_CREATED
