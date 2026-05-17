# CLEANUP_BASELINE_STATUS

Date: 2026-05-17
HEAD before cleanup: `8f001cf`

## git log --oneline -5

```text
8f001cf Sprint 04 holdout feed audit and CTX runner
887e212 Start holdout tracking after Sprint 03 freeze
23d1cc3 Sprint 03 formal candidate rulesets and holdout protocol
3086f8f Sprint 02 recovered validation and canonical state
d38c463 Record 2026-05-15 research cycle
```

## git status --short before cleanup

```text
?? feed_recovered/
?? research/findings/IMPULSE_FADE_LONG_ENTRY_OBSERVABLE_PROXY_SCAN_2026-03-17_to_2026-05-14.md
?? research/findings/IMPULSE_FADE_LONG_FORWARD_WATCHLIST_2026-03-17_to_2026-05-14.md
?? research/findings/IMPULSE_FADE_RECLAIM_SHORT_V1_LOW_STRESS_2026-03-17_to_2026-04-22.md
?? research/findings/IMPULSE_FADE_RECLAIM_SHORT_V1_LOW_STRESS_2026-05-07_to_2026-05-12.md
?? research/findings/IMPULSE_FADE_RECLAIM_SHORT_V1_LOW_STRESS_2026-05-08_to_2026-05-12.md
?? research/findings/IMPULSE_FADE_SHORT_DEEP_RECLAIM_ROBUSTNESS_2026-03-17_to_2026-05-12.md
?? research/findings/IMPULSE_FADE_SHORT_ENTRY_OBSERVABLE_PROXY_SCAN_2026-03-17_to_2026-05-12.md
?? research/findings/IMPULSE_FADE_SHORT_FULL_FADE_PROXY_DIAGNOSTIC_2026-03-17_to_2026-05-12.md
?? research/findings/IMPULSE_FADE_SHORT_REGIME_INTERACTION_2026-03-17_to_2026-05-12.md
?? research/findings/IMPULSE_LONG_GROWTH_OBSERVABLE_SCAN_2026-03-17_to_2026-05-14.md
?? research/findings/LOCAL_H1_RECLAIM_SWEEP_EXTREME_STOP_V1_BUFFER50_DIAGNOSTIC_2026-05-05.md
?? research/findings/LOCAL_H1_RECLAIM_SWEEP_EXTREME_STOP_V1_CLUSTER_PATHOLOGY_2026-05-05.md
?? research/findings/SHORT_IMPULSE_FADE_CONTEXT_FILTER_2026-05-08_to_2026-05-12.md
?? research/results/archive_replay_impulse_short_low_stress_backtest_2026-03-17_to_2026-04-22.json
?? research/results/archive_replay_impulse_short_low_stress_prep_2026-03-17_to_2026-04-22.json
?? research/results/impulse_fade_long_cluster_summary_2026-03-17_to_2026-05-14.csv
?? research/results/impulse_fade_long_coverage_2026-03-17_to_2026-05-14.csv
?? research/results/impulse_fade_long_deep_reclaim_threshold_sweep_2026-03-17_to_2026-05-14.csv
?? research/results/impulse_fade_long_entry_observable_features_2026-03-17_to_2026-05-14.csv
?? research/results/impulse_fade_long_pnl_concentration_2026-03-17_to_2026-05-14.csv
?? research/results/impulse_fade_long_proxy_scan_2026-03-17_to_2026-05-14.csv
?? research/results/impulse_fade_long_proxy_stable_2026-03-17_to_2026-05-14.csv
?? research/results/impulse_fade_long_watchlist_cluster_summary_2026-03-17_to_2026-05-14.csv
?? research/results/impulse_fade_long_watchlist_day_split_2026-03-17_to_2026-05-14.csv
?? research/results/impulse_fade_long_watchlist_pnl_concentration_2026-03-17_to_2026-05-14.csv
?? research/results/impulse_fade_long_watchlist_summary_2026-03-17_to_2026-05-14.csv
?? research/results/impulse_fade_long_watchlist_trades_2026-03-17_to_2026-05-14.csv
?? research/results/impulse_fade_reclaim_short_low_stress_v1_2026-03-17_to_2026-04-22.csv
?? research/results/impulse_fade_reclaim_short_low_stress_v1_2026-05-07_to_2026-05-12.csv
?? research/results/impulse_fade_reclaim_short_low_stress_v1_2026-05-08_to_2026-05-12.csv
?? research/results/impulse_fade_reclaim_short_low_stress_v1_summary_2026-03-17_to_2026-04-22.csv
?? research/results/impulse_fade_reclaim_short_low_stress_v1_summary_2026-05-07_to_2026-05-12.csv
?? research/results/impulse_fade_reclaim_short_low_stress_v1_summary_2026-05-08_to_2026-05-12.csv
?? research/results/impulse_fade_short_deep_reclaim_cluster_detail_2026-03-17_to_2026-05-12.csv
?? research/results/impulse_fade_short_deep_reclaim_cluster_summary_2026-03-17_to_2026-05-12.csv
?? research/results/impulse_fade_short_deep_reclaim_pnl_concentration_2026-03-17_to_2026-05-12.csv
?? research/results/impulse_fade_short_deep_reclaim_split_period_day_2026-03-17_to_2026-05-12.csv
?? research/results/impulse_fade_short_deep_reclaim_split_period_h2_2026-03-17_to_2026-05-12.csv
?? research/results/impulse_fade_short_deep_reclaim_split_period_hour_2026-03-17_to_2026-05-12.csv
?? research/results/impulse_fade_short_deep_reclaim_split_period_spike_2026-03-17_to_2026-05-12.csv
?? research/results/impulse_fade_short_deep_reclaim_split_period_stress_2026-03-17_to_2026-05-12.csv
?? research/results/impulse_fade_short_deep_reclaim_threshold_sweep_2026-03-17_to_2026-05-12.csv
?? research/results/impulse_fade_short_entry_observable_features_2026-03-17_to_2026-05-12.csv
?? research/results/impulse_fade_short_entry_observable_proxy_scan_2026-03-17_to_2026-05-12.csv
?? research/results/impulse_fade_short_entry_observable_proxy_stable_2026-03-17_to_2026-05-12.csv
?? research/results/impulse_fade_short_full_fade_proxy_candidates_2026-03-17_to_2026-05-12.csv
?? research/results/impulse_fade_short_full_fade_proxy_stable_candidates_2026-03-17_to_2026-05-12.csv
?? research/results/impulse_fade_short_regime_interaction_by_day_stress_2026-03-17_to_2026-05-12.csv
?? research/results/impulse_fade_short_regime_interaction_by_period_h2_12_stress_2026-03-17_to_2026-05-12.csv
?? research/results/impulse_fade_short_regime_interaction_by_period_h2_6_stress_2026-03-17_to_2026-05-12.csv
?? research/results/impulse_fade_short_regime_interaction_by_period_regime_stress_2026-03-17_to_2026-05-12.csv
?? research/results/impulse_fade_short_regime_interaction_by_period_spike_signature_2026-03-17_to_2026-05-12.csv
?? research/results/impulse_fade_short_regime_interaction_by_period_stress_2026-03-17_to_2026-05-12.csv
?? research/results/impulse_fade_short_regime_interaction_trades_2026-03-17_to_2026-05-12.csv
?? research/results/impulse_long_growth_cluster_summary_2026-03-17_to_2026-05-14.csv
?? research/results/impulse_long_growth_coverage_2026-03-17_to_2026-05-14.csv
?? research/results/impulse_long_growth_observable_features_2026-03-17_to_2026-05-14.csv
?? research/results/impulse_long_growth_proxy_scan_2026-03-17_to_2026-05-14.csv
?? research/results/impulse_long_growth_proxy_stable_2026-03-17_to_2026-05-14.csv
?? research/results/impulse_long_growth_return_concentration_2026-03-17_to_2026-05-14.csv
?? research/results/local_h1_reclaim_sweep_extreme_stop_v1_buffer50_2026-03-12_to_2026-05-04.csv
?? research/results/short_impulse_fade_context_filter_2026-05-08_to_2026-05-12.csv
?? research/results/short_impulse_fade_context_filter_summary_2026-05-08_to_2026-05-12.csv
?? research/scripts/impulse_fade_long_entry_observable_proxy_scan.py
?? research/scripts/impulse_fade_long_forward_watchlist.py
?? research/scripts/impulse_fade_reclaim_short_low_stress_v1.py
?? research/scripts/impulse_long_growth_observable_scan.py
?? research/scripts/local_h1_reclaim_sweep_extreme_stop_v1.py
?? tests/test_impulse_fade_reclaim_short_low_stress_v1.py
?? tests/test_local_h1_reclaim_sweep_extreme_stop_v1.py
```

