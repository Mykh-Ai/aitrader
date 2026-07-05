# Active Docs

## Current active source of truth — SHI_RESET_39A

Current 39A alignment documents:

- `research/canonical/SHI_RESET_39A_MASTER_RESEARCH_TO_MONITOR_ALIGNMENT_AUDIT_2026_07_02.md`
- `research/canonical/SHI_RESET_39A_CONTROL_CASE_LEDGER_2026_07_02.csv`
- `research/canonical/SHI_RESET_39A_RESEARCH_TO_CODE_DECISION_MATRIX_2026_07_02.csv`
- `docs/SHI_MARKET_MONITOR_TERMINOLOGY_AND_EVENT_LIFECYCLE.md`
- `docs/SHI_MARKET_MONITOR_KNOWN_GAPS_AND_NEXT_PROMOTIONS.md`

No new code promotion should happen until 39A is reviewed.

39A states that Market Monitor is still research infrastructure, `setup_builder` is still a context generator, sweep must be reworked as a sequence/lifecycle event before new setup logic, 38S rows remain discovery-only, replay evidence is not edge proof, and manual conclusions are not code-confirmed facts.

## Baseline active docs

- `README.md`
- `AGENTS.md`
- `STAGE_1_FAILED_RESEARCH_SUMMARY.md`
- `docs/SHI_MARKET_STATE_MONITOR_V1_SPEC.md`
- `docs/FEED_CONTRACT_AND_SCHEMA_NOTES.md`
- `docs/LEGACY_CODE_AUDIT_TODO.md`
- `docs/ACTIVE_DOCS.md`
- `NEXT_TASK_MARKET_MONITOR.md`

Market Monitor exists as research infrastructure. It is not a trading strategy, not Backtester-ready, not Executor-ready, and not live-ready. There are no active trading candidates.

Old Analyzer v1 / Phase2 / Phase3 / Backtester docs are archived historical references and must not be used as current implementation plans.
