# Sprint 07 BTC Surface Repair Report

## 1. Executive Verdict

`BTC_CONTINUE_WITH_REPLAY_SPEC`.

Sprint 07 repairs BTC-only aggregation over Sprint 06 events/outcomes. It does not change Sprint 06 predicates, run Backtester, open Phase 4, touch Executor/live, or create PROMOTE.

## 2. Why Sprint 06 Verdict Was Too Strong

Sprint 06 grouped by too many dimensions at once, causing many top-ranked surfaces to contain only 1-2 events. That supports `BTC_SURFACE_AGGREGATION_REPAIR_REQUIRED`, not a market/universe change.

## 3. Data Used

- Sprint 06 clustered events and outcomes.
- Sprint 06 features for lineage availability check only.
- No new event predicates and no future outcomes as predicates.

## 4. Family-Level Aggregates

| family | side | horizon | events | independent_days | max_day_share | median_return_bp | positive_rate | net_bp_after_0_00015 | MFE_MAE_ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| EXHAUSTION_REVERSAL | SHORT | 24 | 181 | 54 | 0.055249 | 14.338048 | 0.707182 | 11.710062 | 1.757758 | NEEDS_REPLAY_SPEC |
| EXHAUSTION_REVERSAL | SHORT | 12 | 181 | 54 | 0.055249 | 11.744872 | 0.729282 | 10.289549 | 1.757758 | NEEDS_REPLAY_SPEC |
| EXHAUSTION_REVERSAL | SHORT | 60 | 181 | 54 | 0.055249 | 12.876336 | 0.629834 | 8.265443 | 1.305889 | NEEDS_REPLAY_SPEC |
| EXHAUSTION_REVERSAL | LONG | 60 | 161 | 49 | 0.062112 | 10.146359 | 0.658385 | 8.245225 | 1.193008 | NEEDS_REPLAY_SPEC |
| EXHAUSTION_REVERSAL | SHORT | 6 | 181 | 54 | 0.055249 | 8.553625 | 0.718232 | 7.261098 | 1.757758 | NEEDS_REPLAY_SPEC |
| EXHAUSTION_REVERSAL | LONG | 12 | 161 | 49 | 0.062112 | 8.781185 | 0.701863 | 6.666997 | 1.344341 | NEEDS_REPLAY_SPEC |
| VWAP_DEVIATION_REVERSION | SHORT | 60 | 1282 | 56 | 0.060842 | 9.832838 | 0.605304 | 6.624933 | 1.390887 | NEEDS_REPLAY_SPEC |
| VWAP_DEVIATION_REVERSION | LONG | 24 | 1271 | 52 | 0.057435 | 7.091258 | 0.651456 | 6.537441 | 1.875999 | NEEDS_REPLAY_SPEC |
| VWAP_DEVIATION_REVERSION | LONG | 60 | 1271 | 52 | 0.057435 | 8.237094 | 0.609756 | 6.526569 | 1.36754 | NEEDS_REPLAY_SPEC |
| VWAP_DEVIATION_REVERSION | SHORT | 24 | 1283 | 56 | 0.060795 | 8.038477 | 0.638348 | 6.497477 | 1.820122 | NEEDS_REPLAY_SPEC |
| EXHAUSTION_REVERSAL | LONG | 24 | 161 | 49 | 0.062112 | 9.783177 | 0.670807 | 6.10424 | 1.344341 | NEEDS_REPLAY_SPEC |
| VWAP_DEVIATION_REVERSION | LONG | 12 | 1271 | 52 | 0.057435 | 6.484428 | 0.677419 | 5.853668 | 1.875999 | NEEDS_REPLAY_SPEC |
| VWAP_DEVIATION_REVERSION | SHORT | 12 | 1285 | 56 | 0.0607 | 6.637196 | 0.675486 | 5.822693 | 1.822195 | NEEDS_REPLAY_SPEC |
| EXHAUSTION_REVERSAL | SHORT | 3 | 181 | 54 | 0.055249 | 6.364464 | 0.729282 | 5.248432 | 1.757758 | NEEDS_REPLAY_SPEC |
| VWAP_DEVIATION_REVERSION | SHORT | 6 | 1285 | 56 | 0.0607 | 4.783398 | 0.668482 | 4.276802 | 1.822195 | NEEDS_REPLAY_SPEC |
| VWAP_DEVIATION_REVERSION | LONG | 6 | 1271 | 52 | 0.057435 | 4.989863 | 0.667978 | 4.249346 | 1.875999 | NEEDS_REPLAY_SPEC |
| EXHAUSTION_REVERSAL | LONG | 6 | 161 | 49 | 0.062112 | 7.689801 | 0.677019 | 3.946607 | 1.344341 | NEEDS_REPLAY_SPEC |
| VWAP_DEVIATION_REVERSION | SHORT | 3 | 1284 | 56 | 0.060748 | 3.439678 | 0.66433 | 2.845516 | 1.821342 | NEEDS_REPLAY_SPEC |
| VWAP_DEVIATION_REVERSION | LONG | 3 | 1271 | 52 | 0.057435 | 3.611831 | 0.66011 | 2.671613 | 1.875999 | NEEDS_REPLAY_SPEC |
| EXHAUSTION_REVERSAL | LONG | 3 | 161 | 49 | 0.062112 | 5.149519 | 0.652174 | 2.370672 | 1.344341 | NEEDS_REPLAY_SPEC |

