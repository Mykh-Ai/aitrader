# LOCAL_HIGHER_LOW_SWEEP_RECLAIM_LONG_V1 OOS Diagnostic

Date: 2026-05-05

Status: standalone diagnostic research only. This run does not use the old `FAILED_BREAK_RECLAIM` detector, does not run the Backtester, does not change Analyzer behavior, and makes no FIELD/live claims.

## Frozen Contract

- Direction: LONG only.
- Level family: `LOCAL_HIGHER_LOW_SWEEP` only.
- Selected level: local confirmed H4 higher low; prior major low over 30 H4 bars must remain unswept.
- Sweep/reclaim: H4 low sweeps local level, sweep candle excluded, reclaim close above level within max 3 H4 candles.
- Entry: reclaim H4 close timestamp and price.
- Stop: sweep extreme low minus 50 USD; max risk 1500 USD; no buffer compression.
- Cluster rule: conservative 48h same-direction cluster, count only first allowed candidate per cluster.

## Window Selection

- Discovery window remains `2026-03-30_to_2026-05-02` and was not relabeled as OOS.
- Nearest later non-overlap feed window `2026-05-03_to_2026-05-04` was checked first and had zero entry-window candidates; today `2026-05-05` was intentionally not fetched because it is incomplete.
- Earlier non-overlap candidate window used here: `2026-03-22_to_2026-03-29`. Limitation: path diagnostics use available future feed after the entry window, which calendar-overlaps the later discovery period for forward outcomes.

## Summary

| metric | value |
| --- | --- |
| OOS entry window | 2026-03-22_to_2026-03-29 |
| later nearest window check | 2026-05-03_to_2026-05-04 had 0 entry-window candidates |
| raw LOCAL_HIGHER_LOW_SWEEP LONG candidates | 1 |
| allowed candidates | 1 |
| unique clusters | 1 |
| retained cluster-first candidates | 1 |
| median risk | 1106.1000 |
| median MFE_R | 1.3344 |
| median MFE_usd | 1476.0000 |
| median net_MFE_R | 1.2069 |
| hit 1.5R / 2R / 3R / 5R / 10R | 0/1, 0/1, 0/1, 0/1, 0/1 |
| verdict | INCONCLUSIVE |

## Retained / Candidate Rows

| row_number | cluster_id | entry_ts | level_price | prior_major_low_30h4 | sweep_extreme_price | entry_price | stop_price | final_risk_usd | MFE_R | net_MFE_R | hit_1_5R | hit_2R | hit_3R | hit_5R | hit_10R | first_stop_touch_ts | time_to_1_5R | time_to_3R | duplicate_count_in_cluster | keep_or_duplicate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | OOS01 | 2026-03-25 00:00:00+00:00 | 70075.5000 | 67300.0000 | 69467.8000 | 70523.9000 | 69417.8000 | 1106.1000 | 1.3344 | 1.2069 | False | False | False | False | False | 2026-03-26 09:34:00+00:00 |  |  | 0 | keep_cluster_first |

## Discovery Comparison

- Discovery retained cluster-first candidates: 8.
- Discovery median MFE_R: 3.1988.
- Discovery hit 3R: 5/8.
- Discovery hit 5R: 2/8.
- Discovery hit 10R: 1/8.

## Verdict

`INCONCLUSIVE`: Sample is too small for a stable OOS read: one pre-discovery retained cluster-first candidate, and the nearest later window had zero entry-window candidates.

This does not reject the local higher-low surface, but it also does not validate persistence. A real OOS decision needs more post-discovery complete feed days or a clean earlier historical window with enough candidates and non-overlapping forward evaluation.

## Files

- CSV: `research/results/local_higher_low_sweep_reclaim_long_v1_oos_diagnostic_2026-03-22_to_2026-03-29.csv`
- Report: `research/findings/LOCAL_HIGHER_LOW_SWEEP_RECLAIM_LONG_V1_OOS_DIAGNOSTIC_2026-03-22_to_2026-03-29.md`
