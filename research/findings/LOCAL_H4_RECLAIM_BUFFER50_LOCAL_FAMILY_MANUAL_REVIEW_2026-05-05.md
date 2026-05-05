# LOCAL H4 Reclaim Buffer50 Local-Family Manual Review

Date: 2026-05-05

Status: manual/clustering audit for research diagnostics only. Not FIELD, not live strategy, not execution-ready evidence.

Scope is limited to `LOCAL_LOWER_HIGH_SWEEP` and `LOCAL_HIGHER_LOW_SWEEP` from `LOCAL_H4_RECLAIM_SWEEP_EXTREME_STOP_V1_BUFFER50`. This audit does not run the Backtester and does not run the old `FAILED_BREAK_RECLAIM` detector.

## Clustering Rule

- Same-direction entries within 24h are clustered.
- Same-direction entries within 48h are also clustered when the later entry is already a favorable continuation of at least 0.5R from the prior entry, approximating the same directional impulse.
- `recommend_first_candidate_only=yes` means the cluster should be counted as one setup family observation unless a later formal contract explicitly allows repeat entries.

## Summary

- Local candidates reviewed: 20
- Unique clusters: 12
- Duplicate candidates inside multi-row clusters: 13
- First-candidate-only allowed count: 12
- First-candidate-only hit_2R count: 8
- Review CSV: `research/results/local_h4_reclaim_buffer50_local_family_manual_review_2026-05-05.csv`

## Quality By Local Family

| level_family | candidate_count | allowed_count | unique_clusters | duplicate_candidates | hit_1R | hit_1_5R | hit_2R |
| --- | --- | --- | --- | --- | --- | --- | --- |
| LOCAL_HIGHER_LOW_SWEEP | 13 | 12 | 8 | 8 | 10 | 9 | 8 |
| LOCAL_LOWER_HIGH_SWEEP | 7 | 7 | 4 | 5 | 5 | 4 | 3 |

## Manual Classification Counts

| level_family | manual_classification | count |
| --- | --- | --- |
| LOCAL_HIGHER_LOW_SWEEP | clean_reclaim | 5 |
| LOCAL_HIGHER_LOW_SWEEP | duplicate_same_move | 4 |
| LOCAL_HIGHER_LOW_SWEEP | good_boundary_case | 1 |
| LOCAL_HIGHER_LOW_SWEEP | late_signal | 1 |
| LOCAL_HIGHER_LOW_SWEEP | noisy_chop | 1 |
| LOCAL_HIGHER_LOW_SWEEP | risk_too_large | 1 |
| LOCAL_LOWER_HIGH_SWEEP | duplicate_same_move | 3 |
| LOCAL_LOWER_HIGH_SWEEP | good_boundary_case | 2 |
| LOCAL_LOWER_HIGH_SWEEP | late_signal | 1 |
| LOCAL_LOWER_HIGH_SWEEP | noisy_chop | 1 |

## Clusters

