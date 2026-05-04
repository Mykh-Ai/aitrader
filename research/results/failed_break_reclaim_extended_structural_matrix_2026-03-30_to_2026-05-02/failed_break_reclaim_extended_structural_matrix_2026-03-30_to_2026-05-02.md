# FAILED_BREAK_RECLAIM_EXTENDED_V1 Structural Matrix - Large Full-Day Window

Research-only matrix. Strategy logic, baseline Analyzer behavior, and baseline Backtester defaults were not modified. No execution-readiness claim.

## Inputs

- Prep directory: `research/results/failed_break_reclaim_extended_large_window_prep_2026-03-10_to_2026-05-03/`
- Window: `2026-03-30_to_2026-05-02`
- Setup source: `FAILED_BREAK_RECLAIM_EXTENDED_V1`
- confirmation_bars: `60`
- Eligible FULL 5760-bar setups: `153`
- Stop models: `REFERENCE_LEVEL_HARD_STOP`, `SWEEP_EXTREME_HARD_STOP`
- Expiry models: `1440`, `2880`, `4320`, `5760`
- Fixed: `NEXT_BAR_OPEN`, `FIXED_R_MULTIPLE:1.5`, `SAME_BAR_CONSERVATIVE_V0_1`, `COST_MODEL_ZERO_SKELETON_ONLY`, `REPLAY_V0_1`

## Summary By Stop Model And Expiry

| StopModel                 | ExpiryModel                |   Trades |   TP |   SL |   Expiry |   Unresolved |   Winrate |    NetR |    MeanR |   MedianR |   AvgHoldBars |   MaxHoldBars |   AvgRiskDistance |   MedianRiskDistance |   SameBarExitCount |   SameBarCollisionCount |   SetupSyntheticCount |   EntrySyntheticCount |   ExitSyntheticCount |   PathSyntheticCount |
|:--------------------------|:---------------------------|---------:|-----:|-----:|---------:|-------------:|----------:|--------:|---------:|----------:|--------------:|--------------:|------------------:|---------------------:|-------------------:|------------------------:|----------------------:|----------------------:|---------------------:|---------------------:|
| REFERENCE_LEVEL_HARD_STOP | BARS_AFTER_ACTIVATION:1440 |      153 |   71 |   81 |        1 |            0 |  0.464052 | 25.035  | 0.163627 |        -1 |       14.085  |          1440 |           54.8732 |                 31.9 |                 56 |                      21 |                     0 |                     0 |                    0 |                    0 |
| REFERENCE_LEVEL_HARD_STOP | BARS_AFTER_ACTIVATION:2880 |      153 |   71 |   82 |        0 |            0 |  0.464052 | 24.5    | 0.160131 |        -1 |       15.1111 |          1597 |           54.8732 |                 31.9 |                 56 |                      21 |                     0 |                     0 |                    0 |                    0 |
| REFERENCE_LEVEL_HARD_STOP | BARS_AFTER_ACTIVATION:4320 |      153 |   71 |   82 |        0 |            0 |  0.464052 | 24.5    | 0.160131 |        -1 |       15.1111 |          1597 |           54.8732 |                 31.9 |                 56 |                      21 |                     0 |                     0 |                    0 |                    0 |
| REFERENCE_LEVEL_HARD_STOP | BARS_AFTER_ACTIVATION:5760 |      153 |   71 |   82 |        0 |            0 |  0.464052 | 24.5    | 0.160131 |        -1 |       15.1111 |          1597 |           54.8732 |                 31.9 |                 56 |                      21 |                     0 |                     0 |                    0 |                    0 |
| SWEEP_EXTREME_HARD_STOP   | BARS_AFTER_ACTIVATION:1440 |      153 |   65 |   87 |        1 |            0 |  0.424837 | 10.1376 | 0.066259 |        -1 |       40.8562 |          1440 |          137.88   |                111.2 |                 16 |                       2 |                     0 |                     0 |                    0 |                    0 |
| SWEEP_EXTREME_HARD_STOP   | BARS_AFTER_ACTIVATION:2880 |      153 |   65 |   88 |        0 |            0 |  0.424837 |  9.5    | 0.062092 |        -1 |       41.902  |          1600 |          137.88   |                111.2 |                 16 |                       2 |                     0 |                     0 |                    0 |                    0 |
| SWEEP_EXTREME_HARD_STOP   | BARS_AFTER_ACTIVATION:4320 |      153 |   65 |   88 |        0 |            0 |  0.424837 |  9.5    | 0.062092 |        -1 |       41.902  |          1600 |          137.88   |                111.2 |                 16 |                       2 |                     0 |                     0 |                    0 |                    0 |
| SWEEP_EXTREME_HARD_STOP   | BARS_AFTER_ACTIVATION:5760 |      153 |   65 |   88 |        0 |            0 |  0.424837 |  9.5    | 0.062092 |        -1 |       41.902  |          1600 |          137.88   |                111.2 |                 16 |                       2 |                     0 |                     0 |                    0 |                    0 |

