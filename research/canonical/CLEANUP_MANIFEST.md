# CLEANUP_MANIFEST

Date: 2026-05-17
Baseline HEAD: `8f001cf`

## 1. KEEP

| path | reason | action | evidence link | referenced in registry/canonical |
|---|---|---|---|---|
| `research/canonical/` | protected canonical/current candidate evidence | keep in git | Sprint 02-04 canonical layer | yes |
| `research/candidates/CAND_SHORT_CTX_SPIKE_GE2_ENTRY_DELAY_1/` | protected canonical/current candidate evidence | keep in git | Sprint 02-04 canonical layer | yes |
| `research/candidates/CAND_SHORT_IMPULSE_FADE_DEEP_RECLAIM_GT_0_6/` | protected canonical/current candidate evidence | keep in git | Sprint 02-04 canonical layer | yes |
| `research/candidates/CAND_LONG_IMPULSE_FADE_LATE_US_STRUCTURAL/` | protected canonical/current candidate evidence | keep in git | Sprint 02-04 canonical layer | yes |
| `research/candidates/CAND_H4_FAILED_BREAK_RECLAIM_EXTENDED_V1/` | protected canonical/current candidate evidence | keep in git | Sprint 02-04 canonical layer | yes |
| `research/scripts/sprint_03_formal_candidate_rulesets.py` | protected canonical/current candidate evidence | keep in git | Sprint 02-04 canonical layer | yes |
| `research/scripts/sprint_04_holdout_feed_audit.py` | protected canonical/current candidate evidence | keep in git | Sprint 02-04 canonical layer | yes |
| `research/scripts/sprint_04_ctx_holdout_runner.py` | protected canonical/current candidate evidence | keep in git | Sprint 02-04 canonical layer | yes |
| `backtest_runs/sprint_03_candidate_rulesets/sprint_03_pooled_replay_summary.json` | protected canonical/current candidate evidence | keep in git | Sprint 02-04 canonical layer | yes |
| `backtest_runs/sprint_04_ctx_holdout/holdout_summary.json` | protected canonical/current candidate evidence | keep in git | Sprint 02-04 canonical layer | yes |

## 2. DELETE

| path | reason | action | evidence link | referenced in registry/canonical |
|---|---|---|---|---|
| ``__pycache__/`` and nested ``__pycache__/`` | runtime cache; reproducible | delete ignored cache with path-scoped clean | Python runtime generated | no |

## 3. IGNORE

