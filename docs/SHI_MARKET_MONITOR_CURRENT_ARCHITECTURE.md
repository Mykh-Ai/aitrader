# SHI Market Monitor Current Architecture

Status: current architecture note after 38S/38T/38U
Date: 2026-07-01

## Purpose

This document describes the active AiTrader architecture after the 38S full-feed discovery, 38T quality-control audit, and 38U specimen-like evidence review.

It is research-only. It does not define a trading strategy, Backtester campaign, Executor integration, live readiness, orders, PnL, or position sizing.

## Active Modules

### Aggregator And Feed

- `binance_aggregator_shi.py`
- `feed/`
- `feed_recovered/`

These are data-lineage assets. The known recovered/degraded window remains `2026-04-23 17:05:00 UTC -> 2026-05-06 22:51:00 UTC`. Recovered data must be marked and cannot be used to hide provenance.

### Market Monitor Research Layer

Active Market Monitor work lives under `market_monitor/` and current run outputs under `market_monitor_runs/`.

The intended chain is:

`Aggregator / feed -> Market Monitor base layer -> structure levels -> liquidity zones -> zone registry / carry-forward -> event log / post-sweep observation -> significant zone selector -> hidden flow research -> market structure state -> setup_builder -> qualified H1 sweep/reclaim sequence check -> stage-gate replay -> policy replay review -> QC / evidence packs`

The active research gates currently include:

- completed-candle chronological processing;
- market state carry-forward;
- structural level and liquidity-zone context;
- qualified H1 sweep evidence;
- qualified H1 failed reclaim evidence;
- sequence-linked entry-candidate timestamping;
- sequence-extreme stop anchoring;
- stage-gate rejection before policy replay;
- post-generation QC/evidence review.

## Inactive Legacy Modules

### analyzer/

`analyzer/` is legacy / failed / read-only. It did not generate the current 38S 227 rows. It must not be used as the active source of current 38-chain candidates.

Low-level code may be inspected only after audit. Failed-break/reclaim setup logic, old outcomes, rankings, shortlists, and old promotion assumptions are not active.

### backtester/

`backtester/` is legacy / audit-required / not active. It may become a future validation harness only after the Market Monitor candidate contract is explicit and setup_builder crosschecks are complete.

Do not run old Backtester campaigns against Analyzer v1 survivors or 38S raw discovery rows.

## Run Artifacts Vs Reusable Modules

`market_monitor_runs/` contains run artifacts and task-specific builders. Those scripts are not reusable modules unless explicitly promoted into `market_monitor/` with tests, docs, and governance alignment.

38S is especially important:

- 38S used `_build_full_feed_live_like_setup_discovery.py` under `market_monitor_runs/`.
- 38S generated 227 raw discovery/context rows.
- 38S did not use old Analyzer v1.
- 38S did not use canonical `setup_builder.py` as the candidate source.
- 38S transformed every qualified H1 failed-reclaim context into an ARMED review row.
- Therefore 38S rows are overgenerated discovery material until 38V setup_builder crosscheck proves otherwise.

38T and 38U are post-generation QC/evidence-review layers. They are not pre-generation monitor filters.

## Live-Like Candle-Close Processing Model

A valid live-like monitor must process new closed candles chronologically and carry state forward.

After each newly closed candle, a future live-like monitor must update or preserve:

- market state;
- structure levels;
- liquidity zones;
- zone registry / carry-forward state;
- hidden-flow context;
- setup context;
- qualified H1 sweep/reclaim state;
- stage-gate state.

Technical chunks are allowed for runtime/file processing only. They must not reset market logic.

## Current Research Boundaries

Current rows are research artifacts, not edge.

The 2026-05-26 38R/38Q/38U candidate is a confirmed research specimen. It is not a live-ready edge.

38U found partial repeatability, not a fully validated repeatable strategy pattern. The 38S promotion layer remains too permissive.

## Future Backtester Boundary

Backtester becomes meaningful only after 38V or later tasks define a canonical Market Monitor candidate contract that can be replayed without ambiguity.

Before Backtester activation, the project must know:

- candidate source;
- timestamp semantics;
- entry-candidate timestamp;
- stop anchor;
- target/TP rules;
- same-bar policy;
- data-quality rules;
- rejection rules.

## Future Executor Boundary

Executor is future only. No current document, run artifact, or 38-chain row authorizes live trading, orders, position sizing, PnL claims, or live-readiness.