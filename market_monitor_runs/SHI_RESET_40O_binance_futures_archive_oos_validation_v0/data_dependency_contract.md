#40O — inspected source dependency contract

PhaseA inspected the collector, frozen feed/features/hybrid/replay,40F H4 gate,40H selected artifacts and40L composition before the first official archive request. Publication base:def5060680b31b6639c39d3e00b061ccf147d4c9. Executed historical implementation is recovered byte-exact from0862342, not substituted with the later main continuity implementation.

```text
official Binance BTCUSDT USD-M1m ZIP + official CHECKSUM
→ exact original archive kept; schema/time/quantity validation
→ separate research minute observations: exchange-open+60s right-close
→ isolated primary omission policy; chronological H1/H4 without reset
→ frozen EMA24/72/168, ATR24, previous-volume median, flow, shifted references
→ frozen LONG trend-retest / SHORT accepted-break+pressure candidates
→ frozen causal confirmed-H4 short-space gate
→ selected40H raw rolling24h strict(-4,+4) and LONG rolling4h>0
→ pre-book decision parity gate
→ ONLY AFTER PASS: one global futures-price-proxy book/unchanged stops/exits/costs
```

|Source evidence|Mapping|Selected-strategy dependency|
|---|---|---|
|open_time / close_time|Preserve raw exchange clocks; Timestamp=open+60s|H1/H4 completion and availability, rolling windows, entry/expiry clocks|
|open/high/low/close|OpenPrice/HiPrice/LowPrice/ClosePrice,2dec|EMA, retest/break, ATR/risk, prior6/48/96 references, H4 swing/retirement, fills|
|base volume|TotalQty,6dec|H1 volume/prior24-H1 median, signed H1 flow, weighted rolling4/24h delta|
|taker-buy base volume|BuyQty,6dec|Buy-side signed quantity|
|base volume minus taker-buy|SellQty from unrounded values then6dec|Sell-side signed quantity; paired denominator validation|
|trade count / nonzero volume|Traded flag; synthetic/nontraded observations omitted|Quality/continuity; exact count is NOT an entry, gate, stop or exit input|
|OI/funding/liquidations|Unavailable, zero-valued compatibility columns with explicit false availability|Not required by selected40H; never a source blocker/filter/spot funding charge|
|VWAP/quote volume|Not required by selected formulas|Not an entry/gate/exit input|

SHI counts callback aggTrade events; Binance kline count may count component trades. No exact Trades-count equality required. Collector side rule:m=True→SellQty,m=False→BuyQty. Price/quantity comparisons apply the documented2/6decimal output. Tolerances:prices1e-8; base quantities1.0001e-6 for independently rounded components; frozen strategy thresholds unchanged.

Collector CandleBuffer.add_trade has no exchange-time bucket assignment; callbacks accumulate in receipt order, flush_candle stamps the current UTC minute and resets. Archive right-close normalization reproduces the intended clock label but cannot be assumed to reproduce historical callback arrival/grouping. Observed difference is measured, not hidden by a fitted offset. No negative shift/session extrema or future-derived entry context is introduced.

Source-validation context is2026-03-11 13:45–September30 23:59UTC:21dailyMarch11–31 and6monthlyApril–September ZIPs. EarlierMarch1–9 OOS observations are not requested while adapting normalization. Scored parity windows are the entire July/September months, not selected successful candles. July has9andSeptember2SHI nontraded/synthetic discrepancies despite lying outside the April/May recovery window; these are retained, not dropped to improve parity.

Original40H control uses its existing local BTCUSDC evidence only to prove exact historical code identity; no spot history was downloaded. Any later permitted OOS run would use BTCUSDT futures prices only and be labelled FUTURES_PRICE_PROXY. The declared2025-02 warmup and2025-03-01–2026-03-09 score remain unopened after the failed source gate.
