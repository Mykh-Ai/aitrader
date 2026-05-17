# CAND_BTC_VWAP_DEV_SHORT_60_100200_V1 Ruleset Spec

Family: `VWAP_DEVIATION_REVERSION`
Side: `SHORT`
Rule version: `SPRINT08_BTC_FORMAL_REPLAY_V1`
Description: VWAP deviation reversion short, 100-200bp above DayVWAP, 60-bar expiry.

## Observable Entry Predicates

Sprint 06 VWAP SHORT observable predicates: price above DayVWAP, VWAP deviation bucket 100-200bp, stall/rejection context; session/regime recorded only.

Outcomes are not entry predicates.

## Mapping

- Signal after event M1 bar close.
- Entry at next M1 bar open.
- Stop: event bar high.
- Target: DayVWAP observed at entry timestamp, static after entry.
- Expiry: 60 M1 bars after entry.
- Same-bar policy: conservative stop-first.
- Cost levels: 0.00000, 0.00010, 0.00015, 0.00020.
- One active position per candidate; new events while active are skipped in replay.

## Boundary

No live trading, no Executor, no Phase 4, no PROMOTE, no CTX tuning, no Analyzer v1 or Backtester core changes.
