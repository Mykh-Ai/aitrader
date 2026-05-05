# LOCAL_HIGHER_LOW_SWEEP_RECLAIM_LONG_V1 Cluster Quality Audit

Date: 2026-05-05

Scope: audit of the full-range diagnostic CSV only. This does not run the Backtester, does not run the old `FAILED_BREAK_RECLAIM` detector, does not change detector logic, and makes no FIELD/live claims.

Input: `research/results/local_higher_low_sweep_reclaim_long_v1_full_range_2026-03-12_to_2026-05-04.csv`.

## Method

- Clusters are the existing same-direction impulse clusters from the full-range diagnostic.
- `first_allowed_candidate` is the first row in the cluster with `diagnostic_trade_allowed=true`.
- Best rows are selected only among allowed candidates.
- `MFE_R_lost_by_first_rule = best_candidate_MFE_R - first_candidate_MFE_R`.
- Reclaim body percentage is computed from the H4 reclaim candle as `abs(close-open)/(high-low)` using complete local feed `2026-03-12..2026-05-04`.

## Classification Counts

| classification | cluster_count |
| --- | --- |
| FIRST_IS_BEST | 4 |
| INVALID_TECH_ARTIFACT | 1 |
| CLUSTER_WEAK | 1 |
| LATER_IS_MUCH_BETTER | 1 |
| FIRST_IS_ACCEPTABLE | 1 |

## Cluster Comparison

| cluster_id | candidate_rows | first_allowed_candidate | best_MFE_R_candidate | best_net_MFE_R_candidate | earliest_hit_1_5R_candidate | earliest_hit_3R_candidate | first_candidate_MFE_R | best_candidate_MFE_R | MFE_R_lost_by_first_rule | first_candidate_reclaim_body_pct | best_candidate_reclaim_body_pct | first_candidate_risk | best_candidate_risk | first_candidate_entry_ts | best_candidate_entry_ts | cluster_classification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FR01 | 1 |  |  |  |  |  |  |  |  |  |  |  |  |  |  | INVALID_TECH_ARTIFACT |
| FR02 | 2 | row 2 (2026-03-25 00:00:00+00:00) | row 2 (2026-03-25 00:00:00+00:00) | row 2 (2026-03-25 00:00:00+00:00) |  |  | 1.3344 | 1.3344 | 0.0000 | 0.7660 | 0.7660 | 1106.1000 | 1106.1000 | 2026-03-25 00:00:00+00:00 | 2026-03-25 00:00:00+00:00 | CLUSTER_WEAK |
| FR03 | 3, 4 | row 3 (2026-03-30 04:00:00+00:00) | row 4 (2026-03-31 16:00:00+00:00) | row 4 (2026-03-31 16:00:00+00:00) | row 4 (2026-03-31 16:00:00+00:00) | row 4 (2026-03-31 16:00:00+00:00) | 1.1486 | 3.1872 | 2.0386 | 0.6697 | 0.0342 | 1077.9000 | 812.0000 | 2026-03-30 04:00:00+00:00 | 2026-03-31 16:00:00+00:00 | LATER_IS_MUCH_BETTER |
| FR04 | 5 | row 5 (2026-04-05 12:00:00+00:00) | row 5 (2026-04-05 12:00:00+00:00) | row 5 (2026-04-05 12:00:00+00:00) | row 5 (2026-04-05 12:00:00+00:00) | row 5 (2026-04-05 12:00:00+00:00) | 13.1614 | 13.1614 | 0.0000 | 0.5284 | 0.5284 | 447.2000 | 447.2000 | 2026-04-05 12:00:00+00:00 | 2026-04-05 12:00:00+00:00 | FIRST_IS_BEST |
| FR05 | 6, 7, 8, 9, 10 | row 6 (2026-04-07 20:00:00+00:00) | row 10 (2026-04-13 04:00:00+00:00) | row 10 (2026-04-13 04:00:00+00:00) | row 6 (2026-04-07 20:00:00+00:00) | row 6 (2026-04-07 20:00:00+00:00) | 4.8324 | 9.4376 | 4.6052 | 0.8219 | 0.3483 | 992.8000 | 536.6000 | 2026-04-07 20:00:00+00:00 | 2026-04-13 04:00:00+00:00 | FIRST_IS_ACCEPTABLE |
| FR06 | 11, 12 | row 11 (2026-04-15 12:00:00+00:00) | row 11 (2026-04-15 12:00:00+00:00) | row 11 (2026-04-15 12:00:00+00:00) | row 11 (2026-04-15 12:00:00+00:00) |  | 1.6807 | 1.6807 | 0.0000 | 0.7659 | 0.7659 | 756.0000 | 756.0000 | 2026-04-15 12:00:00+00:00 | 2026-04-15 12:00:00+00:00 | FIRST_IS_BEST |
| FR07 | 13 | row 13 (2026-04-19 12:00:00+00:00) | row 13 (2026-04-19 12:00:00+00:00) | row 13 (2026-04-19 12:00:00+00:00) | row 13 (2026-04-19 12:00:00+00:00) |  | 2.2077 | 2.2077 | 0.0000 | 0.4826 | 0.4826 | 291.8000 | 291.8000 | 2026-04-19 12:00:00+00:00 | 2026-04-19 12:00:00+00:00 | FIRST_IS_BEST |
| FR08 | 14, 15 | row 14 (2026-04-22 00:00:00+00:00) | row 14 (2026-04-22 00:00:00+00:00) | row 14 (2026-04-22 00:00:00+00:00) | row 14 (2026-04-22 00:00:00+00:00) | row 14 (2026-04-22 00:00:00+00:00) | 3.2104 | 3.2104 | 0.0000 | 0.8937 | 0.8937 | 983.0000 | 983.0000 | 2026-04-22 00:00:00+00:00 | 2026-04-22 00:00:00+00:00 | FIRST_IS_BEST |

