# SHI RESET 39A Current Snapshot: 2026-09-29 19:19 UTC

Verdict: `PASS / CURRENT_DIAGNOSTIC_SNAPSHOT`

This is a read-only BTCUSDT Market Monitor snapshot at the latest verified closed minute available in the stable server-feed copy: `2026-09-29T19:19:00Z`. It is descriptive evidence, not a candidate, trade signal, edge claim, or live-like lifecycle validation.

## Inputs and reproduction

- Run root: `market_monitor_runs/SHI_RESET_39A_2026_09_29_1919UTC_snapshot_v0/`.
- Reproduce locally with `python -m market_monitor_runs.SHI_RESET_39A_2026_09_29_1919UTC_snapshot_v0.build_snapshot`.
- Main source: server `/opt/aitrader_data/feed/YYYY-MM-DD.csv`, copied into local `feed/`.
- Added four complete days, `2026-09-25` through `2026-09-28`, plus a stable copy of the active `2026-09-29` file through 19:19 UTC.
- Complete-day files each contain 1,440 ordered unique UTC-minute rows with no gaps. The current-day copy contains 1,160 ordered unique rows from 00:00 through 19:19 UTC with no internal gaps.
- The copied files match the server-side SHA-256 values recorded in `source_manifest.csv`. The current-day copy SHA-256 is `7f9e582c7c58d81c63775c17e5a378e0d53bdbd1e91028a101960bfcaedb9a84`.
- During the documented outage `2026-04-23T17:05:00Z` through `2026-05-06T22:51:00Z`, the run selects `feed_recovered/` minute by minute and marks it degraded. No feed row was synthesized or rewritten by this task.
- The run uses the same verified server-copy Market Monitor package as the 2026-09-18 snapshots. The v39A builder SHA-256 is `f10cb65d3e4df0d8ae841cdbf641b50461904583a943bbc164d1e49c3caded0c`; the copied v1 builder SHA-256 is `5d62e1ac5479e3a4834e4c18aec7e0099abfa94c63b66b685fd2a44063bdd2b1`.

## Snapshot at cutoff

| Field | Value |
| --- | ---: |
| Cutoff | `2026-09-29T19:19:00Z` |
| Close price | 83,613.20 USDT |
| Overall readiness | `READY_WITH_RECOVERED_DATA` |
| 5/15/30/60/240-minute windows | `COMPLETE_RAW` |
| 1440-minute window | `COMPLETE_RECOVERED_DEGRADED` |
| v1/37E market state | `MARKET_STRUCTURE_CONTEXT`, LOW confidence, candidate bias `NONE` |
| Observed 240m low / high | 82,851.50 / 83,674.00 USDT |
| Observed 1440m low / high | 82,724.30 / 84,554.90 USDT |

| Window | Rows | Start | Price change | Delta BTC | Delta / total qty | OI change | Status |
| --- | ---: | --- | ---: | ---: | ---: | ---: | --- |
| 5m | 5 | 19:15 | +0.05588364% | -113.134 | -0.2652116836 | -88.21 | `COMPLETE_RAW` |
| 15m | 15 | 19:05 | +0.01232015% | -51.919 | -0.0609596158 | -55.48 | `COMPLETE_RAW` |
| 30m | 30 | 18:50 | +0.01578947% | -185.569 | -0.1378298423 | -83.94 | `COMPLETE_RAW` |
| 60m | 60 | 18:20 | +0.26609490% | -117.461 | -0.0282915639 | -205.67 | `COMPLETE_RAW` |
| 240m | 240 | 15:20 | +0.42674629% | +995.687 | +0.0315261313 | -180.44 | `COMPLETE_RAW` |
| 1440m | 1440 | 2026-09-28 19:20 | -0.08090257% | +156.437 | +0.0012536018 | +91.55 | `COMPLETE_RECOVERED_DEGRADED` |

Every window ends exactly at the cutoff and has zero missing timestamps and zero duplicate rows. The 1440-minute window contains 1,160 RAW current-day rows and 280 rows from `2026-09-28.csv`. That source file contains one synthetic minute at 14:58 UTC, outside the 1440-minute window, but the current adapter conservatively assigns source-file-level degraded provenance to all rows from that file. The window is complete but its lineage remains degraded rather than being silently presented as fully raw.

The v39A JSON field is named `delta_pct`, but this implementation stores the unitless ratio `delta / total_qty` rather than a value multiplied by 100. The table preserves the stored values and labels their units explicitly.

## State and boundary

The v1/37E base reports `MARKET_STRUCTURE_CONTEXT` at LOW confidence with no candidate bias. It identifies high-confidence support at 80,095.90–82,282.80 USDT and no qualified resistance zone. The v39A observed-window structure places the 240m high at 83,674.00 and the 1440m high at 84,554.90.

The snapshot state envelope is `INITIALIZED`: no persisted v39A runtime state was loaded or written, and earlier closed candles were not replayed one by one to reconstruct continuous production state. This point-in-time snapshot must not be interpreted as a validated state transition, setup, or trading instruction.

## Data quality and verification

- Full history used: `2026-03-11T13:45:00Z` through `2026-09-29T19:19:00Z`.
- Rows used: 291,213; RAW: 253,159; RECOVERED_DEGRADED: 38,054.
- Thirteen historical missing minutes remain in the full span; none lies in the six snapshot windows.
- Snapshot SHA-256: `3cc05ed9aab69834a0d23f9430ec27ce29c3f8fd45e77582abae773de9bfe842`.
- Repeated build produced the same snapshot and diagnostics hashes.
- `python -m pytest -q tests/test_snapshot_builder_v39a.py`: 3 passed.
- No Binance API call, order action, deployment, service restart, or production-state write occurred.