## Split By Direction

| StopModel                 | ExpiryModel                | direction   |   Trades |   TP |   SL |   Expiry |   Unresolved |   Winrate |      NetR |    MeanR |   MedianR |   AvgHoldBars |   MaxHoldBars |   AvgRiskDistance |   MedianRiskDistance |   SameBarExitCount |   SameBarCollisionCount |   SetupSyntheticCount |   EntrySyntheticCount |   ExitSyntheticCount |   PathSyntheticCount |
|:--------------------------|:---------------------------|:------------|---------:|-----:|-----:|---------:|-------------:|----------:|----------:|---------:|----------:|--------------:|--------------:|------------------:|---------------------:|-------------------:|------------------------:|----------------------:|----------------------:|---------------------:|---------------------:|
| REFERENCE_LEVEL_HARD_STOP | BARS_AFTER_ACTIVATION:1440 | LONG        |       73 |   33 |   40 |        0 |            0 |  0.452055 |  9.5      | 0.130137 |        -1 |       5.71233 |           101 |           51.7726 |                26.8  |                 34 |                       6 |                     0 |                     0 |                    0 |                    0 |
| REFERENCE_LEVEL_HARD_STOP | BARS_AFTER_ACTIVATION:1440 | SHORT       |       80 |   38 |   41 |        1 |            0 |  0.475    | 15.535    | 0.194187 |        -1 |      21.725   |          1440 |           57.7025 |                37.4  |                 22 |                      15 |                     0 |                     0 |                    0 |                    0 |
| REFERENCE_LEVEL_HARD_STOP | BARS_AFTER_ACTIVATION:2880 | LONG        |       73 |   33 |   40 |        0 |            0 |  0.452055 |  9.5      | 0.130137 |        -1 |       5.71233 |           101 |           51.7726 |                26.8  |                 34 |                       6 |                     0 |                     0 |                    0 |                    0 |
| REFERENCE_LEVEL_HARD_STOP | BARS_AFTER_ACTIVATION:2880 | SHORT       |       80 |   38 |   42 |        0 |            0 |  0.475    | 15        | 0.1875   |        -1 |      23.6875  |          1597 |           57.7025 |                37.4  |                 22 |                      15 |                     0 |                     0 |                    0 |                    0 |
| REFERENCE_LEVEL_HARD_STOP | BARS_AFTER_ACTIVATION:4320 | LONG        |       73 |   33 |   40 |        0 |            0 |  0.452055 |  9.5      | 0.130137 |        -1 |       5.71233 |           101 |           51.7726 |                26.8  |                 34 |                       6 |                     0 |                     0 |                    0 |                    0 |
| REFERENCE_LEVEL_HARD_STOP | BARS_AFTER_ACTIVATION:4320 | SHORT       |       80 |   38 |   42 |        0 |            0 |  0.475    | 15        | 0.1875   |        -1 |      23.6875  |          1597 |           57.7025 |                37.4  |                 22 |                      15 |                     0 |                     0 |                    0 |                    0 |
| REFERENCE_LEVEL_HARD_STOP | BARS_AFTER_ACTIVATION:5760 | LONG        |       73 |   33 |   40 |        0 |            0 |  0.452055 |  9.5      | 0.130137 |        -1 |       5.71233 |           101 |           51.7726 |                26.8  |                 34 |                       6 |                     0 |                     0 |                    0 |                    0 |
| REFERENCE_LEVEL_HARD_STOP | BARS_AFTER_ACTIVATION:5760 | SHORT       |       80 |   38 |   42 |        0 |            0 |  0.475    | 15        | 0.1875   |        -1 |      23.6875  |          1597 |           57.7025 |                37.4  |                 22 |                      15 |                     0 |                     0 |                    0 |                    0 |
| SWEEP_EXTREME_HARD_STOP   | BARS_AFTER_ACTIVATION:1440 | LONG        |       73 |   33 |   40 |        0 |            0 |  0.452055 |  9.5      | 0.130137 |        -1 |      25.2055  |           149 |          124.767  |                97.6  |                  8 |                       1 |                     0 |                     0 |                    0 |                    0 |
| SWEEP_EXTREME_HARD_STOP   | BARS_AFTER_ACTIVATION:1440 | SHORT       |       80 |   32 |   47 |        1 |            0 |  0.4      |  0.637629 | 0.00797  |        -1 |      55.1375  |          1440 |          149.845  |               143.65 |                  8 |                       1 |                     0 |                     0 |                    0 |                    0 |
| SWEEP_EXTREME_HARD_STOP   | BARS_AFTER_ACTIVATION:2880 | LONG        |       73 |   33 |   40 |        0 |            0 |  0.452055 |  9.5      | 0.130137 |        -1 |      25.2055  |           149 |          124.767  |                97.6  |                  8 |                       1 |                     0 |                     0 |                    0 |                    0 |
| SWEEP_EXTREME_HARD_STOP   | BARS_AFTER_ACTIVATION:2880 | SHORT       |       80 |   32 |   48 |        0 |            0 |  0.4      |  0        | 0        |        -1 |      57.1375  |          1600 |          149.845  |               143.65 |                  8 |                       1 |                     0 |                     0 |                    0 |                    0 |
| SWEEP_EXTREME_HARD_STOP   | BARS_AFTER_ACTIVATION:4320 | LONG        |       73 |   33 |   40 |        0 |            0 |  0.452055 |  9.5      | 0.130137 |        -1 |      25.2055  |           149 |          124.767  |                97.6  |                  8 |                       1 |                     0 |                     0 |                    0 |                    0 |
| SWEEP_EXTREME_HARD_STOP   | BARS_AFTER_ACTIVATION:4320 | SHORT       |       80 |   32 |   48 |        0 |            0 |  0.4      |  0        | 0        |        -1 |      57.1375  |          1600 |          149.845  |               143.65 |                  8 |                       1 |                     0 |                     0 |                    0 |                    0 |
| SWEEP_EXTREME_HARD_STOP   | BARS_AFTER_ACTIVATION:5760 | LONG        |       73 |   33 |   40 |        0 |            0 |  0.452055 |  9.5      | 0.130137 |        -1 |      25.2055  |           149 |          124.767  |                97.6  |                  8 |                       1 |                     0 |                     0 |                    0 |                    0 |
| SWEEP_EXTREME_HARD_STOP   | BARS_AFTER_ACTIVATION:5760 | SHORT       |       80 |   32 |   48 |        0 |            0 |  0.4      |  0        | 0        |        -1 |      57.1375  |          1600 |          149.845  |               143.65 |                  8 |                       1 |                     0 |                     0 |                    0 |                    0 |

