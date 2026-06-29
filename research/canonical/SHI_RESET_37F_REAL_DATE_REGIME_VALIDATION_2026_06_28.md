# SHI_RESET_37F Real-Date Regime Validation

Status: SHI_RESET_37F_REAL_DATE_REGIME_VALIDATION_V0

Verdict: PARTIAL

Scope: generated Market Structure State rows only. No Backtester, no Executor, no PnL, no entries/exits, no strategy promotion, no orders, and no live-readiness claim.

## Inputs

- Existing artifact root: `market_monitor_runs/SHI_RESET_37E_live_sim_2026_06_02_0400`
- Feed slice: `market_monitor_runs/SHI_RESET_37E_live_sim_2026_06_02_0400/feed_slice`
- Completed daily artifacts: `market_monitor_runs/SHI_RESET_37E_live_sim_2026_06_02_0400/daily_completed_input/daily`
- Validation output root: `market_monitor_runs/SHI_RESET_37F_real_date_regime_validation_v0`

## Generated Outputs

- `market_monitor_runs/SHI_RESET_37F_real_date_regime_validation_v0/state_2026_06_01/market_structure_state_timeline.csv`
- `market_monitor_runs/SHI_RESET_37F_real_date_regime_validation_v0/state_2026_06_02_asof_0400/market_structure_state_timeline.csv`
- `market_monitor_runs/SHI_RESET_37F_real_date_regime_validation_v0/state_2026_05_15_to_17/market_structure_state_timeline.csv`

## Check 1: 2026-06-01 Expanded Bearish Move

Result: PASS

The generated row does not classify as range. It classifies as `MARKDOWN_ABOVE_SUPPORT` with `candidate_bias=DOWN`, `candidate_strength=HIGH`, `dominant_side=SELLER`, and `range_quality=BIASED`.

| start_timestamp | end_timestamp | market_state | candidate_bias | candidate_strength | price_change_pct | range_pct | close_position | delta_pct | support | resistance | evidence_summary |
|---|---|---|---|---|---:|---:|---:|---:|---|---|---|
| 2026-06-01T00:00:00Z | 2026-06-01T23:59:00Z | MARKDOWN_ABOVE_SUPPORT | DOWN | HIGH | -3.028912 | 4.840137 | 0.2219 | -1.939885 | band_000001 70615.57455-71070.81765 | band_000002 71314.325-71423.2938 | price_change_pct=-3.029; range_pct=4.840; close_position=0.222; delta_pct=-1.940; support_strength=100.0; resistance_strength=28.5; seller_pressure_score=100.0; buyer_response_score=15.4; overhead_supply_score=28.5; underlying_demand_score=94.3; dominant_side=SELLER; range_quality=BIASED; support_context=present; resistance_context=present; downside expansion classified before support/range fallback |

## Check 2: 2026-06-02 As-Of 04:00

Result: PARTIAL

The generated 04:00 row exposes downside context descriptively: negative price change, negative delta, below resistance, and no proven balance. It does not emit action advice. However, the repaired classifier does not classify this row as seller-dominant. It assigns `dominant_side=MIXED`, `candidate_bias=MIXED`, and `candidate_strength=LOW` because the close finished in the upper half of the intraday window and `seller_pressure_score=33.2` stays below the current dominance threshold.

| start_timestamp | end_timestamp | market_state | candidate_bias | candidate_strength | price_change_pct | range_pct | close_position | delta_pct | support | resistance | evidence_summary |
|---|---|---|---|---|---:|---:|---:|---:|---|---|---|
| 2026-06-01T00:00:00Z | 2026-06-01T23:59:00Z | MARKDOWN_ABOVE_SUPPORT | DOWN | HIGH | -3.028912 | 4.840137 | 0.2219 | -1.939885 | band_000001 70615.57455-70841.403 | band_000002 70999.78235-71423.2938 | price_change_pct=-3.029; range_pct=4.840; close_position=0.222; delta_pct=-1.940; support_strength=100.0; resistance_strength=31.5; seller_pressure_score=100.0; buyer_response_score=15.4; overhead_supply_score=31.5; underlying_demand_score=90.4; dominant_side=SELLER; range_quality=BIASED; support_context=present; resistance_context=present; downside expansion classified before support/range fallback |
| 2026-06-02T00:00:00Z | 2026-06-02T04:00:00Z | CONTEXT_BELOW_RESISTANCE | MIXED | LOW | -0.68492 | 1.958651 | 0.6435 | -4.077639 | band_000001 70615.57455-70841.403 | band_000002 70999.78235-71423.2938 | price_change_pct=-0.685; range_pct=1.959; close_position=0.643; delta_pct=-4.078; support_strength=100.0; resistance_strength=31.5; seller_pressure_score=33.2; buyer_response_score=10.4; overhead_supply_score=29.8; underlying_demand_score=98.7; dominant_side=MIXED; range_quality=MIXED; support_context=present; resistance_context=present; price remains below resistance_upper=71423.294 without proven balance |

