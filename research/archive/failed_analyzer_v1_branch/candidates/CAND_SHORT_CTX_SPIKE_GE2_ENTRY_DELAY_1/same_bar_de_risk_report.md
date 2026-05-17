# Same-Bar De-Risk Report

Candidate: `CAND_SHORT_CTX_SPIKE_GE2_ENTRY_DELAY_1`

Rule version: `SPRINT03_CTX_GE2_ENTRY_DELAY_1_V1`

Status: `WAIT_SAME_BAR_NOT_CLEARED`

## Already-Seen Sprint 03 Sample

- Trades: 301
- Same-bar ambiguous trades: 40
- Same-bar percentage: 13.29%
- Cost basis: `0.00015`

## Level 1 - Conservative Policy

The conservative policy is already implemented and remains the default:

- if SL and TP are both possible in the same M1 bar, count worst-case / stop-first;
- use conservative result for promotion-gate accounting.

Already-seen conservative net at cost `0.00015`: `+0.0123921046`.

Verdict: positive, candidate remains alive as `WAIT`.

## Level 2 - Ambiguity Sensitivity

Already-seen sensitivity at cost `0.00015`:

- pessimistic result: `+0.0100437998`
- conservative result: `+0.0123921046`
- optimistic result: `+0.0134791115`

The pessimistic/optimistic spread does not flip the already-seen verdict from positive to negative.

Verdict: ambiguity is not verdict-changing on the already-seen Sprint 03 sample.

## Level 3 - Intrabar Resolution

Available replay input is M1 OHLC. Tick-level or lower-timeframe intrabar path is not available in the current local holdout package.

Required future check:

- identify ambiguous M1 windows from replay events;
- if trade-level or lower-timeframe path exists, run micro-replay for only those windows;
- if intrabar path is unavailable, record same-bar as not fully cleared.

Verdict: intrabar resolution is pending. Same-bar is not fully cleared and blocks Phase 4.

## Final Verdict

`WAIT_SAME_BAR_NOT_CLEARED`

This does not reject the candidate, but it prohibits promotion and execution-readiness.