## Split By Level Timeframe

| StopModel                 | ExpiryModel                | SourceTF   |   Trades |   TP |   SL |   Expiry |   Unresolved |   Winrate |     NetR |     MeanR |   MedianR |   AvgHoldBars |   MaxHoldBars |   AvgRiskDistance |   MedianRiskDistance |   SameBarExitCount |   SameBarCollisionCount |   SetupSyntheticCount |   EntrySyntheticCount |   ExitSyntheticCount |   PathSyntheticCount |
|:--------------------------|:---------------------------|:-----------|---------:|-----:|-----:|---------:|-------------:|----------:|---------:|----------:|----------:|--------------:|--------------:|------------------:|---------------------:|-------------------:|------------------------:|----------------------:|----------------------:|---------------------:|---------------------:|
| REFERENCE_LEVEL_HARD_STOP | BARS_AFTER_ACTIVATION:1440 | H1         |      116 |   48 |   67 |        1 |            0 |  0.413793 |  4.53496 |  0.039094 |      -1   |      16.4138  |          1440 |           53.6224 |                31.45 |                 43 |                      12 |                     0 |                     0 |                    0 |                    0 |
| REFERENCE_LEVEL_HARD_STOP | BARS_AFTER_ACTIVATION:1440 | H4         |       37 |   23 |   14 |        0 |            0 |  0.621622 | 20.5     |  0.554054 |       1.5 |       6.78378 |           101 |           58.7946 |                35.7  |                 13 |                       9 |                     0 |                     0 |                    0 |                    0 |
| REFERENCE_LEVEL_HARD_STOP | BARS_AFTER_ACTIVATION:2880 | H1         |      116 |   48 |   68 |        0 |            0 |  0.413793 |  4       |  0.034483 |      -1   |      17.7672  |          1597 |           53.6224 |                31.45 |                 43 |                      12 |                     0 |                     0 |                    0 |                    0 |
| REFERENCE_LEVEL_HARD_STOP | BARS_AFTER_ACTIVATION:2880 | H4         |       37 |   23 |   14 |        0 |            0 |  0.621622 | 20.5     |  0.554054 |       1.5 |       6.78378 |           101 |           58.7946 |                35.7  |                 13 |                       9 |                     0 |                     0 |                    0 |                    0 |
| REFERENCE_LEVEL_HARD_STOP | BARS_AFTER_ACTIVATION:4320 | H1         |      116 |   48 |   68 |        0 |            0 |  0.413793 |  4       |  0.034483 |      -1   |      17.7672  |          1597 |           53.6224 |                31.45 |                 43 |                      12 |                     0 |                     0 |                    0 |                    0 |
| REFERENCE_LEVEL_HARD_STOP | BARS_AFTER_ACTIVATION:4320 | H4         |       37 |   23 |   14 |        0 |            0 |  0.621622 | 20.5     |  0.554054 |       1.5 |       6.78378 |           101 |           58.7946 |                35.7  |                 13 |                       9 |                     0 |                     0 |                    0 |                    0 |
| REFERENCE_LEVEL_HARD_STOP | BARS_AFTER_ACTIVATION:5760 | H1         |      116 |   48 |   68 |        0 |            0 |  0.413793 |  4       |  0.034483 |      -1   |      17.7672  |          1597 |           53.6224 |                31.45 |                 43 |                      12 |                     0 |                     0 |                    0 |                    0 |
| REFERENCE_LEVEL_HARD_STOP | BARS_AFTER_ACTIVATION:5760 | H4         |       37 |   23 |   14 |        0 |            0 |  0.621622 | 20.5     |  0.554054 |       1.5 |       6.78378 |           101 |           58.7946 |                35.7  |                 13 |                       9 |                     0 |                     0 |                    0 |                    0 |
| SWEEP_EXTREME_HARD_STOP   | BARS_AFTER_ACTIVATION:1440 | H1         |      116 |   43 |   72 |        1 |            0 |  0.37069  | -7.86237 | -0.067779 |      -1   |      31.0948  |          1440 |          121.043  |                90.4  |                 14 |                       2 |                     0 |                     0 |                    0 |                    0 |
| SWEEP_EXTREME_HARD_STOP   | BARS_AFTER_ACTIVATION:1440 | H4         |       37 |   22 |   15 |        0 |            0 |  0.594595 | 18       |  0.486486 |       1.5 |      71.4595  |           646 |          190.665  |               183    |                  2 |                       0 |                     0 |                     0 |                    0 |                    0 |
| SWEEP_EXTREME_HARD_STOP   | BARS_AFTER_ACTIVATION:2880 | H1         |      116 |   43 |   73 |        0 |            0 |  0.37069  | -8.5     | -0.073276 |      -1   |      32.4741  |          1600 |          121.043  |                90.4  |                 14 |                       2 |                     0 |                     0 |                    0 |                    0 |
| SWEEP_EXTREME_HARD_STOP   | BARS_AFTER_ACTIVATION:2880 | H4         |       37 |   22 |   15 |        0 |            0 |  0.594595 | 18       |  0.486486 |       1.5 |      71.4595  |           646 |          190.665  |               183    |                  2 |                       0 |                     0 |                     0 |                    0 |                    0 |
| SWEEP_EXTREME_HARD_STOP   | BARS_AFTER_ACTIVATION:4320 | H1         |      116 |   43 |   73 |        0 |            0 |  0.37069  | -8.5     | -0.073276 |      -1   |      32.4741  |          1600 |          121.043  |                90.4  |                 14 |                       2 |                     0 |                     0 |                    0 |                    0 |
| SWEEP_EXTREME_HARD_STOP   | BARS_AFTER_ACTIVATION:4320 | H4         |       37 |   22 |   15 |        0 |            0 |  0.594595 | 18       |  0.486486 |       1.5 |      71.4595  |           646 |          190.665  |               183    |                  2 |                       0 |                     0 |                     0 |                    0 |                    0 |
| SWEEP_EXTREME_HARD_STOP   | BARS_AFTER_ACTIVATION:5760 | H1         |      116 |   43 |   73 |        0 |            0 |  0.37069  | -8.5     | -0.073276 |      -1   |      32.4741  |          1600 |          121.043  |                90.4  |                 14 |                       2 |                     0 |                     0 |                    0 |                    0 |
| SWEEP_EXTREME_HARD_STOP   | BARS_AFTER_ACTIVATION:5760 | H4         |       37 |   22 |   15 |        0 |            0 |  0.594595 | 18       |  0.486486 |       1.5 |      71.4595  |           646 |          190.665  |               183    |                  2 |                       0 |                     0 |                     0 |                    0 |                    0 |

