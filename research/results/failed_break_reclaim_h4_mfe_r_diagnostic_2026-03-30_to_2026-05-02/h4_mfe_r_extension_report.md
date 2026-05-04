# H4 MFE_R Extension Diagnostic

Research-only diagnostic report from existing large structural matrix and bridge artifacts. No strategy logic, Analyzer behavior, or Backtester behavior was modified.

## Scope And Method

- Source matrix: `research/results/failed_break_reclaim_extended_structural_matrix_2026-03-30_to_2026-05-02`
- Replay raw feed: `research/results/failed_break_reclaim_extended_structural_matrix_2026-03-30_to_2026-05-02/bridge_FAILED_BREAK_RECLAIM_EXTENDED_V1_full_coverage_only/raw.csv`
- Setup source: `FAILED_BREAK_RECLAIM_EXTENDED_V1`
- SourceTF: `H4` only
- Confirmation: `confirmation_bars=60` from EXTENDED_V1 artifacts
- Current replay row used for exit context: `BARS_AFTER_ACTIVATION:4320` with `FIXED_R_MULTIPLE:1.5`
- Forward MFE/MAE scan horizons: `1440`, `2880`, `4320`, `5760` bars.
- Forward scan starts at `entry_activation_ts` inclusive because current replay can resolve on the entry bar under same-bar semantics.
- `TimeToBestMFE_Bars`, `BestMFE_Ts`, and `MAE_R_before_best_MFE` use the best favorable excursion over the 5760-bar diagnostic window. Ties use first occurrence.
- `Was_SL_hit_before_MFE_xR` is true only when the first 1R adverse touch is strictly before first xR favorable touch; same-bar threshold/SL touches are separately counted as collisions.

Important: MFE_R is not an executable TP result unless SL-before-target and same-bar ordering are checked. This report does not claim edge or execution readiness.

## Summary By Stop Model

| StopModel                 |   Trades |   MFE_R_ge_1p5 |   MFE_R_ge_1p5_Pct |   MFE_R_ge_2 |   MFE_R_ge_2_Pct |   MFE_R_ge_3 |   MFE_R_ge_3_Pct |   MFE_R_ge_5 |   MFE_R_ge_5_Pct |   MFE_R_ge_10 |   MFE_R_ge_10_Pct |   MedianMFE_R |   MeanMFE_R |   P75MFE_R |   P90MFE_R |   MedianTimeToBestMFE_Bars |   MeanMAE_R_before_best_MFE |
|:--------------------------|---------:|---------------:|-------------------:|-------------:|-----------------:|-------------:|-----------------:|-------------:|-----------------:|--------------:|------------------:|--------------:|------------:|-----------:|-----------:|---------------------------:|----------------------------:|
| REFERENCE_LEVEL_HARD_STOP |       37 |             37 |           1        |           37 |         1        |           37 |         1        |           36 |         0.972973 |            31 |          0.837838 |       42.6442 |    979.512  |   128.515  |   426.618  |                       2659 |                    56.594   |
| SWEEP_EXTREME_HARD_STOP   |       37 |             34 |           0.918919 |           34 |         0.918919 |           34 |         0.918919 |           29 |         0.783784 |            23 |          0.621622 |       12.4112 |     19.3721 |    23.7537 |    36.7543 |                       2659 |                     7.59917 |

## Same-Bar Clean Subsets

