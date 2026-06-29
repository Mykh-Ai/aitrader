# SHI RESET 37K Live Replay Setup Timeline Audit

Scope: research-only live-replay timeline audit. No Backtester, Executor, orders, live trading, entries/exits, PnL, live-readiness, strategy promotion, or trading advice were used or added.

Output root: `market_monitor_runs/SHI_RESET_37K_live_replay_setup_timeline_v0`

Key contract: `setup_research_timeline.csv` uses `setup_formed_at` from raw regime-window `end_timestamp` when raw evidence exists. State-only context rows remain `WATCH` with `source_time_precision=STATE_WINDOW`. Raw regime-window rows include window length in `source_time_precision` when available, for example `RAW_REGIME_WINDOW_60M`.

## 2026-03-26T09:00Z as-of

- Cutoff used for audit check: `2026-03-26T09:00:00Z`
- Output: `market_monitor_runs\SHI_RESET_37K_live_replay_setup_timeline_v0\smoke_2026_03_26_0900/setup_research_timeline.csv`
- Timeline rows: 4
- Missing inputs: []
- Max setup_formed_at: `2026-03-26 07:59:00+00:00`
- No future rows beyond cutoff: `True`
- No state-only ARMED/TRIGGERED rows: `True`
- Manifest uses_future_data: `False`
- Manifest uses_backtester: `False`
- Manifest uses_executor: `False`

| setup_id | setup_formed_at | source_window_start | source_window_end | source_time_precision | setup_type | direction_context | trigger_status | market_state | dominant_side | nearest_zone_side | zone_position_context |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| setup_000001 | 2026-03-25T01:59:00+00:00 | 2026-03-25T01:00:00+00:00 | 2026-03-25T01:59:00+00:00 | RAW_REGIME_WINDOW_60M | DEMAND_SWEEP_RECLAIM_UP_SETUP | UP | WATCH | UP_EXPANSION_INTO_MAJOR_RESISTANCE | BUYER | SELL_SIDE | near_lower_zone |
| setup_000002 | 2026-03-26T06:59:00+00:00 | 2026-03-26T06:00:00+00:00 | 2026-03-26T06:59:00+00:00 | RAW_REGIME_WINDOW_60M | DEMAND_SWEEP_RECLAIM_UP_SETUP | UP | WATCH | PULLBACK_RETEST_INSIDE_MAJOR_RESISTANCE | SELLER | SELL_SIDE | inside_zone |
| setup_000003 | 2026-03-26T07:59:00+00:00 | 2026-03-25T08:00:00+00:00 | 2026-03-26T07:59:00+00:00 | RAW_REGIME_WINDOW_1440M | SELLER_DOMINANCE_RETEST_DOWN_SETUP | DOWN | ARMED | PULLBACK_RETEST_INSIDE_MAJOR_RESISTANCE | SELLER | SELL_SIDE | inside_zone |
| setup_000004 | 2026-03-26T01:59:00+00:00 | 2026-03-26T01:00:00+00:00 | 2026-03-26T01:59:00+00:00 | RAW_REGIME_WINDOW_60M | SUPPLY_SWEEP_RECLAIM_DOWN_SETUP | DOWN | ARMED | PULLBACK_RETEST_INSIDE_MAJOR_RESISTANCE | SELLER | BUY_SIDE | near_upper_zone |

## 2026-06-02T04:00Z as-of

- Cutoff used for audit check: `2026-06-02T04:00:00Z`
- Output: `market_monitor_runs\SHI_RESET_37K_live_replay_setup_timeline_v0\smoke_2026_06_02_0400/setup_research_timeline.csv`
- Timeline rows: 2
- Missing inputs: []
- Max setup_formed_at: `2026-06-01 12:59:00+00:00`
- No future rows beyond cutoff: `True`
- No state-only ARMED/TRIGGERED rows: `True`
- Manifest uses_future_data: `False`
- Manifest uses_backtester: `False`
- Manifest uses_executor: `False`

