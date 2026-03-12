# Стратегія Ші v1.0 — AI Trader

BTC research and analysis system being built toward algorithmic trading.
Currently at Phase 1: raw data collection + Analyzer facts engine.
Target execution: Binance Spot Margin BTC/USDC (isolated, max 2x) — planned Phase 4.

## System Architecture

```
Binance Futures API (fstream / fapi)
        │
   [raw market data]
        │
   Collector / Aggregator        ← Phase 1: IMPLEMENTED
   BTCUSDT Perpetual 1m feed
        │
   Analyzer (facts engine)       ← Phase 1: IMPLEMENTED
   schema → loader → base metrics
   → swings → sweeps → failed breaks
   → absorption → events → output
        │
   Research / Setup Extraction   ← Phase 2: NEXT
   setup candidates, edge stats
        │
   Backtester                    ← Phase 3: PLANNED
   6-month validation
        │
   Executor                      ← Phase 4: PLANNED
   Binance Spot Margin BTC/USDC (isolated, max 2x)
```

## Project Status

| Phase | Status | Description |
|-------|--------|-------------|
| 1. Raw feed + Analyzer facts engine | ✅ Implemented | 1m collector live; Analyzer computes all Phase 1 features and events |
| 2. Research / setup extraction | 🔜 Next | Candidate generation, edge statistics on labeled events |
| 3. Backtesting | 🔜 Planned | 6-month strategy validation |
| 4. Execution | 🔜 Planned | Live trading via Binance Spot Margin API |

## Analyzer — Scope

The Analyzer is a **facts engine**. It:

- Computes derived features and metrics from raw 1m feed
- Detects and normalizes structural events (swings, sweeps, failed breaks)
- Outputs a deterministic feature table and event table

The Analyzer does **not**:

- Open trades or generate live entry signals
- Perform strategy optimization or ruleset selection
- Act as executor or interface with the exchange

## Analyzer — Module Architecture

Package: `analyzer/`

| Module | Responsibility |
|--------|---------------|
| `schema.py` | Schema contracts: required column lists, feature column registry, `EVENT_COLUMNS`, `SchemaValidationError` |
| `loader.py` | Load and validate raw aggregator CSV: parse UTC timestamps, enforce required columns, coerce numerics, normalize `IsSynthetic`, reject duplicates |
| `base_metrics.py` | Compute per-bar derived metrics: Delta, CVD, DeltaPct, BarRange, BodySize, UpperWick, LowerWick, CloseLocation, BodyToRange, wick ratios, OI_Change, LiqTotal |
| `swings.py` | Detect H1/H4 structural fractal swings with confirmation delay; annotate feature table with `SwingHigh_*_Price`, `SwingHigh_*_ConfirmedAt`, `SwingLow_*` columns |
| `sweeps.py` | Detect H1/H4 sweeps of confirmed swing levels on 1m bars; annotate `Sweep_*_Up`, `Sweep_*_Down`, direction, reference level/timestamp |
| `failed_breaks.py` | Detect H1/H4 failed-break events: track bars-since-sweep forward in time; annotate `FailedBreak_*_Up`, `FailedBreak_*_Down`, confirmed timestamp |
| `absorption.py` | Compute deterministic rolling-ratio context features: `RelVolume_20`, `DeltaAbsRatio_20`, `OIChangeAbsRatio_20`, `LiqTotalRatio_20`, context spike booleans, `AbsorptionScore_v1` |
| `events.py` | Build normalized event table from materialized feature columns; emits `SWING_HIGH`, `SWING_LOW`, `SWEEP_UP`, `SWEEP_DOWN`, `FAILED_BREAK_UP`, `FAILED_BREAK_DOWN`; Confidence and MetaJson are null in this phase |
| `io.py` | Output helpers: ensure output directory exists, save DataFrames to CSV |
| `pipeline.py` | Orchestration entrypoint: wires the full layer sequence and saves artifacts (`analyzer_features.csv`, `analyzer_events.csv`) |

### Tests

`tests/` contains one test file per analyzer module:

```
tests/
├── test_schema.py
├── test_loader.py
├── test_base_metrics.py
├── test_swings.py
├── test_sweeps.py
├── test_failed_breaks.py
├── test_absorption.py
├── test_events.py
└── test_pipeline.py
```

`tests/fixtures/` holds minimal CSV files used as shared test inputs:

```
tests/fixtures/
├── sample_raw_minimal.csv
├── sample_raw_with_gap.csv
└── sample_raw_with_synthetic.csv
```

`docs/Spec_v1.0.md` is the normative Analyzer contract. Tests are written against the spec.

### Structural safety guards

### Synthetic bars and structural safety

The Analyzer preserves all rows in the dataset, including synthetic bars
(`IsSynthetic == 1`). Synthetic bars are required for:

- rolling metrics
- context features
- volume/OI continuity
- research reproducibility

However, synthetic bars are **not allowed to define market structure**.

Structural logic (swings, sweeps, failed-break confirmations) operates with
fail-closed rules:

- synthetic bars cannot define swing structure
- synthetic bars cannot trigger sweep events
- synthetic bars cannot confirm failed-break reclaim logic

Implementation detail:

```python
structure_df = df[df["IsSynthetic"] == 0]
```

Swing detection is performed on this structure-only subset, and confirmed
levels are then attached back to the full dataframe.

This design ensures that structural events are derived only from traded bars,
while synthetic rows remain available for contextual metrics and dataset continuity.

This prevents synthetic carry-forward bars or data-pipeline artifacts from
creating false structural events.

### Gap safety policy

Stateful logic (such as failed-break confirmation) is protected from large
timestamp discontinuities.

If the time difference between consecutive rows exceeds:

```python
MAX_STATE_GAP_MINUTES = 3
```