| StopModel                 | Subset                             |   Trades |   MFE_R_ge_1p5 |   MFE_R_ge_1p5_Pct |   MFE_R_ge_2 |   MFE_R_ge_2_Pct |   MFE_R_ge_3 |   MFE_R_ge_3_Pct |   MFE_R_ge_5 |   MFE_R_ge_5_Pct |   MFE_R_ge_10 |   MFE_R_ge_10_Pct |   MedianMFE_R |   MeanMFE_R |   P75MFE_R |   P90MFE_R |   MedianTimeToBestMFE_Bars |   MeanMAE_R_before_best_MFE |
|:--------------------------|:-----------------------------------|---------:|---------------:|-------------------:|-------------:|-----------------:|-------------:|-----------------:|-------------:|-----------------:|--------------:|------------------:|--------------:|------------:|-----------:|-----------:|---------------------------:|----------------------------:|
| REFERENCE_LEVEL_HARD_STOP | all_h4_trades                      |       37 |             37 |           1        |           37 |         1        |           37 |         1        |           36 |         0.972973 |            31 |          0.837838 |       42.6442 |    979.512  |   128.515  |   426.618  |                     2659   |                    56.594   |
| REFERENCE_LEVEL_HARD_STOP | exclude_same_bar_exits             |       24 |             24 |           1        |           24 |         1        |           24 |         1        |           23 |         0.958333 |            19 |          0.791667 |       39.5136 |   1434.64   |    82.0336 |   686.61   |                     2293.5 |                    71.7217  |
| REFERENCE_LEVEL_HARD_STOP | exclude_same_bar_collisions        |       28 |             28 |           1        |           28 |         1        |           28 |         1        |           28 |         1        |            24 |          0.857143 |       39.5136 |     83.8161 |   100.623  |   182.837  |                     3140.5 |                    26.789   |
| REFERENCE_LEVEL_HARD_STOP | exclude_same_bar_exit_or_collision |       15 |             15 |           1        |           15 |         1        |           15 |         1        |           15 |         1        |            12 |          0.8      |       26.4534 |     35.7482 |    43.1078 |    67.0093 |                     2997   |                    25.1623  |
| SWEEP_EXTREME_HARD_STOP   | all_h4_trades                      |       37 |             34 |           0.918919 |           34 |         0.918919 |           34 |         0.918919 |           29 |         0.783784 |            23 |          0.621622 |       12.4112 |     19.3721 |    23.7537 |    36.7543 |                     2659   |                     7.59917 |
| SWEEP_EXTREME_HARD_STOP   | exclude_same_bar_exits             |       35 |             32 |           0.914286 |           32 |         0.914286 |           32 |         0.914286 |           27 |         0.771429 |            21 |          0.6      |       11.5784 |     18.6575 |    22.5289 |    37.2367 |                     2659   |                     7.54741 |
| SWEEP_EXTREME_HARD_STOP   | exclude_same_bar_collisions        |       37 |             34 |           0.918919 |           34 |         0.918919 |           34 |         0.918919 |           29 |         0.783784 |            23 |          0.621622 |       12.4112 |     19.3721 |    23.7537 |    36.7543 |                     2659   |                     7.59917 |
| SWEEP_EXTREME_HARD_STOP   | exclude_same_bar_exit_or_collision |       35 |             32 |           0.914286 |           32 |         0.914286 |           32 |         0.914286 |           27 |         0.771429 |            21 |          0.6      |       11.5784 |     18.6575 |    22.5289 |    37.2367 |                     2659   |                     7.54741 |

## Direction Split

| StopModel                 | Direction   |   Trades |   MFE_R_ge_1p5 |   MFE_R_ge_1p5_Pct |   MFE_R_ge_2 |   MFE_R_ge_2_Pct |   MFE_R_ge_3 |   MFE_R_ge_3_Pct |   MFE_R_ge_5 |   MFE_R_ge_5_Pct |   MFE_R_ge_10 |   MFE_R_ge_10_Pct |   MedianMFE_R |   MeanMFE_R |   P75MFE_R |   P90MFE_R |   MedianTimeToBestMFE_Bars |   MeanMAE_R_before_best_MFE |
|:--------------------------|:------------|---------:|---------------:|-------------------:|-------------:|-----------------:|-------------:|-----------------:|-------------:|-----------------:|--------------:|------------------:|--------------:|------------:|-----------:|-----------:|---------------------------:|----------------------------:|
| REFERENCE_LEVEL_HARD_STOP | LONG        |       16 |             16 |           1        |           16 |         1        |           16 |         1        |           16 |         1        |            16 |          1        |      90.5992  |  2189.19    |   408.984  |  1375.92   |                       4301 |                    95.9296  |
| REFERENCE_LEVEL_HARD_STOP | SHORT       |       21 |             21 |           1        |           21 |         1        |           21 |         1        |           20 |         0.952381 |            15 |          0.714286 |      27.4138  |    57.8512  |    72.8359 |   128.515  |                       1667 |                    26.6241  |
| SWEEP_EXTREME_HARD_STOP   | LONG        |       16 |             16 |           1        |           16 |         1        |           16 |         1        |           15 |         0.9375   |            15 |          0.9375   |      24.8812  |    33.0699  |    36.3925 |    63.1217 |                       4301 |                    10.9802  |
| SWEEP_EXTREME_HARD_STOP   | SHORT       |       21 |             18 |           0.857143 |           18 |         0.857143 |           18 |         0.857143 |           14 |         0.666667 |             8 |          0.380952 |       8.27336 |     8.93577 |    11.5784 |    17.3965 |                       1667 |                     5.02316 |

