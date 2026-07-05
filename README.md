# AiTrader

## Current source of truth — SHI_RESET_39A

`research/canonical/SHI_RESET_39A_MASTER_RESEARCH_TO_MONITOR_ALIGNMENT_AUDIT_2026_07_02.md` is the current master alignment audit after review.

No new code promotion should happen until 39A is reviewed.

39A preserves the current boundary:

- Market Monitor remains research infrastructure only.
- `setup_builder` remains a context candidate generator, not a final setup engine.
- Sweep must be redefined as a sequence/lifecycle event before new setup logic is added.
- 38S 227 rows remain discovery material, not candidates.
- 38W1-style corrected replay evidence is replay evidence, not edge proof.
- Chat/manual conclusions are preserved separately from code-confirmed facts.

## Project status

RESET AFTER FAILED ANALYZER V1 BRANCH / RESEARCH INFRASTRUCTURE ONLY

## Active goal

BTC Market State Monitor research infrastructure.

AiTrader is currently research infrastructure only. Market Monitor exists as a research-only module for describing BTC market structure and liquidity behavior.

Active candidates = NONE.

Replay candidates = NONE.

Holdout candidates = NONE.

Backtester = LEGACY / AUDIT REQUIRED / BLOCKED FOR MARKET MONITOR USE.

Executor/live = FORBIDDEN.

## Current Market Monitor pipeline

`feed -> market_monitor -> structure levels -> liquidity zones -> registry -> event_log -> unresolved sweep candidates -> post-sweep observations -> labels -> label quality reports`

Market Monitor outputs research artifacts only.

## Current active documents

- `README.md`
- `AGENTS.md`
- `research/canonical/SHI_RESET_39A_MASTER_RESEARCH_TO_MONITOR_ALIGNMENT_AUDIT_2026_07_02.md`
- `research/canonical/SHI_RESET_39A_CONTROL_CASE_LEDGER_2026_07_02.csv`
- `research/canonical/SHI_RESET_39A_RESEARCH_TO_CODE_DECISION_MATRIX_2026_07_02.csv`
- `docs/SHI_MARKET_MONITOR_TERMINOLOGY_AND_EVENT_LIFECYCLE.md`
- `docs/SHI_MARKET_MONITOR_KNOWN_GAPS_AND_NEXT_PROMOTIONS.md`
- `docs/ACTIVE_DOCS.md`
- `NEXT_TASK_MARKET_MONITOR.md`
