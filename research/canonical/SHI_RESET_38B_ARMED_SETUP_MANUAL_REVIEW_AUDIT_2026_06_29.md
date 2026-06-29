# SHI RESET 38B ARMED Setup Manual Review Audit

Scope: research-only manual review pack for ARMED setup rows from 38A replay validation. This audit does not add setup detection, Backtester execution logic, Executor logic, orders, entries/exits, PnL, position sizing, live-readiness, or strategy promotion.

Output root: `market_monitor_runs/SHI_RESET_38B_armed_setup_manual_review_pack_v0`

Required output files:

- `armed_setup_manual_review.csv`
- `armed_setup_manual_review_summary.md`
- `chart_data/*.csv`

Input sources:

- Replay results: `market_monitor_runs\SHI_RESET_38A_setup_replay_validation_v0\setup_replay_results.csv`
- 37K setup timeline interval 1: `market_monitor_runs\SHI_RESET_38A_setup_replay_validation_v0\interval_2026_03_24_to_2026_03_27\setup_builder\setup_research_timeline.csv`
- 37K setup timeline interval 2: `market_monitor_runs\SHI_RESET_38A_setup_replay_validation_v0\interval_2026_06_21_to_2026_06_28\setup_builder\setup_research_timeline.csv`
- Feed directory: `feed`
- Selected zones were passed through as interval metadata where available.

## Filter Result

- Input replay rows: 12
- ARMED rows included: 9
- WATCH rows excluded: 3
- Chart data files written: 9
- Rows by setup_type: `{"SELLER_DOMINANCE_RETEST_DOWN_SETUP": 5, "SUPPLY_SWEEP_RECLAIM_DOWN_SETUP": 4}`
- Rows by direction_context: `{"DOWN": 9}`
- Rows by first_event: `{"": 1, "INVALIDATION": 3, "TARGET": 5}`

## Interval 1

- Window: `2026-03-24T00:00:00Z` -> `2026-03-27T23:59:00Z`
- ARMED rows: 3
- Rows by setup_type: `{"SELLER_DOMINANCE_RETEST_DOWN_SETUP": 2, "SUPPLY_SWEEP_RECLAIM_DOWN_SETUP": 1}`
- Rows by first_event: `{"": 1, "TARGET": 2}`

Included setup rows:

| setup_id | setup_formed_at | setup_type | direction_context | source_time_precision | first_event |
| --- | --- | --- | --- | --- | --- |
| setup_000002 | 2026-03-26T07:59:00Z | SELLER_DOMINANCE_RETEST_DOWN_SETUP | DOWN | RAW_REGIME_WINDOW_1440M | TARGET |
| setup_000003 | 2026-03-26T01:59:00Z | SUPPLY_SWEEP_RECLAIM_DOWN_SETUP | DOWN | RAW_REGIME_WINDOW_60M | TARGET |
| setup_000005 | 2026-03-27T22:59:00Z | SELLER_DOMINANCE_RETEST_DOWN_SETUP | DOWN | RAW_REGIME_WINDOW_720M |  |

## Interval 2

- Window: `2026-06-21T00:00:00Z` -> `2026-06-28T23:59:00Z`
- ARMED rows: 6
- Rows by setup_type: `{"SELLER_DOMINANCE_RETEST_DOWN_SETUP": 3, "SUPPLY_SWEEP_RECLAIM_DOWN_SETUP": 3}`
- Rows by first_event: `{"INVALIDATION": 3, "TARGET": 3}`

Included setup rows:

| setup_id | setup_formed_at | setup_type | direction_context | source_time_precision | first_event |
| --- | --- | --- | --- | --- | --- |
| setup_000001 | 2026-06-21T02:59:00Z | SELLER_DOMINANCE_RETEST_DOWN_SETUP | DOWN | RAW_REGIME_WINDOW_60M | INVALIDATION |
| setup_000002 | 2026-06-23T18:59:00Z | SELLER_DOMINANCE_RETEST_DOWN_SETUP | DOWN | RAW_REGIME_WINDOW_720M | TARGET |
| setup_000003 | 2026-06-23T08:59:00Z | SUPPLY_SWEEP_RECLAIM_DOWN_SETUP | DOWN | RAW_REGIME_WINDOW_60M | TARGET |
| setup_000004 | 2026-06-24T22:59:00Z | SUPPLY_SWEEP_RECLAIM_DOWN_SETUP | DOWN | RAW_REGIME_WINDOW_720M | INVALIDATION |
| setup_000005 | 2026-06-25T15:59:00Z | SELLER_DOMINANCE_RETEST_DOWN_SETUP | DOWN | RAW_REGIME_WINDOW_240M | TARGET |
| setup_000006 | 2026-06-25T11:59:00Z | SUPPLY_SWEEP_RECLAIM_DOWN_SETUP | DOWN | RAW_REGIME_WINDOW_60M | INVALIDATION |

## Chart Data

Chart data files are CSV review inputs, not detection inputs.

Rules applied:

- `RAW_REGIME_WINDOW_60M`: 6h before `setup_formed_at` and 24h after.
- `RAW_REGIME_WINDOW_1440M`: 24h before `setup_formed_at` and 48h after.
- Other raw precisions present in the data, such as `RAW_REGIME_WINDOW_240M` and `RAW_REGIME_WINDOW_720M`, used the 60M-style fallback: 6h before and 24h after.

Each chart CSV includes feed OHLCV rows plus setup reference columns:

- setup id and formed timestamp
- direction context
- entry reference level
- invalidation reference
- target zone lower/upper/side
- chart window start/end

## Manual Review Questions

Each review row includes:

1. Is the setup visually coherent?
2. Is the setup late?
3. Is the target zone logical?
4. Is the invalidation logical?
5. Did price move favorably before invalidation?
6. Should this setup_type be kept for wider replay, modified, or rejected?

## Governance Check

- Only ARMED rows included: `true`
- WATCH rows excluded: `true`
- Setup detection changed: `false`
- Future data used for detection: `false`
- Backtester used: `false`
- Executor used: `false`
- Orders used: `false`
- Entries/exits used: `false`
- PnL used: `false`
- Live-readiness claim: `false`
- Strategy promotion: `false`

## Verdict

SHI_RESET_38B_ARMED_SETUP_MANUAL_REVIEW_PACK_V0_CREATED

The task produced a deterministic manual review pack for ARMED 38A replay rows. The pack is for visual/manual research review only and does not promote any setup into a strategy or execution layer.
