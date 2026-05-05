# LOCAL_HIGHER_LOW_SWEEP_RECLAIM_LONG_V1 Full-Range Diagnostic

Date: 2026-05-05

Status: full-range diagnostic evidence only. This is not clean OOS because the discovery window `2026-03-30_to_2026-05-02` is inside the run range.

This run does not use the old `FAILED_BREAK_RECLAIM` detector, does not run the Backtester, does not tune parameters, does not change Analyzer canonical behavior, and makes no FIELD/live claims.

## Contract

- Direction: LONG only.
- Level family: `LOCAL_HIGHER_LOW_SWEEP` only.
- Prior major low over 30 H4 bars must remain unswept.
- H4 sweep, sweep candle excluded, H4 reclaim close within max 3 H4 candles.
- Entry at reclaim H4 close; stop at sweep extreme low minus 50 USD; max risk 1500 USD; no compression.
- Conservative 48h same-direction cluster rule; only first allowed candidate per cluster counts.

## Summary

| metric | value |
| --- | --- |
| run_window | 2026-03-12_to_2026-05-04 |
| full_range_candidates | 15 |
| allowed_candidates | 13 |
| unique_clusters | 8 |
| retained_cluster_first_rows | 7 |
| duplicate_rows_removed | 6 |
| incomplete_forward_window_rows | 0 |
| median_risk | 983.0000 |
| median_MFE_R | 2.2077 |
| median_MFE_usd | 1476.0000 |
| median_net_MFE_R | 1.6898 |
| hit_1.5R / 2R / 3R / 5R / 10R | 5/7, 4/7, 3/7, 1/7, 1/7 |
| candidates_after_2026-05-02 | 0 |

## Subperiod Split

| subperiod | candidates | allowed | clusters | retained | duplicates_removed | incomplete_forward | median_risk | median_MFE_R | median_MFE_usd | median_net_MFE_R | hit_1_5R | hit_2R | hit_3R | hit_5R | hit_10R |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-03-12_to_2026-03-29 | 2 | 1 | 2 | 1 | 0 | 0 | 1106.1000 | 1.3344 | 1476.0000 | 1.2069 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 |
| 2026-03-30_to_2026-05-02 | 13 | 12 | 6 | 6 | 6 | 0 | 869.5000 | 2.7090 | 2213.2000 | 2.3725 | 5/6 | 4/6 | 3/6 | 1/6 | 1/6 |
| 2026-05-03_to_2026-05-04 | 0 | 0 | 0 | 0 | 0 | 0 | n/a | n/a | n/a | n/a | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 |

## Candidate Rows

