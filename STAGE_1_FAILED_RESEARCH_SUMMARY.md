# Stage 1 Failed Research Summary

Verdict: FAILED ARCHITECTURE / DO NOT CONTINUE.

## 1. What was attempted

The Sprint 02-10 branch attempted to turn Analyzer v1 false-break/reclaim research into replayable BTC strategy candidates, then validate them through deterministic replay, integrity checks, and holdout review.

## 2. What was actually built

The branch built a collector/feed asset, an Analyzer v1 research pipeline, deterministic artifact generation, candidate registries, replay/holdout reports, and a Backtester baseline. It produced research evidence, not an execution-ready strategy.

## 3. Why the branch failed

The branch failed because the research object was wrong. It promoted shallow setup artifacts before a real market-state model existed. Replay and holdout work could audit those artifacts, but could not turn weak event definitions into a professional BTC strategy.

## 4. Why Analyzer v1 failed

Analyzer v1 did not model real liquidity sweeps. Analyzer v1 treated primitive candle/level behavior as false break. 12-bar outcomes were arbitrary research scaffolding. Analyzer v1 did not detect accumulation/distribution zones. Analyzer v1 did not classify market state. Volume/delta/OI/funding/liquidation fields were not integrated into a professional market-state model.

## 5. Why false break concept is not rejected

False break remains a valid market idea only when grounded in liquidity, state, inventory behavior, and post-event acceptance/rejection. The old implementation did not provide that grounding.

## 6. Why old implementation is rejected

The old implementation reduced a market-structure idea into brittle setup rows, shallow sweep detection, and arbitrary forward labels. It created candidates without first proving that the system understood liquidity pools, stop-runs, accumulation, distribution, expansion, chop, or no-trade regimes.

## 7. What remains valuable

Feed and aggregator are the primary valuable assets. The test suite remains valuable. Some Analyzer v1 low-level utilities may be reusable only after audit: feed loading, schema checks, timestamp normalization, VWAP calculations, volume/delta base metrics, session labels, and swing/level primitive code.

## 8. What is legacy

Analyzer v1 is legacy / failed as strategy Analyzer / not active. Backtester is legacy / possibly reusable validation harness / audit required. Old research scripts are archived / not active.

## 9. What is archived

Sprint 02-10 replay branch evidence is archived: candidates, results, canonical sprint reports, old research scripts, analyzer runs, backtest runs, local runs, transfer packages, replay reports, holdout reports, integrity reports, active watchlists, candidate registries, and next-action documents that describe the closed branch.

## 10. What must not be continued

Do not continue Sprint 02-10 research. Do not tune old candidates. Do not replay old failed-break/reclaim survivors. Do not open Phase 4. Do not build Executor/live behavior. Do not present any Analyzer v1 output as an active candidate or trading strategy.

## 11. What next architecture must solve

Next architecture must be BTC Market State Monitor. It must model market state before strategy candidates: liquidity pools, real sweeps/stop-runs, volume/delta/OI context, accumulation/distribution zones, expansion, accepted/failed breakouts, chop, and no-trade states. It must use a feed adaptor/contract instead of ad-hoc column assumptions.
