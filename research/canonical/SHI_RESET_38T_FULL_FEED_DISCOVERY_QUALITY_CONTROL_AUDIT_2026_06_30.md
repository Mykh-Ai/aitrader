# SHI RESET 38T Full-Feed Discovery Quality Control Audit

Verdict: PASS / FULL_FEED_DISCOVERY_QUALITY_CONTROL_CREATED

## Scope

Research-only quality-control audit over 38S redo artifacts. No Executor, orders, live trading, PnL, position sizing, live-readiness, Backtester campaign, strategy promotion, edge claim, parameter optimization, or future-label classification was added.

## Input Files Used

- `market_monitor_runs/SHI_RESET_38S_redo_full_feed_live_like_setup_discovery_v0/live_like_discovered_setup_rows.csv`
- `market_monitor_runs/SHI_RESET_38S_redo_full_feed_live_like_setup_discovery_v0/live_like_stage_gate_events.csv`
- `market_monitor_runs/SHI_RESET_38S_redo_full_feed_live_like_setup_discovery_v0/live_like_sequence_candidates.csv`
- `market_monitor_runs/SHI_RESET_38S_redo_full_feed_live_like_setup_discovery_v0/live_like_policy_allowed_candidates.csv`
- `market_monitor_runs/SHI_RESET_38S_redo_full_feed_live_like_setup_discovery_v0/live_like_rejected_rows.csv`
- `market_monitor_runs/SHI_RESET_38S_redo_full_feed_live_like_setup_discovery_v0/live_like_state_carry_forward_audit.csv`
- `market_monitor_runs/SHI_RESET_38S_redo_full_feed_live_like_setup_discovery_v0/live_like_setup_discovery_audit.csv`
- `market_monitor_runs/SHI_RESET_38S_redo_full_feed_live_like_setup_discovery_v0/live_like_summary.md`
- `market_monitor_runs/SHI_RESET_38S_redo_full_feed_live_like_setup_discovery_v0/live_like_manifest.json`
- `research/canonical/SHI_RESET_38R_SEQUENCE_LINKED_CANDIDATE_EVIDENCE_PACK_AUDIT_2026_06_30.md`
- `feed/*.csv`
- `feed_recovered/2026-04-23.csv through feed_recovered/2026-05-06.csv where present`

## Exact Commands Run

- `python market_monitor_runs\SHI_RESET_38T_full_feed_discovery_quality_control_v0\_build_full_feed_discovery_quality_control.py`
- `python -m compileall -q market_monitor`
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q`
- `git diff --check`
- `git status --short`

## Files Generated

- `market_monitor_runs/SHI_RESET_38T_full_feed_discovery_quality_control_v0/full_feed_setup_quality_review.csv`
- `market_monitor_runs/SHI_RESET_38T_full_feed_discovery_quality_control_v0/policy_allowed_quality_review.csv`
- `market_monitor_runs/SHI_RESET_38T_full_feed_discovery_quality_control_v0/sequence_cluster_quality.csv`
- `market_monitor_runs/SHI_RESET_38T_full_feed_discovery_quality_control_v0/specimen_similarity_review.csv`
- `market_monitor_runs/SHI_RESET_38T_full_feed_discovery_quality_control_v0/manual_review_shortlist_38t.csv`
- `market_monitor_runs/SHI_RESET_38T_full_feed_discovery_quality_control_v0/overgeneration_diagnosis.md`
- `market_monitor_runs/SHI_RESET_38T_full_feed_discovery_quality_control_v0/quality_control_summary.md`
- `market_monitor_runs/SHI_RESET_38T_full_feed_discovery_quality_control_v0/quality_control_manifest.json`
- `research/canonical/SHI_RESET_38T_FULL_FEED_DISCOVERY_QUALITY_CONTROL_AUDIT_2026_06_30.md`

## Counts

- Total setup rows reviewed: `227`
- Total policy-allowed candidates reviewed: `140`
- Raw policy model rows read: `280`
- Unique policy-allowed setup ids: `140`
- Sequence clusters: `140`
- Cluster counts: `{'PRIMARY_UNIQUE_SEQUENCE': 140}`
- Duplicate/reuse candidate rows: `0`
- Quality verdict counts: `{'PRIMARY_CANDIDATE_REVIEW': 80, 'BAD_R_PROFILE_REJECT': 6, 'WEAK_SWEEP_REJECT': 29, 'SPECIMEN_LIKE_PRIMARY_CANDIDATE': 8, 'DATA_QUALITY_REVIEW': 17}`
- Specimen-like primary setup ids: `8`
- Rejected duplicate candidates: `0`
- Data-quality review candidates: `17`
- Candidates from degraded-feed periods: `17`
- 2026-05-26 specimen remains valid: `true`

## Test Results

- `python -m compileall -q market_monitor market_monitor_runs\SHI_RESET_38T_full_feed_discovery_quality_control_v0\_build_full_feed_discovery_quality_control.py` -> passed.
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q` -> `716 passed, 11 warnings in 58.09s`.

## git diff --check Result

Clean; no whitespace errors reported.

## Final Git Status

`?? research/canonical/SHI_RESET_38T_FULL_FEED_DISCOVERY_QUALITY_CONTROL_AUDIT_2026_06_30.md`

Generated 38T run-output files are under ignored `market_monitor_runs/` storage and do not appear in `git status --short`.

## Verdict

PASS / FULL_FEED_DISCOVERY_QUALITY_CONTROL_CREATED