## 5. Bucket-Only Aggregates

| surface_type | family | side | horizon | vwap_bp_bucket | rejection_strength_bucket | volume_bucket | events | independent_days | net_bp_after_0_00015 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| vwap_bucket_only | VWAP_DEVIATION_REVERSION | LONG | 60 | VWAP_GE_200BP | nan | nan | 23 | 5 | 41.680121 | REJECT_SURFACE |
| vwap_bucket_only | VWAP_DEVIATION_REVERSION | LONG | 24 | VWAP_GE_200BP | nan | nan | 23 | 5 | 32.32544 | REJECT_SURFACE |
| vwap_bucket_only | VWAP_DEVIATION_REVERSION | LONG | 12 | VWAP_GE_200BP | nan | nan | 23 | 5 | 25.023577 | REJECT_SURFACE |
| rejection_bucket_only | EXHAUSTION_REVERSAL | LONG | 3 | nan | LOW_LT_0_25 | nan | 1 | 1 | 23.007246 | REJECT_SURFACE |
| volume_bucket_only | EXHAUSTION_REVERSAL | LONG | 60 | nan | nan | Q90_95 | 32 | 27 | 21.485549 | REJECT_SURFACE |
| vwap_bucket_only | VWAP_DEVIATION_REVERSION | LONG | 6 | VWAP_GE_200BP | nan | nan | 23 | 5 | 16.338025 | REJECT_SURFACE |
| rejection_bucket_only | EXHAUSTION_REVERSAL | SHORT | 24 | nan | MID_0_25_0_45 | nan | 78 | 36 | 14.639499 | WATCH_SURFACE |
| rejection_bucket_only | EXHAUSTION_REVERSAL | LONG | 24 | nan | LOW_LT_0_25 | nan | 1 | 1 | 14.349335 | REJECT_SURFACE |
| volume_bucket_only | EXHAUSTION_REVERSAL | SHORT | 60 | nan | nan | Q90_95 | 37 | 24 | 14.023529 | REJECT_SURFACE |
| vwap_bucket_only | VWAP_DEVIATION_REVERSION | SHORT | 60 | VWAP_GE_200BP | nan | nan | 45 | 6 | 13.733992 | REJECT_SURFACE |
| volume_bucket_only | VWAP_DEVIATION_REVERSION | SHORT | 60 | nan | nan | Q90_95 | 166 | 45 | 13.439985 | NEEDS_REPLAY_SPEC |
| volume_bucket_only | EXHAUSTION_REVERSAL | SHORT | 24 | nan | nan | Q95_PLUS | 144 | 54 | 13.288867 | NEEDS_REPLAY_SPEC |
| rejection_bucket_only | EXHAUSTION_REVERSAL | SHORT | 12 | nan | MID_0_25_0_45 | nan | 78 | 36 | 12.9816 | WATCH_SURFACE |
| rejection_bucket_only | EXHAUSTION_REVERSAL | LONG | 6 | nan | LOW_LT_0_25 | nan | 1 | 1 | 12.121404 | REJECT_SURFACE |
| rejection_bucket_only | EXHAUSTION_REVERSAL | LONG | 60 | nan | MID_0_25_0_45 | nan | 71 | 37 | 11.169108 | WATCH_SURFACE |
| vwap_bucket_only | VWAP_DEVIATION_REVERSION | LONG | 3 | VWAP_GE_200BP | nan | nan | 23 | 5 | 10.665433 | REJECT_SURFACE |
| volume_bucket_only | EXHAUSTION_REVERSAL | SHORT | 12 | nan | nan | Q95_PLUS | 144 | 54 | 10.55092 | NEEDS_REPLAY_SPEC |
| volume_bucket_only | EXHAUSTION_REVERSAL | LONG | 24 | nan | nan | Q90_95 | 32 | 27 | 10.216763 | REJECT_SURFACE |
| vwap_bucket_only | VWAP_DEVIATION_REVERSION | LONG | 60 | VWAP_100_200BP | nan | nan | 423 | 30 | 10.214933 | NEEDS_REPLAY_SPEC |
| rejection_bucket_only | EXHAUSTION_REVERSAL | SHORT | 60 | nan | MID_0_25_0_45 | nan | 78 | 36 | 10.016448 | WATCH_SURFACE |

