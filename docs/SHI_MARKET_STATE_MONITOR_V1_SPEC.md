# Shi Market State Monitor v1 Spec

Status: design specification
Date: 2026-05-17

## Purpose

Shi must observe the market as state, not search for one setup pattern.

Market State Monitor v1 replaces the closed Analyzer v1 setup-detector path as the next research architecture. It is not a trading system and does not produce orders or live signals.

## Hard Boundary

Market State Monitor v1 does not:

- generate trading signals;
- run Backtester replay;
- open Phase 4;
- call Executor;
- size positions;
- tune old failed-break/reclaim candidates.

It only reads market data and writes state-monitoring artifacts.

## Input

Primary input is the protected raw feed format:

- `Timestamp`
- `Trades`
- `TotalQty`
- `BuyQty`
- `SellQty`
- `ClosePrice`
- `HiPrice`
- `LowPrice`
- `OpenInterest`
- `FundingRate`

Recovered data may be used only with its documented degraded fields and provenance constraints.

## A. Market Structure Layer

Responsibilities:

- detect H1/H4 levels;
- track previous day high/low;
- track session highs/lows;
- detect equal highs/lows;
- identify range boundaries;
- identify compression zones.

Output responsibilities:

- publish structural levels with timestamps, source timeframe, confidence, and active/inactive status;
- separate observed levels from interpreted liquidity zones;
- avoid trade-entry language.

## B. Liquidity Layer

Responsibilities:

- map liquidity pools above and below current price;
- detect liquidity sweeps;
- detect stop-runs;
- measure sweep magnitude;
- measure sweep speed;
- measure sweep volume;
- measure post-sweep reaction;
- allow reclaim/failure interpretation only after a liquidity event exists.

Minimum event evidence:

- pre-existing pool or level;
- excursion beyond the pool or level;
- measurable volume/trade activity during excursion;
- post-event reaction window;
- explicit unresolved status when evidence is incomplete.

## C. Volume / Delta / OI Layer

Responsibilities:

- detect volume anomaly;
- detect delta spike;
- detect delta divergence;
- detect absorption;
- detect aggression burst;
- detect OI expansion/contraction when available;
- treat funding/OI as external futures context, not isolated signals.

This layer must convert raw quantities into state context. It must not only attach shallow labels to setup rows.

## D. Accumulation / Distribution Layer

Responsibilities:

- detect range compression;
- detect high volume with low price progress;
- detect repeated boundary rejection;
- detect delta pressure without price progress;
- detect VWAP acceptance/rejection;
- detect balance areas.

This layer must describe where inventory may be building or distributing. It does not predict direction by itself.

## E. Market State Classifier

Allowed states:

- `ACCUMULATION`
- `DISTRIBUTION`
- `EXPANSION_UP`
- `EXPANSION_DOWN`
- `STOP_RUN_UP`
- `STOP_RUN_DOWN`
- `FAILED_BREAKOUT`
- `ACCEPTED_BREAKOUT`
- `CHOP`
- `NO_TRADE`

Every state assignment must include:

- start timestamp;
- end timestamp or open-ended flag;
- evidence fields;
- confidence tier;
- invalidation reason when superseded.

## F. Event Layer

Allowed events:

- `LIQUIDITY_SWEEP`
- `STOP_RUN`
- `ABSORPTION`
- `DELTA_DIVERGENCE`
- `VOLUME_CLIMAX`
- `RANGE_REJECTION`
- `RANGE_ACCEPTANCE`
- `ACCUMULATION_BREAK`
- `DISTRIBUTION_BREAK`

Events must be observable from data available at or before the event timestamp. Future outcome labels are prohibited in v1.

## G. Output Contract

Every run must produce:

- `market_state_timeline.csv`
- `liquidity_map.csv`
- `structure_levels.csv`
- `volume_delta_state.csv`
- `accumulation_zones.csv`
- `event_log.csv`
- `market_summary.md`

All CSV outputs must be deterministic for identical input data and configuration.

## H. Rule

No trading signals in v1.

No Backtester in v1.

No Executor.

Only market state monitoring.

## Implementation Direction

The next task must build a package skeleton, not optimize a strategy.

The first implementation should prioritize:

- stable input loading;
- deterministic timestamp handling;
- basic structure level extraction;
- liquidity map scaffolding;
- event log schema;
- market summary generation;
- tests for schema, determinism, and no-signal boundaries.
