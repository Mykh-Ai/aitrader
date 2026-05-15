# IMPULSE_FADE_RECLAIM_SHORT_V1_LOW_STRESS

Window: `2026-05-13` to `2026-05-14`.

Status: bounded research sidecar only. Baseline Analyzer grammar and Backtester rulesets are unchanged.

## Filter

- `RelVolume_20 <= 1.5`
- `DeltaAbsRatio_20 <= 2.0`
- `OIChangeAbsRatio_20 <= 5.0`
- spike count <= 2 across rel-volume/delta/OI/liquidation context spikes

## Outputs

- Detail CSV: `research/results/impulse_fade_reclaim_short_low_stress_v1_2026-05-13_to_2026-05-14.csv`
- Summary CSV: `research/results/impulse_fade_reclaim_short_low_stress_v1_summary_2026-05-13_to_2026-05-14.csv`

## Summary

| Slice | Trades | Wins | Losses | WinRate | TotalReturnPct | TotalPnl | MaxDrawdownPnl | AvgRelVolume_20 | AvgDeltaAbsRatio_20 | AvgOIChangeAbsRatio_20 | RelSpikeRate | DeltaSpikeRate | OISpikeRate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 14 | 10 | 4 | 0.7142857142857143 | 0.002858436168255668 | 228.97000000000116 | -53.09999999999127 | 1.2297054580874243 | 1.1706839531163598 | 1.207122283579794 | 0.07142857142857142 | 0.35714285714285715 | 0.35714285714285715 |
| low_stress_pass | 10 | 7 | 3 | 0.7 | 0.0020192227640910684 | 162.89499999998952 | -23.719999999986612 | 1.0959517148122795 | 0.7349745580683438 | 1.1294325196851447 | 0.0 | 0.1 | 0.3 |
| low_stress_drop | 4 | 3 | 1 | 0.75 | 0.0008392134041646001 | 66.07500000001164 | 0.0 | 1.5640898162752859 | 2.259957440736401 | 1.401346693316417 | 0.25 | 1.0 | 0.5 |

## Day Split

| Date | CandidateFilterPass | Trades | Wins | Pnl |
| --- | --- | --- | --- | --- |
| 2026-05-13 | False | 4 | 3 | 66.07500000001164 |
| 2026-05-13 | True | 10 | 7 | 162.89499999998952 |

## Research Read

- This is not a promotion decision and not a live strategy.
- Use it as the tracked low-stress candidate on the next valid post-gap days.
- If pass-slice quality persists out of sample, consider formalizing a separate ruleset variant; do not mutate the baseline short grammar from this evidence alone.