## 6. Candidate Surfaces

| candidate_id | family | side | horizon | surface_type | bucket | events | independent_days | net_bp_after_0_00015 |
|---|---|---|---|---|---|---|---|---|
| CAND_BTC_EXH_SHORT_24_V1 | EXHAUSTION_REVERSAL | SHORT | 24 | family_side_horizon |  | 181 | 54 | 11.710062 |
| CAND_BTC_EXH_SHORT_12_V1 | EXHAUSTION_REVERSAL | SHORT | 12 | family_side_horizon |  | 181 | 54 | 10.289549 |
| CAND_BTC_EXH_SHORT_60_V1 | EXHAUSTION_REVERSAL | SHORT | 60 | family_side_horizon |  | 181 | 54 | 8.265443 |
| CAND_BTC_EXH_LONG_60_V1 | EXHAUSTION_REVERSAL | LONG | 60 | family_side_horizon |  | 161 | 49 | 8.245225 |
| CAND_BTC_EXH_SHORT_6_V1 | EXHAUSTION_REVERSAL | SHORT | 6 | family_side_horizon |  | 181 | 54 | 7.261098 |
| CAND_BTC_EXH_LONG_12_V1 | EXHAUSTION_REVERSAL | LONG | 12 | family_side_horizon |  | 161 | 49 | 6.666997 |
| CAND_BTC_VWAP_DEV_SHORT_60_V1 | VWAP_DEVIATION_REVERSION | SHORT | 60 | family_side_horizon |  | 1282 | 56 | 6.624933 |
| CAND_BTC_VWAP_DEV_LONG_24_V1 | VWAP_DEVIATION_REVERSION | LONG | 24 | family_side_horizon |  | 1271 | 52 | 6.537441 |
| CAND_BTC_VWAP_DEV_LONG_60_V1 | VWAP_DEVIATION_REVERSION | LONG | 60 | family_side_horizon |  | 1271 | 52 | 6.526569 |
| CAND_BTC_VWAP_DEV_SHORT_24_V1 | VWAP_DEVIATION_REVERSION | SHORT | 24 | family_side_horizon |  | 1283 | 56 | 6.497477 |
| CAND_BTC_EXH_LONG_24_V1 | EXHAUSTION_REVERSAL | LONG | 24 | family_side_horizon |  | 161 | 49 | 6.10424 |
| CAND_BTC_VWAP_DEV_LONG_12_V1 | VWAP_DEVIATION_REVERSION | LONG | 12 | family_side_horizon |  | 1271 | 52 | 5.853668 |
| CAND_BTC_VWAP_DEV_SHORT_12_V1 | VWAP_DEVIATION_REVERSION | SHORT | 12 | family_side_horizon |  | 1285 | 56 | 5.822693 |
| CAND_BTC_EXH_SHORT_3_V1 | EXHAUSTION_REVERSAL | SHORT | 3 | family_side_horizon |  | 181 | 54 | 5.248432 |
| CAND_BTC_VWAP_DEV_SHORT_6_V1 | VWAP_DEVIATION_REVERSION | SHORT | 6 | family_side_horizon |  | 1285 | 56 | 4.276802 |
| CAND_BTC_VWAP_DEV_LONG_6_V1 | VWAP_DEVIATION_REVERSION | LONG | 6 | family_side_horizon |  | 1271 | 52 | 4.249346 |
| CAND_BTC_EXH_LONG_6_V1 | EXHAUSTION_REVERSAL | LONG | 6 | family_side_horizon |  | 161 | 49 | 3.946607 |
| CAND_BTC_VWAP_DEV_SHORT_3_V1 | VWAP_DEVIATION_REVERSION | SHORT | 3 | family_side_horizon |  | 1284 | 56 | 2.845516 |
| CAND_BTC_VWAP_DEV_LONG_3_V1 | VWAP_DEVIATION_REVERSION | LONG | 3 | family_side_horizon |  | 1271 | 52 | 2.671613 |
| CAND_BTC_EXH_LONG_3_V1 | EXHAUSTION_REVERSAL | LONG | 3 | family_side_horizon |  | 161 | 49 | 2.370672 |
| CAND_BTC_VWAP_DEV_LONG_60_100200_V1 | VWAP_DEVIATION_REVERSION | LONG | 60 | vwap_bucket_only | VWAP_100_200BP | 423 | 30 | 10.214933 |
| CAND_BTC_VWAP_DEV_SHORT_60_100200_V1 | VWAP_DEVIATION_REVERSION | SHORT | 60 | vwap_bucket_only | VWAP_100_200BP | 305 | 31 | 8.910669 |
| CAND_BTC_VWAP_DEV_LONG_24_100200_V1 | VWAP_DEVIATION_REVERSION | LONG | 24 | vwap_bucket_only | VWAP_100_200BP | 423 | 30 | 8.172974 |
| CAND_BTC_VWAP_DEV_SHORT_24_100200_V1 | VWAP_DEVIATION_REVERSION | SHORT | 24 | vwap_bucket_only | VWAP_100_200BP | 305 | 31 | 7.969676 |
| CAND_BTC_VWAP_DEV_SHORT_12_100200_V1 | VWAP_DEVIATION_REVERSION | SHORT | 12 | vwap_bucket_only | VWAP_100_200BP | 305 | 31 | 7.92756 |
| CAND_BTC_VWAP_DEV_LONG_24_4560_V1 | VWAP_DEVIATION_REVERSION | LONG | 24 | vwap_bucket_only | VWAP_45_60BP | 371 | 52 | 7.770397 |
| CAND_BTC_VWAP_DEV_LONG_12_4560_V1 | VWAP_DEVIATION_REVERSION | LONG | 12 | vwap_bucket_only | VWAP_45_60BP | 371 | 52 | 6.930782 |
| CAND_BTC_VWAP_DEV_SHORT_24_60100_V1 | VWAP_DEVIATION_REVERSION | SHORT | 24 | vwap_bucket_only | VWAP_60_100BP | 507 | 49 | 6.674585 |
| CAND_BTC_VWAP_DEV_LONG_12_100200_V1 | VWAP_DEVIATION_REVERSION | LONG | 12 | vwap_bucket_only | VWAP_100_200BP | 423 | 30 | 6.507371 |
| CAND_BTC_VWAP_DEV_SHORT_60_4560_V1 | VWAP_DEVIATION_REVERSION | SHORT | 60 | vwap_bucket_only | VWAP_45_60BP | 425 | 54 | 6.056187 |
| CAND_BTC_VWAP_DEV_SHORT_6_100200_V1 | VWAP_DEVIATION_REVERSION | SHORT | 6 | vwap_bucket_only | VWAP_100_200BP | 305 | 31 | 6.000482 |
| CAND_BTC_VWAP_DEV_SHORT_12_60100_V1 | VWAP_DEVIATION_REVERSION | SHORT | 12 | vwap_bucket_only | VWAP_60_100BP | 508 | 49 | 5.418368 |
| CAND_BTC_VWAP_DEV_SHORT_60_60100_V1 | VWAP_DEVIATION_REVERSION | SHORT | 60 | vwap_bucket_only | VWAP_60_100BP | 507 | 49 | 5.095662 |
| CAND_BTC_VWAP_DEV_SHORT_24_4560_V1 | VWAP_DEVIATION_REVERSION | SHORT | 24 | vwap_bucket_only | VWAP_45_60BP | 426 | 54 | 5.075249 |
| CAND_BTC_VWAP_DEV_LONG_6_100200_V1 | VWAP_DEVIATION_REVERSION | LONG | 6 | vwap_bucket_only | VWAP_100_200BP | 423 | 30 | 5.054542 |
| CAND_BTC_VWAP_DEV_SHORT_12_4560_V1 | VWAP_DEVIATION_REVERSION | SHORT | 12 | vwap_bucket_only | VWAP_45_60BP | 427 | 54 | 4.966764 |
| CAND_BTC_VWAP_DEV_LONG_60_4560_V1 | VWAP_DEVIATION_REVERSION | LONG | 60 | vwap_bucket_only | VWAP_45_60BP | 371 | 52 | 4.598498 |
| CAND_BTC_VWAP_DEV_LONG_6_4560_V1 | VWAP_DEVIATION_REVERSION | LONG | 6 | vwap_bucket_only | VWAP_45_60BP | 371 | 52 | 4.043485 |
| CAND_BTC_VWAP_DEV_SHORT_6_4560_V1 | VWAP_DEVIATION_REVERSION | SHORT | 6 | vwap_bucket_only | VWAP_45_60BP | 427 | 54 | 4.008096 |
| CAND_BTC_VWAP_DEV_SHORT_6_60100_V1 | VWAP_DEVIATION_REVERSION | SHORT | 6 | vwap_bucket_only | VWAP_60_100BP | 508 | 49 | 3.619617 |
| CAND_BTC_VWAP_DEV_SHORT_3_100200_V1 | VWAP_DEVIATION_REVERSION | SHORT | 3 | vwap_bucket_only | VWAP_100_200BP | 305 | 31 | 3.528666 |
| CAND_BTC_VWAP_DEV_LONG_12_60100_V1 | VWAP_DEVIATION_REVERSION | LONG | 12 | vwap_bucket_only | VWAP_60_100BP | 454 | 42 | 3.39324 |
| CAND_BTC_VWAP_DEV_LONG_3_100200_V1 | VWAP_DEVIATION_REVERSION | LONG | 3 | vwap_bucket_only | VWAP_100_200BP | 423 | 30 | 3.306174 |
| CAND_BTC_VWAP_DEV_LONG_6_60100_V1 | VWAP_DEVIATION_REVERSION | LONG | 6 | vwap_bucket_only | VWAP_60_100BP | 454 | 42 | 3.054934 |
| CAND_BTC_VWAP_DEV_LONG_60_60100_V1 | VWAP_DEVIATION_REVERSION | LONG | 60 | vwap_bucket_only | VWAP_60_100BP | 454 | 42 | 2.884729 |
| CAND_BTC_VWAP_DEV_LONG_24_60100_V1 | VWAP_DEVIATION_REVERSION | LONG | 24 | vwap_bucket_only | VWAP_60_100BP | 454 | 42 | 2.699599 |
| CAND_BTC_VWAP_DEV_SHORT_3_60100_V1 | VWAP_DEVIATION_REVERSION | SHORT | 3 | vwap_bucket_only | VWAP_60_100BP | 508 | 49 | 2.537075 |
| CAND_BTC_VWAP_DEV_SHORT_3_4560_V1 | VWAP_DEVIATION_REVERSION | SHORT | 3 | vwap_bucket_only | VWAP_45_60BP | 426 | 54 | 2.378103 |
| CAND_BTC_VWAP_DEV_LONG_3_4560_V1 | VWAP_DEVIATION_REVERSION | LONG | 3 | vwap_bucket_only | VWAP_45_60BP | 371 | 52 | 2.334727 |
| CAND_BTC_VWAP_DEV_LONG_3_60100_V1 | VWAP_DEVIATION_REVERSION | LONG | 3 | vwap_bucket_only | VWAP_60_100BP | 454 | 42 | 1.950704 |

