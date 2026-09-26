# AGENTS.md

## Canonical base — 2026-09-26

New Market Monitor work, including 39B/39C, MUST start from `canonical/market-monitor-39a`.
Do not start from old `main`, named 39A, or 38G. Follow `docs/CANONICAL_BASE.md`
and verify canonical ancestry before editing. Branch audit: `research/canonical/CANONICAL_BRANCH_AUDIT_2026_09_26.md`.
This base decision does not promote research into trading or live readiness.

## Purpose

This file tells a new agent how to work in this repository. It is not the project history and it is not the research log. For the project story and current state, read `README.md`. For commit/task summaries and links to evidence folders, read `PROJECT_LOG.md`.

Current work is BTC Market Monitor research after the Analyzer v1 reset. The 39A master research-to-monitor alignment audit remains the canonical architecture source. Its review is complete, and the bounded v39A snapshot contract was promoted on 2026-09-11 for descriptive Executor LLM entry evidence. Remaining lifecycle promotions still require separate scope and evidence.

## Autonomy And Permissions

Do not ask the user for routine permission when the action is normal project work:

- reading files;
- searching the repository;
- inspecting git history and diffs;
- running local tests or lint/check commands;
- creating or editing files directly related to the requested task;
- adding documentation entries, canonical audit notes, or run-output summaries for the current task;
- working around quoting/path/sandbox friction with an equivalent safe local command.

Ask before serious or potentially destructive actions:

- deleting files or directories;
- `git reset`, destructive checkout/restore, or discarding user changes;
- broad formatting or mass rewrites outside the task scope;
- modifying `feed/`, `feed_recovered/`, or other data-lineage assets;
- enabling Backtester as an active validation gate;
- adding Executor/live/order/position-sizing behavior;
- installing dependencies, using network, deploying, pushing, or touching remote systems;
- changing project governance in a way that promotes research outputs to edge/live/production status.

If a tool-level sandbox approval is required by the environment, request it only when the action is actually necessary. Do not use approval prompts as a substitute for normal repository work.

## Start Every Task Here

Before changing anything, read in this order:

1. `README.md`
2. `PROJECT_LOG.md`
3. `docs/ACTIVE_DOCS.md`
4. `docs/FEED_CONTRACT_AND_SCHEMA_NOTES.md`
5. the canonical audit for the task you are continuing

Canonical audits live in:

`research/canonical/`

Generated run outputs live in:

`market_monitor_runs/`

Current audit:

`research/canonical/SHI_RESET_39A_MASTER_RESEARCH_TO_MONITOR_ALIGNMENT_AUDIT_2026_07_02.md`

Current companion artifacts:

- `research/canonical/SHI_RESET_39A_CONTROL_CASE_LEDGER_2026_07_02.csv`
- `research/canonical/SHI_RESET_39A_RESEARCH_TO_CODE_DECISION_MATRIX_2026_07_02.csv`
- `docs/SHI_MARKET_MONITOR_TERMINOLOGY_AND_EVENT_LIFECYCLE.md`
- `docs/SHI_MARKET_MONITOR_KNOWN_GAPS_AND_NEXT_PROMOTIONS.md`

## Live-Like Market Monitor Discipline

The Market Monitor must be treated as a stateful market reader, not as a tool that cuts a convenient window from the feed and pretends that window is the market.

For live-like research runs:

1. Process candles chronologically.
2. At each newly closed H1 candle, recompute or update the monitor using all feed history available up to that candle close.
3. Carry forward market state, structure levels, liquidity zones, qualified sweep/reclaim state, and setup review context from prior data.
4. Do not reset state between technical chunks unless the task is explicitly a reset/diagnostic task and the artifact names that reset clearly.
5. If chunking is needed for performance, write an audit field proving continuity, such as `market_state_reset=false`, `structure_levels_reset=false`, `liquidity_zones_reset=false`, `qualified_h1_state_reset=false`, and `setup_context_reset=false`.
6. Treat a narrow date window as a diagnostic replay only. A diagnostic window must not be presented as live-like discovery unless it reconstructs prior context from earlier feed data.

Market logic should model a live market as state that changes with each new closed candle and new trades. It should not infer setup quality from an isolated slice that lacks prior structure, liquidity, and state memory.

## Post-39A Architecture Rules

