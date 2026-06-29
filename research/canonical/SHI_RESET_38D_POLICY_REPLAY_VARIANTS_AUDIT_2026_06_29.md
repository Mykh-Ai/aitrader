# SHI RESET 38D Policy Replay Variants Audit

Scope: research-only policy replay on the existing 38C manually reviewed ARMED setup rows. This audit does not expand the sample, does not add setup detection, does not modify Setup Builder rules, and does not add Backtester execution logic, Executor logic, orders, entries/exits, PnL, position sizing, live-readiness, or strategy promotion.

Output root: `market_monitor_runs/SHI_RESET_38D_policy_replay_variants_v0`

Required outputs:

- `policy_replay_results.csv`
- `policy_replay_summary.md`
- `policy_replay_manifest.json`

Input sources:

- `market_monitor_runs/SHI_RESET_38C_armed_manual_verdict_and_sequence_audit_v0/armed_setup_manual_verdicts.csv`
- `market_monitor_runs/SHI_RESET_38A_setup_replay_validation_v0/setup_replay_results.csv`
- `market_monitor_runs/SHI_RESET_38B_armed_setup_manual_review_pack_v0/chart_data/*.csv`
- `feed/`

## Sample Control

- 38C setup rows evaluated: 9
- New setup rows evaluated: 0
- WATCH rows evaluated: 0
- Output policy rows: 12
- Sample expanded: false

`NO_APPLICABLE_POLICY` rows are included only to document 38C rows whose `research_action` does not map to one of the three requested 38D policy variants.

## Policy Mapping

- `TP1_BE_POLICY`: `KEEP_FOR_TP_BE_POLICY_REPLAY`, `KEEP_FOR_WIDER_REPLAY`
- `SWING_STOP_POLICY`: `KEEP_FOR_SWING_STOP_REPLAY`, `KEEP_FOR_WIDER_REPLAY`
- `LATE_ENTRY_FILTER_POLICY`: `REJECT_OR_DOWNGRADE`, `DOWNGRADE_OR_REJECT_FOR_ENTRY_MODEL`, late/last-wagon sequence roles

## Counts

### Rows by policy_name

- TP1_BE_POLICY: 4
- SWING_STOP_POLICY: 4
- LATE_ENTRY_FILTER_POLICY: 2
- NO_APPLICABLE_POLICY: 2

### Outcomes by policy_name

- TP1_BE_POLICY:
  - TP1_THEN_TARGET: 3
  - NO_TP1_INVALIDATION: 1
- SWING_STOP_POLICY:
  - SWING_STOP_TARGET: 3
  - SWING_STOP_INVALIDATION: 1
- LATE_ENTRY_FILTER_POLICY:
  - FILTERED_OUT: 2
- NO_APPLICABLE_POLICY:
  - NO_POLICY_APPLIED: 2

### Required metrics

- TP1 touched count: 3
- BE-after-TP1 count: 0
- Swing-stop target count: 3
- Swing-stop invalidation count: 1
- Filtered late/last-wagon count: 2

## Setups That Improve Under Policy Replay

- 2026-03-26T01:59:00Z `SUPPLY_SWEEP_RECLAIM_DOWN_SETUP`, `INITIAL_IDEAL_SETUP`
  - `TP1_BE_POLICY`: TP1_THEN_TARGET
  - `SWING_STOP_POLICY`: SWING_STOP_TARGET
- 2026-03-26T07:59:00Z `SELLER_DOMINANCE_RETEST_DOWN_SETUP`, `CONFIRMATION_SETUP`
  - `TP1_BE_POLICY`: TP1_THEN_TARGET
  - `SWING_STOP_POLICY`: SWING_STOP_TARGET
- 2026-06-23T18:59:00Z `SELLER_DOMINANCE_RETEST_DOWN_SETUP`, `HIGH_QUALITY_CONTINUATION_SETUP`
  - `TP1_BE_POLICY`: TP1_THEN_TARGET
  - `SWING_STOP_POLICY`: SWING_STOP_TARGET

## Setups That Remain Rejected Or Not Improved

- 2026-03-27T22:59:00Z `SELLER_DOMINANCE_RETEST_DOWN_SETUP`, `LATE_LAST_WAGON`
  - `LATE_ENTRY_FILTER_POLICY`: FILTERED_OUT
- 2026-06-21T02:59:00Z `SELLER_DOMINANCE_RETEST_DOWN_SETUP`, `TP_BE_DEPENDENT_SETUP`
  - `TP1_BE_POLICY`: NO_TP1_INVALIDATION
  - Note: this is based on the strict rule `TP1_MOVE_USD=750` before original invalidation, not on total later MFE.
- 2026-06-25T11:59:00Z `SUPPLY_SWEEP_RECLAIM_DOWN_SETUP`, `CORRECTION_END_ENTRY_SETUP`
  - `SWING_STOP_POLICY`: SWING_STOP_INVALIDATION
- 2026-06-25T15:59:00Z `SELLER_DOMINANCE_RETEST_DOWN_SETUP`, `LATE_CONFIRMATION_OR_LAST_WAGON`
  - `LATE_ENTRY_FILTER_POLICY`: FILTERED_OUT

## No Applicable Policy Rows

- 2026-06-23T08:59:00Z `SUPPLY_SWEEP_RECLAIM_DOWN_SETUP`, `POST_IMPULSE_CORRECTION_PRECURSOR`
  - Research action: `KEEP_BUT_REVIEW_SETUP_NAMING_AND_DIRECTION_LOGIC`
- 2026-06-24T22:59:00Z `SUPPLY_SWEEP_RECLAIM_DOWN_SETUP`, `EARLY_CORRECTION_SETUP`
  - Research action: `MODIFY_OR_REQUIRE_CORRECTION_COMPLETION_FILTER`

These were included as `NO_APPLICABLE_POLICY` for accounting only. They were not counted as candidate entries or policy successes.

## Method Notes

- TP1 threshold: `750` USD.
- TP1 was checked before original invalidation.
- BE-after-TP1 was checked after TP1 and before target.
- Swing stop was resolved from the 37K source-window high/low and compared against original invalidation.
- Policy results are descriptive research labels, not trade instructions.

## Governance Check

- Sample expansion: false
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

SHI_RESET_38D_POLICY_REPLAY_VARIANTS_V0_CREATED
