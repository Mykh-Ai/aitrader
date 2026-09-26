# SHI RESET 38A Setup Replay Validation Audit

Scope: research-only replay validation of existing 37K setup timeline rows. This audit does not add Backtester execution logic, Executor logic, orders, entries/exits, PnL, position sizing, live-readiness, or strategy promotion.

Output root: `market_monitor_runs/SHI_RESET_38A_setup_replay_validation_v0`

Required output files:

- `setup_replay_results.csv`
- `setup_replay_summary.md`
- `setup_replay_manifest.json`

Input contract:

- Detection was performed by 37K setup builder.
- 38A reads existing `setup_research_timeline.csv` rows.
- Forward feed rows are used only after `setup_formed_at` for outcome evaluation.
- 38A does not create new setup detection logic.

## Intervals

### interval_2026_03_24_to_2026_03_27

- Requested window: `2026-03-24T00:00:00Z` -> `2026-03-27T23:59:00Z`
- 37K setup timeline: `market_monitor_runs\SHI_RESET_38A_setup_replay_validation_v0\interval_2026_03_24_to_2026_03_27\setup_builder\setup_research_timeline.csv`
- Feed rows loaded for replay: 5760
- Setup rows replayed: 5
- Rows by setup_type: `{"DEMAND_SWEEP_RECLAIM_UP_SETUP": 2, "SELLER_DOMINANCE_RETEST_DOWN_SETUP": 2, "SUPPLY_SWEEP_RECLAIM_DOWN_SETUP": 1}`
- Rows by direction_context: `{"DOWN": 3, "UP": 2}`
- Rows by trigger_status: `{"ARMED": 3, "WATCH": 2}`
- Target-first count: 3
- Invalidation-first count: 0
- No-decisive-outcome count: 2
- Unresolved count: 0
- Median MFE: 1.027513
- Median MAE: -1.068576
- Worst MAE: -8.091496
- Best MFE: 8.091496

### interval_2026_06_21_to_2026_06_28

- Requested window: `2026-06-21T00:00:00Z` -> `2026-06-28T23:59:00Z`
- 37K setup timeline: `market_monitor_runs\SHI_RESET_38A_setup_replay_validation_v0\interval_2026_06_21_to_2026_06_28\setup_builder\setup_research_timeline.csv`
- Feed rows loaded for replay: 11520
- Setup rows replayed: 7
- Data note: `2026-06-25` was processed with `RECOVERED_DEGRADED=1440` in the daily batch manifest.
- Rows by setup_type: `{"DEMAND_SWEEP_RECLAIM_UP_SETUP": 1, "SELLER_DOMINANCE_RETEST_DOWN_SETUP": 3, "SUPPLY_SWEEP_RECLAIM_DOWN_SETUP": 3}`
- Rows by direction_context: `{"DOWN": 6, "UP": 1}`
- Rows by trigger_status: `{"ARMED": 6, "WATCH": 1}`
- Target-first count: 3
- Invalidation-first count: 3
- No-decisive-outcome count: 1
- Unresolved count: 0
- Median MFE: 4.892793
- Median MAE: -1.129047
- Worst MAE: -3.861801
- Best MFE: 8.333308

## Replay Outcome Notes

- MFE is capped at minimum `0.0` and measures maximum favorable move from `entry_reference_level`.
- MAE is capped at maximum `0.0` and measures maximum adverse move from `entry_reference_level`.
- UP context favorable path uses forward `High`; adverse path uses forward `Low`.
- DOWN context favorable path uses forward `Low`; adverse path uses forward `High`.
- Target touch is true when a forward candle range intersects `target_reference_zone`.
- Invalidation touch uses 37K `invalidation_level`, emitted in 38A as `invalidation_reference`.

## Governance Check

- Backtester used: `false`
- Executor used: `false`
- Orders used: `false`
- Entries/exits used: `false`
- PnL used: `false`
- Position sizing used: `false`
- Live-readiness claim: `false`
- Strategy promotion: `false`
- Setup detection changed: `false`
- Future data used for detection: `false`

## Verdict

SHI_RESET_38A_SETUP_REPLAY_VALIDATION_V0_CREATED

The task produced deterministic replay-validation artifacts for both requested intervals. The artifacts evaluate what happened after existing 37K `setup_formed_at` timestamps; they do not promote the setup builder into a strategy or execution layer.
