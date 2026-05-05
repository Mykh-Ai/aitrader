# LOCAL HIGHER LOW SWEEP RECLAIM Cluster Dedup Diagnostic

Date: 2026-05-05

Status: diagnostic only. This does not run the Backtester, does not run the old `FAILED_BREAK_RECLAIM` detector, does not change Analyzer canonical behavior, and makes no FIELD/live claims.

Scope: `direction=LONG`, `level_family=LOCAL_HIGHER_LOW_SWEEP`.

Cluster rule: count only the first `diagnostic_trade_allowed` candidate per same-direction impulse cluster. Existing manual-review clusters are used as the frozen cluster IDs; they group same-direction candidates within 24h and same-direction continuation candidates within 48h when the later entry is part of the same impulse. Later valid rows are marked `duplicate_same_move`; invalid rows are marked `reject_not_valid`.

## Summary

- original_rows: 13
- allowed_rows: 12
- unique_clusters: 8
- cluster_first_retained_rows: 8
- duplicate_rows_removed: 4
- median_risk: 784.0
- median_MFE_R: 3.1988
- median_MFE_usd: 2871.9
- median_net_MFE_R: 3.039
- hit_1_5R: 7
- hit_2R: 6
- hit_3R: 5
- hit_5R: 2
- hit_10R: 1
- Detail CSV: `research/results/local_higher_low_sweep_reclaim_cluster_dedup_2026-05-05.csv`

## Retained Cluster-First Rows

| row_number | cluster_id | entry_ts | level_price | prior_major_low_30h4 | sweep_depth_usd | reclaim_close_distance_usd | candle_body_direction | reclaim_body_pct_of_range | final_risk_usd | MFE_R | MFE_usd | net_MFE_R | net_MFE_usd | hit_1_5R_before_stop | hit_2R_before_stop | hit_3R_before_stop | hit_5R_before_stop | hit_10R_before_stop | time_to_1_5R | time_to_3R | formation_read | entry_timing | keep_or_duplicate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1.0 | L01 | 2026-03-30 04:00:00+0000 | 66233.6 | 65501.0 | 122.6 | 905.3 | bullish | 0.6697 | 1077.9 | 1.1486 | 1238.1 | 1.024 | 1103.8222 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 50.33 |  | late/slow bounce with weak expansion profile | mixed/weak timing | keep_cluster_first |
| 3.0 | L02 | 2026-03-31 16:00:00+0000 | 66200.1 | 64918.2 | 262.1 | 499.9 | bullish | 0.0342 | 812.0 | 3.1872 | 2588.0 | 3.0229 | 2454.6 | 1.0 | 1.0 | 1.0 | 0.0 | 0.0 | 0.68 | 14.73 | countertrend bounce / possible early reversal after local sweep | near start of directional leg | keep_cluster_first |
| 7.0 | L03 | 2026-04-05 12:00:00+0000 | 66745.5 | 65676.1 | 170.0 | 227.2 | bullish | 0.5284 | 447.2 | 13.1614 | 5885.8 | 12.8619 | 5751.8546 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 3.5 | 10.95 | clean pullback-continuation after shallow local higher-low sweep | near start of directional leg | keep_cluster_first |
| 10.0 | L04 | 2026-04-07 20:00:00+0000 | 68227.5 | 65676.1 | 194.5 | 748.3 | bullish | 0.8219 | 992.8 | 4.8324 | 4797.6 | 4.6934 | 4659.6484 | 1.0 | 1.0 | 1.0 | 0.0 | 0.0 | 2.1 | 3.35 | first signal in clustered long impulse after strong bullish reclaim | near start of directional leg | keep_cluster_first |
| 17.0 | L05 | 2026-04-13 04:00:00+0000 | 70566.5 | 67711.0 | 108.3 | 378.3 | bullish | 0.3483 | 536.6 | 9.4376 | 5064.2 | 9.1731 | 4922.3104 | 1.0 | 1.0 | 1.0 | 1.0 | 0.0 | 10.57 | 15.27 | local reversal / pullback-continuation after heavy selloff into higher-low shelf | near start of directional leg | keep_cluster_first |
| 20.0 | L06 | 2026-04-15 12:00:00+0000 | 73766.8 | 70458.2 | 317.8 | 388.2 | bullish | 0.7659 | 756.0 | 1.6807 | 1270.6 | 1.4845 | 1122.29 | 1.0 | 0.0 | 0.0 | 0.0 | 0.0 | 10.65 | 49.03 | weak first cluster signal; later cluster member stopped quickly | mixed/weak timing | keep_cluster_first |
| 23.0 | L07 | 2026-04-19 12:00:00+0000 | 75395.9 | 73256.8 | 81.9 | 159.9 | bullish | 0.4826 | 291.8 | 2.2077 | 644.2 | 1.6898 | 493.0884 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 | 1.32 | 30.88 | boundary case, fast 2R but stop touched same afternoon | mixed/weak timing | keep_cluster_first |
| 25.0 | L08 | 2026-04-22 00:00:00+0000 | 75433.1 | 73256.8 | 77.9 | 855.1 | bullish | 0.8937 | 983.0 | 3.2104 | 3155.8 | 3.0552 | 3003.2236 | 1.0 | 1.0 | 1.0 | 0.0 | 0.0 | 5.27 | 15.5 | first signal in new V-style impulse after local higher-low sweep | near start of directional leg | keep_cluster_first |