## 7. Rejected Surfaces

| surface_type | family | side | horizon | events | independent_days | median_return_bp | positive_rate | net_bp_after_0_00015 | verdict_reason |
|---|---|---|---|---|---|---|---|---|---|
| vwap_bucket_only | VWAP_DEVIATION_REVERSION | LONG | 60 | 23 | 5 | 37.038731 | 0.913043 | 41.680121 | events_below_50;independent_days_below_15;day_concentration_above_0_15 |
| vwap_bucket_only | VWAP_DEVIATION_REVERSION | LONG | 24 | 23 | 5 | 30.342245 | 0.869565 | 32.32544 | events_below_50;independent_days_below_15;day_concentration_above_0_15 |
| vwap_bucket_only | VWAP_DEVIATION_REVERSION | LONG | 12 | 23 | 5 | 27.89841 | 0.826087 | 25.023577 | events_below_50;independent_days_below_15;day_concentration_above_0_15 |
| rejection_bucket_only | EXHAUSTION_REVERSAL | LONG | 3 | 1 | 1 | 24.507246 | 1.0 | 23.007246 | events_below_50;independent_days_below_15;day_concentration_above_0_15;session_concentration_above_0_75 |
| volume_bucket_only | EXHAUSTION_REVERSAL | LONG | 60 | 32 | 27 | 22.238928 | 0.875 | 21.485549 | events_below_50 |
| vwap_bucket_only | VWAP_DEVIATION_REVERSION | LONG | 6 | 23 | 5 | 15.526493 | 0.782609 | 16.338025 | events_below_50;independent_days_below_15;day_concentration_above_0_15 |
| rejection_bucket_only | EXHAUSTION_REVERSAL | LONG | 24 | 1 | 1 | 15.849335 | 1.0 | 14.349335 | events_below_50;independent_days_below_15;day_concentration_above_0_15;session_concentration_above_0_75 |
| volume_bucket_only | EXHAUSTION_REVERSAL | SHORT | 60 | 37 | 24 | 13.870016 | 0.675676 | 14.023529 | events_below_50 |
| vwap_bucket_only | VWAP_DEVIATION_REVERSION | SHORT | 60 | 45 | 6 | 13.870016 | 0.6 | 13.733992 | events_below_50;independent_days_below_15;day_concentration_above_0_15 |
| rejection_bucket_only | EXHAUSTION_REVERSAL | LONG | 6 | 1 | 1 | 13.621404 | 1.0 | 12.121404 | events_below_50;independent_days_below_15;day_concentration_above_0_15;session_concentration_above_0_75 |
| vwap_bucket_only | VWAP_DEVIATION_REVERSION | LONG | 3 | 23 | 5 | 11.092514 | 0.826087 | 10.665433 | events_below_50;independent_days_below_15;day_concentration_above_0_15 |
| volume_bucket_only | EXHAUSTION_REVERSAL | LONG | 24 | 32 | 27 | 19.759245 | 0.71875 | 10.216763 | events_below_50 |
| volume_bucket_only | EXHAUSTION_REVERSAL | SHORT | 12 | 37 | 24 | 12.052689 | 0.756757 | 9.272321 | events_below_50 |
| vwap_bucket_only | VWAP_DEVIATION_REVERSION | SHORT | 24 | 45 | 6 | 9.241657 | 0.533333 | 7.987571 | events_below_50;independent_days_below_15;day_concentration_above_0_15 |
| volume_bucket_only | EXHAUSTION_REVERSAL | LONG | 12 | 32 | 27 | 10.575333 | 0.65625 | 6.666188 | events_below_50 |
| vwap_bucket_only | VWAP_DEVIATION_REVERSION | SHORT | 3 | 45 | 6 | 9.046767 | 0.666667 | 6.122078 | events_below_50;independent_days_below_15;day_concentration_above_0_15 |
| volume_bucket_only | EXHAUSTION_REVERSAL | SHORT | 24 | 37 | 24 | 11.220306 | 0.648649 | 5.565525 | events_below_50 |
| rejection_bucket_only | EXHAUSTION_REVERSAL | SHORT | 6 | 3 | 3 | 8.553625 | 1.0 | 4.77654 | events_below_50;independent_days_below_15;day_concentration_above_0_15 |
| vwap_bucket_only | VWAP_DEVIATION_REVERSION | SHORT | 12 | 45 | 6 | 6.28506 | 0.577778 | 4.242573 | events_below_50;independent_days_below_15;day_concentration_above_0_15 |
| volume_bucket_only | EXHAUSTION_REVERSAL | SHORT | 6 | 37 | 24 | 4.656121 | 0.702703 | 4.12958 | events_below_50 |

