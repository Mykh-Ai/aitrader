# SHI RESET 37H Pre-0326 09:00 Monitor View Audit

Verdict: MIXED_CANDIDATES_FOUND

Scope: research-only artifact audit. No production code was modified. No Backtester, Executor, orders, entries, exits, PnL, live-readiness, strategy promotion, or trading advice were used or added.

## Cutoff And Inputs

- Primary cutoff: 2026-03-26T09:00:00Z.
- Primary audit window: 2026-03-26T00:00:00Z -> 2026-03-26T09:00:00Z.
- Context window: 2026-03-24T00:00:00Z -> 2026-03-26T09:00:00Z.
- Feed source: feed/ copied into an isolated cutoff slice at `market_monitor_runs/SHI_RESET_37H_pre_0326_0900_monitor_view_audit_v0/feed_asof_0900`. The source feed was not modified.
- Recovered feed: not used; this date is before the documented 2026-04-23 to 2026-05-06 outage window.
- State manifest as-of: 2026-03-26T09:00:00Z; completed daily artifacts through 2026-03-25; repo commit c83564f70f9e58ff0ab1069412f97d066e8ab882.
- Hidden-flow manifest: detection and episode context do not use future data; future labels are evaluation-only.

## Generated Artifacts

- State: `market_monitor_runs/SHI_RESET_37H_pre_0326_0900_monitor_view_audit_v0/state_asof_0900/market_structure_state_timeline.csv`
- State events: `market_monitor_runs/SHI_RESET_37H_pre_0326_0900_monitor_view_audit_v0/state_asof_0900/market_structure_events.csv`
- State levels: `market_monitor_runs/SHI_RESET_37H_pre_0326_0900_monitor_view_audit_v0/state_asof_0900/market_structure_levels.csv`
- State summary: `market_monitor_runs/SHI_RESET_37H_pre_0326_0900_monitor_view_audit_v0/state_asof_0900/market_structure_state_summary.md`
- State manifest: `market_monitor_runs/SHI_RESET_37H_pre_0326_0900_monitor_view_audit_v0/state_asof_0900/market_structure_state_manifest.json`
- Hidden-flow candidates: `market_monitor_runs/SHI_RESET_37H_pre_0326_0900_monitor_view_audit_v0/hidden_flow_asof_0900/hidden_flow_candidates.csv`
- Regime windows: `market_monitor_runs/SHI_RESET_37H_pre_0326_0900_monitor_view_audit_v0/hidden_flow_asof_0900/market_regime_windows.csv`
- Future labels, evaluation-only: `market_monitor_runs/SHI_RESET_37H_pre_0326_0900_monitor_view_audit_v0/hidden_flow_asof_0900/hidden_flow_future_labels.csv`
- Hidden-flow summary: `market_monitor_runs/SHI_RESET_37H_pre_0326_0900_monitor_view_audit_v0/hidden_flow_asof_0900/hidden_flow_research_summary.md`
- Hidden-flow manifest: `market_monitor_runs/SHI_RESET_37H_pre_0326_0900_monitor_view_audit_v0/hidden_flow_asof_0900/hidden_flow_manifest.json`

## Answer

Before 2026-03-26T09:00:00Z, the monitor produced review-worthy research context, but not a promoted hidden-flow candidate. The state layer showed a pullback/retest inside or near major resistance with seller-dominant pressure: price_change_pct=-1.830115, range_pct=2.417437, close_position=0.1562, delta_pct=-6.420618, seller_pressure_score=93.3, buyer_response_score=5.7, and dominant_side=SELLER.

The promoted candidate file was empty. Raw regime windows before cutoff were mixed: 36 windows in the primary window, including 22 UNCLEAR_FLOW_ANOMALY, 5 COMPRESSION_BEFORE_EXPANSION_CANDIDATE, 1 DOWNTREND_EXHAUSTION_CANDIDATE, 6 NORMALIZATION_AFTER_MARKDOWN, and 2 NORMALIZATION_AFTER_MARKUP. The strongest raw row was a HIGH confidence DOWNTREND_EXHAUSTION_CANDIDATE ending 2026-03-26T06:59:00Z; it remained unpromoted in `hidden_flow_candidates.csv`.