the internal pending state is reset.

This is a fail-closed safety mechanism designed to prevent structural
misinterpretation after:

- reconnects
- packet loss
- data gaps
- delayed ingestion

### Research note

The value of `MAX_STATE_GAP_MINUTES` is currently a conservative safety choice.
It may be adjusted after sufficient dataset collection and empirical analysis.

The goal at this stage is structural data integrity rather than maximal
event capture.

## Repository Structure

```
Aitrader/
├── binance_aggregator_shi.py   # Phase 1: raw 1m collector (LIVE)
├── analyzer/                   # Analyzer package (Phase 1)
│   ├── __init__.py
│   ├── schema.py
│   ├── loader.py
│   ├── base_metrics.py
│   ├── swings.py
│   ├── sweeps.py
│   ├── failed_breaks.py
│   ├── absorption.py
│   ├── events.py
│   ├── io.py
│   └── pipeline.py
├── tests/                      # Unit tests for Analyzer
│   ├── fixtures/               # Shared CSV test fixtures
│   ├── test_schema.py
│   ├── test_loader.py
│   └── ...
├── docs/
│   └── Spec_v1.0.md            # Analyzer spec and contract
├── feed/                       # 1m CSV files by day (not in git)
│   └── YYYY-MM-DD.csv
├── logs/                       # Aggregator logs (not in git)
├── Dockerfile
├── docker-compose.yml
└── CLAUDE.md
```

## Phase 1: Aggregator

### Raw feed schema (1m candles)

| Column | Source | Description |
|--------|--------|-------------|
| Timestamp | system | UTC bar open time |
| Open, High, Low, Close | aggTrade WS | OHLCV prices |
| Volume | aggTrade WS | Total volume |
| AggTrades | aggTrade WS | Number of Binance aggTrade messages (not individual fills) |
| BuyQty | aggTrade WS | Taker buy volume (for delta) |
| SellQty | aggTrade WS | Taker sell volume (for delta) |
| VWAP | aggTrade WS | 1m volume-weighted average traded price |
| OpenInterest | REST /fapi/v1/openInterest | Open interest snapshot (BTC) |
| FundingRate | markPrice WS | Funding rate |
| LiqBuyQty | forceOrder WS | Short liquidation volume |
| LiqSellQty | forceOrder WS | Long liquidation volume |
| IsSynthetic | system | 1 = synthetic candle (no trades in interval) |

### Data notes

**AggTrades** counts Binance aggTrade messages, not individual exchange fills. BuyQty / SellQty are accurate for delta and CVD. AggTrades should not be interpreted as true fill count.

**Synthetic candles** — when no trades occur during a 1m interval, the collector writes a synthetic candle using the last known price (mark price or last trade). Marked `IsSynthetic=1`. Analyzer modules may exclude these when computing compression or volatility features.

**Liquidation data** — derived from the `forceOrder` stream. Observed liquidation events; not a guaranteed complete record of all market liquidations. Intended for contextual analysis.

**BuyQty / SellQty** — taker-aggressor volume. They indicate which side initiated market orders but do not by themselves indicate directional control. Always combine with price response (close location, wick structure, range behavior).

**VWAP** — `sum(price * qty) / sum(qty)` per bar. Falls back to Close on synthetic candles.

### Storage

CSV by day: `feed/YYYY-MM-DD.csv`

### WebSocket streams

- `btcusdt@aggTrade` — trades
- `btcusdt@forceOrder` — liquidations
- `btcusdt@markPrice@1s` — funding rate, mark price

### REST endpoints

- `GET /fapi/v1/openInterest?symbol=BTCUSDT` — OI snapshot once per minute

## Running

### Collector — Docker (production)

```bash
docker compose up -d --build
docker logs -f shi-aggregator
```

### Collector — Local (dev)

```bash
pip install websocket-client requests
python binance_aggregator_shi.py
```

Output: `feed/YYYY-MM-DD.csv` — one file per UTC day.

### Analyzer pipeline

```python
from analyzer.pipeline import run

result = run("feed/2024-03-15.csv", output_dir="output/")
# writes: output/analyzer_features.csv
#         output/analyzer_events.csv

features = result["features"]   # pd.DataFrame — one row per 1m bar
events   = result["events"]     # pd.DataFrame — one row per detected event
```

Requires `pandas`. Tests: `pytest tests/`.

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| FEED_DIR | ./feed | CSV data directory |
| LOGS_DIR | ./logs | Log directory |

## Infrastructure

- **Server:** VPS 95.216.139.172 (Ubuntu 24.04, 4GB RAM, 38GB disk)
- **Location:** /opt/aitrader
- **Container:** shi-aggregator
- **Data:** /opt/aitrader/feed/ (mounted as volume)
- **Logs:** /opt/aitrader/logs/aggregator.log

## Health monitoring

Every 5 minutes:
```
💓 Health: WS=✅ | OI=83287 | FR=0.000027 | Mark=70400.00 | Candles=120/1440
```

## Target Architecture Constraints (Phase 4)

The following are fixed design constraints for the eventual execution layer.
They are not yet implemented — execution is Phase 4.

**Regulatory (MiCA / EU):**
- Futures trading prohibited for EU residents
- Futures public API (signal data) — no restrictions
- Execution: Binance Spot Margin BTC/USDC (max 10x, design target: 2x)

**Risk management (fixed, non-negotiable):**
- Risk per trade: 1%
- Position sizing: Risk / StopDistance
- Mode: Isolated Margin, max 2x leverage
- No cross margin, no martingale, no manual intervention
- Drawdown halt: 3% / day, 7% / week

**Scope constraints:**
- BTC only — no altcoins
- No parameter changes during drawdown
- No risk increases after a loss