| cluster_id | direction | rows | first_entry | last_entry | size | families | classifications |
| --- | --- | --- | --- | --- | --- | --- | --- |
| L01 | LONG | 1 | 2026-03-30 04:00:00+0000 | 2026-03-30 04:00:00+0000 | 1 | LOCAL_HIGHER_LOW_SWEEP | late_signal |
| L02 | LONG | 3 | 2026-03-31 16:00:00+0000 | 2026-03-31 16:00:00+0000 | 1 | LOCAL_HIGHER_LOW_SWEEP | clean_reclaim |
| L03 | LONG | 7 | 2026-04-05 12:00:00+0000 | 2026-04-05 12:00:00+0000 | 1 | LOCAL_HIGHER_LOW_SWEEP | clean_reclaim |
| L04 | LONG | 10,11,13,15 | 2026-04-07 20:00:00+0000 | 2026-04-11 20:00:00+0000 | 4 | LOCAL_HIGHER_LOW_SWEEP | clean_reclaim,duplicate_same_move |
| L05 | LONG | 17 | 2026-04-13 04:00:00+0000 | 2026-04-13 04:00:00+0000 | 1 | LOCAL_HIGHER_LOW_SWEEP | clean_reclaim |
| L06 | LONG | 20,22 | 2026-04-15 12:00:00+0000 | 2026-04-16 16:00:00+0000 | 2 | LOCAL_HIGHER_LOW_SWEEP | duplicate_same_move,noisy_chop |
| L07 | LONG | 23 | 2026-04-19 12:00:00+0000 | 2026-04-19 12:00:00+0000 | 1 | LOCAL_HIGHER_LOW_SWEEP | good_boundary_case |
| L08 | LONG | 25,26 | 2026-04-22 00:00:00+0000 | 2026-04-23 16:00:00+0000 | 2 | LOCAL_HIGHER_LOW_SWEEP | clean_reclaim,risk_too_large |
| S01 | SHORT | 2,4,5 | 2026-03-31 08:00:00+0000 | 2026-04-01 20:00:00+0000 | 3 | LOCAL_LOWER_HIGH_SWEEP | duplicate_same_move,late_signal |
| S02 | SHORT | 6,8 | 2026-04-04 20:00:00+0000 | 2026-04-05 20:00:00+0000 | 2 | LOCAL_LOWER_HIGH_SWEEP | duplicate_same_move,good_boundary_case |
| S03 | SHORT | 21 | 2026-04-16 08:00:00+0000 | 2026-04-16 08:00:00+0000 | 1 | LOCAL_LOWER_HIGH_SWEEP | good_boundary_case |
| S04 | SHORT | 24 | 2026-04-21 16:00:00+0000 | 2026-04-21 16:00:00+0000 | 1 | LOCAL_LOWER_HIGH_SWEEP | noisy_chop |

## Best Examples

| row_number | direction | entry_ts | level_family | cluster_id | manual_classification | final_risk_usd | hit_1R_before_stop | hit_1_5R_before_stop | hit_2R_before_stop | time_to_2R | post_entry_resweep_yes_no |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 7 | LONG | 2026-04-05 12:00:00+0000 | LOCAL_HIGHER_LOW_SWEEP | L03 | clean_reclaim | 447.1999999999971 | True | True | True | 10.73 | no |
| 17 | LONG | 2026-04-13 04:00:00+0000 | LOCAL_HIGHER_LOW_SWEEP | L05 | clean_reclaim | 536.6000000000058 | True | True | True | 10.77 | no |
| 3 | LONG | 2026-03-31 16:00:00+0000 | LOCAL_HIGHER_LOW_SWEEP | L02 | clean_reclaim | 812.0 | True | True | True | 1.23 | no |
| 23 | LONG | 2026-04-19 12:00:00+0000 | LOCAL_HIGHER_LOW_SWEEP | L07 | good_boundary_case | 291.8000000000029 | True | True | True | 1.35 | yes |
| 21 | SHORT | 2026-04-16 08:00:00+0000 | LOCAL_LOWER_HIGH_SWEEP | S03 | good_boundary_case | 622.3000000000029 | True | True | True | 5.9 | yes |

## Failure Modes

| manual_classification | count |
| --- | --- |
| clean_reclaim | 5 |
| duplicate_same_move | 7 |
| good_boundary_case | 3 |
| late_signal | 2 |
| noisy_chop | 2 |
| risk_too_large | 1 |

## LOCAL_LOWER_HIGH_SWEEP Quality

- Rows: 7, unique clusters: 4, duplicate candidates: 5.
- Hit profile: 1R=5, 1.5R=4, 2R=3.
- Quality is mixed: several rows participate in repeated same-direction clusters, and at least one short cluster is more likely a single move being re-sampled than independent setup evidence.

## LOCAL_HIGHER_LOW_SWEEP Quality

- Rows: 13, unique clusters: 8, duplicate candidates: 8.
- Hit profile: 1R=10, 1.5R=9, 2R=8.
- The raw hit profile is strong, but much of the strength is clustered inside recurring long continuation/pullback sequences rather than clean independent reversals.

## Verdict

- The local family is not dead, but the strong-looking row-level diagnostic is inflated by clustered repeated signals.
- It should not be pooled with main structural H4 reclaim evidence.
- A formal ruleset draft is premature until the next diagnostic freezes cluster de-duplication, probably first-candidate-only per same-direction impulse, and separately reviews clean examples vs continuation duplicates.
- Best next research surface: local family with explicit cluster de-duplication and no repeat entries inside the same directional impulse.