## 8. Watch Surfaces

| surface_type | family | side | horizon | events | independent_days | median_return_bp | positive_rate | net_bp_after_0_00015 | verdict_reason |
|---|---|---|---|---|---|---|---|---|---|
| rejection_bucket_only | EXHAUSTION_REVERSAL | SHORT | 24 | 78 | 36 | 16.517527 | 0.74359 | 14.639499 | watch_surface_below_replay_spec_gate |
| rejection_bucket_only | EXHAUSTION_REVERSAL | SHORT | 12 | 78 | 36 | 12.38677 | 0.769231 | 12.9816 | watch_surface_below_replay_spec_gate |
| rejection_bucket_only | EXHAUSTION_REVERSAL | LONG | 60 | 71 | 37 | 16.834851 | 0.676056 | 11.169108 | watch_surface_below_replay_spec_gate |
| rejection_bucket_only | EXHAUSTION_REVERSAL | SHORT | 60 | 78 | 36 | 17.820191 | 0.628205 | 10.016448 | watch_surface_below_replay_spec_gate |
| rejection_bucket_only | EXHAUSTION_REVERSAL | SHORT | 6 | 78 | 36 | 11.394742 | 0.794872 | 9.651871 | watch_surface_below_replay_spec_gate |
| rejection_bucket_only | EXHAUSTION_REVERSAL | LONG | 24 | 71 | 37 | 9.160842 | 0.690141 | 8.805771 | watch_surface_below_replay_spec_gate |
| rejection_bucket_only | EXHAUSTION_REVERSAL | SHORT | 3 | 78 | 36 | 9.470345 | 0.807692 | 8.510424 | watch_surface_below_replay_spec_gate |
| rejection_bucket_only | EXHAUSTION_REVERSAL | LONG | 12 | 71 | 37 | 5.625135 | 0.746479 | 6.830897 | watch_surface_below_replay_spec_gate |
| rejection_bucket_only | EXHAUSTION_REVERSAL | LONG | 12 | 89 | 39 | 10.408987 | 0.662921 | 6.570338 | watch_surface_below_replay_spec_gate |
| rejection_bucket_only | EXHAUSTION_REVERSAL | LONG | 60 | 89 | 39 | 7.625343 | 0.640449 | 6.017908 | watch_surface_below_replay_spec_gate |
| rejection_bucket_only | EXHAUSTION_REVERSAL | LONG | 6 | 71 | 37 | 9.408101 | 0.732394 | 5.665371 | watch_surface_below_replay_spec_gate |
| rejection_bucket_only | EXHAUSTION_REVERSAL | LONG | 24 | 89 | 39 | 10.282064 | 0.651685 | 3.856444 | watch_surface_below_replay_spec_gate |
| rejection_bucket_only | EXHAUSTION_REVERSAL | LONG | 3 | 71 | 37 | 8.113914 | 0.732394 | 2.83215 | watch_surface_below_replay_spec_gate |
| rejection_bucket_only | EXHAUSTION_REVERSAL | LONG | 6 | 89 | 39 | 6.778426 | 0.629213 | 2.483607 | watch_surface_below_replay_spec_gate |
| rejection_bucket_only | EXHAUSTION_REVERSAL | LONG | 3 | 89 | 39 | 3.336237 | 0.58427 | 1.770655 | watch_surface_below_replay_spec_gate |

