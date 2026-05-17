# CAND_LONG_IMPULSE_FADE_LATE_US_STRUCTURAL Contract

Status: frozen watch candidate, `WATCH`

## Frozen Definition

- side = `LONG`
- timeframe = `H2`
- family = `H2 impulse fade / late-US structural watch`
- primary selector = `SetupCloseLocationInImpulseRange >= 0.75 & entry_hour_16_23 & Impulse_BodyToRange > 0.75`
- child selector remains watch-only: `low_stress_long & ReclaimDepthToImpulseRange > 0.3 & entry_hour_16_23`
- current source = sidecar watchlist diagnostic, not official Phase 4 mapping
- risk/exits = not promotion-frozen yet

## Lock Rules

- status = `WATCH`
- do not tune
- do not add filters
- do not replace the primary selector after seeing more rows
- continue forward evidence collection unchanged
- no live trading

## Current Evidence

- Primary selector: 20 rows, 19 resolved return rows, 13 trade-days.
- Cost stress sidecar remains positive through `0.00020`, but one row is unresolved and sample is insufficient.
- Post-recovery evidence remains below promotion gate.

## Promotion Status

No promotion. This candidate remains watch-only.