## SL Before MFE Threshold Audit

| StopModel                 |   Trades |   SLBeforeMFE_2R_Count |   SameBarSLAndMFE_2R_Count |   MFE_2R_Reached_Count |   SLBeforeMFE_3R_Count |   SameBarSLAndMFE_3R_Count |   MFE_3R_Reached_Count |   SLBeforeMFE_5R_Count |   SameBarSLAndMFE_5R_Count |   MFE_5R_Reached_Count |
|:--------------------------|---------:|-----------------------:|---------------------------:|-----------------------:|-----------------------:|---------------------------:|-----------------------:|-----------------------:|---------------------------:|-----------------------:|
| REFERENCE_LEVEL_HARD_STOP |       37 |                     15 |                          8 |                     37 |                     18 |                          7 |                     37 |                     24 |                          5 |                     36 |
| SWEEP_EXTREME_HARD_STOP   |       37 |                     17 |                          0 |                     34 |                     20 |                          0 |                     34 |                     25 |                          0 |                     29 |

## Highest MFE_R Examples

| SetupId                  | Direction   | EntryTs                   | StopModel                 |   RiskDistance | ExitReason_1p5R   |   MFE_R_1440 |   MFE_R_2880 |   MFE_R_4320 |   MFE_R_5760 |   TimeToBestMFE_Bars | BestMFE_Ts                |   MAE_R_before_best_MFE |
|:-------------------------|:------------|:--------------------------|:--------------------------|---------------:|:------------------|-------------:|-------------:|-------------:|-------------:|---------------------:|:--------------------------|------------------------:|
| a7041ce1f10fd1f3af817637 | LONG        | 2026-04-05T06:29:00+00:00 | REFERENCE_LEVEL_HARD_STOP |            0.2 | STOP              |   14186.5    |   17934      |   29988.5    |   30564      |                 4730 | 2026-04-08T13:19:00+00:00 |               478.5     |
| 0d25765ec7778c11c037cd24 | LONG        | 2026-04-19T18:03:00+00:00 | REFERENCE_LEVEL_HARD_STOP |            2.4 | STOP              |     515.083  |     905.125  |    1923.88   |    1923.88   |                 4203 | 2026-04-22T16:06:00+00:00 |               482.375   |
| 7d7d5ff4a49433f6625e6d11 | LONG        | 2026-04-07T10:55:00+00:00 | REFERENCE_LEVEL_HARD_STOP |            6.3 | STOP              |     715.81   |     734.079  |     776.857  |     827.968  |                 4896 | 2026-04-10T20:31:00+00:00 |                82.9841  |
| a4b5b44714ca7e13a0dfd875 | LONG        | 2026-04-15T08:08:00+00:00 | REFERENCE_LEVEL_HARD_STOP |            9.1 | TARGET            |     181.286  |     189.462  |     497.154  |     497.154  |                 3376 | 2026-04-17T16:24:00+00:00 |                57.044   |
| 9ec69c6605ca85675e0e6e06 | LONG        | 2026-04-12T22:30:00+00:00 | REFERENCE_LEVEL_HARD_STOP |           14.3 | TARGET            |     270.993  |     379.594  |     379.594  |     379.594  |                 2403 | 2026-04-14T14:33:00+00:00 |                 8.57343 |
| 747855283015820c70664969 | SHORT       | 2026-04-21T08:54:00+00:00 | REFERENCE_LEVEL_HARD_STOP |            4.9 | TARGET            |     356.776  |     356.776  |     356.776  |     356.776  |                  651 | 2026-04-21T19:45:00+00:00 |                64.9796  |
| 84b4a773e173b42be1f3ea1f | LONG        | 2026-04-10T08:10:00+00:00 | REFERENCE_LEVEL_HARD_STOP |           13.5 | TARGET            |     140.489  |     164.444  |     164.444  |     247.896  |                 5700 | 2026-04-14T07:10:00+00:00 |                81.1259  |
| c3eed66a7fa6c67beef867a1 | LONG        | 2026-03-31T10:07:00+00:00 | REFERENCE_LEVEL_HARD_STOP |           19.8 | TARGET            |     154.955  |     154.955  |     154.955  |     154.955  |                 1264 | 2026-04-01T07:11:00+00:00 |                 1.57576 |
| 0a844825ee63e3ed0feb88be | SHORT       | 2026-04-09T22:20:00+00:00 | REFERENCE_LEVEL_HARD_STOP |           18.4 | TARGET            |      79.2391 |      79.2391 |     123.565  |     129.451  |                 4331 | 2026-04-12T22:31:00+00:00 |                50.7228  |
| 405013a764fde5de604ad58a | SHORT       | 2026-04-11T18:44:00+00:00 | REFERENCE_LEVEL_HARD_STOP |           23.1 | STOP              |     123.827  |     128.515  |     128.515  |     128.515  |                 1667 | 2026-04-12T22:31:00+00:00 |                15       |
| 3006cd3533f5bb2880b10b4d | LONG        | 2026-04-11T13:14:00+00:00 | REFERENCE_LEVEL_HARD_STOP |           29.2 | STOP              |      40.3356 |      40.3356 |      78.9178 |     116.897  |                 4399 | 2026-04-14T14:33:00+00:00 |                73.1986  |
| 2b972c2d5c1154445cef48ed | SHORT       | 2026-04-15T20:09:00+00:00 | REFERENCE_LEVEL_HARD_STOP |           13.4 | TARGET            |     109.627  |     109.627  |     109.627  |     109.627  |                 1067 | 2026-04-16T13:56:00+00:00 |                52.2239  |
| 3711c617488c92d9828c70cf | SHORT       | 2026-03-31T01:38:00+00:00 | REFERENCE_LEVEL_HARD_STOP |           25.7 | STOP              |      85.0078 |      85.0078 |      95.1984 |      95.1984 |                 3598 | 2026-04-02T13:36:00+00:00 |                45.3424  |
| 9ec69c6605ca85675e0e6e06 | LONG        | 2026-04-12T22:30:00+00:00 | SWEEP_EXTREME_HARD_STOP   |           58.8 | STOP              |      65.9048 |      92.3163 |      92.3163 |      92.3163 |                 2403 | 2026-04-14T14:33:00+00:00 |                 2.08503 |
| 513de79500f119ebdc89e724 | SHORT       | 2026-04-01T05:28:00+00:00 | REFERENCE_LEVEL_HARD_STOP |           39.6 | TARGET            |      60.3182 |      72.8359 |      72.8359 |      72.8359 |                 1928 | 2026-04-02T13:36:00+00:00 |                18.3737  |