| path | reason | action | evidence link | referenced in registry/canonical |
|---|---|---|---|---|
| ``feed_recovered/`` | local external recovered data mirror, documented by hash manifest | add to .gitignore; do not delete | ``FEED_RECOVERED_MANIFEST.csv`` | yes |
| ``research/findings/IMPULSE_*.md`` / ``research/findings/SHORT_IMPULSE_*.md`` / ``research/findings/LOCAL_H1_*.md`` | sidecar finding reports; some referenced by registry | ignore local archive copies | candidate registry and Sprint 02 snapshot | mixed |
| ``research/results/impulse_*.csv`` / ``research/results/short_impulse_*.csv`` / ``research/results/local_h1_*.csv`` / ``research/results/archive_replay_impulse_*.json`` | sidecar result tables; some referenced by registry | ignore local archive copies | candidate registry and Sprint 02 snapshot | mixed |
| explicit untracked exploratory ``research/scripts/*.py`` listed in .gitignore | sidecar/probe scripts not current Sprint 03/04 runners | ignore, do not delete | Sprint 02 snapshot | mixed |
| explicit untracked sidecar ``tests/*.py`` listed in .gitignore | tests for ignored exploratory scripts; protected from deletion | ignore, do not delete | Sprint 02 snapshot | no |

## 4. ARCHIVE_ONLY

| path | reason | action | evidence link | referenced in registry/canonical |
|---|---|---|---|---|
| `feed_recovered/` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/findings/IMPULSE_FADE_LONG_ENTRY_OBSERVABLE_PROXY_SCAN_2026-03-17_to_2026-05-14.md` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/findings/IMPULSE_FADE_LONG_FORWARD_WATCHLIST_2026-03-17_to_2026-05-14.md` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/findings/IMPULSE_FADE_RECLAIM_SHORT_V1_LOW_STRESS_2026-03-17_to_2026-04-22.md` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/findings/IMPULSE_FADE_RECLAIM_SHORT_V1_LOW_STRESS_2026-05-07_to_2026-05-12.md` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/findings/IMPULSE_FADE_RECLAIM_SHORT_V1_LOW_STRESS_2026-05-08_to_2026-05-12.md` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/findings/IMPULSE_FADE_SHORT_DEEP_RECLAIM_ROBUSTNESS_2026-03-17_to_2026-05-12.md` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/findings/IMPULSE_FADE_SHORT_ENTRY_OBSERVABLE_PROXY_SCAN_2026-03-17_to_2026-05-12.md` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/findings/IMPULSE_FADE_SHORT_FULL_FADE_PROXY_DIAGNOSTIC_2026-03-17_to_2026-05-12.md` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/findings/IMPULSE_FADE_SHORT_REGIME_INTERACTION_2026-03-17_to_2026-05-12.md` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/findings/IMPULSE_LONG_GROWTH_OBSERVABLE_SCAN_2026-03-17_to_2026-05-14.md` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/findings/LOCAL_H1_RECLAIM_SWEEP_EXTREME_STOP_V1_BUFFER50_DIAGNOSTIC_2026-05-05.md` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/findings/LOCAL_H1_RECLAIM_SWEEP_EXTREME_STOP_V1_CLUSTER_PATHOLOGY_2026-05-05.md` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/findings/SHORT_IMPULSE_FADE_CONTEXT_FILTER_2026-05-08_to_2026-05-12.md` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/archive_replay_impulse_short_low_stress_backtest_2026-03-17_to_2026-04-22.json` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/archive_replay_impulse_short_low_stress_prep_2026-03-17_to_2026-04-22.json` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_fade_long_cluster_summary_2026-03-17_to_2026-05-14.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_fade_long_coverage_2026-03-17_to_2026-05-14.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_fade_long_deep_reclaim_threshold_sweep_2026-03-17_to_2026-05-14.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_fade_long_entry_observable_features_2026-03-17_to_2026-05-14.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_fade_long_pnl_concentration_2026-03-17_to_2026-05-14.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_fade_long_proxy_scan_2026-03-17_to_2026-05-14.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_fade_long_proxy_stable_2026-03-17_to_2026-05-14.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_fade_long_watchlist_cluster_summary_2026-03-17_to_2026-05-14.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_fade_long_watchlist_day_split_2026-03-17_to_2026-05-14.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_fade_long_watchlist_pnl_concentration_2026-03-17_to_2026-05-14.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_fade_long_watchlist_summary_2026-03-17_to_2026-05-14.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_fade_long_watchlist_trades_2026-03-17_to_2026-05-14.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_fade_reclaim_short_low_stress_v1_2026-03-17_to_2026-04-22.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_fade_reclaim_short_low_stress_v1_2026-05-07_to_2026-05-12.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_fade_reclaim_short_low_stress_v1_2026-05-08_to_2026-05-12.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_fade_reclaim_short_low_stress_v1_summary_2026-03-17_to_2026-04-22.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_fade_reclaim_short_low_stress_v1_summary_2026-05-07_to_2026-05-12.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_fade_reclaim_short_low_stress_v1_summary_2026-05-08_to_2026-05-12.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_fade_short_deep_reclaim_cluster_detail_2026-03-17_to_2026-05-12.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_fade_short_deep_reclaim_cluster_summary_2026-03-17_to_2026-05-12.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_fade_short_deep_reclaim_pnl_concentration_2026-03-17_to_2026-05-12.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_fade_short_deep_reclaim_split_period_day_2026-03-17_to_2026-05-12.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_fade_short_deep_reclaim_split_period_h2_2026-03-17_to_2026-05-12.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_fade_short_deep_reclaim_split_period_hour_2026-03-17_to_2026-05-12.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_fade_short_deep_reclaim_split_period_spike_2026-03-17_to_2026-05-12.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_fade_short_deep_reclaim_split_period_stress_2026-03-17_to_2026-05-12.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_fade_short_deep_reclaim_threshold_sweep_2026-03-17_to_2026-05-12.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_fade_short_entry_observable_features_2026-03-17_to_2026-05-12.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_fade_short_entry_observable_proxy_scan_2026-03-17_to_2026-05-12.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_fade_short_entry_observable_proxy_stable_2026-03-17_to_2026-05-12.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_fade_short_full_fade_proxy_candidates_2026-03-17_to_2026-05-12.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_fade_short_full_fade_proxy_stable_candidates_2026-03-17_to_2026-05-12.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_fade_short_regime_interaction_by_day_stress_2026-03-17_to_2026-05-12.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_fade_short_regime_interaction_by_period_h2_12_stress_2026-03-17_to_2026-05-12.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_fade_short_regime_interaction_by_period_h2_6_stress_2026-03-17_to_2026-05-12.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_fade_short_regime_interaction_by_period_regime_stress_2026-03-17_to_2026-05-12.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_fade_short_regime_interaction_by_period_spike_signature_2026-03-17_to_2026-05-12.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_fade_short_regime_interaction_by_period_stress_2026-03-17_to_2026-05-12.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_fade_short_regime_interaction_trades_2026-03-17_to_2026-05-12.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_long_growth_cluster_summary_2026-03-17_to_2026-05-14.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_long_growth_coverage_2026-03-17_to_2026-05-14.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_long_growth_observable_features_2026-03-17_to_2026-05-14.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_long_growth_proxy_scan_2026-03-17_to_2026-05-14.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_long_growth_proxy_stable_2026-03-17_to_2026-05-14.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/impulse_long_growth_return_concentration_2026-03-17_to_2026-05-14.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/local_h1_reclaim_sweep_extreme_stop_v1_buffer50_2026-03-12_to_2026-05-04.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/short_impulse_fade_context_filter_2026-05-08_to_2026-05-12.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/results/short_impulse_fade_context_filter_summary_2026-05-08_to_2026-05-12.csv` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/scripts/impulse_fade_long_entry_observable_proxy_scan.py` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/scripts/impulse_fade_long_forward_watchlist.py` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/scripts/impulse_fade_reclaim_short_low_stress_v1.py` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/scripts/impulse_long_growth_observable_scan.py` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `research/scripts/local_h1_reclaim_sweep_extreme_stop_v1.py` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `tests/test_impulse_fade_reclaim_short_low_stress_v1.py` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |
| `tests/test_local_h1_reclaim_sweep_extreme_stop_v1.py` | local archive/sidecar artifact; no git commit in Sprint 05 | keep on disk and ignore | `CLEANUP_BASELINE_STATUS.md` | yes |

## 5. NEEDS_FUTURE_REVIEW

| path | reason | action | evidence link | referenced in registry/canonical |
|---|---|---|---|---|
| sidecar ``research/findings`` and ``research/results`` families | may deserve external archive bundle or canonical promotion later | review only after active holdout cycle is stable | this manifest | mixed |
| ignored exploratory ``tests`` files | may be promoted if the matching research scripts become official | review before deletion or tracking | this manifest | no |
