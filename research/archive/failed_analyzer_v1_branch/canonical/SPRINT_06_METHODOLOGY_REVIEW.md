# Sprint 06 Methodology Review

## Answers

1. Surface grouping was too granular: `True`. Sprint 06 grouped by family, side, horizon, session, regime, VWAP bucket, volume bucket, and rejection bucket at the same time.

2. Surface size distribution:

| bucket | surfaces |
|---|---:|
| 1_event | 2106 |
| 2_5_events | 2089 |
| 6_20_events | 665 |
| 21_50_events | 5 |
| 50_plus_events | 0 |
| 100_plus_events | 0 |

One-event surface share: `0.4329`.

3. Positive family/side/horizon aggregates after repaired grouping: `20`.
4. Positive bucket-only aggregates after repaired grouping: `124`.
5. `CHANGE_UNIVERSE_OR_DATA` was premature because the rejection was dominated by fragmented 1-2 event surfaces, not by a repaired BTC-only aggregate test.
6. Corrected verdict: `BTC_SURFACE_AGGREGATION_REPAIR_REQUIRED`.
