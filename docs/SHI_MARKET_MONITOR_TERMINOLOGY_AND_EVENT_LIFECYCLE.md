# SHI Market Monitor Terminology and Event Lifecycle

Date: 2026-07-02
Status: Canonical terminology reference / documentation only

This document defines event language for future Market Monitor promotion work. It does not implement code, filters, tests, strategy logic, live trading, or Executor behavior.

## Evidence boundary

These definitions are documentation-level terminology. Until implemented and tested in market_monitor code, they are not current code behavior.

## Core principle

A sweep is not a candle. A sweep is a sequence.

A single candle can only create a touch, penetration, or sweep candidate. Final event classification requires follow-through/reclaim evidence from the next 1-3 H1 candles or another explicitly defined confirmation window.

## Terms

### LEVEL_TOUCH

Price reaches or overlaps a known level/zone without a confirmed penetration beyond that level. A touch can produce useful reaction evidence but is not a sweep.

### LEVEL_PENETRATION

Price moves beyond a known support/resistance level or liquidity-zone boundary. This is the first mechanical break of the level. It is not yet a confirmed sweep, accepted breakout, or accepted breakdown.

### SWEEP_CANDIDATE

A level penetration that may become a sweep if the following confirmation sequence reclaims the broken level. The penetration candle can create this candidate, but cannot finalize it alone.

### CONFIRMED_SWEEP_RECLAIM

A sweep candidate where the following 1-3 H1 candles reclaim the broken level and hold back inside/above/below the prior structure in the direction consistent with a failed break. This confirms the sweep/reclaim event, not automatically a trade setup.

### FAILED_BREAK_RECLAIM

A failed breakout or failed breakdown where price penetrates a level and then returns back through it. This is a lifecycle classification. It can be bullish or bearish depending on which side failed.

### ACCEPTED_BREAKDOWN

A support penetration where following candles close and hold below the broken support instead of reclaiming it. This invalidates a bullish sweep interpretation and supports a continuation/breakdown interpretation.

### ACCEPTED_BREAKOUT

A resistance penetration where following candles close and hold above the broken resistance instead of rejecting/reclaiming below it. This invalidates a bearish sweep interpretation and supports a continuation/breakout interpretation.

### COUNTER_SWEEP_INVALIDATION

A second sweep/penetration sequence appears inside the confirmation window and invalidates or reverses the previous directional interpretation. Example: a support sweep starts, but a later upper sweep/seller response blocks the long setup interpretation.

### RETEST_REACTION

After a break/reclaim/accepted break, price returns to the level and reacts. A retest reaction can confirm the level behavior, but it still needs lifecycle context.

### LEVEL_CONFIRMED_BY_REACTION

A level shows repeated meaningful reactions after touch, penetration, reclaim, accepted break, or retest. This strengthens confidence that the market is respecting the level.

### LEVEL_STRENGTHENED

A level gains importance because of repeated reactions, clean reclaims, clean accepted breaks followed by retests, or sustained structural influence.

### LEVEL_WEAKENED

A level loses importance because of repeated failed reactions, messy overlap, shallow/noisy pseudo-sweeps, or inability to produce directional response.

### LEVEL_INVALIDATED

A level is no longer useful as active structure because price has accepted beyond it, reactions stopped mattering, or later lifecycle evidence superseded it.

### LAST_WAGON / PRIOR_MOVE_MATURITY

A setup risk context where price has already travelled far in the intended direction before the candidate forms. A late continuation candidate after a mature prior move requires special caution and should not be promoted without a prior-move distance/maturity model.

### SHORT_INTO_MAJOR_SUPPORT

A short-context candidate whose target or continuation path runs directly into nearby major support. This is a blocker/risk context unless future code explicitly resolves the target and structural-risk conditions.

### LONG_INTO_MAJOR_RESISTANCE

A long-context candidate whose target or continuation path runs directly into nearby major resistance. This is a blocker/risk context unless future code explicitly resolves the target and structural-risk conditions.

## Canonical classification flow

1. Detect level touch / penetration.
2. If penetration occurs, create `SWEEP_CANDIDATE` only.
3. Inspect next 1-3 H1 candles.
4. If reclaimed: classify as `FAILED_BREAK_RECLAIM` / `CONFIRMED_SWEEP_RECLAIM`.
5. If accepted beyond level: classify as `ACCEPTED_BREAKDOWN` or `ACCEPTED_BREAKOUT`.
6. If opposite/counter event appears: classify as `COUNTER_SWEEP_INVALIDATION` and stop direct promotion of the original directional setup.
7. Track retests and reactions to strengthen/weaken/invalidate the level over time.

## Non-goals

This document does not define entries, exits, position sizing, stop-loss rules, take-profit rules, PnL, live readiness, or Executor behavior.