## Synthetic Row Impact

| Metric                                               |   Count |
|:-----------------------------------------------------|--------:|
| Unique setups with synthetic SetupBarTs              |       0 |
| Trade rows with synthetic SetupBarTs                 |       0 |
| Trade rows with synthetic entry bars                 |       0 |
| Trade rows with synthetic exit bars                  |       0 |
| Trade rows with synthetic bars in entry-to-exit path |       0 |

- Synthetic path rows are counted when any synthetic raw bar appears between entry activation and exit inclusive.
- No replay paths involved synthetic rows, so synthetic data did not materially affect this matrix.

## Expiry Sensitivity

| Metric                                        |   Count |
|:----------------------------------------------|--------:|
| trades where 1d differs from longer expiry    |       2 |
| 1d expiry converts to TP under longer holding |       0 |
| 1d expiry converts to SL under longer holding |       2 |
| trades unchanged across expiries              |     304 |

### Changed Examples

| StopModel                 | SetupId                  | Direction   | SourceTF   | Exit1440   | Exit2880   | Exit4320   | Exit5760   |     R1440 |   R2880 |   R4320 |   R5760 |   Hold1440 |   Hold5760 | ChangedVs1440   | Expiry1440ToTP   | Expiry1440ToSL   | UnchangedAcrossExpiries   |
|:--------------------------|:-------------------------|:------------|:-----------|:-----------|:-----------|:-----------|:-----------|----------:|--------:|--------:|--------:|-----------:|-----------:|:----------------|:-----------------|:-----------------|:--------------------------|
| REFERENCE_LEVEL_HARD_STOP | dcf0abfc7c987bdb44720ccd | SHORT       | H1         | EXPIRY     | STOP       | STOP       | STOP       | -0.465045 |      -1 |      -1 |      -1 |       1440 |       1597 | True            | False            | True             | False                     |
| SWEEP_EXTREME_HARD_STOP   | dcf0abfc7c987bdb44720ccd | SHORT       | H1         | EXPIRY     | STOP       | STOP       | STOP       | -0.362371 |      -1 |      -1 |      -1 |       1440 |       1600 | True            | False            | True             | False                     |

