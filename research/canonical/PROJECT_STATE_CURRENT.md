# Project State Current

Date: 2026-07-02

## Current source of truth

Current master audit: `research/canonical/SHI_RESET_39A_MASTER_RESEARCH_TO_MONITOR_ALIGNMENT_AUDIT_2026_07_02.md`.

No new code promotion should happen until 39A is reviewed.

## State

active_candidates = NONE

replay_candidates = NONE

holdout_candidates = NONE

old_research_branch = archived / not active

Analyzer_v1 = legacy / failed / read-only

Backtester = legacy / audit required / not active for current monitor

Implementation = Market Monitor research infrastructure active

setup_builder = context candidate generator only / not final setup engine

Executor_live = forbidden

Phase_4 = not open

## 39A preserved conclusions

- Sweep must be redefined as sequence/lifecycle event before new setup logic is added.
- 38S 227 rows are discovery material, not candidates.
- 38W1-style corrected replay evidence is replay evidence, not edge proof.
- Chat/manual conclusions are preserved separately from code-confirmed and run-artifact-confirmed facts.
- Implementation promotion candidates are documentation-only backlog items until a future explicit promotion task.

## Boundary

No live. No Executor. No orders. No PnL. No position sizing. No live readiness. No active trading strategy.

Market Monitor labels, setup_builder rows, replay outputs, and manual reviews are research artifacts only unless future code promotion and validation explicitly prove otherwise.