## Current 1.5R Stops With Later MFE_R >= 2

| SetupId                  | Direction   | EntryTs                   | StopModel                 |   RiskDistance | ExitReason_1p5R   | ExitTs_1p5R               |   MFE_R_5760 |   TimeToBestMFE_Bars | Was_SL_hit_before_MFE_2R   | SLBeforeMFE_2R_Status           |
|:-------------------------|:------------|:--------------------------|:--------------------------|---------------:|:------------------|:--------------------------|-------------:|---------------------:|:---------------------------|:--------------------------------|
| a7041ce1f10fd1f3af817637 | LONG        | 2026-04-05T06:29:00+00:00 | REFERENCE_LEVEL_HARD_STOP |            0.2 | STOP              | 2026-04-05T06:30:00+00:00 |   30564      |                 4730 | False                      | SAME_BAR_SL_AND_THRESHOLD_TOUCH |
| 0d25765ec7778c11c037cd24 | LONG        | 2026-04-19T18:03:00+00:00 | REFERENCE_LEVEL_HARD_STOP |            2.4 | STOP              | 2026-04-19T18:04:00+00:00 |    1923.88   |                 4203 | False                      | SAME_BAR_SL_AND_THRESHOLD_TOUCH |
| 7d7d5ff4a49433f6625e6d11 | LONG        | 2026-04-07T10:55:00+00:00 | REFERENCE_LEVEL_HARD_STOP |            6.3 | STOP              | 2026-04-07T10:57:00+00:00 |     827.968  |                 4896 | False                      | SAME_BAR_SL_AND_THRESHOLD_TOUCH |
| 405013a764fde5de604ad58a | SHORT       | 2026-04-11T18:44:00+00:00 | REFERENCE_LEVEL_HARD_STOP |           23.1 | STOP              | 2026-04-11T18:44:00+00:00 |     128.515  |                 1667 | True                       | SL_TOUCH_BEFORE_THRESHOLD       |
| 3006cd3533f5bb2880b10b4d | LONG        | 2026-04-11T13:14:00+00:00 | REFERENCE_LEVEL_HARD_STOP |           29.2 | STOP              | 2026-04-11T13:15:00+00:00 |     116.897  |                 4399 | True                       | SL_TOUCH_BEFORE_THRESHOLD       |
| 3711c617488c92d9828c70cf | SHORT       | 2026-03-31T01:38:00+00:00 | REFERENCE_LEVEL_HARD_STOP |           25.7 | STOP              | 2026-03-31T01:38:00+00:00 |      95.1984 |                 3598 | True                       | SL_TOUCH_BEFORE_THRESHOLD       |
| 9ec69c6605ca85675e0e6e06 | LONG        | 2026-04-12T22:30:00+00:00 | SWEEP_EXTREME_HARD_STOP   |           58.8 | STOP              | 2026-04-12T22:31:00+00:00 |      92.3163 |                 2403 | True                       | SL_TOUCH_BEFORE_THRESHOLD       |
| f015269d47c4d8b05862fd28 | LONG        | 2026-04-09T00:51:00+00:00 | REFERENCE_LEVEL_HARD_STOP |           47.5 | STOP              | 2026-04-09T00:51:00+00:00 |      64.3011 |                 3975 | True                       | SL_TOUCH_BEFORE_THRESHOLD       |
| 7d7d5ff4a49433f6625e6d11 | LONG        | 2026-04-07T10:55:00+00:00 | SWEEP_EXTREME_HARD_STOP   |           82   | STOP              | 2026-04-07T11:01:00+00:00 |      63.6122 |                 4896 | True                       | SL_TOUCH_BEFORE_THRESHOLD       |
| 20bbebe07f85f5df26d3a600 | LONG        | 2026-04-16T10:09:00+00:00 | REFERENCE_LEVEL_HARD_STOP |           87.5 | STOP              | 2026-04-16T10:13:00+00:00 |      43.5714 |                 1815 | True                       | SL_TOUCH_BEFORE_THRESHOLD       |
| 20bbebe07f85f5df26d3a600 | LONG        | 2026-04-16T10:09:00+00:00 | SWEEP_EXTREME_HARD_STOP   |           99.8 | STOP              | 2026-04-16T10:14:00+00:00 |      38.2014 |                 1815 | True                       | SL_TOUCH_BEFORE_THRESHOLD       |
| f015269d47c4d8b05862fd28 | LONG        | 2026-04-09T00:51:00+00:00 | SWEEP_EXTREME_HARD_STOP   |           87.1 | STOP              | 2026-04-09T00:51:00+00:00 |      35.0666 |                 3975 | True                       | SL_TOUCH_BEFORE_THRESHOLD       |
| 5b5778d8476b895e6de94ff8 | SHORT       | 2026-04-17T08:53:00+00:00 | REFERENCE_LEVEL_HARD_STOP |           59.9 | STOP              | 2026-04-17T08:53:00+00:00 |      29.5676 |                 3788 | True                       | SL_TOUCH_BEFORE_THRESHOLD       |
| 41b0c0d1c811e60feabed7db | SHORT       | 2026-04-04T15:17:00+00:00 | REFERENCE_LEVEL_HARD_STOP |           26.9 | STOP              | 2026-04-04T15:17:00+00:00 |      27.7918 |                  901 | True                       | SL_TOUCH_BEFORE_THRESHOLD       |
| 0d25765ec7778c11c037cd24 | LONG        | 2026-04-19T18:03:00+00:00 | SWEEP_EXTREME_HARD_STOP   |          211.7 | STOP              | 2026-04-19T18:25:00+00:00 |      21.8106 |                 4203 | True                       | SL_TOUCH_BEFORE_THRESHOLD       |
| 513de79500f119ebdc89e724 | SHORT       | 2026-04-01T05:28:00+00:00 | SWEEP_EXTREME_HARD_STOP   |          165.2 | STOP              | 2026-04-01T06:20:00+00:00 |      17.4594 |                 1928 | True                       | SL_TOUCH_BEFORE_THRESHOLD       |
| 08ece5642f91aaa3c0c93b7d | LONG        | 2026-04-18T16:21:00+00:00 | REFERENCE_LEVEL_HARD_STOP |          221.7 | STOP              | 2026-04-18T18:02:00+00:00 |      15.8399 |                 5745 | True                       | SL_TOUCH_BEFORE_THRESHOLD       |
| db5b6d371b68357ad98b0e95 | SHORT       | 2026-04-08T13:16:00+00:00 | REFERENCE_LEVEL_HARD_STOP |          153   | STOP              | 2026-04-08T13:19:00+00:00 |      14.1333 |                  729 | True                       | SL_TOUCH_BEFORE_THRESHOLD       |
| 405013a764fde5de604ad58a | SHORT       | 2026-04-11T18:44:00+00:00 | SWEEP_EXTREME_HARD_STOP   |          256.4 | STOP              | 2026-04-11T19:06:00+00:00 |      11.5784 |                 1667 | True                       | SL_TOUCH_BEFORE_THRESHOLD       |
| db5b6d371b68357ad98b0e95 | SHORT       | 2026-04-08T13:16:00+00:00 | SWEEP_EXTREME_HARD_STOP   |          209.6 | STOP              | 2026-04-08T13:19:00+00:00 |      10.3168 |                  729 | True                       | SL_TOUCH_BEFORE_THRESHOLD       |