## Duplicate Rows Removed

| row_number | cluster_id | entry_ts | level_price | final_risk_usd | MFE_R | net_MFE_R | formation_read | entry_timing | keep_or_duplicate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 11.0 | L04 | 2026-04-09 08:00:00+0000 | 70671.6 | 567.0 | 4.9884 | 4.7381 | duplicate continuation or weak repeat inside existing impulse | late duplicate inside existing cluster | duplicate_same_move |
| 13.0 | L04 | 2026-04-10 12:00:00+0000 | 71539.9 | 760.2 | 2.2114 | 2.0217 | duplicate continuation or weak repeat inside existing impulse | late duplicate inside existing cluster | duplicate_same_move |
| 15.0 | L04 | 2026-04-11 20:00:00+0000 | 72566.4 | 1233.9 | 0.0105 | -0.1088 | duplicate continuation or weak repeat inside existing impulse | late duplicate inside existing cluster | duplicate_same_move |
| 22.0 | L06 | 2026-04-16 16:00:00+0000 | 74400.0 | 483.2 | 0.5012 | 0.1922 | duplicate continuation or weak repeat inside existing impulse | late duplicate inside existing cluster | duplicate_same_move |

## Best Exemplars

| row_number | cluster_id | entry_ts | final_risk_usd | MFE_R | MFE_usd | net_MFE_R | net_MFE_usd | hit_3R_before_stop | hit_5R_before_stop | hit_10R_before_stop | formation_read |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 7.0 | L03 | 2026-04-05 12:00:00+0000 | 447.2 | 13.1614 | 5885.8 | 12.8619 | 5751.8546 | 1.0 | 1.0 | 1.0 | clean pullback-continuation after shallow local higher-low sweep |
| 17.0 | L05 | 2026-04-13 04:00:00+0000 | 536.6 | 9.4376 | 5064.2 | 9.1731 | 4922.3104 | 1.0 | 1.0 | 0.0 | local reversal / pullback-continuation after heavy selloff into higher-low shelf |
| 10.0 | L04 | 2026-04-07 20:00:00+0000 | 992.8 | 4.8324 | 4797.6 | 4.6934 | 4659.6484 | 1.0 | 0.0 | 0.0 | first signal in clustered long impulse after strong bullish reclaim |
| 25.0 | L08 | 2026-04-22 00:00:00+0000 | 983.0 | 3.2104 | 3155.8 | 3.0552 | 3003.2236 | 1.0 | 0.0 | 0.0 | first signal in new V-style impulse after local higher-low sweep |
| 3.0 | L02 | 2026-03-31 16:00:00+0000 | 812.0 | 3.1872 | 2588.0 | 3.0229 | 2454.6 | 1.0 | 0.0 | 0.0 | countertrend bounce / possible early reversal after local sweep |
| 23.0 | L07 | 2026-04-19 12:00:00+0000 | 291.8 | 2.2077 | 644.2 | 1.6898 | 493.0884 | 0.0 | 0.0 | 0.0 | boundary case, fast 2R but stop touched same afternoon |

## Rejected Or Weak Examples

| row_number | cluster_id | entry_ts | final_risk_usd | MFE_R | net_MFE_R | diagnostic_trade_allowed | no_trade_reason | formation_read | keep_or_duplicate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1.0 | L01 | 2026-03-30 04:00:00+0000 | 1077.9 | 1.1486 | 1.024 | 1.0 |  | late/slow bounce with weak expansion profile | keep_cluster_first |
| 20.0 | L06 | 2026-04-15 12:00:00+0000 | 756.0 | 1.6807 | 1.4845 | 1.0 |  | weak first cluster signal; later cluster member stopped quickly | keep_cluster_first |
| 26.0 | L08 | 2026-04-23 16:00:00+0000 | 1874.6 | 0.0734 | -0.0102 | 0.0 | sweep_extreme_risk_too_large | duplicate continuation or weak repeat inside existing impulse | reject_not_valid |

## Verdict

After cluster de-duplication, the setup still looks interesting as a diagnostic surface: the retained cluster-first set keeps multiple strong expansion examples, including one 10R case and one 5R case. The row-level result was inflated by duplicates, but the surface does not disappear.

Do not promote to ruleset yet. The next step should freeze this cluster-first contract and test it on a later/out-of-sample feed window before any formal ruleset draft.