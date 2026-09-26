# Active Docs

## Canonical base — 2026-09-26

New Market Monitor work, including 39B/39C, MUST start from `canonical/market-monitor-39a`.
Do not start from old `main`, named 39A, or 38G. Follow `docs/CANONICAL_BASE.md`
and verify canonical ancestry before editing. Branch audit: `research/canonical/CANONICAL_BRANCH_AUDIT_2026_09_26.md`.
This base decision does not promote research into trading or live readiness.

Active docs describe the reset boundary, feed/data lineage, the 39A architecture audit, and the bounded v39A snapshot promotion completed on 2026-09-11.

Current active documents, in source-of-truth order:

1. `research/canonical/SHI_RESET_39A_MASTER_RESEARCH_TO_MONITOR_ALIGNMENT_AUDIT_2026_07_02.md`
2. `research/canonical/SHI_RESET_39A_CONTROL_CASE_LEDGER_2026_07_02.csv`
3. `research/canonical/SHI_RESET_39A_RESEARCH_TO_CODE_DECISION_MATRIX_2026_07_02.csv`
4. `docs/SHI_MARKET_MONITOR_TERMINOLOGY_AND_EVENT_LIFECYCLE.md`
5. `docs/SHI_MARKET_MONITOR_KNOWN_GAPS_AND_NEXT_PROMOTIONS.md`
6. `README.md`
7. `AGENTS.md`
8. `PROJECT_LOG.md`
9. `docs/ACTIVE_DOCS.md`
10. `docs/FEED_CONTRACT_AND_SCHEMA_NOTES.md`
11. `docs/SHI_MARKET_MONITOR_CURRENT_ARCHITECTURE.md` (post-38U architecture snapshot; retained as historical context and superseded by 39A where they differ)
12. `research/canonical/PROJECT_STATE_CURRENT.md`
13. `NEXT_TASK_MARKET_MONITOR.md`
14. `docs/SHI_MARKET_STATE_MONITOR_V1_SPEC.md` (historical baseline / v1 spec)

Current status:

- 39A is the current canonical alignment source and its review is complete.
- The v39A snapshot contract is promoted for descriptive entry-time LLM evidence; remaining promotion items require separate scope.
- setup_builder is a context generator, not a final setup engine.
- Sweep must be modeled as a sequence/lifecycle event before new setup logic is added.
- The 38S 227 rows remain discovery material, not canonical candidates.
- 38W1 is corrected replay evidence, not edge proof.
- Chat/manual conclusions are preserved separately from code-confirmed and run-artifact-confirmed facts.
- Canonical 38U/38V/38W/38W1/38X/38Y audit files are absent in this checkout; their available conclusions remain run-artifact evidence unless another canonical source exists.
- Executor consumes the snapshot as advisory entry evidence only; trading-policy authority and Backtester promotion remain future gates.

Current research evidence index:

- `PROJECT_LOG.md`
- `research/canonical/`
- `market_monitor_runs/`

Archived historical docs remain evidence and must not be used as current implementation plans unless the user explicitly asks for archive review:

- `docs/Spec_v1.0.md`
- `docs/Phase2_Implementation_Plan_AiTrader_v2_2_updated.md`
- `docs/Analyzer_Run_Storage_v0.1.md`
- `docs/Phase3_Multi_Ruleset_Replay_Roadmap.md`
- `docs/Backtesting_Spec_v0.1.md`
- `docs/Backtesting_Architecture_v0.1.md`
- `docs/H4_False_Break_Reclaim_Research_Contract_v0.1.md`

New work must keep `README.md`, `AGENTS.md`, `PROJECT_LOG.md`, this file, `research/canonical/PROJECT_STATE_CURRENT.md`, and `NEXT_TASK_MARKET_MONITOR.md` aligned.
