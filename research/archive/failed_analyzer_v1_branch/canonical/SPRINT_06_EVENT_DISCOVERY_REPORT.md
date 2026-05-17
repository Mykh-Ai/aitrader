# Sprint 06 Event Discovery Report

## 1. Executive Verdict

Managerial verdict: `CHANGE_UNIVERSE_OR_DATA`.

Sprint 06 tested only `EXHAUSTION_REVERSAL` and `VWAP_DEVIATION_REVERSION`. It did not test Momentum Continuation and did not rerun Analyzer v1 broad failed-break/reclaim.

No `PROMOTE` was created. This is discovery only.

## Managerial Answer

- Replay-worthy surfaces: 0.
- Discovery-review surfaces: 0.
- BTC-only research should not move to replay yet; collect more data or broaden market/data if review surfaces do not mature.
- Market/universe/data: current BTC-only feed shows behavior surfaces, but replay-spec work is justified only for `NEEDS_REPLAY_SPEC`; otherwise broaden data/universe before spending more effort.
- Analyzer v1 should remain baseline/control only.

## 2. Data Used

- Clean usable days: 66.
- Discovery feature rows: 95037.
- Sources: {"primary": 52, "primary_plus_recovered_gap": 14}.

## 3. Data Excluded

- Primary contaminated window: `2026-04-23 17:05:00` -> `2026-05-06 22:51:00` UTC.
- Synthetic rows.
- Zero/nonpositive OHLC rows.
- Partial current UTC day.
- Events without enough future bars for the requested horizon.

## 4. Families Tested

- `EXHAUSTION_REVERSAL` clustered events: 342.
- `VWAP_DEVIATION_REVERSION` clustered events: 2556.

## 5. Top Surfaces By Gross Edge

| family | side | horizon | session | regime | clustered_events | independent_trade_days | gross_edge_bp | verdict |
|---|---|---|---|---|---|---|---|---|
| VWAP_DEVIATION_REVERSION | SHORT | 60 | US | CHOP | 1 | 1 | 181.885734 | REJECT_DISCOVERY_SURFACE |
| VWAP_DEVIATION_REVERSION | SHORT | 60 | LONDON | EXPANSION | 1 | 1 | 173.193384 | REJECT_DISCOVERY_SURFACE |
| VWAP_DEVIATION_REVERSION | SHORT | 24 | US | REVERSAL_CANDIDATE | 1 | 1 | 151.066434 | REJECT_DISCOVERY_SURFACE |
| VWAP_DEVIATION_REVERSION | SHORT | 60 | ASIA | EXPANSION | 2 | 1 | 149.756652 | REJECT_DISCOVERY_SURFACE |
| VWAP_DEVIATION_REVERSION | SHORT | 60 | US | EXPANSION | 1 | 1 | 146.656071 | REJECT_DISCOVERY_SURFACE |
| EXHAUSTION_REVERSAL | LONG | 60 | LONDON | REVERSAL_CANDIDATE | 1 | 1 | 141.209355 | REJECT_DISCOVERY_SURFACE |
| VWAP_DEVIATION_REVERSION | LONG | 60 | US | UNKNOWN | 1 | 1 | 139.835082 | REJECT_DISCOVERY_SURFACE |
| VWAP_DEVIATION_REVERSION | SHORT | 24 | LONDON | REVERSAL_CANDIDATE | 1 | 1 | 135.08588 | REJECT_DISCOVERY_SURFACE |
| VWAP_DEVIATION_REVERSION | SHORT | 60 | US | CHOP | 1 | 1 | 132.499362 | REJECT_DISCOVERY_SURFACE |
| EXHAUSTION_REVERSAL | SHORT | 60 | LONDON | REVERSAL_CANDIDATE | 1 | 1 | 132.29618 | REJECT_DISCOVERY_SURFACE |

## 6. Top Surfaces By Net Edge After 0.00015

| family | side | horizon | session | regime | clustered_events | independent_trade_days | net_edge_bp_after_0_00015 | verdict |
|---|---|---|---|---|---|---|---|---|
| VWAP_DEVIATION_REVERSION | SHORT | 60 | US | CHOP | 1 | 1 | 180.385734 | REJECT_DISCOVERY_SURFACE |
| VWAP_DEVIATION_REVERSION | SHORT | 60 | LONDON | EXPANSION | 1 | 1 | 171.693384 | REJECT_DISCOVERY_SURFACE |
| VWAP_DEVIATION_REVERSION | SHORT | 24 | US | REVERSAL_CANDIDATE | 1 | 1 | 149.566434 | REJECT_DISCOVERY_SURFACE |
| VWAP_DEVIATION_REVERSION | SHORT | 60 | ASIA | EXPANSION | 2 | 1 | 148.256652 | REJECT_DISCOVERY_SURFACE |
| VWAP_DEVIATION_REVERSION | SHORT | 60 | US | EXPANSION | 1 | 1 | 145.156071 | REJECT_DISCOVERY_SURFACE |
| EXHAUSTION_REVERSAL | LONG | 60 | LONDON | REVERSAL_CANDIDATE | 1 | 1 | 139.709355 | REJECT_DISCOVERY_SURFACE |
| VWAP_DEVIATION_REVERSION | LONG | 60 | US | UNKNOWN | 1 | 1 | 138.335082 | REJECT_DISCOVERY_SURFACE |
| VWAP_DEVIATION_REVERSION | SHORT | 24 | LONDON | REVERSAL_CANDIDATE | 1 | 1 | 133.58588 | REJECT_DISCOVERY_SURFACE |
| VWAP_DEVIATION_REVERSION | SHORT | 60 | US | CHOP | 1 | 1 | 130.999362 | REJECT_DISCOVERY_SURFACE |
| EXHAUSTION_REVERSAL | SHORT | 60 | LONDON | REVERSAL_CANDIDATE | 1 | 1 | 130.79618 | REJECT_DISCOVERY_SURFACE |

