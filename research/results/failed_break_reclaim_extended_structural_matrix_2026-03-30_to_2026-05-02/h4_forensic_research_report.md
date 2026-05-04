# H4 Failed-Break/Reclaim Forensic Research Report

Research-only diagnostic slice from the existing large structural matrix. No strategy logic, Analyzer behavior, or Backtester behavior was modified for this report.

## Scope

- Source artifact: `research/results/failed_break_reclaim_extended_structural_matrix_2026-03-30_to_2026-05-02/structural_matrix_all_trades.csv`
- Setup source: `FAILED_BREAK_RECLAIM_EXTENDED_V1`
- SourceTF filter: `H4` only
- Confirmation: `confirmation_bars=60` inherited from the EXTENDED_V1 setup source
- Representative expiry: `BARS_AFTER_ACTIVATION:4320`
- Stop models: `REFERENCE_LEVEL_HARD_STOP`, `SWEEP_EXTREME_HARD_STOP`
- Risk buckets used here: tiny `<= 25` dollars, normal `(25, 100]` dollars, large `> 100` dollars of risk distance per 1R.

## Representative Expiry Check

H4 metrics are unchanged between `BARS_AFTER_ACTIVATION:2880` and `BARS_AFTER_ACTIVATION:4320` in this matrix, so `4320` is a representative forensic horizon.

| StopModel                 | ExpiryModel                |   Trades |   TP |   SL |   Expiry |   Unresolved |   Winrate |   NetR |    MeanR |   MedianR |   AvgHoldBars |   MedianHoldBars |   AvgRiskDistance |   MedianRiskDistance |   SameBarExitCount |   SameBarCollisionCount |
|:--------------------------|:---------------------------|---------:|-----:|-----:|---------:|-------------:|----------:|-------:|---------:|----------:|--------------:|-----------------:|------------------:|---------------------:|-------------------:|------------------------:|
| REFERENCE_LEVEL_HARD_STOP | BARS_AFTER_ACTIVATION:2880 |       37 |   23 |   14 |        0 |            0 |  0.621622 |   20.5 | 0.554054 |       1.5 |       6.78378 |                1 |           58.7946 |                 35.7 |                 13 |                       9 |
| REFERENCE_LEVEL_HARD_STOP | BARS_AFTER_ACTIVATION:4320 |       37 |   23 |   14 |        0 |            0 |  0.621622 |   20.5 | 0.554054 |       1.5 |       6.78378 |                1 |           58.7946 |                 35.7 |                 13 |                       9 |
| SWEEP_EXTREME_HARD_STOP   | BARS_AFTER_ACTIVATION:2880 |       37 |   22 |   15 |        0 |            0 |  0.594595 |   18   | 0.486486 |       1.5 |      71.4595  |               15 |          190.665  |                183   |                  2 |                       0 |
| SWEEP_EXTREME_HARD_STOP   | BARS_AFTER_ACTIVATION:4320 |       37 |   22 |   15 |        0 |            0 |  0.594595 |   18   | 0.486486 |       1.5 |      71.4595  |               15 |          190.665  |                183   |                  2 |                       0 |

## H4-Only Summary

| StopModel                 |   Trades |   TP |   SL |   Expiry |   Unresolved |   Winrate |   NetR |    MeanR |   MedianR |   AvgHoldBars |   MedianHoldBars |   AvgRiskDistance |   MedianRiskDistance |   SameBarExitCount |   SameBarCollisionCount |
|:--------------------------|---------:|-----:|-----:|---------:|-------------:|----------:|-------:|---------:|----------:|--------------:|-----------------:|------------------:|---------------------:|-------------------:|------------------------:|
| REFERENCE_LEVEL_HARD_STOP |       37 |   23 |   14 |        0 |            0 |  0.621622 |   20.5 | 0.554054 |       1.5 |       6.78378 |                1 |           58.7946 |                 35.7 |                 13 |                       9 |
| SWEEP_EXTREME_HARD_STOP   |       37 |   22 |   15 |        0 |            0 |  0.594595 |   18   | 0.486486 |       1.5 |      71.4595  |               15 |          190.665  |                183   |                  2 |                       0 |

## Same-Bar Audit