| setup_id | setup_formed_at | source_window_start | source_window_end | source_time_precision | setup_type | direction_context | trigger_status | market_state | dominant_side | nearest_zone_side | zone_position_context |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| setup_000001 | 2026-06-01T08:59:00+00:00 | 2026-06-01T08:00:00+00:00 | 2026-06-01T08:59:00+00:00 | RAW_REGIME_WINDOW_60M | DEMAND_SWEEP_RECLAIM_UP_SETUP | UP | WATCH | MARKDOWN_ABOVE_SUPPORT | SELLER | SELL_SIDE | near_lower_zone |
| setup_000002 | 2026-06-01T12:59:00+00:00 | 2026-06-01T12:00:00+00:00 | 2026-06-01T12:59:00+00:00 | RAW_REGIME_WINDOW_60M | SELLER_DOMINANCE_RETEST_DOWN_SETUP | DOWN | ARMED | MARKDOWN_ABOVE_SUPPORT | SELLER | SELL_SIDE | unclear |

## 2026-06-01 daily state

- Cutoff used for audit check: `2026-06-01T23:59:00Z`
- Output: `market_monitor_runs\SHI_RESET_37K_live_replay_setup_timeline_v0\smoke_2026_06_01/setup_research_timeline.csv`
- Timeline rows: 2
- Missing inputs: []
- Max setup_formed_at: `2026-06-01 12:59:00+00:00`
- No future rows beyond cutoff: `True`
- No state-only ARMED/TRIGGERED rows: `True`
- Manifest uses_future_data: `False`
- Manifest uses_backtester: `False`
- Manifest uses_executor: `False`

| setup_id | setup_formed_at | source_window_start | source_window_end | source_time_precision | setup_type | direction_context | trigger_status | market_state | dominant_side | nearest_zone_side | zone_position_context |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| setup_000001 | 2026-06-01T08:59:00+00:00 | 2026-06-01T08:00:00+00:00 | 2026-06-01T08:59:00+00:00 | RAW_REGIME_WINDOW_60M | DEMAND_SWEEP_RECLAIM_UP_SETUP | UP | WATCH | MARKDOWN_ABOVE_SUPPORT | SELLER | SELL_SIDE | near_lower_zone |
| setup_000002 | 2026-06-01T12:59:00+00:00 | 2026-06-01T12:00:00+00:00 | 2026-06-01T12:59:00+00:00 | RAW_REGIME_WINDOW_60M | SELLER_DOMINANCE_RETEST_DOWN_SETUP | DOWN | ARMED | MARKDOWN_ABOVE_SUPPORT | SELLER | SELL_SIDE | unclear |

## 2026-05-15..17 transition

- Cutoff used for audit check: `2026-05-17T23:59:00Z`
- Output: `market_monitor_runs\SHI_RESET_37K_live_replay_setup_timeline_v0\smoke_2026_05_15_to_17/setup_research_timeline.csv`
- Timeline rows: 0
- Missing inputs: ["market_monitor_runs\\SHI_RESET_37K_live_replay_setup_timeline_v0\\missing_2026_05_15_to_17\\market_regime_windows.csv", "market_monitor_runs\\SHI_RESET_37K_live_replay_setup_timeline_v0\\missing_2026_05_15_to_17\\selected_zones.csv"]
- Max setup_formed_at: ``
- No future rows beyond cutoff: `True`
- No state-only ARMED/TRIGGERED rows: `True`
- Manifest uses_future_data: `False`
- Manifest uses_backtester: `False`
- Manifest uses_executor: `False`

No setup research timeline rows generated.

## Verdict

PASS_WITH_INPUT_GAP_NOTE

- Violations: `[]`
- Future labels were not passed to the builder.
- `hidden_flow_research.py` remains unchanged.

The builder emits `setup_research_timeline.csv` with `setup_formed_at`, `source_window_start`, `source_window_end`, and `source_time_precision`. Raw-window rows form at raw `end_timestamp`; state-only context is limited to `WATCH`. The 2026-05-15..17 smoke remains empty because local raw regime-window and selected-zone artifacts for that window are missing.
