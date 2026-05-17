# Feed Opportunity Audit

Last updated: 2026-05-17

## Purpose

This audit describes what market behavior exists in the local clean feed surface. It does not define trading rules, entry predicates, exits, stops, or promotion claims.

Generated artifacts:

- `research/results/feed_opportunity_audit.csv`
- `research/results/discovery_surface_summary.csv`

Generator:

- `research/scripts/sprint_05_discovery_surface_scan.py`

## Data Lineage

Primary `feed/` is contaminated from `2026-04-23 17:05:00` through `2026-05-06 22:51:00` UTC.

The scan excludes that primary-feed window. For timestamps inside the outage window, it uses `feed_recovered/` only because recovered lineage is present in `research/canonical/FEED_RECOVERED_MANIFEST.csv`.

Recovered gap caveat:

- real price/OHLCV/trades/buy/sell/VWAP are usable for descriptive opportunity audit;
- open interest may be copied or forward-filled;
- funding is degraded during the WebSocket gap;
- historical liquidation quantities may be missing;
- no funding/liquidation conclusion should be made from recovered rows unless explicitly marked degraded.

The script also filters rows with nonpositive OHLC values before metric calculation.

## Metric Definitions

Per date, the audit computes:

- `rows`: clean rows used after outage and nonpositive-OHLC filtering.
- `synthetic_pct`: percent of rows with `IsSynthetic != 0`.
- `volume_sum`: sum of `Volume`.
- `daily_return_pct`: last clean close vs first clean close.
- `high_low_range_pct`: day high minus day low divided by first clean close.
- `realized_volatility`: square-root sum of one-minute log-return squares, in percent.
- `max_1h_move`: maximum absolute close-to-close 60-bar move, in percent.
- `max_4h_move`: maximum absolute close-to-close 240-bar move, in percent.
- `trend_day`, `chop_day`, `expansion_day`, `reversal_day`: descriptive labels from the day's return, range, realized volatility, and intraday reversal profile.
- `session_volatility_distribution`: JSON map for Asia, London, US, and late-US realized volatility.
- `large_move_windows`: top descriptive 1h/4h close-to-close move windows.

Labels are descriptive only. They are not entry rules.

## Summary

The scan produced 68 dated feed surfaces:

- 54 primary-only clean surfaces.
- 14 surfaces that splice primary rows outside the outage with recovered rows inside the outage.

Discovery surface summary:

| surface | days | avg_volume_sum | avg_daily_return_pct | avg_high_low_range_pct | avg_realized_volatility | avg_max_1h_move | avg_max_4h_move |
|---|---:|---:|---:|---:|---:|---:|---:|
| trend_day | 32 | 147438.751797 | 0.230209 | 3.877930 | 2.129347 | 1.781476 | 2.558361 |
| chop_day | 11 | 50004.505791 | -0.053910 | 1.854029 | 1.467316 | 0.901556 | 1.268009 |
| expansion_day | 24 | 190219.481686 | 0.688759 | 4.353045 | 2.584153 | 1.938024 | 2.976264 |
| reversal_day | 9 | 167144.797462 | 0.582639 | 4.200669 | 2.359231 | 1.938258 | 3.063953 |
| data_lineage | 68 | 129015.100697 | 0.146850 | 3.173727 | 2.023863 | 1.512908 | 2.112817 |

Largest range days in the local clean surface include:

- `2026-04-07`: 7.312622% range, 4.555349% daily return, 6.120538% max 4h move.
- `2026-03-23`: 6.471563% range, 4.507553% daily return, 5.095177% max 4h move.
- `2026-04-13`: 6.155628% range, 5.265242% daily return, 3.381531% max 4h move.
- `2026-03-18`: 5.654352% range, -3.604193% daily return, 4.023056% max 4h move.
- `2026-03-27`: 5.294084% range, -3.572711% daily return, 3.378946% max 4h move.

Recovered-window surfaces are mostly low-volume relative to primary clean days, but they still contain trend/chop/expansion/reversal behavior after replacing contaminated primary rows.

## Interpretation

The feed contains multiple market behavior classes: directional trend days, low-range chop days, high-range expansion days, and intraday reversal days. This supports a research reset toward behavior discovery rather than another broad failed-break/reclaim rerun.

No strategy edge is claimed from this audit.