| StopModel                 | Filter                             |   Trades |   TP |   SL |   Expiry |   Unresolved |   Winrate |   NetR |    MeanR |   MedianR |   AvgHoldBars |   MedianHoldBars |   AvgRiskDistance |   MedianRiskDistance |   SameBarExitCount |   SameBarCollisionCount |
|:--------------------------|:-----------------------------------|---------:|-----:|-----:|---------:|-------------:|----------:|-------:|---------:|----------:|--------------:|-----------------:|------------------:|---------------------:|-------------------:|------------------------:|
| REFERENCE_LEVEL_HARD_STOP | all_h4_trades                      |       37 |   23 |   14 |        0 |            0 |  0.621622 |   20.5 | 0.554054 |       1.5 |       6.78378 |                1 |           58.7946 |                35.7  |                 13 |                       9 |
| REFERENCE_LEVEL_HARD_STOP | exclude_same_bar_collisions        |       28 |   18 |   10 |        0 |            0 |  0.642857 |   17   | 0.607143 |       1.5 |       8.53571 |                1 |           73.3    |                61.4  |                 13 |                       0 |
| REFERENCE_LEVEL_HARD_STOP | exclude_all_same_bar_exits         |       24 |   16 |    8 |        0 |            0 |  0.666667 |   16   | 0.666667 |       1.5 |      10.4583  |                2 |           71.8042 |                51.25 |                  0 |                       9 |
| REFERENCE_LEVEL_HARD_STOP | exclude_same_bar_exit_or_collision |       15 |   11 |    4 |        0 |            0 |  0.733333 |   12.5 | 0.833333 |       1.5 |      15.9333  |                5 |          106.687  |                89.3  |                  0 |                       0 |
| SWEEP_EXTREME_HARD_STOP   | all_h4_trades                      |       37 |   22 |   15 |        0 |            0 |  0.594595 |   18   | 0.486486 |       1.5 |      71.4595  |               15 |          190.665  |               183    |                  2 |                       0 |
| SWEEP_EXTREME_HARD_STOP   | exclude_same_bar_collisions        |       37 |   22 |   15 |        0 |            0 |  0.594595 |   18   | 0.486486 |       1.5 |      71.4595  |               15 |          190.665  |               183    |                  2 |                       0 |
| SWEEP_EXTREME_HARD_STOP   | exclude_all_same_bar_exits         |       35 |   21 |   14 |        0 |            0 |  0.6      |   17.5 | 0.5      |       1.5 |      75.5429  |               16 |          197.609  |               188.8  |                  0 |                       0 |
| SWEEP_EXTREME_HARD_STOP   | exclude_same_bar_exit_or_collision |       35 |   21 |   14 |        0 |            0 |  0.6      |   17.5 | 0.5      |       1.5 |      75.5429  |               16 |          197.609  |               188.8  |                  0 |                       0 |

Interpretation: `REFERENCE_LEVEL_HARD_STOP` has materially more same-bar exposure on H4: 13 same-bar exits and 9 same-bar collisions out of 37 trades. Excluding all same-bar exits still leaves it positive: 24 trades, 16 TP / 8 SL, NetR `16.0`. Under the strict filter excluding either same-bar exits or same-bar collisions, reference stop remains positive but the sample drops to 15 trades and NetR `12.5`. `SWEEP_EXTREME_HARD_STOP` has only 2 same-bar exits and 0 collisions; under the same strict filter it has 35 trades and NetR `17.5`.

## Risk-Distance Audit

### Risk Distance Distribution

| StopModel                 |   Count |   Min |   P10 |   P25 |   Median |   P75 |    P90 |   Max |     Mean |
|:--------------------------|--------:|------:|------:|------:|---------:|------:|-------:|------:|---------:|
| REFERENCE_LEVEL_HARD_STOP |      37 |   0.2 |  7.38 |  17.4 |     35.7 |  87.5 | 124.08 | 278   |  58.7946 |
| SWEEP_EXTREME_HARD_STOP   |      37 |  46.2 | 72.72 | 111.2 |    183   | 231.4 | 317    | 472.9 | 190.665  |

### Results By R Bucket

| StopModel                 | RiskBucket         |   Trades |   TP |   SL |   Expiry |   Unresolved |   Winrate |   NetR |    MeanR |   MedianR |   AvgHoldBars |   MedianHoldBars |   AvgRiskDistance |   MedianRiskDistance |   SameBarExitCount |   SameBarCollisionCount |
|:--------------------------|:-------------------|---------:|-----:|-----:|---------:|-------------:|----------:|-------:|---------:|----------:|--------------:|-----------------:|------------------:|---------------------:|-------------------:|------------------------:|
| REFERENCE_LEVEL_HARD_STOP | tiny_R_<=25        |       14 |    9 |    5 |        0 |            0 |  0.642857 |    8.5 | 0.607143 |       1.5 |      0.785714 |                1 |           12.2643 |                13.45 |                  6 |                       7 |
| REFERENCE_LEVEL_HARD_STOP | normal_R_25_to_100 |       17 |   10 |    7 |        0 |            0 |  0.588235 |    8   | 0.470588 |       1.5 |      2.58824  |                1 |           56.7706 |                59.9  |                  7 |                       2 |
| REFERENCE_LEVEL_HARD_STOP | large_R_>100       |        6 |    4 |    2 |        0 |            0 |  0.666667 |    4   | 0.666667 |       1.5 |     32.6667   |               18 |          173.1    |               166.1  |                  0 |                       0 |
| SWEEP_EXTREME_HARD_STOP   | normal_R_25_to_100 |        9 |    5 |    4 |        0 |            0 |  0.555556 |    3.5 | 0.388889 |       1.5 |     21.6667   |                3 |           74.5556 |                82    |                  2 |                       0 |
| SWEEP_EXTREME_HARD_STOP   | large_R_>100       |       28 |   17 |   11 |        0 |            0 |  0.607143 |   14.5 | 0.517857 |       1.5 |     87.4643   |               20 |          227.986  |               210.65 |                  0 |                       0 |

