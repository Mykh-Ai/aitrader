# LOCAL_HIGHER_LOW_SWEEP_RECLAIM_LONG_V1 Quality Score Diagnostic

Date: 2026-05-05

Scope: diagnostic audit only. This does not run the Backtester, does not run the old `FAILED_BREAK_RECLAIM` detector, does not change detector logic, does not select hindsight-best candidates, and makes no FIELD/live claims.

Inputs:

- `research/results/local_higher_low_sweep_reclaim_long_v1_full_range_2026-03-12_to_2026-05-04.csv`
- `research/findings/LOCAL_HIGHER_LOW_SWEEP_RECLAIM_LONG_V1_CLUSTER_QUALITY_AUDIT_2026-05-05.md`

## Feature Definitions

- Features are calculated only for allowed candidates using pre-entry / entry-time data.
- `cluster_position_index` is the allowed-candidate order inside the existing impulse cluster.
- `prior_6h4_drift` and `prior_12h4_drift` are reclaim H4 close minus H4 close 6/12 H4 bars earlier.
- `reclaim_number` is the H4 bar distance from sweep candle open to reclaim candle open; the sweep candle is excluded.

## Fixed Quality Score

- `+1` bullish reclaim candle.
- `+1` reclaim close distance above level greater than sweep depth.
- `+1` risk between 300 and 1000 USD.
- `+1` local level at least 500 USD above prior major low.
- `+1` reclaim number <= 2.
- `-1` risk > 1500 USD.
- `-1` cluster position index > 1.

Weights were not tuned after outcome inspection.

## Scenario Comparison

| scenario | retained_count | median_MFE_R | median_net_MFE_R | hit_1_5R | hit_2R | hit_3R | hit_5R | hit_10R | weak_clusters_removed | good_clusters_accidentally_removed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all_cluster_first_baseline | 7 | 2.2077 | 1.6898 | 5/7 | 4/7 | 3/7 | 1/7 | 1/7 |  |  |
| cluster_first_quality_score_ge_3 | 7 | 2.2077 | 1.6898 | 5/7 | 4/7 | 3/7 | 1/7 | 1/7 |  |  |
| cluster_first_quality_score_ge_4 | 6 | 2.7090 | 2.3725 | 5/6 | 4/6 | 3/6 | 1/6 | 1/6 | FR02/row2 |  |

## Allowed Candidate Score Distribution

| quality_score | allowed_candidate_count |
| --- | --- |
| 3 | 3 |
| 4 | 6 |
| 5 | 4 |

## Cluster-First Rows With Scores

| row_number | cluster_id | cluster_classification | quality_score | entry_ts | final_risk_usd | reclaim_candle_bullish | reclaim_body_pct | reclaim_close_distance_above_level | sweep_depth | local_level_distance_above_major_low | reclaim_number | cluster_position_index | MFE_R | net_MFE_R | hit_1_5R | hit_2R | hit_3R | hit_5R | hit_10R |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | FR02 | CLUSTER_WEAK | 3 | 2026-03-25 00:00:00+00:00 | 1106.1000 | True | 0.7660 | 448.4000 | 607.7000 | 2775.5000 | 2 | 1 | 1.3344 | 1.2069 | False | False | False | False | False |
| 3 | FR03 | LATER_IS_MUCH_BETTER | 4 | 2026-03-30 04:00:00+00:00 | 1077.9000 | True | 0.6697 | 905.3000 | 122.6000 | 732.6000 | 2 | 1 | 1.1486 | 1.0240 | False | False | False | False | False |
| 5 | FR04 | FIRST_IS_BEST | 5 | 2026-04-05 12:00:00+00:00 | 447.2000 | True | 0.5284 | 227.2000 | 170.0000 | 1069.4000 | 1 | 1 | 13.1614 | 12.8619 | True | True | True | True | True |
| 6 | FR05 | FIRST_IS_ACCEPTABLE | 5 | 2026-04-07 20:00:00+00:00 | 992.8000 | True | 0.8219 | 748.3000 | 194.5000 | 2551.4000 | 2 | 1 | 4.8324 | 4.6934 | True | True | True | False | False |
| 11 | FR06 | FIRST_IS_BEST | 5 | 2026-04-15 12:00:00+00:00 | 756.0000 | True | 0.7659 | 388.2000 | 317.8000 | 3308.6000 | 1 | 1 | 1.6807 | 1.4845 | True | False | False | False | False |
| 13 | FR07 | FIRST_IS_BEST | 4 | 2026-04-19 12:00:00+00:00 | 291.8000 | True | 0.4826 | 159.9000 | 81.9000 | 2139.1000 | 2 | 1 | 2.2077 | 1.6898 | True | True | False | False | False |
| 14 | FR08 | FIRST_IS_BEST | 5 | 2026-04-22 00:00:00+00:00 | 983.0000 | True | 0.8937 | 855.1000 | 77.9000 | 2176.3000 | 2 | 1 | 3.2104 | 3.0552 | True | True | True | False | False |

## Interpretation

- `quality_score >= 3` does not filter any cluster-first rows in this sample, so it does not improve selection.
- `quality_score >= 4` removes the weak pre-discovery cluster `FR02` and does not remove any cluster classified as good in the cluster-quality audit.
- The score is useful as a diagnostic lens, but it should not replace the frozen cluster-first rule without more data. This result is based on only seven cluster-first rows, and the threshold behavior can change sharply around fixed score cutoffs.

## Verdict

- Non-hindsight scoring can filter one weak cluster at `quality_score >= 4`, but this is not enough sample to promote a score gate.
- No ruleset promotion and no parameter tuning from this result.

## Files

- CSV: `research/results/local_higher_low_sweep_reclaim_long_v1_quality_score_2026-05-05.csv`
- Report: `research/findings/LOCAL_HIGHER_LOW_SWEEP_RECLAIM_LONG_V1_QUALITY_SCORE_DIAGNOSTIC_2026-05-05.md`
