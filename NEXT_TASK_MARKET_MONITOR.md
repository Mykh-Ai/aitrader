# NEXT TASK: SHI_RESET_38V_FULL_FEED_38S_TO_SETUP_BUILDER_CROSSCHECK_V0

## Status

This supersedes the post-38T generic candidate-contract note.

38S produced 227 discovery/context rows with a permissive run script under `market_monitor_runs/`. 38T and 38U reviewed those rows after generation. They did not prove that the rows are canonical `setup_builder` candidates.

## Goal

Compare the 227 38S full-feed discovery rows against canonical Market Monitor `setup_builder` output over the same full-feed scope.

The core question: which 38S rows are actually produced or confirmed by canonical `setup_builder` / monitor gates, and which are raw discovery contexts or overgeneration from the 38S run artifact?

## Required Inputs

Use:

- `README.md`
- `AGENTS.md`
- `PROJECT_LOG.md`
- `docs/ACTIVE_DOCS.md`
- `docs/SHI_MARKET_MONITOR_CURRENT_ARCHITECTURE.md`
- `research/canonical/PROJECT_STATE_CURRENT.md`
- `research/canonical/SHI_RESET_38S_REDO_FULL_FEED_LIVE_LIKE_SETUP_DISCOVERY_AUDIT_2026_06_30.md`
- `research/canonical/SHI_RESET_38T_FULL_FEED_DISCOVERY_QUALITY_CONTROL_AUDIT_2026_06_30.md`
- `research/canonical/SHI_RESET_38U_SPECIMEN_LIKE_CANDIDATE_EVIDENCE_REVIEW_2026_07_01.md`
- `market_monitor_runs/SHI_RESET_38S_redo_full_feed_live_like_setup_discovery_v0/live_like_discovered_setup_rows.csv`
- canonical `market_monitor` setup_builder / monitor-gate code
- `feed/` plus `feed_recovered/` only under documented degraded-feed rules

## Required Output

Create a new run root:

`market_monitor_runs/SHI_RESET_38V_full_feed_38s_to_setup_builder_crosscheck_v0/`

Create a canonical audit:

`research/canonical/SHI_RESET_38V_FULL_FEED_38S_TO_SETUP_BUILDER_CROSSCHECK_AUDIT_2026_07_01.md`

## Questions To Answer

- How many of the 227 38S rows match canonical `setup_builder` output?
- How many are raw discovery rows only?
- How many are overgeneration caused by the 38S runner turning every qualified H1 failed reclaim into ARMED review context?
- Does the 2026-05-26 specimen survive canonical setup_builder crosscheck?
- Which 38T/38U partial/numeric-only rows survive canonical setup_builder crosscheck?
- What exact setup_builder fields should become the candidate contract before Backtester is considered?

## Boundary

Research-only.

Do not claim edge from 38S, 38T, 38U, or 38V alone.

Do not run old `analyzer/` as active research.

Do not run old `backtester/` as active validation.

Do not add Executor, orders, live trading, PnL, position sizing, live-readiness, or strategy promotion.

Do not rewrite 38S/38T/38U artifacts in place.