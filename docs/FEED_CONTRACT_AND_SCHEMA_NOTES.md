# Feed Contract and Schema Notes

## Preserved inputs

- `feed/` preserved.
- `feed_recovered/` preserved.

Do not overwrite `feed/` to hide the 2026 websocket outage. Use `feed_recovered/` only as documented recovered input.

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

## Recovery caveats

Primary contamination window:

`2026-04-23 17:05:00 UTC -> 2026-05-06 22:51:00 UTC`

`feed_recovered/` is usable with caveats. Recovered rows mirror DeltaScout's recovered SHI-compatible feed. Price/OHLCV/trades/buy/sell/VWAP were recovered from the legacy volume-alert archive where available; OI was copied or forward-filled where possible; funding is untrusted during the websocket gap; historical liquidation quantities are missing.

OI/Funding/Liquidations during the recovered gap must be treated carefully. Do not make funding/liquidation-based conclusions from recovered rows unless explicitly marked degraded/unsupported.

Future Market State Monitor work must use an adaptor/contract layer, not ad-hoc column assumptions.
