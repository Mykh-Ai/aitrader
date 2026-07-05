# AGENTS.md

## 0. Current Source of Truth — SHI_RESET_39A

Before new Market Monitor code-promotion work, read:

1. `research/canonical/SHI_RESET_39A_MASTER_RESEARCH_TO_MONITOR_ALIGNMENT_AUDIT_2026_07_02.md`
2. `research/canonical/SHI_RESET_39A_CONTROL_CASE_LEDGER_2026_07_02.csv`
3. `research/canonical/SHI_RESET_39A_RESEARCH_TO_CODE_DECISION_MATRIX_2026_07_02.csv`
4. `docs/SHI_MARKET_MONITOR_TERMINOLOGY_AND_EVENT_LIFECYCLE.md`
5. `docs/SHI_MARKET_MONITOR_KNOWN_GAPS_AND_NEXT_PROMOTIONS.md`

No new code promotion should happen until 39A is reviewed.

Required 39A boundaries:

- `setup_builder` is a context candidate generator, not a final setup engine.
- Sweep is a sequence/lifecycle event, not a candle and not a quality gate.
- 38S 227 rows are discovery material only, not candidates.
- 38W1-style corrected replay evidence is not edge proof.
- Chat/manual conclusions must stay separate from CODE_CONFIRMED and RUN_ARTIFACT_CONFIRMED facts.
- Implementation promotion candidates are documentation-only until explicitly promoted later.

## 1. Current Project State

AiTrader is currently in RESET / research infrastructure mode.

Active candidates = NONE.

Replay candidates = NONE.

Holdout candidates = NONE.

Analyzer v1 = LEGACY / FAILED / READ-ONLY.

Backtester = LEGACY / AUDIT REQUIRED / NOT ACTIVE.

Old Sprint 02-10 research branch = archived / not active.

Active direction = BTC Market State Monitor research infrastructure.

Market Monitor research infrastructure exists and is active as a research-only module.

It produces structure/liquidity artifacts, zone registry/carry-forward outputs, event logs, unresolved sweep candidates, post-sweep observations, descriptive sweep labels, label quality reports, research summaries, and batch research outputs.

It does not produce trading signals, entries, exits, positions, PnL, Backtester verdicts, Executor actions, orders, or live instructions.

## 2. Active Sources of Truth

Use these as current authority, in this order:

1. `README.md`
2. `AGENTS.md`
3. `research/canonical/SHI_RESET_39A_MASTER_RESEARCH_TO_MONITOR_ALIGNMENT_AUDIT_2026_07_02.md`
4. `research/canonical/SHI_RESET_39A_CONTROL_CASE_LEDGER_2026_07_02.csv`
5. `research/canonical/SHI_RESET_39A_RESEARCH_TO_CODE_DECISION_MATRIX_2026_07_02.csv`
6. `docs/SHI_MARKET_MONITOR_TERMINOLOGY_AND_EVENT_LIFECYCLE.md`
7. `docs/SHI_MARKET_MONITOR_KNOWN_GAPS_AND_NEXT_PROMOTIONS.md`
8. `docs/ACTIVE_DOCS.md`
9. `NEXT_TASK_MARKET_MONITOR.md`

Archived historical docs are not active implementation plans.

## 3. Hard Prohibitions

Do not run live, run Executor, open Phase 4, restore old candidates, use Analyzer v1 as active research, run Backtester replay campaigns, use future labels for event generation, treat shallow sweep detection as a liquidity sweep model, treat passing tests as edge evidence, or add new Market Monitor feature work unless governance docs remain aligned and the task is explicitly scoped as research infrastructure.

## 4. Module Boundaries

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

Active docs must remain reset / feed contract / Market State Monitor / 39A alignment only.

## 5. Evidence and Archive Rules

Do not hide negative evidence. If a referenced artifact is missing, mark it `NOT_FOUND` / `NOT_VERIFIED` instead of reconstructing it from memory.

The old Analyzer v1 / Sprint 02-10 branch is archive-only. Do not use it to justify active candidates, replay survivors, Phase 4, or live readiness.

## 6. Test Discipline

Canonical local test command:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q
```

Passing tests only proves current code contracts still execute. It does not prove edge, candidate validity, replay validity, or live readiness.
