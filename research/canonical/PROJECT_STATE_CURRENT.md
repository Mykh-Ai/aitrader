# Project State Current

Date: 2026-07-01

## State

Current active direction: BTC Market Monitor / live-like stage-gated qualified H1 sweep-reclaim research.

Latest accepted research anchor: `SHI_RESET_38U_SPECIMEN_LIKE_CANDIDATE_EVIDENCE_REVIEW_2026_07_01.md`.

Current discipline: live-like discovery must process closed candles chronologically, carry market state forward from prior feed context, and avoid treating arbitrary isolated windows as complete market state.

Active system: Market Monitor research, not Analyzer v1.

Canonical candidate source should be canonical Market Monitor `setup_builder` / monitor gates, not 38S raw discovery rows.

38S redo generated 227 setup/context rows and 140 policy-allowed research candidates using a permissive run script under `market_monitor_runs/SHI_RESET_38S_redo_full_feed_live_like_setup_discovery_v0/`. Those rows remain unvalidated until the 38V setup_builder crosscheck.

38T and 38U are post-generation QC/evidence-review layers. They are not pre-generation monitor filters and do not promote 38S rows to edge.

Confirmed research specimen: one strong 2026-05-26 sequence-linked H1 sweep/reclaim specimen from 38R/38Q/38U. 38U found 6 partial relatives and 1 numeric-only lookalike among the 8 specimen-like 38T rows.

Live / Executor candidates: none active.

Phase 4 / production candidates: none active.

Validated edge: not established.

Analyzer v1: legacy / failed / archive only.

Backtester: legacy / audit required / future validation gate after candidate-contract definition.

Executor: future integration gate after research and Backtester evidence, not current active layer.

## Current Evidence Index

- `README.md`
- `AGENTS.md`
- `PROJECT_LOG.md`
- `docs/ACTIVE_DOCS.md`
- `docs/SHI_MARKET_MONITOR_CURRENT_ARCHITECTURE.md`
- `research/canonical/SHI_RESET_38S_REDO_FULL_FEED_LIVE_LIKE_SETUP_DISCOVERY_AUDIT_2026_06_30.md`
- `research/canonical/SHI_RESET_38T_FULL_FEED_DISCOVERY_QUALITY_CONTROL_AUDIT_2026_06_30.md`
- `research/canonical/SHI_RESET_38U_SPECIMEN_LIKE_CANDIDATE_EVIDENCE_REVIEW_2026_07_01.md`
- `market_monitor_runs/SHI_RESET_38S_redo_full_feed_live_like_setup_discovery_v0/`
- `market_monitor_runs/SHI_RESET_38T_full_feed_discovery_quality_control_v0/`
- `market_monitor_runs/SHI_RESET_38U_specimen_like_candidate_evidence_review_v0/`

## Next

`SHI_RESET_38V_FULL_FEED_38S_TO_SETUP_BUILDER_CROSSCHECK_V0`

Compare the 227 38S discovery rows against canonical Market Monitor `setup_builder` output over the same full-feed scope. Classify rows as setup_builder-confirmed, raw discovery only, or overgeneration before any broader statistical interpretation or Backtester gate.