Interpretation for research review only: the as-of view exposed bearish state context plus mixed raw hidden-flow context, including a possible countertrend/exhaustion raw window and prior compression rows. It did not expose a promoted hidden-flow setup candidate.

## State Chain

| start_timestamp | end_timestamp | market_state | candidate_bias | candidate_strength | dominant_side | seller_pressure_score | buyer_response_score | overhead_supply_score | underlying_demand_score | range_quality | price_change_pct | range_pct | close_position | delta_pct | open_interest_change | support_context | resistance_context | evidence_summary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-03-24T00:00:00Z | 2026-03-24T23:59:00Z | MARKET_STRUCTURE_CONTEXT | NONE | LOW | MIXED | 33.1 | 17.8 | 100.0 | 89.2 | BIASED | -0.526464 | 3.619102 | 0.654 | -0.035677 | 722.27 | present | present | price_change_pct=-0.526; range_pct=3.619; close_position=0.654; delta_pct=-0.036; support_strength=100.0; resistance_strength=100.0; seller_pressure_score=33.1; buyer_response_score=17.8; overhead_supply_score=100.0; underlying_demand_score=89.2; dominant_side=MIXED; range_quality=BIASED; support_context=present; resistance_context=present; no dominant state transition |
| 2026-03-25T00:00:00Z | 2026-03-25T23:59:00Z | UP_EXPANSION_INTO_MAJOR_RESISTANCE | UP | HIGH | BUYER | 9.2 | 42.0 | 100.0 | 99.6 | BIASED | 1.100193 | 2.308917 | 0.5635 | 2.779979 | 146.7 | present | present | price_change_pct=1.100; range_pct=2.309; close_position=0.564; delta_pct=2.780; support_strength=100.0; resistance_strength=100.0; seller_pressure_score=9.2; buyer_response_score=42.0; overhead_supply_score=100.0; underlying_demand_score=99.6; dominant_side=BUYER; range_quality=BIASED; support_context=present; resistance_context=present; upside expansion reached next strong resistance band |
| 2026-03-26T00:00:00Z | 2026-03-26T09:00:00Z | PULLBACK_RETEST_INSIDE_MAJOR_RESISTANCE | MIXED | MEDIUM | SELLER | 93.3 | 5.7 | 98.8 | 98.2 | BIASED | -1.830115 | 2.417437 | 0.1562 | -6.420618 | 663.6 | present | present | price_change_pct=-1.830; range_pct=2.417; close_position=0.156; delta_pct=-6.421; support_strength=100.0; resistance_strength=100.0; seller_pressure_score=93.3; buyer_response_score=5.7; overhead_supply_score=98.8; underlying_demand_score=98.2; dominant_side=SELLER; range_quality=BIASED; support_context=present; resistance_context=present; post-expansion price remains inside/near major resistance band |

## Candidate Chain

No promoted hidden-flow candidates had `end_timestamp <= 2026-03-26T09:00:00Z`; `hidden_flow_candidates.csv` contains only the header.

## Raw Regime Windows Because Candidate Chain Was Empty

- Primary raw window count: 36
- Label counts: {'UNCLEAR_FLOW_ANOMALY': 22, 'COMPRESSION_BEFORE_EXPANSION_CANDIDATE': 5, 'DOWNTREND_EXHAUSTION_CANDIDATE': 1, 'NORMALIZATION_AFTER_MARKDOWN': 6, 'NORMALIZATION_AFTER_MARKUP': 2}
- Trend counts: {'RANGE': 9, 'DOWN': 22, 'UP': 5}
- Zone-position counts: {'near_upper_zone': 8, 'near_lower_zone': 12, 'between_zones': 8, 'inside_zone': 8}