## git diff --stat

```text
(empty)
```

## git diff --ignore-cr-at-eol --stat

```text
(empty)
```

## Modified Files

- None. No tracked modified files before cleanup.

## EOL Noise Assessment

- No tracked modified files and no EOL-only tracked diff before cleanup.

## Untracked Classification

- `feed_recovered/` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: external recovered data mirror; keep local; hash manifest required before ignoring
- `research/findings/IMPULSE_FADE_LONG_ENTRY_OBSERVABLE_PROXY_SCAN_2026-03-17_to_2026-05-14.md` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/findings/IMPULSE_FADE_LONG_FORWARD_WATCHLIST_2026-03-17_to_2026-05-14.md` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/findings/IMPULSE_FADE_RECLAIM_SHORT_V1_LOW_STRESS_2026-03-17_to_2026-04-22.md` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/findings/IMPULSE_FADE_RECLAIM_SHORT_V1_LOW_STRESS_2026-05-07_to_2026-05-12.md` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/findings/IMPULSE_FADE_RECLAIM_SHORT_V1_LOW_STRESS_2026-05-08_to_2026-05-12.md` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/findings/IMPULSE_FADE_SHORT_DEEP_RECLAIM_ROBUSTNESS_2026-03-17_to_2026-05-12.md` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/findings/IMPULSE_FADE_SHORT_ENTRY_OBSERVABLE_PROXY_SCAN_2026-03-17_to_2026-05-12.md` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/findings/IMPULSE_FADE_SHORT_FULL_FADE_PROXY_DIAGNOSTIC_2026-03-17_to_2026-05-12.md` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/findings/IMPULSE_FADE_SHORT_REGIME_INTERACTION_2026-03-17_to_2026-05-12.md` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/findings/IMPULSE_LONG_GROWTH_OBSERVABLE_SCAN_2026-03-17_to_2026-05-14.md` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/findings/LOCAL_H1_RECLAIM_SWEEP_EXTREME_STOP_V1_BUFFER50_DIAGNOSTIC_2026-05-05.md` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/findings/LOCAL_H1_RECLAIM_SWEEP_EXTREME_STOP_V1_CLUSTER_PATHOLOGY_2026-05-05.md` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/findings/SHORT_IMPULSE_FADE_CONTEXT_FILTER_2026-05-08_to_2026-05-12.md` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/archive_replay_impulse_short_low_stress_backtest_2026-03-17_to_2026-04-22.json` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/archive_replay_impulse_short_low_stress_prep_2026-03-17_to_2026-04-22.json` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_fade_long_cluster_summary_2026-03-17_to_2026-05-14.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_fade_long_coverage_2026-03-17_to_2026-05-14.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_fade_long_deep_reclaim_threshold_sweep_2026-03-17_to_2026-05-14.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_fade_long_entry_observable_features_2026-03-17_to_2026-05-14.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_fade_long_pnl_concentration_2026-03-17_to_2026-05-14.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_fade_long_proxy_scan_2026-03-17_to_2026-05-14.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_fade_long_proxy_stable_2026-03-17_to_2026-05-14.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_fade_long_watchlist_cluster_summary_2026-03-17_to_2026-05-14.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_fade_long_watchlist_day_split_2026-03-17_to_2026-05-14.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_fade_long_watchlist_pnl_concentration_2026-03-17_to_2026-05-14.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_fade_long_watchlist_summary_2026-03-17_to_2026-05-14.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_fade_long_watchlist_trades_2026-03-17_to_2026-05-14.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_fade_reclaim_short_low_stress_v1_2026-03-17_to_2026-04-22.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_fade_reclaim_short_low_stress_v1_2026-05-07_to_2026-05-12.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_fade_reclaim_short_low_stress_v1_2026-05-08_to_2026-05-12.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_fade_reclaim_short_low_stress_v1_summary_2026-03-17_to_2026-04-22.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_fade_reclaim_short_low_stress_v1_summary_2026-05-07_to_2026-05-12.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_fade_reclaim_short_low_stress_v1_summary_2026-05-08_to_2026-05-12.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_fade_short_deep_reclaim_cluster_detail_2026-03-17_to_2026-05-12.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_fade_short_deep_reclaim_cluster_summary_2026-03-17_to_2026-05-12.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_fade_short_deep_reclaim_pnl_concentration_2026-03-17_to_2026-05-12.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_fade_short_deep_reclaim_split_period_day_2026-03-17_to_2026-05-12.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_fade_short_deep_reclaim_split_period_h2_2026-03-17_to_2026-05-12.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_fade_short_deep_reclaim_split_period_hour_2026-03-17_to_2026-05-12.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_fade_short_deep_reclaim_split_period_spike_2026-03-17_to_2026-05-12.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_fade_short_deep_reclaim_split_period_stress_2026-03-17_to_2026-05-12.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_fade_short_deep_reclaim_threshold_sweep_2026-03-17_to_2026-05-12.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_fade_short_entry_observable_features_2026-03-17_to_2026-05-12.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_fade_short_entry_observable_proxy_scan_2026-03-17_to_2026-05-12.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_fade_short_entry_observable_proxy_stable_2026-03-17_to_2026-05-12.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_fade_short_full_fade_proxy_candidates_2026-03-17_to_2026-05-12.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_fade_short_full_fade_proxy_stable_candidates_2026-03-17_to_2026-05-12.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_fade_short_regime_interaction_by_day_stress_2026-03-17_to_2026-05-12.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_fade_short_regime_interaction_by_period_h2_12_stress_2026-03-17_to_2026-05-12.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_fade_short_regime_interaction_by_period_h2_6_stress_2026-03-17_to_2026-05-12.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_fade_short_regime_interaction_by_period_regime_stress_2026-03-17_to_2026-05-12.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_fade_short_regime_interaction_by_period_spike_signature_2026-03-17_to_2026-05-12.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_fade_short_regime_interaction_by_period_stress_2026-03-17_to_2026-05-12.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_fade_short_regime_interaction_trades_2026-03-17_to_2026-05-12.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_long_growth_cluster_summary_2026-03-17_to_2026-05-14.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_long_growth_coverage_2026-03-17_to_2026-05-14.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_long_growth_observable_features_2026-03-17_to_2026-05-14.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_long_growth_proxy_scan_2026-03-17_to_2026-05-14.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_long_growth_proxy_stable_2026-03-17_to_2026-05-14.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/impulse_long_growth_return_concentration_2026-03-17_to_2026-05-14.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/local_h1_reclaim_sweep_extreme_stop_v1_buffer50_2026-03-12_to_2026-05-04.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/short_impulse_fade_context_filter_2026-05-08_to_2026-05-12.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/results/short_impulse_fade_context_filter_summary_2026-05-08_to_2026-05-12.csv` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar research artifact; keep local for traceability, not committed
- `research/scripts/impulse_fade_long_entry_observable_proxy_scan.py` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: exploratory sidecar script; exact-ignore, do not delete this sprint
- `research/scripts/impulse_fade_long_forward_watchlist.py` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: exploratory sidecar script; exact-ignore, do not delete this sprint
- `research/scripts/impulse_fade_reclaim_short_low_stress_v1.py` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: exploratory sidecar script; exact-ignore, do not delete this sprint
- `research/scripts/impulse_long_growth_observable_scan.py` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: exploratory sidecar script; exact-ignore, do not delete this sprint
- `research/scripts/local_h1_reclaim_sweep_extreme_stop_v1.py` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: exploratory sidecar script; exact-ignore, do not delete this sprint
- `tests/test_impulse_fade_reclaim_short_low_stress_v1.py` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar tests for untracked exploratory scripts; protected from deletion
- `tests/test_local_h1_reclaim_sweep_extreme_stop_v1.py` | classification: `ARCHIVE_ONLY` | canonical_reference: `yes` | reason: sidecar tests for untracked exploratory scripts; protected from deletion

## git clean -nd before cleanup

```text
Would remove feed_recovered/
Would remove research/findings/IMPULSE_FADE_LONG_ENTRY_OBSERVABLE_PROXY_SCAN_2026-03-17_to_2026-05-14.md
Would remove research/findings/IMPULSE_FADE_LONG_FORWARD_WATCHLIST_2026-03-17_to_2026-05-14.md
Would remove research/findings/IMPULSE_FADE_RECLAIM_SHORT_V1_LOW_STRESS_2026-03-17_to_2026-04-22.md
Would remove research/findings/IMPULSE_FADE_RECLAIM_SHORT_V1_LOW_STRESS_2026-05-07_to_2026-05-12.md
Would remove research/findings/IMPULSE_FADE_RECLAIM_SHORT_V1_LOW_STRESS_2026-05-08_to_2026-05-12.md
Would remove research/findings/IMPULSE_FADE_SHORT_DEEP_RECLAIM_ROBUSTNESS_2026-03-17_to_2026-05-12.md
Would remove research/findings/IMPULSE_FADE_SHORT_ENTRY_OBSERVABLE_PROXY_SCAN_2026-03-17_to_2026-05-12.md
Would remove research/findings/IMPULSE_FADE_SHORT_FULL_FADE_PROXY_DIAGNOSTIC_2026-03-17_to_2026-05-12.md
Would remove research/findings/IMPULSE_FADE_SHORT_REGIME_INTERACTION_2026-03-17_to_2026-05-12.md
Would remove research/findings/IMPULSE_LONG_GROWTH_OBSERVABLE_SCAN_2026-03-17_to_2026-05-14.md
Would remove research/findings/LOCAL_H1_RECLAIM_SWEEP_EXTREME_STOP_V1_BUFFER50_DIAGNOSTIC_2026-05-05.md
Would remove research/findings/LOCAL_H1_RECLAIM_SWEEP_EXTREME_STOP_V1_CLUSTER_PATHOLOGY_2026-05-05.md
Would remove research/findings/SHORT_IMPULSE_FADE_CONTEXT_FILTER_2026-05-08_to_2026-05-12.md
Would remove research/results/archive_replay_impulse_short_low_stress_backtest_2026-03-17_to_2026-04-22.json
Would remove research/results/archive_replay_impulse_short_low_stress_prep_2026-03-17_to_2026-04-22.json
Would remove research/results/impulse_fade_long_cluster_summary_2026-03-17_to_2026-05-14.csv
Would remove research/results/impulse_fade_long_coverage_2026-03-17_to_2026-05-14.csv
Would remove research/results/impulse_fade_long_deep_reclaim_threshold_sweep_2026-03-17_to_2026-05-14.csv
Would remove research/results/impulse_fade_long_entry_observable_features_2026-03-17_to_2026-05-14.csv
Would remove research/results/impulse_fade_long_pnl_concentration_2026-03-17_to_2026-05-14.csv
Would remove research/results/impulse_fade_long_proxy_scan_2026-03-17_to_2026-05-14.csv
Would remove research/results/impulse_fade_long_proxy_stable_2026-03-17_to_2026-05-14.csv
Would remove research/results/impulse_fade_long_watchlist_cluster_summary_2026-03-17_to_2026-05-14.csv
Would remove research/results/impulse_fade_long_watchlist_day_split_2026-03-17_to_2026-05-14.csv
Would remove research/results/impulse_fade_long_watchlist_pnl_concentration_2026-03-17_to_2026-05-14.csv
Would remove research/results/impulse_fade_long_watchlist_summary_2026-03-17_to_2026-05-14.csv
Would remove research/results/impulse_fade_long_watchlist_trades_2026-03-17_to_2026-05-14.csv
Would remove research/results/impulse_fade_reclaim_short_low_stress_v1_2026-03-17_to_2026-04-22.csv
Would remove research/results/impulse_fade_reclaim_short_low_stress_v1_2026-05-07_to_2026-05-12.csv
Would remove research/results/impulse_fade_reclaim_short_low_stress_v1_2026-05-08_to_2026-05-12.csv
Would remove research/results/impulse_fade_reclaim_short_low_stress_v1_summary_2026-03-17_to_2026-04-22.csv
Would remove research/results/impulse_fade_reclaim_short_low_stress_v1_summary_2026-05-07_to_2026-05-12.csv
Would remove research/results/impulse_fade_reclaim_short_low_stress_v1_summary_2026-05-08_to_2026-05-12.csv
Would remove research/results/impulse_fade_short_deep_reclaim_cluster_detail_2026-03-17_to_2026-05-12.csv
Would remove research/results/impulse_fade_short_deep_reclaim_cluster_summary_2026-03-17_to_2026-05-12.csv
Would remove research/results/impulse_fade_short_deep_reclaim_pnl_concentration_2026-03-17_to_2026-05-12.csv
Would remove research/results/impulse_fade_short_deep_reclaim_split_period_day_2026-03-17_to_2026-05-12.csv
Would remove research/results/impulse_fade_short_deep_reclaim_split_period_h2_2026-03-17_to_2026-05-12.csv
Would remove research/results/impulse_fade_short_deep_reclaim_split_period_hour_2026-03-17_to_2026-05-12.csv
Would remove research/results/impulse_fade_short_deep_reclaim_split_period_spike_2026-03-17_to_2026-05-12.csv
Would remove research/results/impulse_fade_short_deep_reclaim_split_period_stress_2026-03-17_to_2026-05-12.csv
Would remove research/results/impulse_fade_short_deep_reclaim_threshold_sweep_2026-03-17_to_2026-05-12.csv
Would remove research/results/impulse_fade_short_entry_observable_features_2026-03-17_to_2026-05-12.csv
Would remove research/results/impulse_fade_short_entry_observable_proxy_scan_2026-03-17_to_2026-05-12.csv
Would remove research/results/impulse_fade_short_entry_observable_proxy_stable_2026-03-17_to_2026-05-12.csv
Would remove research/results/impulse_fade_short_full_fade_proxy_candidates_2026-03-17_to_2026-05-12.csv
Would remove research/results/impulse_fade_short_full_fade_proxy_stable_candidates_2026-03-17_to_2026-05-12.csv
Would remove research/results/impulse_fade_short_regime_interaction_by_day_stress_2026-03-17_to_2026-05-12.csv
Would remove research/results/impulse_fade_short_regime_interaction_by_period_h2_12_stress_2026-03-17_to_2026-05-12.csv
Would remove research/results/impulse_fade_short_regime_interaction_by_period_h2_6_stress_2026-03-17_to_2026-05-12.csv
Would remove research/results/impulse_fade_short_regime_interaction_by_period_regime_stress_2026-03-17_to_2026-05-12.csv
Would remove research/results/impulse_fade_short_regime_interaction_by_period_spike_signature_2026-03-17_to_2026-05-12.csv
Would remove research/results/impulse_fade_short_regime_interaction_by_period_stress_2026-03-17_to_2026-05-12.csv
Would remove research/results/impulse_fade_short_regime_interaction_trades_2026-03-17_to_2026-05-12.csv
Would remove research/results/impulse_long_growth_cluster_summary_2026-03-17_to_2026-05-14.csv
Would remove research/results/impulse_long_growth_coverage_2026-03-17_to_2026-05-14.csv
Would remove research/results/impulse_long_growth_observable_features_2026-03-17_to_2026-05-14.csv
Would remove research/results/impulse_long_growth_proxy_scan_2026-03-17_to_2026-05-14.csv
Would remove research/results/impulse_long_growth_proxy_stable_2026-03-17_to_2026-05-14.csv
Would remove research/results/impulse_long_growth_return_concentration_2026-03-17_to_2026-05-14.csv
Would remove research/results/local_h1_reclaim_sweep_extreme_stop_v1_buffer50_2026-03-12_to_2026-05-04.csv
Would remove research/results/short_impulse_fade_context_filter_2026-05-08_to_2026-05-12.csv
Would remove research/results/short_impulse_fade_context_filter_summary_2026-05-08_to_2026-05-12.csv
Would remove research/scripts/impulse_fade_long_entry_observable_proxy_scan.py
Would remove research/scripts/impulse_fade_long_forward_watchlist.py
Would remove research/scripts/impulse_fade_reclaim_short_low_stress_v1.py
Would remove research/scripts/impulse_long_growth_observable_scan.py
Would remove research/scripts/local_h1_reclaim_sweep_extreme_stop_v1.py
Would remove tests/test_impulse_fade_reclaim_short_low_stress_v1.py
Would remove tests/test_local_h1_reclaim_sweep_extreme_stop_v1.py
```