Interpretation: reference-stop H4 profitability is not only from the tiny bucket by this explicit bucket definition. It is positive in tiny, normal, and large buckets. The larger concern is that the tiny and normal buckets carry most same-bar exposure, so the attractive reference-stop result still needs a stricter intrabar/same-bar treatment before it can be treated as robust. Sweep-extreme shifts most H4 trades into large absolute risk distances and remains positive there, though with lower NetR than reference stop.

## Direction Split

| StopModel                 | direction   |   Trades |   TP |   SL |   Expiry |   Unresolved |   Winrate |   NetR |    MeanR |   MedianR |   AvgHoldBars |   MedianHoldBars |   AvgRiskDistance |   MedianRiskDistance |   SameBarExitCount |   SameBarCollisionCount |
|:--------------------------|:------------|---------:|-----:|-----:|---------:|-------------:|----------:|-------:|---------:|----------:|--------------:|-----------------:|------------------:|---------------------:|-------------------:|------------------------:|
| REFERENCE_LEVEL_HARD_STOP | LONG        |       16 |    9 |    7 |        0 |            0 |  0.5625   |    6.5 | 0.40625  |       1.5 |       7.9375  |                1 |           47.7188 |                 25   |                  7 |                       3 |
| REFERENCE_LEVEL_HARD_STOP | SHORT       |       21 |   14 |    7 |        0 |            0 |  0.666667 |   14   | 0.666667 |       1.5 |       5.90476 |                1 |           67.2333 |                 39.6 |                  6 |                       6 |
| SWEEP_EXTREME_HARD_STOP   | LONG        |       16 |    9 |    7 |        0 |            0 |  0.5625   |    6.5 | 0.40625  |       1.5 |      32.875   |               10 |          146.931  |                105.5 |                  1 |                       0 |
| SWEEP_EXTREME_HARD_STOP   | SHORT       |       21 |   13 |    8 |        0 |            0 |  0.619048 |   11.5 | 0.547619 |       1.5 |     100.857   |               18 |          223.986  |                209.6 |                  1 |                       0 |

## Stop Comparison

| ExpiryModel                |   ComparedTrades |   SweepSavesReferenceSL |   SweepMakesTPUnreachable |   ReferenceWinsTinyR |   AvgRDiff_SweepMinusRef |   MedianRDiff_SweepMinusRef |
|:---------------------------|-----------------:|------------------------:|--------------------------:|---------------------:|-------------------------:|----------------------------:|
| BARS_AFTER_ACTIVATION:4320 |               37 |                       4 |                         5 |                    5 |                -0.067568 |                           0 |

### Flagged Examples

| SetupId                  | Direction   | RefExit   | SweepExit   |   RefR |   SweepR |   DeltaR_SweepMinusRef |   RefRiskDistance |   SweepRiskDistance | SweepSavesReferenceSL   | SweepMakesTPUnreachable   | ReferenceWinsTinyR   |
|:-------------------------|:------------|:----------|:------------|-------:|---------:|-----------------------:|------------------:|--------------------:|:------------------------|:--------------------------|:---------------------|
| 4a4a99cd318717852e39bf35 | SHORT       | TARGET    | STOP        |    1.5 |     -1   |                   -2.5 |             278   |               405.7 | False                   | True                      | True                 |
| 513de79500f119ebdc89e724 | SHORT       | TARGET    | STOP        |    1.5 |     -1   |                   -2.5 |              39.6 |               165.2 | False                   | True                      | True                 |
| 752a04162f5f952bae4ebb52 | LONG        | TARGET    | STOP        |    1.5 |     -1   |                   -2.5 |              95.3 |               381   | False                   | True                      | True                 |
| 7b888d3386fe39dad14954b7 | SHORT       | TARGET    | STOP        |    1.5 |     -1   |                   -2.5 |              33.4 |               219.5 | False                   | True                      | True                 |
| 9ec69c6605ca85675e0e6e06 | LONG        | TARGET    | STOP        |    1.5 |     -1   |                   -2.5 |              14.3 |                58.8 | False                   | True                      | True                 |
| 3006cd3533f5bb2880b10b4d | LONG        | STOP      | TARGET      |   -1   |      1.5 |                    2.5 |              29.2 |               143.7 | True                    | False                     | False                |
| 3711c617488c92d9828c70cf | SHORT       | STOP      | TARGET      |   -1   |      1.5 |                    2.5 |              25.7 |               254.3 | True                    | False                     | False                |
| 41b0c0d1c811e60feabed7db | SHORT       | STOP      | TARGET      |   -1   |      1.5 |                    2.5 |              26.9 |               231.4 | True                    | False                     | False                |
| a7041ce1f10fd1f3af817637 | LONG        | STOP      | TARGET      |   -1   |      1.5 |                    2.5 |               0.2 |                97.6 | True                    | False                     | False                |

