# Feed Contract and Schema Notes

## Preserved inputs

- `feed/` preserved.
- `feed_recovered/` preserved.

Do not overwrite `feed/` to hide the 2026 websocket outage. Use `feed_recovered/` only as documented recovered input.

User-authorized40K refresh on2026-10-15 extends local primary futures data throughOctober14 23:59UTC. October13partial480rows was backed up and replaced with its exact1440-row server continuation; October14added. Both full days have1440orderedRAW minutes without gaps/duplicates/synthetics and exact serverSHA256. October15partial not imported; recovered history unchanged. Separate officialBTCUSDC spot13/14archives and combined normalized CSV live under`market_monitor_runs/SHI_RESET_40K_data_refresh_through_2026_10_14_v0/spot_BTCUSDC/`. Last spot right-closeOctober15 00:00 is the finalOctober14candle, not partialOctober15data. Existing40B/40G/40H identities/cutoffs remain frozen; latest local availability does not imply the old experiment admitted October signals. See40K canonical audit/data-readiness evidence.

The separately declared40L continuation now admits October1–14 with selected40H rules. It consumes313093futures rows/232source files and313063RAW spot observations through the commonOctober14 23:59UTC cutoff; the spot right-closeOctober15 00:00 is trimmed from this replay. Last completed signalH1 closesOctober14 23:00UTC; its next observed minute may support a precise entry without fabricating a future completedH1. Prior-state prefix/source identities verified; no protected feed write occurs in40L. Read `research/canonical/SHI_RESET_40L_CHRONOLOGICAL_REPLAY_AUDIT_2026_10_15.md`.

## Removed legacy feed day

`feed/2026-03-10.csv` was removed from the active repo because it used a legacy incompatible feed schema. Active feed starts from the normalized schema after 2026-03-10. This avoids carrying an adapter exception for a single early legacy day.

## Historical SHI feed schema

- `Timestamp`
- `Open`
- `High`
- `Low`
- `Close`
- `Volume`
- `AggTrades`
- `BuyQty`
- `SellQty`
- `VWAP`
- `OpenInterest`
- `FundingRate`
- `LiqBuyQty`
- `LiqSellQty`
- `IsSynthetic`

## Mapping to protected raw schema

| Historical SHI column | Protected raw schema |
|---|---|
| `AggTrades` | `Trades` |
| `Volume` | `TotalQty` |
| `Close` | `ClosePrice` |
| `High` | `HiPrice` |
| `Low` | `LowPrice` |
| `Open` | `OpenPrice` |

`market_monitor.feed_adapter` also preserves `LiqBuyQty` and `LiqSellQty` under
their source names. `LiquidationDataAvailable` distinguishes feed rows whose
source schema actually supplied both fields from compatibility rows where the
adapter supplies numeric zero placeholders. The base `volume_delta_state.csv`
therefore carries `liq_buy_qty`, `liq_sell_qty`, `liq_total_qty`, and
`liquidation_data_available`; this is evidence transport only and does not, by
itself, promote liquidations into zone scoring or setup policy.

## Recovery caveats

Primary contamination window:

`2026-04-23 17:05:00 UTC -> 2026-05-06 22:51:00 UTC`

`feed_recovered/` is usable with caveats. Recovered rows mirror DeltaScout's recovered SHI-compatible feed. Price/OHLCV/trades/buy/sell/VWAP were recovered from the legacy volume-alert archive where available; OI was copied or forward-filled where possible; funding is untrusted during the websocket gap; historical liquidation quantities are missing.

OI/Funding/Liquidations during the recovered gap must be treated carefully. Do not make funding/liquidation-based conclusions from recovered rows unless explicitly marked degraded/unsupported.

## Diagnostic replay source selection

For read-only Market Monitor diagnostics, replays, visual overlays, and research summaries, do not blindly prefer `feed/` during the known recovery/contamination window:

`2026-04-23 17:05:00 UTC -> 2026-05-06 22:51:00 UTC`

