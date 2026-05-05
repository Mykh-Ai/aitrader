# H4 Active-Level Reclaim-Close Test V1 Structural Split After Feed Fix

Date: 2026-05-05

Status: diagnostic research only. This report does not change detector logic, does not run the old failed-break detector, does not run the Backtester, and does not make FIELD/live claims.

Joined standalone registry-aware diagnostic, compressed buffer350 diagnostics, and structural audit lens by `candidate_id`.

## Summary By Level Family

| level_family | candidate_count | direction_count | diagnostic_trade_allowed_count | no_trade_reason_counts | buffer_was_compressed_count | hit_1R_before_stop_count | hit_1_5R_before_stop_count | hit_2R_before_stop_count | same_bar_ambiguity_count | first_stop_touch_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MAIN_STRUCTURAL_HIGH_SWEEP | 9 | SHORT=9 | 5 | <allowed>=5; bearish_reclaim_required=2; sweep_extreme_risk_too_large;bearish_reclaim_required=1; sweep_extreme_risk_too_large=1 | 3 | 2 | 1 | 1 | 0 | 9 |
| MAIN_STRUCTURAL_LOW_SWEEP | 1 | LONG=1 | 0 | sweep_extreme_risk_too_large=1 | 0 | 0 | 0 | 0 | 0 | 1 |
| LOCAL_HIGHER_LOW_SWEEP | 2 | LONG=2 | 1 | bullish_reclaim_required=1; <allowed>=1 | 0 | 2 | 2 | 2 | 0 | 2 |

## Focused Rows

| row_number | direction | entry_ts | level_family | active_level_price | structural_extreme_price_30h4 | active_is_structural_extreme_30h4 | sweep_extreme_price | diagnostic_trade_allowed_compressed | no_trade_reason_compressed | buffer_was_compressed | final_risk_usd | hit_1R_before_stop | hit_1_5R_before_stop | hit_2R_before_stop | first_stop_touch_ts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | LONG | 2026-03-30 04:00:00+0000 | MAIN_STRUCTURAL_LOW_SWEEP | 65501.0 | 65501.0 | True | 64918.2 | False | sweep_extreme_risk_too_large | False |  | False | False | False |  |
| 5 | LONG | 2026-04-09 08:00:00+0000 | LOCAL_HIGHER_LOW_SWEEP | 70671.6 | 66575.5 | False | 70428.0 | False | bullish_reclaim_required | False | 867.0 | True | True | True |  |
| 7 | SHORT | 2026-04-11 00:00:00+0000 | MAIN_STRUCTURAL_HIGH_SWEEP | 73128.0 | 73128.0 | True | 73255.7 | True |  | False | 688.3000000000029 | False | False | False | 2026-04-11 18:36:00+0000 |
| 8 | SHORT | 2026-04-12 00:00:00+0000 | MAIN_STRUCTURAL_HIGH_SWEEP | 73450.0 | 73450.0 | True | 73773.4 | True |  | False | 1110.0 | True | True | True | 2026-04-13 22:16:00+0000 |
| 10 | LONG | 2026-04-20 04:00:00+0000 | LOCAL_HIGHER_LOW_SWEEP | 74480.0 | 73256.8 | False | 73700.2 | True |  | False | 1243.699999999997 | True | True | True |  |
| 12 | SHORT | 2026-04-23 00:00:00+0000 | MAIN_STRUCTURAL_HIGH_SWEEP | 78447.5 | 78447.5 | True | 79370.0 | True |  | True | 1500.0 | True | False | False |  |

## Files

- Detail CSV: `research/results/h4_active_level_reclaim_close_test_v1_structural_split_after_feed_fix_2026-05-05.csv`
- Report: `research/findings/H4_ACTIVE_LEVEL_RECLAIM_CLOSE_TEST_V1_STRUCTURAL_SPLIT_AFTER_FEED_FIX_2026-05-05.md`

## Interpretation Boundary

- `MAIN_STRUCTURAL_HIGH_SWEEP` and `MAIN_STRUCTURAL_LOW_SWEEP` are structural-family diagnostics under the 30-H4 pivot-extreme heuristic.
- `LOCAL_HIGHER_LOW_SWEEP` / `LOCAL_LOWER_HIGH_SWEEP` are separate local/internal families and must not be mixed into main structural evidence.
- The SHORT main structural bucket remains diagnostic research only; no execution claim is made.