Interpretation: in H4, sweep-extreme saves 4 reference-stop losses, while 5 trades are flagged where the wider sweep stop makes the 1.5R target unreachable relative to the reference stop. H4 remains positive with sweep-extreme: 37 trades, 22 TP, 15 SL, NetR `18.0`, MeanR `0.486486`, MedianR `1.5`.

## H1 Contrast

| StopModel                 |   Trades |   TP |   SL |   Expiry |   Unresolved |   Winrate |   NetR |     MeanR |   MedianR |   AvgHoldBars |   MedianHoldBars |   AvgRiskDistance |   MedianRiskDistance |   SameBarExitCount |   SameBarCollisionCount |
|:--------------------------|---------:|-----:|-----:|---------:|-------------:|----------:|-------:|----------:|----------:|--------------:|-----------------:|------------------:|---------------------:|-------------------:|------------------------:|
| REFERENCE_LEVEL_HARD_STOP |      116 |   48 |   68 |        0 |            0 |  0.413793 |    4   |  0.034483 |        -1 |       17.7672 |                1 |           53.6224 |                31.45 |                 43 |                      12 |
| SWEEP_EXTREME_HARD_STOP   |      116 |   43 |   73 |        0 |            0 |  0.37069  |   -8.5 | -0.073276 |        -1 |       32.4741 |                6 |          121.043  |                90.4  |                 14 |                       2 |

H1 is weak in this same representative expiry, especially under `SWEEP_EXTREME_HARD_STOP` where NetR is negative. This supports treating H1 as weak for this research slice unless later evidence changes that.

## Verdict

- Do not claim edge or execution readiness from this sample.
- H4-only deserves promotion to a dedicated ruleset research candidate, not because it is proven, but because it remains positive under both stop models and is much stronger than H1 in the same matrix.
- The strongest caveat is same-bar ambiguity on the reference-level stop: reference H4 is attractive in aggregate, but 9/37 trades have same-bar collisions and 13/37 exit on the same bar. The stricter clean subset remains positive, but it is only 15 trades.
- Sweep-extreme H4 is cleaner on same-bar ambiguity and still positive, but the wider stop reduces reward reachability under fixed `1.5R`; this points to stop/TP interaction as a key bottleneck.
- Current bottlenecks for dedicated H4 research: same-bar handling, fixed `1.5R` TP under sweep-extreme risk, and entry timing. Synthetic data impact is not indicated in the parent matrix for this window.
- Research-only: these are deterministic backtest diagnostics, not live-ready execution rules.

## Files Written

- `research/results/failed_break_reclaim_extended_structural_matrix_2026-03-30_to_2026-05-02/h4_forensic_research_report.md`
- `research/results/failed_break_reclaim_extended_structural_matrix_2026-03-30_to_2026-05-02/h4_forensic_summary.csv`
- `research/results/failed_break_reclaim_extended_structural_matrix_2026-03-30_to_2026-05-02/h4_same_bar_audit.csv`
- `research/results/failed_break_reclaim_extended_structural_matrix_2026-03-30_to_2026-05-02/h4_risk_distance_distribution.csv`
- `research/results/failed_break_reclaim_extended_structural_matrix_2026-03-30_to_2026-05-02/h4_risk_bucket_summary.csv`
- `research/results/failed_break_reclaim_extended_structural_matrix_2026-03-30_to_2026-05-02/h4_direction_summary.csv`
- `research/results/failed_break_reclaim_extended_structural_matrix_2026-03-30_to_2026-05-02/h4_stop_comparison_summary.csv`
- `research/results/failed_break_reclaim_extended_structural_matrix_2026-03-30_to_2026-05-02/h4_stop_comparison_examples.csv`
- `research/results/failed_break_reclaim_extended_structural_matrix_2026-03-30_to_2026-05-02/h4_representative_expiry_check.csv`