## Interpretation

- `REFERENCE_LEVEL_HARD_STOP` H4 MFE extension is large in R terms: median MFE_R `42.644178`, p75 `128.515152`, p90 `426.618182`. Count >= 2R: `37/37`; >= 3R: `37/37`; >= 5R: `36/37`.
- `SWEEP_EXTREME_HARD_STOP` also shows extension beyond 1.5R but naturally lower in R terms because risk distance is wider: median MFE_R `12.411209`, p75 `23.753653`, p90 `36.754302`. Count >= 2R: `34/37`; >= 3R: `34/37`; >= 5R: `29/37`.
- Same-bar-clean subset remains informative: reference strict-clean has `15` trades with median MFE_R `26.453386`; sweep strict-clean has `35` trades with median MFE_R `11.578393`.
- Treat these as excursion diagnostics, not TP results. The SL-before-threshold table is the guardrail for whether larger R moves were reachable before the stop at bar resolution.
- Research-only verdict: H4 failed-break/reclaim deserves a dedicated MFE/exit-shape research candidate. The next bottleneck is not simply whether favorable excursion exists; it is whether entry/stop/same-bar ordering allows harvesting it without relying on ambiguous intrabar paths.

## Files Written

- `research/results/failed_break_reclaim_h4_mfe_r_diagnostic_2026-03-30_to_2026-05-02/h4_mfe_r_extension_report.md`
- `research/results/failed_break_reclaim_h4_mfe_r_diagnostic_2026-03-30_to_2026-05-02/h4_mfe_r_per_trade.csv`
- `research/results/failed_break_reclaim_h4_mfe_r_diagnostic_2026-03-30_to_2026-05-02/h4_mfe_r_summary_by_stop_model.csv`
- `research/results/failed_break_reclaim_h4_mfe_r_diagnostic_2026-03-30_to_2026-05-02/h4_mfe_r_summary_by_direction.csv`
- `research/results/failed_break_reclaim_h4_mfe_r_diagnostic_2026-03-30_to_2026-05-02/h4_mfe_r_summary_by_same_bar_subset.csv`
- `research/results/failed_break_reclaim_h4_mfe_r_diagnostic_2026-03-30_to_2026-05-02/h4_mfe_r_sl_before_threshold_summary.csv`