## 9. Replay Spec Candidates

| candidate_id | family | side | horizon | observable_entry_predicates | required_next_validation |
|---|---|---|---|---|---|
| CAND_BTC_EXH_SHORT_24_V1 | EXHAUSTION_REVERSAL | SHORT | 24 | Sprint 06 observable exhaustion predicate: prior impulse, high volume quantile, rejection/stall, delta dominance, VWAP stretch; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_EXH_SHORT_12_V1 | EXHAUSTION_REVERSAL | SHORT | 12 | Sprint 06 observable exhaustion predicate: prior impulse, high volume quantile, rejection/stall, delta dominance, VWAP stretch; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_EXH_SHORT_60_V1 | EXHAUSTION_REVERSAL | SHORT | 60 | Sprint 06 observable exhaustion predicate: prior impulse, high volume quantile, rejection/stall, delta dominance, VWAP stretch; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_EXH_LONG_60_V1 | EXHAUSTION_REVERSAL | LONG | 60 | Sprint 06 observable exhaustion predicate: prior impulse, high volume quantile, rejection/stall, delta dominance, VWAP stretch; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_EXH_SHORT_6_V1 | EXHAUSTION_REVERSAL | SHORT | 6 | Sprint 06 observable exhaustion predicate: prior impulse, high volume quantile, rejection/stall, delta dominance, VWAP stretch; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_EXH_LONG_12_V1 | EXHAUSTION_REVERSAL | LONG | 12 | Sprint 06 observable exhaustion predicate: prior impulse, high volume quantile, rejection/stall, delta dominance, VWAP stretch; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_VWAP_DEV_SHORT_60_V1 | VWAP_DEVIATION_REVERSION | SHORT | 60 | Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_VWAP_DEV_LONG_24_V1 | VWAP_DEVIATION_REVERSION | LONG | 24 | Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_VWAP_DEV_LONG_60_V1 | VWAP_DEVIATION_REVERSION | LONG | 60 | Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_VWAP_DEV_SHORT_24_V1 | VWAP_DEVIATION_REVERSION | SHORT | 24 | Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_EXH_LONG_24_V1 | EXHAUSTION_REVERSAL | LONG | 24 | Sprint 06 observable exhaustion predicate: prior impulse, high volume quantile, rejection/stall, delta dominance, VWAP stretch; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_VWAP_DEV_LONG_12_V1 | VWAP_DEVIATION_REVERSION | LONG | 12 | Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_VWAP_DEV_SHORT_12_V1 | VWAP_DEVIATION_REVERSION | SHORT | 12 | Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_EXH_SHORT_3_V1 | EXHAUSTION_REVERSAL | SHORT | 3 | Sprint 06 observable exhaustion predicate: prior impulse, high volume quantile, rejection/stall, delta dominance, VWAP stretch; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_VWAP_DEV_SHORT_6_V1 | VWAP_DEVIATION_REVERSION | SHORT | 6 | Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_VWAP_DEV_LONG_6_V1 | VWAP_DEVIATION_REVERSION | LONG | 6 | Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_EXH_LONG_6_V1 | EXHAUSTION_REVERSAL | LONG | 6 | Sprint 06 observable exhaustion predicate: prior impulse, high volume quantile, rejection/stall, delta dominance, VWAP stretch; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_VWAP_DEV_SHORT_3_V1 | VWAP_DEVIATION_REVERSION | SHORT | 3 | Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_VWAP_DEV_LONG_3_V1 | VWAP_DEVIATION_REVERSION | LONG | 3 | Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_EXH_LONG_3_V1 | EXHAUSTION_REVERSAL | LONG | 3 | Sprint 06 observable exhaustion predicate: prior impulse, high volume quantile, rejection/stall, delta dominance, VWAP stretch; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_VWAP_DEV_LONG_60_100200_V1 | VWAP_DEVIATION_REVERSION | LONG | 60 | Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_VWAP_DEV_SHORT_60_100200_V1 | VWAP_DEVIATION_REVERSION | SHORT | 60 | Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_VWAP_DEV_LONG_24_100200_V1 | VWAP_DEVIATION_REVERSION | LONG | 24 | Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_VWAP_DEV_SHORT_24_100200_V1 | VWAP_DEVIATION_REVERSION | SHORT | 24 | Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_VWAP_DEV_SHORT_12_100200_V1 | VWAP_DEVIATION_REVERSION | SHORT | 12 | Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_VWAP_DEV_LONG_24_4560_V1 | VWAP_DEVIATION_REVERSION | LONG | 24 | Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_VWAP_DEV_LONG_12_4560_V1 | VWAP_DEVIATION_REVERSION | LONG | 12 | Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_VWAP_DEV_SHORT_24_60100_V1 | VWAP_DEVIATION_REVERSION | SHORT | 24 | Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_VWAP_DEV_LONG_12_100200_V1 | VWAP_DEVIATION_REVERSION | LONG | 12 | Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_VWAP_DEV_SHORT_60_4560_V1 | VWAP_DEVIATION_REVERSION | SHORT | 60 | Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_VWAP_DEV_SHORT_6_100200_V1 | VWAP_DEVIATION_REVERSION | SHORT | 6 | Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_VWAP_DEV_SHORT_12_60100_V1 | VWAP_DEVIATION_REVERSION | SHORT | 12 | Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_VWAP_DEV_SHORT_60_60100_V1 | VWAP_DEVIATION_REVERSION | SHORT | 60 | Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_VWAP_DEV_SHORT_24_4560_V1 | VWAP_DEVIATION_REVERSION | SHORT | 24 | Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_VWAP_DEV_LONG_6_100200_V1 | VWAP_DEVIATION_REVERSION | LONG | 6 | Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_VWAP_DEV_SHORT_12_4560_V1 | VWAP_DEVIATION_REVERSION | SHORT | 12 | Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_VWAP_DEV_LONG_60_4560_V1 | VWAP_DEVIATION_REVERSION | LONG | 60 | Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_VWAP_DEV_LONG_6_4560_V1 | VWAP_DEVIATION_REVERSION | LONG | 6 | Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_VWAP_DEV_SHORT_6_4560_V1 | VWAP_DEVIATION_REVERSION | SHORT | 6 | Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_VWAP_DEV_SHORT_6_60100_V1 | VWAP_DEVIATION_REVERSION | SHORT | 6 | Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_VWAP_DEV_SHORT_3_100200_V1 | VWAP_DEVIATION_REVERSION | SHORT | 3 | Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_VWAP_DEV_LONG_12_60100_V1 | VWAP_DEVIATION_REVERSION | LONG | 12 | Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_VWAP_DEV_LONG_3_100200_V1 | VWAP_DEVIATION_REVERSION | LONG | 3 | Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_VWAP_DEV_LONG_6_60100_V1 | VWAP_DEVIATION_REVERSION | LONG | 6 | Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_VWAP_DEV_LONG_60_60100_V1 | VWAP_DEVIATION_REVERSION | LONG | 60 | Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_VWAP_DEV_LONG_24_60100_V1 | VWAP_DEVIATION_REVERSION | LONG | 24 | Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_VWAP_DEV_SHORT_3_60100_V1 | VWAP_DEVIATION_REVERSION | SHORT | 3 | Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_VWAP_DEV_SHORT_3_4560_V1 | VWAP_DEVIATION_REVERSION | SHORT | 3 | Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_VWAP_DEV_LONG_3_4560_V1 | VWAP_DEVIATION_REVERSION | LONG | 3 | Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |
| CAND_BTC_VWAP_DEV_LONG_3_60100_V1 | VWAP_DEVIATION_REVERSION | LONG | 3 | Sprint 06 observable VWAP deviation predicate: price stretched from DayVWAP bucket with stall/rejection, session/regime recorded; outcomes are excluded from entry predicates. | Write formal replay spec, deterministic mapper, Backtester replay, cost stress, same-bar review, source concentration, true holdout. |

## 10. Managerial Answer

- BTC-only research continues.
- Formal replay candidate surfaces exist: `True`.
- Do not change universe in Sprint 07.
- Do not wait passively if replay candidates exist; write formal replay specs next.
- Next action: formalize deterministic replay specs for the extracted candidates, without threshold tuning.
