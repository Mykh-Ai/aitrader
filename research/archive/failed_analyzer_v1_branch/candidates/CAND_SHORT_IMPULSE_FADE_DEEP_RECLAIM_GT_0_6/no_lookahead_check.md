# No-Lookahead Check

Status: `PASS`
Candidate events: 14

## Checks

- Entry predicates use only setup-time/context/depth fields.
- Future/outcome fields such as `H2_Post*`, `TradeReturn*`, `TradePnl`, `ExitTs`, `ExitReason`, `Win*`, `FullFade`, and `NoFade` are forbidden from candidate_events.
- `feature_snapshot_hash` is built from observable feature payload only.

## Issues

- none