## Stop Model Comparison

| ExpiryModel                |   ComparedTrades |   SweepSavesReferenceSL |   SweepMakesTPUnreachable |   ReferenceWinsTinyR |   AvgRDiff_SweepMinusRef |   MedianRDiff_SweepMinusRef |
|:---------------------------|-----------------:|------------------------:|--------------------------:|---------------------:|-------------------------:|----------------------------:|
| BARS_AFTER_ACTIVATION:1440 |              153 |                      14 |                        20 |                   20 |                -0.097368 |                           0 |
| BARS_AFTER_ACTIVATION:2880 |              153 |                      14 |                        20 |                   20 |                -0.098039 |                           0 |
| BARS_AFTER_ACTIVATION:4320 |              153 |                      14 |                        20 |                   20 |                -0.098039 |                           0 |
| BARS_AFTER_ACTIVATION:5760 |              153 |                      14 |                        20 |                   20 |                -0.098039 |                           0 |

### Stop Model Interesting Cases

| ExpiryModel                | SetupId                  | Direction   | SourceTF   | RefExit   | SweepExit   |   RefR |   SweepR |   DeltaR_SweepMinusRef |   RefRiskDistance |   SweepRiskDistance | SweepSavesReferenceSL   | SweepMakesTPUnreachable   | ReferenceWinsTinyR   |
|:---------------------------|:-------------------------|:------------|:-----------|:----------|:------------|-------:|---------:|-----------------------:|------------------:|--------------------:|:------------------------|:--------------------------|:---------------------|
| BARS_AFTER_ACTIVATION:1440 | 043d80cf1fff7e8444a7cce2 | LONG        | H1         | TARGET    | STOP        |    1.5 |     -1   |                   -2.5 |              39.8 |                77.9 | False                   | True                      | True                 |
| BARS_AFTER_ACTIVATION:1440 | 29b1ca502ec72d82d0b31169 | LONG        | H1         | TARGET    | STOP        |    1.5 |     -1   |                   -2.5 |              22   |               246.5 | False                   | True                      | True                 |
| BARS_AFTER_ACTIVATION:1440 | 3006cd3533f5bb2880b10b4d | LONG        | H4         | STOP      | TARGET      |   -1   |      1.5 |                    2.5 |              29.2 |               143.7 | True                    | False                     | False                |
| BARS_AFTER_ACTIVATION:1440 | 3711c617488c92d9828c70cf | SHORT       | H4         | STOP      | TARGET      |   -1   |      1.5 |                    2.5 |              25.7 |               254.3 | True                    | False                     | False                |
| BARS_AFTER_ACTIVATION:1440 | 41b0c0d1c811e60feabed7db | SHORT       | H4         | STOP      | TARGET      |   -1   |      1.5 |                    2.5 |              26.9 |               231.4 | True                    | False                     | False                |
| BARS_AFTER_ACTIVATION:1440 | 44ea31beeb5dd694163eae90 | LONG        | H1         | TARGET    | STOP        |    1.5 |     -1   |                   -2.5 |              26.8 |               381   | False                   | True                      | True                 |
| BARS_AFTER_ACTIVATION:1440 | 4988f84f62d2335a2b42538f | SHORT       | H1         | STOP      | TARGET      |   -1   |      1.5 |                    2.5 |               0.7 |                42.6 | True                    | False                     | False                |
| BARS_AFTER_ACTIVATION:1440 | 4a4a99cd318717852e39bf35 | SHORT       | H4         | TARGET    | STOP        |    1.5 |     -1   |                   -2.5 |             278   |               405.7 | False                   | True                      | True                 |
| BARS_AFTER_ACTIVATION:1440 | 4de20c1a78c94ab868cfc6ee | LONG        | H1         | STOP      | TARGET      |   -1   |      1.5 |                    2.5 |              60.4 |               128.1 | True                    | False                     | False                |
| BARS_AFTER_ACTIVATION:1440 | 513de79500f119ebdc89e724 | SHORT       | H4         | TARGET    | STOP        |    1.5 |     -1   |                   -2.5 |              39.6 |               165.2 | False                   | True                      | True                 |
| BARS_AFTER_ACTIVATION:1440 | 5f2ad97cd2153b5366d43956 | SHORT       | H1         | TARGET    | STOP        |    1.5 |     -1   |                   -2.5 |              36.7 |               156.7 | False                   | True                      | True                 |
| BARS_AFTER_ACTIVATION:1440 | 6a8bf19c00c0f910ef988ca9 | SHORT       | H1         | TARGET    | STOP        |    1.5 |     -1   |                   -2.5 |              23.7 |               217.9 | False                   | True                      | True                 |
| BARS_AFTER_ACTIVATION:1440 | 6d0e09c4a42a93ab19e9b46f | SHORT       | H1         | TARGET    | STOP        |    1.5 |     -1   |                   -2.5 |              27.7 |                40.4 | False                   | True                      | True                 |
| BARS_AFTER_ACTIVATION:1440 | 715ba4f3eaf520fc8a7b6be7 | LONG        | H1         | TARGET    | STOP        |    1.5 |     -1   |                   -2.5 |               8.9 |                88   | False                   | True                      | True                 |
| BARS_AFTER_ACTIVATION:1440 | 752a04162f5f952bae4ebb52 | LONG        | H4         | TARGET    | STOP        |    1.5 |     -1   |                   -2.5 |              95.3 |               381   | False                   | True                      | True                 |
| BARS_AFTER_ACTIVATION:1440 | 7b888d3386fe39dad14954b7 | SHORT       | H4         | TARGET    | STOP        |    1.5 |     -1   |                   -2.5 |              33.4 |               219.5 | False                   | True                      | True                 |
| BARS_AFTER_ACTIVATION:1440 | 7e9aea218f3084b2c0574d9d | SHORT       | H1         | TARGET    | STOP        |    1.5 |     -1   |                   -2.5 |              12.5 |               367.6 | False                   | True                      | True                 |
| BARS_AFTER_ACTIVATION:1440 | 7eb2f64f0f4dd2e6b4008c7a | SHORT       | H1         | TARGET    | STOP        |    1.5 |     -1   |                   -2.5 |              19.5 |                32.8 | False                   | True                      | True                 |
| BARS_AFTER_ACTIVATION:1440 | 8e85a4468a9719d03a0d0171 | LONG        | H1         | STOP      | TARGET      |   -1   |      1.5 |                    2.5 |               1.4 |                69.4 | True                    | False                     | False                |
| BARS_AFTER_ACTIVATION:1440 | 938d42fcd70403ea85ab5f50 | SHORT       | H1         | STOP      | TARGET      |   -1   |      1.5 |                    2.5 |              56.8 |               175   | True                    | False                     | False                |
| BARS_AFTER_ACTIVATION:1440 | 9c6b9223803a95ea039e6862 | SHORT       | H1         | TARGET    | STOP        |    1.5 |     -1   |                   -2.5 |              63.6 |               192   | False                   | True                      | True                 |
| BARS_AFTER_ACTIVATION:1440 | 9ec69c6605ca85675e0e6e06 | LONG        | H4         | TARGET    | STOP        |    1.5 |     -1   |                   -2.5 |              14.3 |                58.8 | False                   | True                      | True                 |
| BARS_AFTER_ACTIVATION:1440 | a7041ce1f10fd1f3af817637 | LONG        | H4         | STOP      | TARGET      |   -1   |      1.5 |                    2.5 |               0.2 |                97.6 | True                    | False                     | False                |
| BARS_AFTER_ACTIVATION:1440 | a8e1fa3c303b62aa7726cd86 | SHORT       | H1         | TARGET    | STOP        |    1.5 |     -1   |                   -2.5 |              47.2 |               124   | False                   | True                      | True                 |
| BARS_AFTER_ACTIVATION:1440 | a9380a59eae2b8756ef2ebaa | LONG        | H1         | TARGET    | STOP        |    1.5 |     -1   |                   -2.5 |              99.5 |               151.4 | False                   | True                      | True                 |
| BARS_AFTER_ACTIVATION:1440 | ab515ec62a26b795637b1b95 | SHORT       | H1         | TARGET    | STOP        |    1.5 |     -1   |                   -2.5 |              26.2 |                75.3 | False                   | True                      | True                 |
| BARS_AFTER_ACTIVATION:1440 | b57ffd69bb4bc51c6d340de9 | SHORT       | H1         | TARGET    | STOP        |    1.5 |     -1   |                   -2.5 |               7.2 |                44.1 | False                   | True                      | True                 |
| BARS_AFTER_ACTIVATION:1440 | c0ee1adcb346eaf3c7e53024 | LONG        | H1         | TARGET    | STOP        |    1.5 |     -1   |                   -2.5 |              20.6 |                99.8 | False                   | True                      | True                 |
| BARS_AFTER_ACTIVATION:1440 | c47506b520c5969be32172e3 | SHORT       | H1         | STOP      | TARGET      |   -1   |      1.5 |                    2.5 |              43.7 |                45   | True                    | False                     | False                |
| BARS_AFTER_ACTIVATION:1440 | ce59a92a83d5dc5da249c770 | LONG        | H1         | STOP      | TARGET      |   -1   |      1.5 |                    2.5 |              15.6 |               143.7 | True                    | False                     | False                |
| BARS_AFTER_ACTIVATION:1440 | d235dbdf1db7fde5aa3c23f6 | LONG        | H1         | STOP      | TARGET      |   -1   |      1.5 |                    2.5 |              14.1 |                42.2 | True                    | False                     | False                |
| BARS_AFTER_ACTIVATION:1440 | d242492dd6326c57a795e5d4 | LONG        | H1         | STOP      | TARGET      |   -1   |      1.5 |                    2.5 |              51.4 |               103.1 | True                    | False                     | False                |
| BARS_AFTER_ACTIVATION:1440 | f105f7ceb9afde2a065a6337 | SHORT       | H1         | STOP      | TARGET      |   -1   |      1.5 |                    2.5 |             157.9 |               258.9 | True                    | False                     | False                |
| BARS_AFTER_ACTIVATION:1440 | f5d1f1a385a289fbee74ac65 | LONG        | H1         | STOP      | TARGET      |   -1   |      1.5 |                    2.5 |              66.5 |               228.5 | True                    | False                     | False                |
| BARS_AFTER_ACTIVATION:2880 | 043d80cf1fff7e8444a7cce2 | LONG        | H1         | TARGET    | STOP        |    1.5 |     -1   |                   -2.5 |              39.8 |                77.9 | False                   | True                      | True                 |
| BARS_AFTER_ACTIVATION:2880 | 29b1ca502ec72d82d0b31169 | LONG        | H1         | TARGET    | STOP        |    1.5 |     -1   |                   -2.5 |              22   |               246.5 | False                   | True                      | True                 |
| BARS_AFTER_ACTIVATION:2880 | 3006cd3533f5bb2880b10b4d | LONG        | H4         | STOP      | TARGET      |   -1   |      1.5 |                    2.5 |              29.2 |               143.7 | True                    | False                     | False                |
| BARS_AFTER_ACTIVATION:2880 | 3711c617488c92d9828c70cf | SHORT       | H4         | STOP      | TARGET      |   -1   |      1.5 |                    2.5 |              25.7 |               254.3 | True                    | False                     | False                |
| BARS_AFTER_ACTIVATION:2880 | 41b0c0d1c811e60feabed7db | SHORT       | H4         | STOP      | TARGET      |   -1   |      1.5 |                    2.5 |              26.9 |               231.4 | True                    | False                     | False                |
| BARS_AFTER_ACTIVATION:2880 | 44ea31beeb5dd694163eae90 | LONG        | H1         | TARGET    | STOP        |    1.5 |     -1   |                   -2.5 |              26.8 |               381   | False                   | True                      | True                 |

