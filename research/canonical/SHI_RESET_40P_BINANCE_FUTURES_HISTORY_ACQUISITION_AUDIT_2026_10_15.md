# SHI_RESET_40P_BINANCE_FUTURES_HISTORY_ACQUISITION_V0

Executed 2026-10-15. User request: “Підтягуй з бінанс архів необхідних данних для бектесту з березня 2025.”

## Scope and repository

This subsequent instruction authorizes historical **data acquisition** after 40O stopped; it does not waive the failed source gate or request OOS strategy execution. The end date and warm-up follow the user's existing 40O interval without selecting dates from outcomes. No strategy module is imported by the data tool. No features, candidates, trades or financial returns are computed. No API keys, spot downloads, funding charges, orders, borrowing, live services, Executor or production-rule changes.

Starting commit: `733177740850675f98d50fe0e2ae412870725c82`, the completed 40O research commit. Dedicated branch: `codex/SHI_RESET_40P_binance_futures_history_acquisition_v0`. The publication base `def5060680b31b6639c39d3e00b061ccf147d4c9` remains preserved in history. Final commit is recorded by Git history; no automatic merge/push to main.

Run root: [SHI_RESET_40P_binance_futures_history_acquisition_v0](../../market_monitor_runs/SHI_RESET_40P_binance_futures_history_acquisition_v0/). [Run manifest](../../market_monitor_runs/SHI_RESET_40P_binance_futures_history_acquisition_v0/run_manifest.json) was written before acquisition and freezes the source plan, adapter/tool hashes, boundaries, prior file hashes and data-only scope.

## Official sources and integrity

Official Binance public [USD-M archive source](https://data.binance.vision/) and [schema](https://github.com/binance/binance-public-data/blob/master/README.md#futures): BTCUSDT perpetual futures, 1-minute klines.

**23 ZIPs**, each with its unchanged published `.CHECKSUM`: 13 monthly February 2025–February 2026, nine daily March 1–9 2026, one daily January 31 2025 boundary source. All 23 official SHA256 values match local bytes. ZIP total **24,596,772 bytes**; **580,320 original rows**. The manifest records exact URL/path, cadence/date, symbol/market/interval, size, checksum, rows, first/last original exchange clocks and normalized labels. No private API is used.

The original ZIPs, CHECKSUM files and normalized daily CSVs remain in the isolated local run cache. Bulk cache bytes are not Git-tracked; exact documented references, full checksums and the acquisition/reproduction tool are committed. Transfer these cache files or reproduce them from the pinned official URLs; a Git clone alone does not contain the bulk data. See [run README](../../market_monitor_runs/SHI_RESET_40P_binance_futures_history_acquisition_v0/README.md) and [source manifest](../../market_monitor_runs/SHI_RESET_40P_binance_futures_history_acquisition_v0/source_manifest.json).

## Time and normalized observations

Unchanged 40O source adapter: exchange candle open +60 seconds → right-close label. Original raw epoch values and exchange open/close UTC clocks remain alongside the normalized timestamp. Prices round to 2 decimals; base quantities to 6. BuyQty = taker-buy base quantity; SellQty = unrounded total minus unrounded buy, then rounded. Binance number-of-trades is retained with its component-trade semantics; it is not claimed equal to SHI aggTrade callback counts. OI/funding/liquidation fields are flagged unavailable placeholders and are not a blocker or additional filter.

The complete normalized interval is **2025-02-01 00:00 through 2026-03-09 23:59 UTC**, **578,880 rows / 402 daily CSVs / 175,750,532 bytes**:

| Source partition | Right-close UTC labels | Rows |
|---|---|---:|
| Warm-up only | 2025-02-01 00:00–2025-02-28 23:59 | 40,320 |
| Intended later evaluation source | 2025-03-01 00:00–2026-03-09 23:59 | 538,560 |

January 31 23:59 exchange-open supplies February 1 00:00 right-close. Exactly 1,440 source rows outside the declared right-close boundaries are excluded from normalization: 1,439 earlier January 31 labels and one March 10 00:00 label. Original archives remain untouched; no scored date is moved. No expiry tail beyond the inherited cutoff is acquired or implied.

Every normalized daily file has 1,440 unique chronological minute labels. **Zero missing minutes, zero duplicate minutes**. **18 consecutive official non-traded minutes**, August 29 2025 06:20–06:37 UTC right-close labels, remain with zero quantity/status flags; they are observations from the archive, not missing minutes or fabricated replacement bars. This contiguous interval is explicitly listed in [nontraded_minutes.csv](../../market_monitor_runs/SHI_RESET_40P_binance_futures_history_acquisition_v0/nontraded_minutes.csv). No entry-policy decision about that interval is made in this data-acquisition task. Continuous UTC is preserved.

[Normalized inventory](../../market_monitor_runs/SHI_RESET_40P_binance_futures_history_acquisition_v0/normalized_inventory.csv) records each daily file's SHA256, size, time bounds, counts and partition. [Normalization summary](../../market_monitor_runs/SHI_RESET_40P_binance_futures_history_acquisition_v0/normalization_summary.json) records coverage and schema semantics. [Verification](../../market_monitor_runs/SHI_RESET_40P_binance_futures_history_acquisition_v0/verification.json) independently reopens all files and verifies checksums, hashes, full minute grid and +60-second mapping.

## Preservation and phase decision

40O `artifact_hashes.json` and its listed artifacts, its original source/strategy identity map, protected feed assets and selected 40H/L pointers remain unchanged. The complete 40O failure and null/NOT_RUN result are historical evidence and are not rewritten to describe the later 40P acquisition. New data acquisition does not alter the result `BINANCE_KLINE_SURROGATE_PARITY_FAILED`.

**Outcome: requested historical data acquired and integrity-verified. Historical strategy outcomes remain unseen.** Source-semantics/parity resolution remains necessary before the previously declared 40O OOS replay. No server-shadow or live phase is advanced. No BTCUSDC execution history was downloaded in this follow-up.

## Verification

Research-only tests cover the declared archive plan/boundary source, strict warm-up versus evaluation-source separation, and rejection of missing/duplicate minutes. Together with the existing normalization/parity contracts, **16 targeted tests pass**. Full regression: **787 passed**, 11 existing warnings; results are recorded in `test_regression.xml` under the new run. Existing tests are unchanged. Before downloading, an initial local test exposed a naive/UTC endpoint mismatch in the new plan helper; it was corrected before manifest freeze and acquisition, then all targeted checks passed.