| start_timestamp | end_timestamp | candidate_label | confidence | candidate_score | trend_direction | prior_trend_direction | nearest_zone_side | zone_position_context | delta_pct | range_pct | close_position | open_interest_change | evidence_summary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-03-26T06:00:00+00:00 | 2026-03-26T06:59:00+00:00 | DOWNTREND_EXHAUSTION_CANDIDATE | HIGH | 83.688 | RANGE | DOWN | SELL_SIDE | inside_zone | 0.079974 | 0.444643 | 0.8123 | 394.78 | delta_pct=0.0800; relative_volume=1.372; price_change_pct=0.114; range_pct=0.445; pressure_without_progress=61.5; compression=53.5; buyer_absorption=37.2; seller_absorption=57.4; accumulation=83.7; distribution=47.8; neutral_compression=51.3; prior_trend=DOWN; zone_context=inside_zone; close_location=0.81; nearest_zone=zone_000006:SELL_SIDE |
| 2026-03-25T08:00:00+00:00 | 2026-03-26T07:59:00+00:00 | NORMALIZATION_AFTER_MARKDOWN | LOW | 77.889 | DOWN | DOWN | SELL_SIDE | inside_zone | 0.009647 | 3.211989 | 0.1469 | -138.74 | delta_pct=0.0096; relative_volume=0.880; price_change_pct=-1.189; range_pct=3.212; pressure_without_progress=50.7; compression=39.4; buyer_absorption=33.8; seller_absorption=21.1; accumulation=58.3; distribution=27.7; neutral_compression=43.0; prior_trend=DOWN; zone_context=inside_zone; close_location=0.15; nearest_zone=zone_000006:SELL_SIDE |
| 2026-03-25T02:00:00+00:00 | 2026-03-26T01:59:00+00:00 | NORMALIZATION_AFTER_MARKUP | LOW | 77.195 | UP | RANGE | BUY_SIDE | near_upper_zone | 0.020965 | 2.300151 | 0.5284 | 511.9 | delta_pct=0.0210; relative_volume=0.835; price_change_pct=0.836; range_pct=2.300; pressure_without_progress=46.5; compression=56.6; buyer_absorption=21.4; seller_absorption=39.7; accumulation=37.3; distribution=57.2; neutral_compression=53.4; prior_trend=RANGE; zone_context=near_upper_zone; close_location=0.53; nearest_zone=zone_000011:BUY_SIDE |
| 2026-03-25T01:00:00+00:00 | 2026-03-26T00:59:00+00:00 | COMPRESSION_BEFORE_EXPANSION_CANDIDATE | LOW | 77.126 | UP | RANGE | BUY_SIDE | near_upper_zone | 0.017753 | 2.294914 | 0.5283 | 238.17 | delta_pct=0.0178; relative_volume=0.848; price_change_pct=0.606; range_pct=2.295; pressure_without_progress=50.0; compression=56.7; buyer_absorption=21.3; seller_absorption=39.6; accumulation=37.2; distribution=57.1; neutral_compression=54.6; prior_trend=RANGE; zone_context=near_upper_zone; close_location=0.53; nearest_zone=zone_000011:BUY_SIDE |
| 2026-03-26T03:00:00+00:00 | 2026-03-26T06:59:00+00:00 | UNCLEAR_FLOW_ANOMALY | LOW | 75.066 | DOWN | DOWN | SELL_SIDE | inside_zone | -0.08025 | 1.594101 | 0.2238 | -84.6 | delta_pct=-0.0803; relative_volume=1.005; price_change_pct=-1.110; range_pct=1.594; pressure_without_progress=41.6; compression=22.9; buyer_absorption=31.5; seller_absorption=18.8; accumulation=53.9; distribution=23.4; neutral_compression=28.9; prior_trend=DOWN; zone_context=inside_zone; close_location=0.22; nearest_zone=zone_000006:SELL_SIDE |
| 2026-03-26T04:00:00+00:00 | 2026-03-26T07:59:00+00:00 | UNCLEAR_FLOW_ANOMALY | LOW | 74.607 | DOWN | DOWN | SELL_SIDE | inside_zone | -0.071828 | 1.640741 | 0.2878 | -25.48 | delta_pct=-0.0718; relative_volume=1.091; price_change_pct=-1.147; range_pct=1.641; pressure_without_progress=42.3; compression=20.7; buyer_absorption=31.1; seller_absorption=18.4; accumulation=53.2; distribution=22.7; neutral_compression=27.6; prior_trend=DOWN; zone_context=inside_zone; close_location=0.29; nearest_zone=zone_000006:SELL_SIDE |
| 2026-03-25T22:00:00+00:00 | 2026-03-26T01:59:00+00:00 | UNCLEAR_FLOW_ANOMALY | LOW | 73.889 | UP | RANGE | BUY_SIDE | near_upper_zone | -0.017704 | 0.984365 | 0.4672 | 207.3 | delta_pct=-0.0177; relative_volume=0.525; price_change_pct=0.329; range_pct=0.984; pressure_without_progress=43.7; compression=52.4; buyer_absorption=24.2; seller_absorption=35.5; accumulation=39.9; distribution=52.1; neutral_compression=49.6; prior_trend=RANGE; zone_context=near_upper_zone; close_location=0.47; nearest_zone=zone_000011:BUY_SIDE |
| 2026-03-25T18:00:00+00:00 | 2026-03-26T05:59:00+00:00 | UNCLEAR_FLOW_ANOMALY | LOW | 72.814 | DOWN | DOWN | SELL_SIDE | between_zones | -0.040749 | 2.402452 | 0.0424 | -1210.66 | delta_pct=-0.0407; relative_volume=0.584; price_change_pct=-1.095; range_pct=2.402; pressure_without_progress=41.4; compression=30.9; buyer_absorption=26.7; seller_absorption=23.3; accumulation=50.5; distribution=30.0; neutral_compression=34.3; prior_trend=DOWN; zone_context=between_zones; close_location=0.04; nearest_zone=zone_000006:SELL_SIDE |

