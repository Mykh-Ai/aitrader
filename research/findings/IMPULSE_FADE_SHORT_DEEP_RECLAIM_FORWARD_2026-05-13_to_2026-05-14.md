# IMPULSE_FADE_RECLAIM_SHORT_V1 Deep Reclaim Forward Check

Date: 2026-05-15

Status: forward watchlist diagnostic only. No baseline grammar change, no promotion.

## Window

`2026-05-13` to `2026-05-14`

## Routine Backtester Context

Both new routine runs were processed on the server:

- `2026-05-13_to_2026-05-13_run_001`: `BACKTESTED_REJECT`
- `2026-05-14_to_2026-05-14_run_001`: `BACKTESTED_REJECT`

No REVIEW/PROMOTE appeared.

## Short Baseline vs Deep Reclaim Watch

| Slice | Trades | Wins | WinRate | FULL_FADE rate | NO_FADE rate | PnL |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline_short | 14 | 10 | 71.43% | 50.00% | 0.00% | 228.97 |
| deep_reclaim_watch | 2 | 1 | 50.00% | 50.00% | 0.00% | 23.64 |

## Read

The new two-day forward sample is too small to validate or reject `DEEP_RECLAIM`.

Useful points:

- the watchlist did trigger;
- no `NO_FADE` rows appeared in the watchlist;
- PnL stayed positive;
- `FULL_FADE` rate did not outperform the strong two-day short baseline.

Conclusion: keep watching. Do not promote.