| row_number | cluster_id | keep_or_duplicate | entry_ts | level_price | prior_major_low_30h4 | sweep_extreme_price | entry_price | stop_price | final_risk_usd | MFE_R | fee_as_R | net_MFE_R | hit_1_5R | hit_2R | hit_3R | hit_5R | hit_10R | first_stop_touch_ts | time_to_1_5R | time_to_2R | time_to_3R | time_to_5R | time_to_10R | duplicate_count_in_cluster | incomplete_forward_window |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | FR01 | reject_not_valid | 2026-03-15 16:00:00+00:00 | 70256.0000 | 69150.0000 | 0.0000 | 71444.4000 | -50.0000 | 71494.4000 |  |  |  | False | False | False | False | False |  |  |  |  |  |  | 0 | False |
| 2 | FR02 | keep_cluster_first | 2026-03-25 00:00:00+00:00 | 70075.5000 | 67300.0000 | 69467.8000 | 70523.9000 | 69417.8000 | 1106.1000 | 1.3344 | 0.1275 | 1.2069 | False | False | False | False | False | 2026-03-26 09:34:00+00:00 |  |  |  |  |  | 0 | False |
| 3 | FR03 | keep_cluster_first | 2026-03-30 04:00:00+00:00 | 66233.6000 | 65501.0000 | 66111.0000 | 67138.9000 | 66061.0000 | 1077.9000 | 1.1486 | 0.1246 | 1.0240 | False | False | False | False | False | 2026-03-31 09:56:00+00:00 | 50.3300 |  |  |  |  | 1 | False |
| 4 | FR03 | duplicate_same_move | 2026-03-31 16:00:00+00:00 | 66200.1000 | 64918.2000 | 65938.0000 | 66700.0000 | 65888.0000 | 812.0000 | 3.1872 | 0.1643 | 3.0229 | True | True | True | False | False | 2026-04-02 13:17:00+00:00 | 0.6800 | 1.2300 | 14.7300 |  |  | 1 | False |
| 5 | FR04 | keep_cluster_first | 2026-04-05 12:00:00+00:00 | 66745.5000 | 65676.1000 | 66575.5000 | 66972.7000 | 66525.5000 | 447.2000 | 13.1614 | 0.2995 | 12.8619 | True | True | True | True | True |  | 3.5000 | 10.7300 | 10.9500 | 12.0000 | 58.9800 | 0 | False |
| 6 | FR05 | keep_cluster_first | 2026-04-07 20:00:00+00:00 | 68227.5000 | 65676.1000 | 68033.0000 | 68975.8000 | 67983.0000 | 992.8000 | 4.8324 | 0.1390 | 4.6934 | True | True | True | False | False |  | 2.1000 | 2.5300 | 3.3500 |  |  | 4 | False |
| 7 | FR05 | duplicate_same_move | 2026-04-09 08:00:00+00:00 | 70671.6000 | 66575.5000 | 70428.0000 | 70945.0000 | 70378.0000 | 567.0000 | 4.9884 | 0.2502 | 4.7381 | True | True | True | False | False |  | 7.5500 | 7.5700 | 13.1200 |  |  | 4 | False |
| 8 | FR05 | duplicate_same_move | 2026-04-10 12:00:00+00:00 | 71539.9000 | 66575.5000 | 71382.1000 | 72092.3000 | 71332.1000 | 760.2000 | 2.2114 | 0.1897 | 2.0217 | True | True | False | False | False | 2026-04-12 01:49:00+00:00 | 3.4000 | 30.6000 | 82.2700 |  |  | 4 | False |
| 9 | FR05 | duplicate_same_move | 2026-04-11 20:00:00+00:00 | 72566.4000 | 67711.0000 | 72451.9000 | 73635.8000 | 72401.9000 | 1233.9000 | 0.0105 | 0.1194 | -0.1088 | False | False | False | False | False | 2026-04-12 01:35:00+00:00 | 66.0000 |  |  |  |  | 4 | False |
| 10 | FR05 | duplicate_same_move | 2026-04-13 04:00:00+00:00 | 70566.5000 | 67711.0000 | 70458.2000 | 70944.8000 | 70408.2000 | 536.6000 | 9.4376 | 0.2644 | 9.1731 | True | True | True | True | False |  | 10.5700 | 10.7700 | 15.2700 | 18.2300 |  | 4 | False |
| 11 | FR06 | keep_cluster_first | 2026-04-15 12:00:00+00:00 | 73766.8000 | 70458.2000 | 73449.0000 | 74155.0000 | 73399.0000 | 756.0000 | 1.6807 | 0.1962 | 1.4845 | True | False | False | False | False | 2026-04-16 13:54:00+00:00 | 10.6500 | 44.9000 | 49.0300 | 50.7000 |  | 1 | False |
| 12 | FR06 | duplicate_same_move | 2026-04-16 16:00:00+00:00 | 74400.0000 | 70458.2000 | 74226.2000 | 74659.4000 | 74176.2000 | 483.2000 | 0.5012 | 0.3090 | 0.1922 | False | False | False | False | False | 2026-04-16 16:52:00+00:00 | 4.0000 | 16.8000 | 17.4700 | 21.8500 |  | 1 | False |
| 13 | FR07 | keep_cluster_first | 2026-04-19 12:00:00+00:00 | 75395.9000 | 73256.8000 | 75314.0000 | 75555.8000 | 75264.0000 | 291.8000 | 2.2077 | 0.5179 | 1.6898 | True | True | False | False | False | 2026-04-19 16:55:00+00:00 | 1.3200 | 1.3500 | 30.8800 | 62.2800 | 72.2800 | 0 | False |
| 14 | FR08 | keep_cluster_first | 2026-04-22 00:00:00+00:00 | 75433.1000 | 73256.8000 | 75355.2000 | 76288.2000 | 75305.2000 | 983.0000 | 3.2104 | 0.1552 | 3.0552 | True | True | True | False | False |  | 5.2700 | 5.4000 | 15.5000 |  |  | 1 | False |
| 15 | FR08 | reject_not_valid | 2026-04-23 16:00:00+00:00 | 77410.7000 | 73669.0000 | 76504.6000 | 78329.2000 | 76454.6000 | 1874.6000 |  |  |  | False | False | False | False | False |  |  |  |  |  |  | 1 | False |

## Post-Discovery Check

- No candidates after 2026-05-02.
- The available post-discovery complete feed currently covers only `2026-05-03_to_2026-05-04`, so absence of candidates there is not a rejection of the surface.

## Feed Note

- `feed/2026-03-15.csv` contains 1439 rows and one `IsSynthetic=1` zero-OHLC minute at `2026-03-15 09:50:00`.
- Candidate row 1 is a rejected/no-trade artifact affected by that zero sweep extreme (`sweep_extreme_price=0.0`) and is not retained in cluster-first evidence.

## Verdict

- This is full-range diagnostic evidence, not clean OOS.
- The surface is present in the full range, but persistence outside discovery remains weakly sampled.
- No ruleset promotion yet. The next useful step is more complete post-discovery feed days or a larger earlier historical window with enough candidates and clean forward coverage.

## Files

- CSV: `research/results/local_higher_low_sweep_reclaim_long_v1_full_range_2026-03-12_to_2026-05-04.csv`
- Report: `research/findings/LOCAL_HIGHER_LOW_SWEEP_RECLAIM_LONG_V1_FULL_RANGE_2026-03-12_to_2026-05-04.md`
