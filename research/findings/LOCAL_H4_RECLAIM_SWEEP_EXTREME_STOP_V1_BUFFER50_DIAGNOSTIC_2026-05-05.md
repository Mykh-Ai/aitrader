# LOCAL H4 Reclaim Sweep-Extreme Stop V1 Buffer50 Diagnostic

Date: 2026-05-05

Status: standalone diagnostic research only. Not FIELD, not live strategy, not execution-ready evidence.

This diagnostic uses latest/local confirmed H4 swing high/low selection, H4 reclaim-close entry, and sweep-extreme stop with fixed `buffer_usd=50`. It does not use `FAILED_BREAK_RECLAIM_EXTENDED_V1`, does not use 1m entry, does not use reference-level stops, and does not run the Backtester.

## Local Diagnostic Summary By Level Family

| level_family | candidate_count | direction_count | diagnostic_trade_allowed_count | no_trade_reason_counts | buffer_was_compressed_count | hit_1R_before_stop_count | hit_1_5R_before_stop_count | hit_2R_before_stop_count | same_bar_ambiguity_count | first_stop_touch_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MAIN_STRUCTURAL_HIGH_SWEEP | 6 | SHORT=6 | 4 | <allowed>=4; sweep_extreme_risk_too_large=2 | 0 | 2 | 1 | 1 | 0 | 6 |
| LOCAL_LOWER_HIGH_SWEEP | 7 | SHORT=7 | 7 | <allowed>=7 | 0 | 5 | 4 | 3 | 0 | 6 |
| LOCAL_HIGHER_LOW_SWEEP | 13 | LONG=13 | 12 | <allowed>=12; sweep_extreme_risk_too_large=1 | 0 | 10 | 9 | 8 | 0 | 7 |

## Current Active-Level Registry Comparison

| level_family | candidate_count | direction_count | diagnostic_trade_allowed_count | no_trade_reason_counts | buffer_was_compressed_count | hit_1R_before_stop_count | hit_1_5R_before_stop_count | hit_2R_before_stop_count | same_bar_ambiguity_count | first_stop_touch_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MAIN_STRUCTURAL_HIGH_SWEEP | 9 | SHORT=9 | 5 | <allowed>=5; bearish_reclaim_required=2; sweep_extreme_risk_too_large;bearish_reclaim_required=1; sweep_extreme_risk_too_large=1 | 3 | 2 | 1 | 1 | 0 | 6 |
| MAIN_STRUCTURAL_LOW_SWEEP | 1 | LONG=1 | 0 | sweep_extreme_risk_too_large=1 | 0 | 0 | 0 | 0 | 0 | 0 |
| LOCAL_HIGHER_LOW_SWEEP | 2 | LONG=2 | 1 | bullish_reclaim_required=1; <allowed>=1 | 0 | 2 | 2 | 2 | 0 | 0 |

## Overlap By Direction, Level, Sweep Time, Entry Time

- Overlap rows: 5

| direction | level_price | sweep_h4_open_ts | entry_ts | local_row_number | local_level_family | active_row_number | active_level_family |
| --- | --- | --- | --- | --- | --- | --- | --- |
| LONG | 70671.6 | 2026-04-09 00:00:00+00:00 | 2026-04-09 08:00:00+00:00 | 11 | LOCAL_HIGHER_LOW_SWEEP | 5 | LOCAL_HIGHER_LOW_SWEEP |
| SHORT | 72858.5 | 2026-04-09 20:00:00+00:00 | 2026-04-10 04:00:00+00:00 | 12 | MAIN_STRUCTURAL_HIGH_SWEEP | 6 | MAIN_STRUCTURAL_HIGH_SWEEP |
| SHORT | 73128 | 2026-04-10 12:00:00+00:00 | 2026-04-11 00:00:00+00:00 | 14 | MAIN_STRUCTURAL_HIGH_SWEEP | 7 | MAIN_STRUCTURAL_HIGH_SWEEP |
| SHORT | 73450 | 2026-04-11 16:00:00+00:00 | 2026-04-12 00:00:00+00:00 | 16 | MAIN_STRUCTURAL_HIGH_SWEEP | 8 | MAIN_STRUCTURAL_HIGH_SWEEP |
| SHORT | 74900 | 2026-04-14 12:00:00+00:00 | 2026-04-14 20:00:00+00:00 | 19 | MAIN_STRUCTURAL_HIGH_SWEEP | 9 | MAIN_STRUCTURAL_HIGH_SWEEP |

