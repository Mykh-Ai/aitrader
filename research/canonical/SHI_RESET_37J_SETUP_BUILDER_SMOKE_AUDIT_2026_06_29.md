# SHI RESET 37J Setup Builder Smoke Audit

Scope: research-only downstream Setup Builder smoke audit. No Backtester, Executor, orders, live trading, entries/exits, PnL, live-readiness, strategy promotion, or trading advice were used or added.

Builder output root: `market_monitor_runs/SHI_RESET_37J_setup_builder_downstream_v0`

## 2026-03-26T09:00Z as-of

- Output: `market_monitor_runs\SHI_RESET_37J_setup_builder_downstream_v0\smoke_2026_03_26_0900`
- Candidate count: 4
- Missing inputs: []
- research_only: True
- uses_future_data: False
- uses_backtester: False
- uses_executor: False
- output_is_trading_signal: False
- setup_candidates_require_replay: True

| setup_id | start_timestamp | end_timestamp | setup_type | direction_context | trigger_status | market_state | dominant_side | nearest_zone_side | zone_position_context | seller_pressure_score | buyer_response_score | target_reference_zone |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| setup_000001 | 2026-03-25T00:00:00Z | 2026-03-25T23:59:00Z | DEMAND_SWEEP_RECLAIM_UP_SETUP | UP | WATCH | UP_EXPANSION_INTO_MAJOR_RESISTANCE | BUYER | SELL_SIDE | near_lower_zone | 9.2 | 42.0 | zone_000011:BUY_SIDE:71341.81125-71413.18875 |
| setup_000002 | 2026-03-26T00:00:00Z | 2026-03-26T09:00:00Z | DEMAND_SWEEP_RECLAIM_UP_SETUP | UP | WATCH | PULLBACK_RETEST_INSIDE_MAJOR_RESISTANCE | SELLER | SELL_SIDE | inside_zone | 93.3 | 5.7 | zone_000011:BUY_SIDE:71341.81125-71413.18875 |
| setup_000003 | 2026-03-26T00:00:00Z | 2026-03-26T09:00:00Z | SELLER_DOMINANCE_RETEST_DOWN_SETUP | DOWN | ARMED | PULLBACK_RETEST_INSIDE_MAJOR_RESISTANCE | SELLER | SELL_SIDE | inside_zone | 93.3 | 5.7 | zone_000019:SELL_SIDE:68850.05775-68918.94225 |
| setup_000004 | 2026-03-26T00:00:00Z | 2026-03-26T09:00:00Z | SUPPLY_SWEEP_RECLAIM_DOWN_SETUP | DOWN | ARMED | PULLBACK_RETEST_INSIDE_MAJOR_RESISTANCE | SELLER | BUY_SIDE | near_upper_zone | 93.3 | 5.7 | zone_000019:SELL_SIDE:68850.05775-68918.94225 |

## 2026-06-02T04:00Z as-of

- Output: `market_monitor_runs\SHI_RESET_37J_setup_builder_downstream_v0\smoke_2026_06_02_0400`
- Candidate count: 2
- Missing inputs: []
- research_only: True
- uses_future_data: False
- uses_backtester: False
- uses_executor: False
- output_is_trading_signal: False
- setup_candidates_require_replay: True

| setup_id | start_timestamp | end_timestamp | setup_type | direction_context | trigger_status | market_state | dominant_side | nearest_zone_side | zone_position_context | seller_pressure_score | buyer_response_score | target_reference_zone |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| setup_000001 | 2026-06-01T00:00:00Z | 2026-06-01T23:59:00Z | DEMAND_SWEEP_RECLAIM_UP_SETUP | UP | WATCH | MARKDOWN_ABOVE_SUPPORT | SELLER | SELL_SIDE | near_lower_zone | 100.0 | 15.4 | zone_000185:BUY_SIDE:77509.72575-77587.27425 |
| setup_000002 | 2026-06-01T00:00:00Z | 2026-06-01T23:59:00Z | SELLER_DOMINANCE_RETEST_DOWN_SETUP | DOWN | ARMED | MARKDOWN_ABOVE_SUPPORT | SELLER | SELL_SIDE | unclear | 100.0 | 15.4 | zone_000026:SELL_SIDE:80353.803-80434.197 |

## 2026-06-01 daily state

- Output: `market_monitor_runs\SHI_RESET_37J_setup_builder_downstream_v0\smoke_2026_06_01`
- Candidate count: 2
- Missing inputs: []
- research_only: True
- uses_future_data: False
- uses_backtester: False
- uses_executor: False
- output_is_trading_signal: False
- setup_candidates_require_replay: True

| setup_id | start_timestamp | end_timestamp | setup_type | direction_context | trigger_status | market_state | dominant_side | nearest_zone_side | zone_position_context | seller_pressure_score | buyer_response_score | target_reference_zone |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| setup_000001 | 2026-06-01T00:00:00Z | 2026-06-01T23:59:00Z | DEMAND_SWEEP_RECLAIM_UP_SETUP | UP | WATCH | MARKDOWN_ABOVE_SUPPORT | SELLER | SELL_SIDE | near_lower_zone | 100.0 | 15.4 | zone_000185:BUY_SIDE:77509.72575-77587.27425 |
| setup_000002 | 2026-06-01T00:00:00Z | 2026-06-01T23:59:00Z | SELLER_DOMINANCE_RETEST_DOWN_SETUP | DOWN | ARMED | MARKDOWN_ABOVE_SUPPORT | SELLER | SELL_SIDE | unclear | 100.0 | 15.4 | zone_000026:SELL_SIDE:80353.803-80434.197 |

## 2026-05-15..17 transition

- Output: `market_monitor_runs\SHI_RESET_37J_setup_builder_downstream_v0\smoke_2026_05_15_to_17`
- Candidate count: 0
- Missing inputs: ["market_monitor_runs\\SHI_RESET_37J_setup_builder_downstream_v0\\missing_2026_05_15_to_17\\market_regime_windows.csv", "market_monitor_runs\\SHI_RESET_37J_setup_builder_downstream_v0\\missing_2026_05_15_to_17\\selected_zones.csv"]
- research_only: True
- uses_future_data: False
- uses_backtester: False
- uses_executor: False
- output_is_trading_signal: False
- setup_candidates_require_replay: True

No setup research candidates generated.

## Verdict

PASS_WITH_INPUT_GAP_NOTE

The Setup Builder generated deterministic `setup_research_candidates.csv` files for all four smoke cases. Full-input smoke cases produced candidates from state plus raw regime-window and visible-zone artifacts. The 2026-05-15..17 transition smoke produced an empty deterministic CSV because local raw `market_regime_windows.csv` and `selected_zones.csv` inputs for that window were not present.

Future labels were not passed to the builder and are not used for detection. Promoted hidden-flow candidates are optional supporting evidence only; empty promoted candidate files do not block setup creation from Market Structure State plus raw regime windows.
