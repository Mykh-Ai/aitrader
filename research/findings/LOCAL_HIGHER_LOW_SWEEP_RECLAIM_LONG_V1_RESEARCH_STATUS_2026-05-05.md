# LOCAL_HIGHER_LOW_SWEEP_RECLAIM_LONG_V1 Research Status

Date: 2026-05-05

Status: `DIAGNOSTIC_SURFACE_CONFIRMED_BUT_NOT_VALIDATED`

This note consolidates the recent standalone diagnostic work for `LOCAL_HIGHER_LOW_SWEEP_RECLAIM_LONG_V1`. It is research status only: no Backtester run, no old `FAILED_BREAK_RECLAIM` detector run, no Analyzer canonical behavior change, and no FIELD/live claims.

## Frozen Diagnostic Contract

- Direction: LONG only.
- Level family: `LOCAL_HIGHER_LOW_SWEEP` only.
- Selected level: local confirmed H4 higher low.
- Prior major low over 30 H4 bars must remain unswept.
- Sweep: H4 Low below the local higher-low level.
- Reclaim: H4 Close above the local level, with the sweep candle excluded and a maximum 3 H4 candle reclaim window.
- Entry: reclaim H4 close timestamp and close price.
- Stop: sweep extreme low minus 50 USD.
- Max risk: 1500 USD.
- No buffer compression.
- Cluster-first counting: only the first allowed candidate in the same-direction impulse cluster counts; later rows are duplicate_same_move.

## Evidence Summary

The local higher-low long surface remains interesting after cluster deduplication, but it is not validated.

Full-range diagnostic over `2026-03-12_to_2026-05-04`:

- Full-range candidates: 15.
- Allowed candidates: 13.
- Unique clusters: 8.
- Retained cluster-first rows: 7.
- Duplicate rows removed: 6.
- Incomplete forward-window rows: 0.
- Median risk: 983.0000.
- Median MFE_R: 2.2077.
- Median net_MFE_R: 1.6898.
- Hit 1.5R / 2R / 3R / 5R / 10R: 5/7, 4/7, 3/7, 1/7, 1/7.
- Candidates after 2026-05-02: 0.

Subperiod split:

- `2026-03-12_to_2026-03-29`: 2 candidates, 1 retained, weak expansion.
- `2026-03-30_to_2026-05-02`: 13 candidates, 6 retained, main discovery evidence.
- `2026-05-03_to_2026-05-04`: 0 candidates.

OOS diagnostic:

- Nearest later complete window `2026-05-03_to_2026-05-04` produced no entry-window candidates.
- Earlier non-overlapping window `2026-03-22_to_2026-03-29` produced 1 retained candidate with weak expansion.
- Verdict: `INCONCLUSIVE`.

Cluster quality audit:

- `FIRST_IS_BEST`: 4 clusters.
- `FIRST_IS_ACCEPTABLE`: 1 cluster.
- `LATER_IS_MUCH_BETTER`: 1 cluster.
- `CLUSTER_WEAK`: 1 cluster.
- `INVALID_TECH_ARTIFACT`: 1 cluster.

The cluster-first rule is conservative and prevents inflated row-level results, but it can miss later stronger duplicate candidates inside the same impulse.

Quality-score diagnostic:

- Baseline cluster-first: 7 retained, median MFE_R 2.2077, median net_MFE_R 1.6898.
- `quality_score >= 3`: unchanged versus baseline.
- `quality_score >= 4`: 6 retained, median MFE_R 2.7090, median net_MFE_R 2.3725; removes the weak `FR02` cluster and does not remove a good cluster in this small sample.
- This is not enough evidence to promote a score gate.

## Key Strength

`LOCAL_HIGHER_LOW_SWEEP_RECLAIM_LONG_V1` remains an interesting diagnostic surface after cluster deduplication. The discovery-window cluster-first evidence still shows meaningful expansion after removing duplicate row inflation.

## Key Weakness

The sample is small, OOS is not validated, and the cluster-first rule can miss later better candidates in the same impulse. The available post-discovery complete feed currently has too little data to validate persistence.

## Status

`DIAGNOSTIC_SURFACE_CONFIRMED_BUT_NOT_VALIDATED`

No ruleset promotion. No Backtester/FIELD/live claims.

## Next Evidence Requirement

Minimum evidence before ruleset draft discussion:

- At least 20 retained cluster-first candidates under the frozen contract.
- More complete post-discovery data.
- No tuning of buffer, score, cluster rule, or thresholds before that evidence exists.

## Canonical Supporting Notes

- `research/findings/LOCAL_H4_RECLAIM_SWEEP_EXTREME_STOP_V1_BUFFER50_DIAGNOSTIC_2026-05-05.md`
- `research/findings/LOCAL_H4_RECLAIM_BUFFER50_LOCAL_FAMILY_MANUAL_REVIEW_2026-05-05.md`
- `research/findings/LOCAL_H4_RECLAIM_BUFFER50_R_SIZE_EXPANSION_EXPECTANCY_AUDIT_2026-05-05.md`
- `research/findings/LOCAL_HIGHER_LOW_SWEEP_LONG_CONTEXT_AUDIT_2026-05-05.md`
- `research/findings/LOCAL_HIGHER_LOW_SWEEP_RECLAIM_CLUSTER_DEDUP_2026-05-05.md`
- `research/findings/LOCAL_HIGHER_LOW_SWEEP_RECLAIM_LONG_V1_OOS_DIAGNOSTIC_2026-03-22_to_2026-03-29.md`
- `research/findings/LOCAL_HIGHER_LOW_SWEEP_RECLAIM_LONG_V1_FULL_RANGE_2026-03-12_to_2026-05-04.md`
- `research/findings/LOCAL_HIGHER_LOW_SWEEP_RECLAIM_LONG_V1_CLUSTER_QUALITY_AUDIT_2026-05-05.md`
- `research/findings/LOCAL_HIGHER_LOW_SWEEP_RECLAIM_LONG_V1_QUALITY_SCORE_DIAGNOSTIC_2026-05-05.md`