## Candidate Lists By Cluster

| cluster_id | all_candidates |
| --- | --- |
| FR01 | row 1 reject_not_valid entry=2026-03-15 16:00:00+00:00 MFE_R= net= risk=71494.4 body_pct=0.6133 |
| FR02 | row 2 keep_cluster_first entry=2026-03-25 00:00:00+00:00 MFE_R=1.3344 net=1.2069 risk=1106.1 body_pct=0.766 |
| FR03 | row 3 keep_cluster_first entry=2026-03-30 04:00:00+00:00 MFE_R=1.1486 net=1.024 risk=1077.9 body_pct=0.6697; row 4 duplicate_same_move entry=2026-03-31 16:00:00+00:00 MFE_R=3.1872 net=3.0229 risk=812.0 body_pct=0.0342 |
| FR04 | row 5 keep_cluster_first entry=2026-04-05 12:00:00+00:00 MFE_R=13.1614 net=12.8619 risk=447.2 body_pct=0.5284 |
| FR05 | row 6 keep_cluster_first entry=2026-04-07 20:00:00+00:00 MFE_R=4.8324 net=4.6934 risk=992.8 body_pct=0.8219; row 7 duplicate_same_move entry=2026-04-09 08:00:00+00:00 MFE_R=4.9884 net=4.7381 risk=567.0 body_pct=0.0384; row 8 duplicate_same_move entry=2026-04-10 12:00:00+00:00 MFE_R=2.2114 net=2.0217 risk=760.2 body_pct=0.7567; row 9 duplicate_same_move entry=2026-04-11 20:00:00+00:00 MFE_R=0.0105 net=-0.1088 risk=1233.9 body_pct=0.8202; row 10 duplicate_same_move entry=2026-04-13 04:00:00+00:00 MFE_R=9.4376 net=9.1731 risk=536.6 body_pct=0.3483 |
| FR06 | row 11 keep_cluster_first entry=2026-04-15 12:00:00+00:00 MFE_R=1.6807 net=1.4845 risk=756.0 body_pct=0.7659; row 12 duplicate_same_move entry=2026-04-16 16:00:00+00:00 MFE_R=0.5012 net=0.1922 risk=483.2 body_pct=0.076 |
| FR07 | row 13 keep_cluster_first entry=2026-04-19 12:00:00+00:00 MFE_R=2.2077 net=1.6898 risk=291.8 body_pct=0.4826 |
| FR08 | row 14 keep_cluster_first entry=2026-04-22 00:00:00+00:00 MFE_R=3.2104 net=3.0552 risk=983.0 body_pct=0.8937; row 15 reject_not_valid entry=2026-04-23 16:00:00+00:00 MFE_R= net= risk=1874.6 body_pct=0.5126 |

## Interpretation

| cluster_id | cluster_classification | interpretation |
| --- | --- | --- |
| FR01 | INVALID_TECH_ARTIFACT | Invalid/rejected technical artifact; no allowed first candidate contributes to evidence. |
| FR02 | CLUSTER_WEAK | First candidate is weak and cluster has no later candidate strong enough to justify counting the impulse as a success. |
| FR03 | LATER_IS_MUCH_BETTER | Cluster-first rule loses 2.04R versus the best later duplicate; first rule is conservative here. |
| FR04 | FIRST_IS_BEST | First allowed candidate is also the best MFE candidate. |
| FR05 | FIRST_IS_ACCEPTABLE | Later row may improve MFE by 4.61R, but the first candidate already captures meaningful expansion. |
| FR06 | FIRST_IS_BEST | First allowed candidate is also the best MFE candidate. |
| FR07 | FIRST_IS_BEST | First allowed candidate is also the best MFE candidate. |
| FR08 | FIRST_IS_BEST | First allowed candidate is also the best MFE candidate. |

## Verdict

- Cluster-first counting is conservative and prevents inflated row-level results.
- One cluster (`FR03`) shows a materially better later candidate, meaning the first-only rule can understate expansion when the earliest reclaim is weak.
- The strongest discovery cluster (`FR05`) still has a strong first candidate even though later duplicates include higher MFE; this supports keeping cluster-first as the default anti-duplication rule instead of selecting hindsight-best rows.
- No ruleset promotion is made from this audit.
