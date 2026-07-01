# Active Docs

Active docs describe the reset boundary, feed/data lineage, and the current BTC Market Monitor / live-like stage-gated qualified H1 sweep-reclaim research track.

Current active documents, in source-of-truth order:

1. `README.md`
2. `AGENTS.md`
3. `PROJECT_LOG.md`
4. `docs/ACTIVE_DOCS.md`
5. `docs/FEED_CONTRACT_AND_SCHEMA_NOTES.md`
6. `docs/SHI_MARKET_MONITOR_CURRENT_ARCHITECTURE.md`
7. `docs/SHI_MARKET_STATE_MONITOR_V1_SPEC.md` (historical baseline / v1 spec, not the full current 38-chain architecture)
8. `NEXT_TASK_MARKET_MONITOR.md`
9. `research/canonical/SHI_RESET_38U_SPECIMEN_LIKE_CANDIDATE_EVIDENCE_REVIEW_2026_07_01.md`
10. future `research/canonical/SHI_RESET_38V_FULL_FEED_38S_TO_SETUP_BUILDER_CROSSCHECK_AUDIT_*.md`

Current status:

- Market Monitor research infrastructure is active.
- Live-like runs must carry market state forward from prior feed context, not slice arbitrary windows and treat them as the market.
- 38U is the latest accepted evidence-review anchor.
- 38S rows are permissive discovery/context material, not canonical setup_builder candidates until 38V proves a match.
- 38T/38U are post-generation QC/evidence reviews, not pre-generation monitor filters.
- 38V is the next active task: crosscheck 38S rows against canonical setup_builder output over the same full-feed scope.
- Backtester and Executor are future gates after candidate-contract tightening, not current active layers.

Current research evidence index:

- `PROJECT_LOG.md`
- `research/canonical/`
- `market_monitor_runs/`

Archived historical docs are preserved as evidence and must not be used as current implementation plans unless the user explicitly asks for archive review:

- `docs/Spec_v1.0.md`
- `docs/Phase2_Implementation_Plan_AiTrader_v2_2_updated.md`
- `docs/Analyzer_Run_Storage_v0.1.md`
- `docs/Phase3_Multi_Ruleset_Replay_Roadmap.md`
- `docs/Backtesting_Spec_v0.1.md`
- `docs/Backtesting_Architecture_v0.1.md`
- `docs/H4_False_Break_Reclaim_Research_Contract_v0.1.md`

New work must keep `README.md`, `AGENTS.md`, `PROJECT_LOG.md`, this file, and `NEXT_TASK_MARKET_MONITOR.md` aligned.