## Local Candidate Rows

| row_number | direction | entry_ts | level_family | level_price | sweep_extreme_price | entry_price | stop_price | final_risk_usd | diagnostic_trade_allowed | no_trade_reason | hit_1R_before_stop | hit_1_5R_before_stop | hit_2R_before_stop | first_stop_touch_ts | same_bar_ambiguity |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | LONG | 2026-03-30 04:00:00+00:00 | LOCAL_HIGHER_LOW_SWEEP | 66233.6 | 66111 | 67138.9 | 66061 | 1077.9 | True |  | True | False | False | 2026-03-31 09:56:00+00:00 | False |
| 2 | SHORT | 2026-03-31 08:00:00+00:00 | LOCAL_LOWER_HIGH_SWEEP | 68148.4 | 68377 | 67343.9 | 68427 | 1083.1 | True |  | True | False | False | 2026-03-31 17:14:00+00:00 | False |
| 3 | LONG | 2026-03-31 16:00:00+00:00 | LOCAL_HIGHER_LOW_SWEEP | 66200.1 | 65938 | 66700 | 65888 | 812 | True |  | True | True | True | 2026-04-02 13:17:00+00:00 | False |
| 4 | SHORT | 2026-04-01 00:00:00+00:00 | LOCAL_LOWER_HIGH_SWEEP | 68377 | 68600 | 68241.4 | 68650 | 408.6 | True |  | True | True | False | 2026-04-01 05:25:00+00:00 | False |
| 5 | SHORT | 2026-04-01 20:00:00+00:00 | LOCAL_LOWER_HIGH_SWEEP | 68600 | 69288 | 68143.7 | 69338 | 1194.3 | True |  | True | True | True |  | False |
| 6 | SHORT | 2026-04-04 20:00:00+00:00 | LOCAL_LOWER_HIGH_SWEEP | 67350 | 67554.5 | 67262.7 | 67604.5 | 341.8 | True |  | True | True | True | 2026-04-05 15:30:00+00:00 | False |
| 7 | LONG | 2026-04-05 12:00:00+00:00 | LOCAL_HIGHER_LOW_SWEEP | 66745.5 | 66575.5 | 66972.7 | 66525.5 | 447.2 | True |  | True | True | True |  | False |
| 8 | SHORT | 2026-04-05 20:00:00+00:00 | LOCAL_LOWER_HIGH_SWEEP | 67554.5 | 67828.6 | 67329.1 | 67878.6 | 549.5 | True |  | False | False | False | 2026-04-05 22:44:00+00:00 | False |
| 9 | SHORT | 2026-04-07 00:00:00+00:00 | MAIN_STRUCTURAL_HIGH_SWEEP | 70252.9 | 70332.5 | 68818 | 70382.5 | 1564.5 | False | sweep_extreme_risk_too_large | False | False | False | 2026-04-07 22:06:00+00:00 | False |
| 10 | LONG | 2026-04-07 20:00:00+00:00 | LOCAL_HIGHER_LOW_SWEEP | 68227.5 | 68033 | 68975.8 | 67983 | 992.8 | True |  | True | True | True |  | False |
| 11 | LONG | 2026-04-09 08:00:00+00:00 | LOCAL_HIGHER_LOW_SWEEP | 70671.6 | 70428 | 70945 | 70378 | 567 | True |  | True | True | True |  | False |
| 12 | SHORT | 2026-04-10 04:00:00+00:00 | MAIN_STRUCTURAL_HIGH_SWEEP | 72858.5 | 73128 | 71837.3 | 73178 | 1340.7 | True |  | False | False | False | 2026-04-10 15:24:00+00:00 | False |
| 13 | LONG | 2026-04-10 12:00:00+00:00 | LOCAL_HIGHER_LOW_SWEEP | 71539.9 | 71382.1 | 72092.3 | 71332.1 | 760.2 | True |  | True | True | True | 2026-04-12 01:49:00+00:00 | False |
| 14 | SHORT | 2026-04-11 00:00:00+00:00 | MAIN_STRUCTURAL_HIGH_SWEEP | 73128 | 73255.7 | 72917.4 | 73305.7 | 388.3 | True |  | True | False | False | 2026-04-11 18:35:00+00:00 | False |
| 15 | LONG | 2026-04-11 20:00:00+00:00 | LOCAL_HIGHER_LOW_SWEEP | 72566.4 | 72451.9 | 73635.8 | 72401.9 | 1233.9 | True |  | False | False | False | 2026-04-12 01:35:00+00:00 | False |
| 16 | SHORT | 2026-04-12 00:00:00+00:00 | MAIN_STRUCTURAL_HIGH_SWEEP | 73450 | 73773.4 | 73013.4 | 73823.4 | 810 | True |  | True | True | True | 2026-04-13 22:14:00+00:00 | False |
| 17 | LONG | 2026-04-13 04:00:00+00:00 | LOCAL_HIGHER_LOW_SWEEP | 70566.5 | 70458.2 | 70944.8 | 70408.2 | 536.6 | True |  | True | True | True |  | False |
| 18 | SHORT | 2026-04-14 12:00:00+00:00 | MAIN_STRUCTURAL_HIGH_SWEEP | 74870 | 74900 | 74342.5 | 74950 | 607.5 | True |  | False | False | False | 2026-04-14 13:40:00+00:00 | False |
| 19 | SHORT | 2026-04-14 20:00:00+00:00 | MAIN_STRUCTURAL_HIGH_SWEEP | 74900 | 76009 | 74171.9 | 76059 | 1887.1 | False | sweep_extreme_risk_too_large | False | False | False | 2026-04-17 09:28:00+00:00 | False |
| 20 | LONG | 2026-04-15 12:00:00+00:00 | LOCAL_HIGHER_LOW_SWEEP | 73766.8 | 73449 | 74155 | 73399 | 756 | True |  | True | True | False | 2026-04-16 13:54:00+00:00 | False |
| 21 | SHORT | 2026-04-16 08:00:00+00:00 | LOCAL_LOWER_HIGH_SWEEP | 74739.2 | 75240 | 74667.7 | 75290 | 622.3 | True |  | True | True | True | 2026-04-16 19:53:00+00:00 | False |
| 22 | LONG | 2026-04-16 16:00:00+00:00 | LOCAL_HIGHER_LOW_SWEEP | 74400 | 74226.2 | 74659.4 | 74176.2 | 483.2 | True |  | False | False | False | 2026-04-16 16:52:00+00:00 | False |
| 23 | LONG | 2026-04-19 12:00:00+00:00 | LOCAL_HIGHER_LOW_SWEEP | 75395.9 | 75314 | 75555.8 | 75264 | 291.8 | True |  | True | True | True | 2026-04-19 16:55:00+00:00 | False |
| 24 | SHORT | 2026-04-21 16:00:00+00:00 | LOCAL_LOWER_HIGH_SWEEP | 76531 | 76999 | 75800 | 77049 | 1249 | True |  | False | False | False | 2026-04-22 02:17:00+00:00 | False |
| 25 | LONG | 2026-04-22 00:00:00+00:00 | LOCAL_HIGHER_LOW_SWEEP | 75433.1 | 75355.2 | 76288.2 | 75305.2 | 983 | True |  | True | True | True |  | False |
| 26 | LONG | 2026-04-23 16:00:00+00:00 | LOCAL_HIGHER_LOW_SWEEP | 77410.7 | 76504.6 | 78329.2 | 76454.6 | 1874.6 | False | sweep_extreme_risk_too_large | False | False | False |  | False |

## Files

- Diagnostic CSV: `research/results/local_h4_reclaim_sweep_extreme_stop_v1_buffer50_2026-05-05.csv`
- Report: `research/findings/LOCAL_H4_RECLAIM_SWEEP_EXTREME_STOP_V1_BUFFER50_DIAGNOSTIC_2026-05-05.md`

## Interpretation Boundary

- This answers whether local H4 swing selection looks different once entry and stop are cleaned up.
- MAIN and LOCAL buckets are separate setup families and must not be pooled as one H4 false-break/reclaim edge.
- Any positive path-order rows remain diagnostic only until a separate research decision defines a formal contract and holdout path.