## 7. Surfaces Rejected And Why

| family | side | horizon | session | regime | clustered_events | verdict_reason |
|---|---|---|---|---|---|---|
| VWAP_DEVIATION_REVERSION | SHORT | 60 | US | CHOP | 1 | sample_below_50;independent_days_below_15;day_concentration_above_0_15 |
| VWAP_DEVIATION_REVERSION | SHORT | 60 | LONDON | EXPANSION | 1 | sample_below_50;independent_days_below_15;day_concentration_above_0_15 |
| VWAP_DEVIATION_REVERSION | SHORT | 24 | US | REVERSAL_CANDIDATE | 1 | sample_below_50;independent_days_below_15;day_concentration_above_0_15 |
| VWAP_DEVIATION_REVERSION | SHORT | 60 | ASIA | EXPANSION | 2 | sample_below_50;independent_days_below_15;day_concentration_above_0_15 |
| VWAP_DEVIATION_REVERSION | SHORT | 60 | US | EXPANSION | 1 | sample_below_50;independent_days_below_15;day_concentration_above_0_15 |
| EXHAUSTION_REVERSAL | LONG | 60 | LONDON | REVERSAL_CANDIDATE | 1 | sample_below_50;independent_days_below_15;day_concentration_above_0_15 |
| VWAP_DEVIATION_REVERSION | LONG | 60 | US | UNKNOWN | 1 | sample_below_50;independent_days_below_15;day_concentration_above_0_15 |
| VWAP_DEVIATION_REVERSION | SHORT | 24 | LONDON | REVERSAL_CANDIDATE | 1 | sample_below_50;independent_days_below_15;day_concentration_above_0_15 |
| VWAP_DEVIATION_REVERSION | SHORT | 60 | US | CHOP | 1 | sample_below_50;independent_days_below_15;day_concentration_above_0_15 |
| EXHAUSTION_REVERSAL | SHORT | 60 | LONDON | REVERSAL_CANDIDATE | 1 | sample_below_50;independent_days_below_15;day_concentration_above_0_15 |
| VWAP_DEVIATION_REVERSION | SHORT | 24 | LONDON | EXPANSION | 1 | sample_below_50;independent_days_below_15;day_concentration_above_0_15 |
| EXHAUSTION_REVERSAL | LONG | 60 | US | REVERSAL_CANDIDATE | 1 | sample_below_50;independent_days_below_15;day_concentration_above_0_15 |
| VWAP_DEVIATION_REVERSION | LONG | 60 | US | UNKNOWN | 1 | sample_below_50;independent_days_below_15;day_concentration_above_0_15 |
| VWAP_DEVIATION_REVERSION | SHORT | 60 | US | UNKNOWN | 1 | sample_below_50;independent_days_below_15;day_concentration_above_0_15 |
| EXHAUSTION_REVERSAL | SHORT | 60 | US | REVERSAL_CANDIDATE | 1 | sample_below_50;independent_days_below_15;day_concentration_above_0_15 |
| VWAP_DEVIATION_REVERSION | LONG | 24 | LATE_US | EXPANSION | 1 | sample_below_50;independent_days_below_15;day_concentration_above_0_15 |
| VWAP_DEVIATION_REVERSION | LONG | 6 | LATE_US | EXPANSION | 1 | sample_below_50;independent_days_below_15;day_concentration_above_0_15 |
| VWAP_DEVIATION_REVERSION | LONG | 60 | US | REVERSAL_CANDIDATE | 1 | sample_below_50;independent_days_below_15;day_concentration_above_0_15 |
| VWAP_DEVIATION_REVERSION | SHORT | 60 | LONDON | REVERSAL_CANDIDATE | 1 | sample_below_50;independent_days_below_15;day_concentration_above_0_15 |
| VWAP_DEVIATION_REVERSION | SHORT | 12 | LONDON | EXPANSION | 1 | sample_below_50;independent_days_below_15;day_concentration_above_0_15 |

## 8. Surfaces Needing Review

None.

## 9. Surfaces Needing Replay Spec

None.

## 10. Research Perspective

The project still has research perspective only if discovery surfaces survive replay-spec formalization and later Backtester/holdout gates. Discovery is not strategy validation.

## 11. BTC-Only Current Feed Edge

BTC-only feed has visible descriptive event surfaces. Confirmed edge remains unproven until a replayable spec passes deterministic replay, cost, same-bar, concentration, and holdout gates.

## 12. Next Action

If `NEEDS_REPLAY_SPEC` surfaces exist, draft a formal replay spec without tuning predicates. If none exist, do not force replay; gather more data or change universe/data before more BTC-only rule work.

## Boundary Confirmation

- Analyzer v1 remains baseline/control.
- Sprint 06 did not change Analyzer v1 contract.
- Sprint 06 did not change Backtester.
- Sprint 06 did not change CTX holdout.
- Sprint 06 did not touch Executor/live.

## Verdict Counts

{"REJECT_DISCOVERY_SURFACE": 4865}