- Never treat `analyzer/` as an active source of current 38-chain candidates.
- Never say the 227 rows came from old Analyzer v1; they came from the 38S run script under `market_monitor_runs/`.
- Never treat the 38S 227 rows as the canonical candidate source. They remain discovery material even when a row matched the 38V crosscheck.
- Scripts under `market_monitor_runs/` are run artifacts, not reusable modules unless explicitly promoted into `market_monitor/` with tests and docs.
- Treat `setup_builder` as a context candidate generator, not a final setup engine.
- Treat a sweep as a sequence/lifecycle event, not one penetration candle or a generic quality label.
- Keep chat/manual conclusions separate from code-confirmed, run-artifact-confirmed, and canonical-doc-confirmed facts.
- Scope and validate every remaining 39A promotion separately; the completed snapshot promotion does not approve the remaining lifecycle backlog.
- Canonical live-like monitor work must process closed candles chronologically and carry market state forward.
- A valid future live monitor must update market state, structure levels, liquidity zones, hidden flow, setup context, and stage gates after each new closed candle.
- 38T and 38U are post-generation QC/evidence reviews, not pre-generation monitor filters.
- 38W1 is corrected replay evidence, not edge proof.

## Run And Artifact Rules

For each new SHI_RESET research task:

1. Create a run root under `market_monitor_runs/<TASK_ID>_v0/` or a clearly versioned successor.
2. Write generated CSV/JSON/MD artifacts into that run root.
3. Write a canonical audit summary under `research/canonical/<TASK_ID>_AUDIT_<YYYY_MM_DD>.md`.
4. Add a short entry to `PROJECT_LOG.md` with the task id, commit hash if available, canonical audit path, run-output root, key result, verification, and next implication.
5. Keep `README.md`, `AGENTS.md`, `PROJECT_LOG.md`, `docs/ACTIVE_DOCS.md`, and `NEXT_TASK_MARKET_MONITOR.md` aligned when the project state changes.

Do not bury negative evidence. If a run overgenerates, fails a gate, depends on degraded feed, or contradicts a prior assumption, record that directly in the audit and project log.

## Feed/Data Rules

Protected data-lineage assets:

- `binance_aggregator_shi.py`
- `feed/`
- `feed_recovered/`

Do not modify feed data or recovered feed data unless the user explicitly asks for a feed/data-lineage task.

Known outage/contamination window:

`2026-04-23 17:05:00 UTC -> 2026-05-06 22:51:00 UTC`

Inside that window, use `feed_recovered/YYYY-MM-DD.csv` when available and mark affected conclusions as recovered/degraded. Do not copy recovered rows into `feed/` and do not hide the degraded provenance.

## Current Research Semantics

Use current semantics carefully:

- `RAW_SWEEP` is observation/context only.
- `QUALIFIED_H1_SWEEP` requires completed H1 evidence and a meaningful H1/H4/structural level.
- `QUALIFIED_H1_FAILED_RECLAIM` requires a completed H1 close back through the swept level.
- `entry_candidate_ts` is the reclaim/rejection close timestamp.
- `setup_formed_at` is a setup review timestamp, not the entry timestamp.
- `policy_allowed` means a row passed the current research policy screen. It is not edge proof.
- `specimen_like` means similar to the current evidence specimen by QC criteria. It still requires review.

For sequence-linked H1 sweep/reclaim candidates:

- short stop anchor should be `sweep_h1_high_stop` unless a farther valid structural stop exists;
- long stop anchor should be `sweep_h1_low_stop` unless a farther valid structural stop exists;
- a structural stop inside the sweep range is invalid.

## Backtester And Executor Gates

Backtester and Executor are future gates, not current active layers.

The legacy `backtester/` package can become relevant again only after the current Market Monitor candidate contract is explicit enough to backtest. Do not run old Backtester campaigns against old Analyzer v1 survivors.

Executor integration requires a later explicit user-scoped phase after research and Backtester evidence. Do not add live/order/position-sizing behavior during Market Monitor research tasks.

## Tests

Canonical local test command:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q
```

PowerShell form:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"
python -m pytest -q
Remove-Item Env:PYTEST_DISABLE_PLUGIN_AUTOLOAD
```

Current targeted tests for the 38M-38U chain:

```bash
python -m pytest -q tests/test_stage_gate_replay.py tests/test_policy_replay_fixed_stops.py tests/test_qualified_h1_sweep_reclaim.py tests/test_sequence_window_h1_replay.py
```

Passing tests proves executable contracts still run. It does not prove market edge.