Missed case: 2026-06-02 04:00 does not expose seller dominance as a state-level classification. It exposes descriptive downside context but remains below the current seller-dominance gate.

## Check 3: 2026-05-15 To 2026-05-17 Transition

Result: PASS

The transition window shows persistent seller pressure and failed buyer continuation as descriptive state context. All three generated rows classify as `MARKDOWN_ABOVE_SUPPORT`; May 15 is high strength, May 16-17 are medium strength. The evidence shows overhead supply remained strong while seller pressure persisted.

| start_timestamp | end_timestamp | market_state | candidate_bias | candidate_strength | price_change_pct | range_pct | close_position | delta_pct | support | resistance | evidence_summary |
|---|---|---|---|---|---:|---:|---:|---:|---|---|---|
| 2026-05-15T00:00:00Z | 2026-05-15T23:59:00Z | MARKDOWN_ABOVE_SUPPORT | DOWN | HIGH | -2.408614 | 3.833863 | 0.1554 | -0.328851 | band_000001 76627.667-76704.333 | band_000003 78047.9565-79907.934 | price_change_pct=-2.409; range_pct=3.834; close_position=0.155; delta_pct=-0.329; support_strength=26.5; resistance_strength=100.0; seller_pressure_score=100.0; buyer_response_score=11.3; overhead_supply_score=100.0; underlying_demand_score=0.0; dominant_side=SELLER; range_quality=BIASED; support_context=present; resistance_context=present; downside expansion classified before support/range fallback |
| 2026-05-16T00:00:00Z | 2026-05-16T23:59:00Z | MARKDOWN_ABOVE_SUPPORT | DOWN | MEDIUM | -1.190464 | 2.059102 | 0.3349 | -6.221427 | band_000001 76627.667-76704.333 | band_000003 78047.9565-79907.934 | price_change_pct=-1.190; range_pct=2.059; close_position=0.335; delta_pct=-6.221; support_strength=26.5; resistance_strength=100.0; seller_pressure_score=60.0; buyer_response_score=4.2; overhead_supply_score=100.0; underlying_demand_score=4.5; dominant_side=SELLER; range_quality=BIASED; support_context=present; resistance_context=present; downside expansion classified before support/range fallback |
| 2026-05-17T00:00:00Z | 2026-05-17T23:59:00Z | MARKDOWN_ABOVE_SUPPORT | DOWN | MEDIUM | -0.917107 | 2.476065 | 0.3974 | -6.483481 | band_000001 76627.667-76704.333 | band_000002 77562.9991-81828.894 | price_change_pct=-0.917; range_pct=2.476; close_position=0.397; delta_pct=-6.483; support_strength=26.5; resistance_strength=100.0; seller_pressure_score=51.4; buyer_response_score=5.9; overhead_supply_score=97.2; underlying_demand_score=15.4; dominant_side=SELLER; range_quality=BIASED; support_context=present; resistance_context=present; downside expansion classified before support/range fallback |

## Missed Cases

1. `2026-06-02T00:00:00Z -> 2026-06-02T04:00:00Z`: downside context is visible, but the row is not seller-dominant under the current scoring gate. Current output is `CONTEXT_BELOW_RESISTANCE`, `candidate_bias=MIXED`, `candidate_strength=LOW`, `dominant_side=MIXED`.

## Final Verdict

PARTIAL

37F fixes the severe 37E failure where expanded bearish moves above support were classified as range. It passes the 2026-06-01 and 2026-05-15..17 checks. It partially misses the 2026-06-02 04:00 requirement because the generated row is descriptive and non-range, but not seller-dominant.