## Required Checks

- Bearish state context: present in the 2026-03-26 00:00-09:00 state row via seller dominance, low close position, negative price change, and negative delta.
- Bullish countertrend context: present only as an unpromoted raw DOWNTREND_EXHAUSTION_CANDIDATE ending 2026-03-26T06:59:00Z.
- Compression before expansion: present only in raw market_regime_windows.csv; no promoted hidden-flow candidate.
- Seller absorption: not promoted; raw seller_absorption_score was visible but not the dominant promoted output.
- Buyer absorption: not promoted; raw buyer_absorption_score was visible but not the dominant promoted output.
- Failed breakout / seller reclaim: not directly emitted as a promoted hidden-flow candidate in this as-of run. State context did show post-expansion pullback/retest inside or near major resistance.
- Only unclear flow: not solely; the primary raw windows include unclear flow plus compression/exhaustion/normalization labels.
- No relevant context: false; relevant state context was present before cutoff.

## Missed Or Limited Cases

- No promoted hidden-flow candidate was produced before cutoff despite raw windows containing compression and exhaustion labels.
- The strongest raw hidden-flow candidate was countertrend/exhaustion, while the state row was seller-dominant; this is why the verdict is mixed rather than a clean bearish candidate verdict.
- `market_structure_events.csv` was header-only for this as-of state run.
- `hidden_flow_future_labels.csv` was header-only under the cutoff-limited feed and was not used as evidence.

## Contract

- No production code changes.
- No Backtester.
- No Executor.
- No orders.
- No entries or exits.
- No PnL.
- No live-readiness claim.
- No strategy promotion.
- No trading advice.
