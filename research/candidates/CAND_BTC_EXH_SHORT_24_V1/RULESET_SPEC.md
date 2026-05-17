# CAND_BTC_EXH_SHORT_24_V1 Ruleset Spec

Family: `EXHAUSTION_REVERSAL`
Side: `SHORT`
Rule version: `SPRINT08_BTC_FORMAL_REPLAY_V1`
Description: Exhaustion reversal short, 24-bar expiry, event-high stop, entry-time DayVWAP target.

## Observable Entry Predicates

Sprint 06 exhaustion SHORT observable predicates: prior impulse up, high volume quantile, rejection/stall, delta dominance, VWAP stretch.

Outcomes are not entry predicates.

## Mapping

- Signal after event M1 bar close.
- Entry at next M1 bar open.
- Stop: event bar high.
- Target: DayVWAP observed at entry timestamp, static after entry.
- Expiry: 24 M1 bars after entry.
- Same-bar policy: conservative stop-first.
- Cost levels: 0.00000, 0.00010, 0.00015, 0.00020.
- One active position per candidate; new events while active are skipped in replay.

## Boundary

No live trading, no Executor, no Phase 4, no PROMOTE, no CTX tuning, no Analyzer v1 or Backtester core changes.
