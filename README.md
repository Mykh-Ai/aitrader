# AiTrader

## Project status

RESET AFTER FAILED ANALYZER V1 BRANCH

## Active goal

BTC Market State Monitor design.

The current active work is design-only reset/research infrastructure. This repository is not an active strategy project, not an execution bot, and not in Phase 4.

## Archived

Sprint 02-10 Analyzer v1 / Backtester research branch is archived as failed research evidence.

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
| `backtester/` | LEGACY / POSSIBLY REUSABLE VALIDATION HARNESS / AUDIT REQUIRED |
| `research/` | RESET BOUNDARY ONLY / NO ACTIVE CANDIDATES |

## Canonical local test command

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q
```

Reason: plain `pytest` may hang or time out in some environments due to external pytest plugins.

Pre-cleanup baseline recorded for the old full tree: `501 passed, 11 warnings`.

Active-tree reset baseline after excluding archived research-script tests: `464 passed, 11 warnings`.

## Current reset documents

- `STAGE_1_FAILED_RESEARCH_SUMMARY.md`
- `docs/LEGACY_CODE_AUDIT_TODO.md`
- `docs/FEED_CONTRACT_AND_SCHEMA_NOTES.md`
- `docs/SHI_MARKET_STATE_MONITOR_V1_SPEC.md`
- `research/archive_note.md`
- `research/canonical/PROJECT_STATE_CURRENT.md`
- `research/canonical/SHI_RESET_2026_05_ANALYZER_V1_VERDICT.md`
- `research/canonical/ARCHIVE_MANIFEST_FAILED_ANALYZER_V1.csv`

## Hard boundary

No live. No Executor. No Phase 4. No active trading strategy.
