# SHI RESET 38C ARMED Manual Verdict And Sequence Audit

Scope: research-only audit. This records user manual chart-review verdicts for all 38B ARMED setup rows and classifies each setup by sequence role. It does not change setup detection logic, does not change Setup Builder, and does not add Backtester execution logic, Executor logic, orders, entries/exits, PnL, position sizing, live-readiness, or strategy promotion.

Output root: `market_monitor_runs/SHI_RESET_38C_armed_manual_verdict_and_sequence_audit_v0`

Required outputs:

- `armed_setup_manual_verdicts.csv`
- `setup_sequence_quality_summary.md`

Input sources:

- `market_monitor_runs/SHI_RESET_38B_armed_setup_manual_review_pack_v0/armed_setup_manual_review.csv`
- `market_monitor_runs/SHI_RESET_38A_setup_replay_validation_v0/setup_replay_results.csv`
- `market_monitor_runs/SHI_RESET_38B_armed_setup_manual_review_pack_v0/chart_data/*.csv`

## Manual Verdicts Recorded

| setup_formed_at | setup_type | replay_outcome | sequence_role | research_action |
| --- | --- | --- | --- | --- |
| 2026-03-26T01:59:00Z | SUPPLY_SWEEP_RECLAIM_DOWN_SETUP | TARGET | INITIAL_IDEAL_SETUP | KEEP_FOR_WIDER_REPLAY |
| 2026-03-26T07:59:00Z | SELLER_DOMINANCE_RETEST_DOWN_SETUP | TARGET | CONFIRMATION_SETUP | KEEP_FOR_WIDER_REPLAY |
| 2026-03-27T22:59:00Z | SELLER_DOMINANCE_RETEST_DOWN_SETUP | NO_EVENT | LATE_LAST_WAGON | REJECT_OR_DOWNGRADE |
| 2026-06-21T02:59:00Z | SELLER_DOMINANCE_RETEST_DOWN_SETUP | INVALIDATION | TP_BE_DEPENDENT_SETUP | KEEP_FOR_TP_BE_POLICY_REPLAY |
| 2026-06-23T08:59:00Z | SUPPLY_SWEEP_RECLAIM_DOWN_SETUP | TARGET | POST_IMPULSE_CORRECTION_PRECURSOR | KEEP_BUT_REVIEW_SETUP_NAMING_AND_DIRECTION_LOGIC |
| 2026-06-23T18:59:00Z | SELLER_DOMINANCE_RETEST_DOWN_SETUP | TARGET | HIGH_QUALITY_CONTINUATION_SETUP | KEEP_FOR_WIDER_REPLAY |
| 2026-06-24T22:59:00Z | SUPPLY_SWEEP_RECLAIM_DOWN_SETUP | INVALIDATION | EARLY_CORRECTION_SETUP | MODIFY_OR_REQUIRE_CORRECTION_COMPLETION_FILTER |
| 2026-06-25T11:59:00Z | SUPPLY_SWEEP_RECLAIM_DOWN_SETUP | INVALIDATION | CORRECTION_END_ENTRY_SETUP | KEEP_FOR_SWING_STOP_REPLAY |
| 2026-06-25T15:59:00Z | SELLER_DOMINANCE_RETEST_DOWN_SETUP | TARGET | LATE_CONFIRMATION_OR_LAST_WAGON | DOWNGRADE_OR_REJECT_FOR_ENTRY_MODEL |

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

## Action Buckets

### Kept For Wider Replay

- 2026-03-26T01:59:00Z `SUPPLY_SWEEP_RECLAIM_DOWN_SETUP`
- 2026-03-26T07:59:00Z `SELLER_DOMINANCE_RETEST_DOWN_SETUP`
- 2026-06-23T18:59:00Z `SELLER_DOMINANCE_RETEST_DOWN_SETUP`

### Requiring TP/BE Replay

- 2026-06-21T02:59:00Z `SELLER_DOMINANCE_RETEST_DOWN_SETUP`

### Requiring Swing-Stop Replay

- 2026-06-25T11:59:00Z `SUPPLY_SWEEP_RECLAIM_DOWN_SETUP`

### Late / Last-Wagon Setups To Downgrade Or Reject

- 2026-03-27T22:59:00Z `SELLER_DOMINANCE_RETEST_DOWN_SETUP`
- 2026-06-25T15:59:00Z `SELLER_DOMINANCE_RETEST_DOWN_SETUP`

### Modify / Review Logic

- 2026-06-23T08:59:00Z `SUPPLY_SWEEP_RECLAIM_DOWN_SETUP`: keep, but review setup naming and direction logic.
- 2026-06-24T22:59:00Z `SUPPLY_SWEEP_RECLAIM_DOWN_SETUP`: modify or require correction-completion filter.

## Conclusions

1. Replay outcome alone is insufficient.
2. ARMED setup quality depends on sequence role.
3. `SUPPLY_SWEEP_RECLAIM_DOWN_SETUP` is not automatically bad; it can be ideal when it appears at the right correction phase.
4. `SELLER_DOMINANCE_RETEST_DOWN_SETUP` can be strong as confirmation/continuation, but late instances must be downgraded.
5. Future replay must evaluate TP/BE and swing-stop variants.
6. Wider sample expansion should be split by sequence role, not only setup_type.

## Governance Check

- Setup detection changed: false
- Setup Builder changed: false
- Backtester execution logic added: false
- Executor added: false
- Orders added: false
- Entries/exits added: false
- PnL added: false
- Position sizing added: false
- Live-readiness added: false
- Strategy promotion added: false

## Verdict

SHI_RESET_38C_ARMED_MANUAL_VERDICT_AND_SEQUENCE_AUDIT_V0_CREATED