For day-level diagnostic replays that include this window, use `feed_recovered/YYYY-MM-DD.csv` for `2026-04-23` through `2026-05-06` when those recovered files exist. Do not use the flat zero-volume placeholder rows from `feed/` as market evidence for those dates.

For minute-precise tooling, `feed/` is usable before `2026-04-23 17:05:00 UTC` and after `2026-05-06 22:51:00 UTC`; rows inside the known outage window must come from `feed_recovered/` when available.

Do not copy recovered rows into `feed/` and do not overwrite primary feed evidence.

Every artifact that uses recovered rows must mark the source as `RECOVERED_DEGRADED` and state the caveat in the report. If recovered data is also missing or invalid, report the data gap instead of synthesizing rows or forcing a phase/liquidity conclusion.

Future Market State Monitor work must use an adaptor/contract layer, not ad-hoc column assumptions.

## Signal market versus execution market — user clarification40G

`binance_aggregator_shi.py` collects Binance BTCUSDT perpetual futures prices/flow for signals. Its declared trading target is Binance Spot Margin BTC/USDC. The protected futures feed is not a spot-price feed. 40C–40F1 financial experiments used futures execution-price proxies and must retain that label.

40G freezes separate official BTCUSDC Spot1m archives under `market_monitor_runs/SHI_RESET_40G_futures_signals_spot_execution_v0/spot_BTCUSDC/`:48 archives, each verified against official SHA256.33 were reused read-only from Executor's existing official archive cache and15 days downloaded publicly. No spot row is copied into `feed/` or `feed_recovered/`. Raw archives, normalized CSV, daily quality and source manifest are retained.

The2026 official spot epoch is microseconds. Normalize candle-open UTC to a right-close label by adding60 seconds; do not mistake the exchange's inclusive close timestamp ending59.999999 for a different minute. Restrict selected spot observations to the same frozen source cutoff used by signals. Zero-trade spot minutes remain in provenance and are skipped as execution observations; isolated omissions continue on the next real minute with actual timestamps, while extended gaps remain separately classified.

Futures feed features/H4 state generate decisions. Spot minute open/high/low/close determines execution. In the primary40G contract, futures structural levels/ATR are mapped to USDC using the last known BTCUSDC spot close divided by last known BTCUSDT futures close at the signal decision, each no older than one minute. Never use the later entry open to estimate that mapping. A native-spot stop-source sensitivity is a different declared contract. Record market, symbol, quote currency, reference timestamps, conversion and omissions in the journal.

The user model is3,000 USDC notional,5 USDC commission per completed trade and2bps adverse slippage per fill, with dollar display assuming USDC/USD parity. Futures funding is not a spot trading charge. Short requires BTC margin borrowing; actual historical loan availability/rates and exchange charging are not established by spot OHLCV.40G keeps hypothetical borrowing sensitivities separate from its fee/slippage result. Candle-price replay also does not prove orderbook liquidity or actual account fills.

## Continuous-context and quality contract

Historical Market Monitor entry points select daily files through the governed
source resolver. Required recovered days fail loudly when the recovered file is
missing; base feed is not a fallback inside the known outage interval.

`DataQuality` is row-level: `RAW`, `RECOVERED_DEGRADED`, or `SYNTHETIC`.
`SourceClass` separately preserves raw versus recovered lineage. Exact rolling
window diagnostics retain duplicates until they have been counted and report
missing timestamps instead of silently treating sparse rows as a complete
window. A degraded row does not remove the rest of its day from progression.

40N publication preserves both the40M research handoff and the existing production-continuity ADR`docs/MARKET_MONITOR_CONTINUOUS_CONTEXT_AND_GAP_POLICY_ADR.md`. Read `research/canonical/SHI_RESET_40N_GIT_PUBLICATION_AUDIT_2026_10_15.md` for exact snapshot reproduction after the merge; do not rewrite historical source/code hashes to match current runtime files.
