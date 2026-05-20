# AGENTS.md

## 1. Current Project State

AiTrader is currently in RESET / research infrastructure mode.

Active candidates = NONE.

Replay candidates = NONE.

Holdout candidates = NONE.

Analyzer v1 = LEGACY / FAILED / READ-ONLY.

Backtester = LEGACY / AUDIT REQUIRED / NOT ACTIVE.

Old Sprint 02-10 research branch = archived / not active.

Active direction = BTC Market State Monitor design, but implementation has not started.

No Phase 4. No Executor. No live. No old Analyzer v1 workflow. No old failed-break/reclaim research. No old backtester replay campaigns. No old candidates.

## 2. Active Sources of Truth

Use these as current authority, in this order:

1. `README.md`
2. `STAGE_1_FAILED_RESEARCH_SUMMARY.md`
3. `docs/SHI_MARKET_STATE_MONITOR_V1_SPEC.md`
4. `docs/FEED_CONTRACT_AND_SCHEMA_NOTES.md`
5. `docs/LEGACY_CODE_AUDIT_TODO.md`
6. `docs/ACTIVE_DOCS.md`
7. `NEXT_TASK_MARKET_MONITOR.md`

Archived historical docs are not active implementation plans.

## 3. Not Active Sources

Do not treat these as active source of truth:

- `docs/Spec_v1.0.md`
- `docs/Backtesting_Spec_v0.1.md`
- `docs/Backtesting_Architecture_v0.1.md`
- `docs/Analyzer_Run_Storage_v0.1.md`
- `docs/Phase2_Implementation_Plan_AiTrader_v2_2_updated.md`
- `docs/Phase3_Multi_Ruleset_Replay_Roadmap.md`
- `research/OPS.md`
- `scripts/run_analyzer_daily.sh`
- `prompts/Shi_research.txt`
- `prompts/weekly_research.txt`

If a file from this list reappears, treat it as governance leakage unless the user explicitly asks to inspect archive evidence.

## 4. Hard Prohibitions

Do not:

- run live;
- run Executor;
- open Phase 4;
- restore old candidates;
- use Analyzer v1 as active research;
- run Backtester replay campaigns;
- use future labels for event generation;
- use 12-bar outcome logic;
- treat shallow sweep detection as a liquidity sweep model;
- treat passing legacy tests as edge evidence;
- continue Sprint 02-10;
- restore old research scripts;
- restore old research prompts;
- write a new Analyzer;
- write Market Monitor implementation before governance cleanup is accepted.

## 5. Module Boundaries

### Aggregator and Feed

`binance_aggregator_shi.py`, `feed/`, and `feed_recovered/` are core data-lineage assets.

Do not modify feed data or recovered feed data unless the user explicitly asks for a feed/data-lineage task.

### analyzer/

Legacy only. Read `analyzer/README.md` before touching anything under `analyzer/`.

Analyzer v1 failed as a strategy Analyzer. It may be read for audited low-level references only. It must not be run as active research.

### backtester/

Legacy only. Read `backtester/README.md` before touching anything under `backtester/`.

Backtester may be reusable only after audit and contract refactor. It must not be used for old replay campaigns.

### docs/

Active docs must remain reset / feed contract / Market State Monitor only.

Old Analyzer v1 / Phase2 / Phase3 / Backtester docs are archive evidence only.

## 6. Evidence and Archive Rules

Do not hide negative evidence. If old research artifacts must be removed from active tree, archive them first or ensure an archive manifest already records them.

The old Analyzer v1 / Sprint 02-10 branch is archive-only. Do not use it to justify active candidates, replay survivors, Phase 4, or live readiness.

## 7. Test Discipline

Canonical local test command:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q
```

Passing tests only proves current code contracts still execute. It does not prove edge, candidate validity, replay validity, or live readiness.