## Verdict

- Best row by NetR/MeanR: `REFERENCE_LEVEL_HARD_STOP BARS_AFTER_ACTIVATION:1440 NetR=25.034955, MeanR=0.163627`
- No execution-readiness claim. This remains research-only backtest evidence over historical artifacts.
- Research signal: the larger sample is useful because all 153 setups have 5760-bar forward coverage. Treat any apparent performance as provisional until robustness, synthetic-row review, same-bar analysis, and out-of-sample validation are done.
- Current bottleneck indications: `same-bar ambiguity / micro entry timing, stop placement + fixed 1.5R TP interaction`
- Do not claim edge from this matrix alone.

## Files

- `bridge_FAILED_BREAK_RECLAIM_EXTENDED_V1_full_coverage_only/`
- `structural_matrix_all_trades.csv`
- `structural_matrix_summary.csv`
- `structural_matrix_by_direction.csv`
- `structural_matrix_by_source_tf.csv`
- `structural_matrix_synthetic_summary.csv`
- `structural_matrix_synthetic_detail.csv`
- `structural_matrix_expiry_sensitivity.csv`
- `structural_matrix_expiry_sensitivity_summary.csv`
- `structural_matrix_stop_model_comparison.csv`
- `structural_matrix_stop_model_comparison_summary.csv`
- `structural_matrix_manifest.json`