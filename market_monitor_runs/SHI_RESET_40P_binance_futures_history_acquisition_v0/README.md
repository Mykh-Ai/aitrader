# 40P — Binance historical futures data acquisition

User-authorized follow-up after the completed 40O source-parity failure. Data acquisition and integrity checks only; no strategy execution or outcome inspection.

- Market: official Binance BTCUSDT USD-M Perpetual Futures, 1-minute klines.
- Intended later evaluation interval, inherited unchanged from 40O: **2025-03-01 00:00 through 2026-03-09 23:59 UTC**, right-close labels.
- Warm-up: **2025-02-01 00:00 through 2025-02-28 23:59 UTC**. The January 31 daily archive supplies only the exchange-open 23:59 candle needed for the first February 1 right-close label.
- 23 original ZIPs and their published CHECKSUM files: 13 monthly archives February 2025–February 2026, nine daily March 1–9 2026, one January 31 boundary archive.
- 578,880 normalized rows in 402 daily files: 40,320 warm-up and 538,560 evaluation-source rows. No missing or duplicate UTC minutes. Eighteen consecutive official rows, August 29 2025 06:20–06:37 UTC right-close labels, have no trades and remain explicitly marked; no replacement rows were fabricated. See [nontraded observations](nontraded_minutes.csv).

Local cache directories: [official archives](official_archives/klines/) and [normalized daily observations](normalized_futures_feed/). The cache is retained locally under this run, outside the protected SHI feed. Bulk cache bytes are not Git-tracked. [Source manifest](source_manifest.json), [archive inventory](archive_inventory.csv), [normalized inventory](normalized_inventory.csv), and [verification](verification.json) provide exact URLs, paths, byte sizes, official/local SHA256 and row counts for transfer or reproduction. Cloning the repository alone does not supply these bulk data files.

Normalization reuses the **unchanged** [40O archive adapter](../SHI_RESET_40O_binance_futures_archive_oos_validation_v0/archive_source.py), with its output directory explicitly redirected here and its hash frozen. Exchange-open +60 seconds gives the right-close label. Original exchange open/close timestamps remain in each row. Prices use two decimals, quantities six; buy quantity is taker-buy base volume, sell quantity is raw total minus raw buy before rounding. Trade counts are Binance component trades, not SHI received aggTrade-event counts. OI/funding/liquidation zeros are inherited unavailable schema placeholders with availability flags, not measured values or new filters.

Reproduction from the repository root (Python and pandas already installed):

```powershell
# The original run_manifest.json is committed; do not prepare or overwrite it again.
python market_monitor_runs/SHI_RESET_40P_binance_futures_history_acquisition_v0/acquire_history.py acquire
python market_monitor_runs/SHI_RESET_40P_binance_futures_history_acquisition_v0/acquire_history.py normalize
python market_monitor_runs/SHI_RESET_40P_binance_futures_history_acquisition_v0/acquire_history.py verify
```

`acquire` needs access only to public `data.binance.vision`; no API key. Existing archives are reused only after official checksum verification. A failure is retained in the source manifest and prevents normalization. `verify` is offline and checks every archive checksum, normalized file hash, complete UTC grid, timestamp mapping and preserved prior identities. The preservation checks in `normalize`/`verify` also require the hash-pinned prior 40O source assets, including the external SHI inputs documented by 40N; keep those available when reproducing this complete audit.

Verification: 16 targeted tests and 787 full regression tests passed; 11 existing warnings. JUnit results are retained in this run.

**Data-ready is not source-parity acceptance.** The 40O gate remains `BINANCE_KLINE_SURROGATE_PARITY_FAILED`. The later user instruction authorizes downloading this history; it does not waive the gate or authorize an OOS strategy replay. No historical signal candidates, trades, returns, variants or production changes were produced. Old 40O manifests/results accurately describe that task's earlier stop and remain byte-identical.
