# AiTrader

## Project status

RESET AFTER FAILED ANALYZER V1 BRANCH / RESEARCH INFRASTRUCTURE ONLY

## Active goal

BTC Market State Monitor research infrastructure.

AiTrader is currently research infrastructure only. Market Monitor exists as a research-only module for describing BTC market structure and liquidity behavior. This repository is not an active strategy project, not an execution bot, and not in Phase 4.

Active candidates = NONE.

Replay candidates = NONE.

Holdout candidates = NONE.

Backtester = LEGACY / AUDIT REQUIRED / BLOCKED FOR MARKET MONITOR USE.

Executor/live = FORBIDDEN.

## Current Market Monitor pipeline

Current research pipeline:

`feed -> market_monitor -> structure levels -> liquidity zones -> registry -> event_log -> unresolved sweep candidates -> post-sweep observations -> labels -> label quality reports`

Market Monitor outputs research artifacts only. It does not produce trading signals, entries, exits, positions, PnL, Backtester verdicts, Executor actions, or live instructions.

Labels are descriptive research labels only. `SWEEP_REJECTED` does not mean short. `SWEEP_ACCEPTED` does not mean long. No trading action is implied by any label.

## Archived

Sprint 02-10 Analyzer v1 / Backtester research branch is archived as failed research evidence.

Old Analyzer v1 / Sprint 02-10 = archived / not active.

Primary archive package:

- `_archive/FAILED_ANALYZER_V1_RESEARCH_BRANCH_2026_05.zip`
- `_archive/FAILED_ANALYZER_V1_RESEARCH_BRANCH_2026_05_MANIFEST.csv`

The archive zip is intentionally not tracked because repository `.gitignore` ignores `*.zip`. The CSV manifest is tracked and records the archived evidence set.

## Not active

- old candidates;
- old replay survivors;
- old failed-break/reclaim setup logic;
- old Analyzer v1 research branch;
- old Sprint 02-10 replay/holdout workflow;
- Phase 4;
- Executor/live execution;
- active trading strategy.

## Core asset

- BTC feed;
- recovered feed;
- aggregator/data lineage;
- test suite.

## Module status

| Area | Status |
|---|---|
| `feed/` | KEEP / CORE ASSET |
| `feed_recovered/` | KEEP / DEGRADED GAP RECOVERY INPUT WITH CAVEATS |
| `binance_aggregator_shi.py` | KEEP / CORE DATA LINEAGE |
| `tests/` | KEEP / EXECUTABLE CONTRACT CHECKS |
| `analyzer/` | LEGACY / FAILED AS STRATEGY ANALYZER / NOT ACTIVE |
| `backtester/` | LEGACY / POSSIBLY REUSABLE VALIDATION HARNESS / AUDIT REQUIRED / BLOCKED |
| `market_monitor/` | ACTIVE RESEARCH INFRASTRUCTURE / NOT A STRATEGY |
| `research/` | RESET BOUNDARY ONLY / NO ACTIVE CANDIDATES |

## Canonical local test command

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q
```

Reason: plain `pytest` may hang or time out in some environments due to external pytest plugins.

Pre-cleanup baseline recorded for the old full tree: `501 passed, 11 warnings`.

Active-tree reset baseline after physically removing archived research-script tests: `464 passed, 11 warnings`.

## Current active documents

- `README.md`
- `AGENTS.md`
- `STAGE_1_FAILED_RESEARCH_SUMMARY.md`
- `docs/SHI_MARKET_STATE_MONITOR_V1_SPEC.md`
- `docs/FEED_CONTRACT_AND_SCHEMA_NOTES.md`
- `docs/LEGACY_CODE_AUDIT_TODO.md`
- `docs/ACTIVE_DOCS.md`
- `NEXT_TASK_MARKET_MONITOR.md`

## Hard boundary

No live. No Executor. No Phase 4. No active trading strategy. No Backtester replay campaigns. No trading candidates.

New Market Monitor feature work must remain explicitly scoped as research infrastructure and must keep the governance/source-of-truth documents aligned.
