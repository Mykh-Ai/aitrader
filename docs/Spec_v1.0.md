# Strategy Shi — Analyzer Spec v1.0

Version: 1.0
Phase 1 Status: **Implemented**

---

## Phase 1 Implementation Status

### Implemented (Phase 1 complete)

| Layer | Module | Status |
|-------|--------|--------|
| Schema contract | `analyzer/schema.py` | ✅ |
| Input loader / validation | `analyzer/loader.py` | ✅ |
| Base metrics | `analyzer/base_metrics.py` | ✅ |
| H1/H4 structural swings | `analyzer/swings.py` | ✅ |
| H1/H4 sweep detection | `analyzer/sweeps.py` | ✅ |
| H1/H4 failed-break detection | `analyzer/failed_breaks.py` | ✅ |
| Absorption / context features v1 | `analyzer/absorption.py` | ✅ |
| Normalized event table | `analyzer/events.py` | ✅ |
| Output helpers | `analyzer/io.py` | ✅ |
| Pipeline orchestration | `analyzer/pipeline.py` | ✅ |

### Planned (Phase 2+)

| Layer | Status |
|-------|--------|
| Session context features (`session`, `minutes_from_eu_open`, `minutes_from_us_open`) | 🔜 Planned |
| Confidence scoring (Block 5) | 🔜 Planned |
| Setup / candidate extraction | 🔜 Phase 2 |
| Statistical edge validation | 🔜 Phase 3 |
| Ruleset selection | 🔜 Phase 3 |
| Live execution decisions | 🔜 Phase 4 |

---

## Implemented Analyzer Architecture

The Analyzer is a layered facts engine. Each layer adds columns to a shared DataFrame and passes it forward.

```
load_raw_csv()          schema.py / loader.py    — input validation, UTC parsing
        ↓
add_base_metrics()      base_metrics.py           — per-bar derived metrics
        ↓
annotate_swings()       swings.py                 — H1/H4 fractal swing detection
        ↓
detect_sweeps()         sweeps.py                 — sweep of confirmed swing levels
        ↓
detect_failed_breaks()  failed_breaks.py          — forward-in-time failed-break confirmation
        ↓
detect_absorption()     absorption.py             — rolling-ratio context features
        ↓
build_events()          events.py                 — normalize to event table
        ↓
save_dataframe()        io.py                     — write analyzer_features.csv + analyzer_events.csv
```

### Layer responsibilities

**schema.py** — Defines `REQUIRED_RAW_COLUMNS`, `NUMERIC_RAW_COLUMNS`, `FEATURE_COLUMNS_IMPLEMENTED`,
`FEATURE_COLUMNS_PLANNED`, `EVENT_COLUMNS`, and `SchemaValidationError`.
The feature column registry is the authoritative list of what the Phase 1 pipeline materializes.

**loader.py** — Loads raw aggregator CSV. Validates required columns, coerces numeric fields,
normalizes `IsSynthetic` to `{0,1}`, parses `Timestamp` as UTC datetime, sorts ascending,
rejects duplicate timestamps. Preserves gaps (no synthetic backfill).

**base_metrics.py** — Computes: Delta, CVD, DeltaPct, BarRange, BodySize, UpperWick, LowerWick,
CloseLocation, BodyToRange, UpperWickToRange, LowerWickToRange, OI_Change, LiqTotal.

**swings.py** — Builds H1 and H4 bars from 1m data. Applies strict 3-bar local extremum
(1 left / 1 right neighbor) for both TFs. No ATR filter in Phase 1. Writes
`SwingHigh_{TF}_Price`, `SwingHigh_{TF}_ConfirmedAt`, `SwingLow_{TF}_Price`,
`SwingLow_{TF}_ConfirmedAt` columns. `ConfirmedAt = swing_bar_start + 2×TF`
(H1: +2h; H4: +8h).

**sweeps.py** — On 1m bars, detects first-cross of confirmed H1/H4 swing levels.
Writes `Sweep_{TF}_Up`, `Sweep_{TF}_Down`, `Sweep_{TF}_Direction`, `Sweep_{TF}_ReferenceLevel`,
`Sweep_{TF}_ReferenceTs`. Sweep direction is mutually exclusive per timeframe per bar;
ambiguous double-breach bars fail closed (no sweep emitted).

**failed_breaks.py** — Scans forward in time from each sweep bar to detect failed-break confirmation.
Writes `FailedBreak_{TF}_Up`, `FailedBreak_{TF}_Down`, `FailedBreak_{TF}_Direction`,
`FailedBreak_{TF}_ReferenceLevel`, `FailedBreak_{TF}_ReferenceSweepTs`, `FailedBreak_{TF}_ConfirmedTs`.
References only already-known sweep facts; confirms forward.

**absorption.py** — Computes rolling-ratio context features over a 20-bar window (no future leakage):
`RelVolume_20`, `DeltaAbsRatio_20`, `OIChangeAbsRatio_20`, `LiqTotalRatio_20`;
spike boolean flags (`CtxRelVolumeSpike_v1`, `CtxDeltaSpike_v1`, `CtxOISpike_v1`, `CtxLiqSpike_v1`,
`CtxWickReclaim_v1`); additive `AbsorptionScore_v1`.
This is a context-stress helper for research — not a trading signal.

**events.py** — Reads materialized feature columns and emits a normalized event DataFrame.
Anti-duplication: swing events are emitted only when the confirmation timestamp changes versus
the prior row (prevents re-emission from persistent "latest confirmed swing" columns).
Sweep and failed-break events emit only on rows where the boolean flag is True.
Output is sorted deterministically by `[Timestamp, SourceTF, EventType, Side]`.

**io.py** — `ensure_output_dir()`, `save_dataframe()` (CSV). Current output format is CSV.

**pipeline.py** — `run(input_path, output_dir)` wires the full sequence and returns a metadata
dict with in-memory DataFrames and output file paths.

---

## Implemented Event Types

The following event types are currently emitted by `events.py`:

| EventType | Source | Description |
|-----------|--------|-------------|
| `SWING_HIGH` | swings layer | New H1 or H4 swing high confirmed |
| `SWING_LOW` | swings layer | New H1 or H4 swing low confirmed |
| `SWEEP_UP` | sweeps layer | Upward sweep of a confirmed swing high level |
| `SWEEP_DOWN` | sweeps layer | Downward sweep of a confirmed swing low level |
| `FAILED_BREAK_UP` | failed-breaks layer | Failed break of an upward-swept level |
| `FAILED_BREAK_DOWN` | failed-breaks layer | Failed break of a downward-swept level |

> **Note on naming:** The spec sections below (3.11, 3.7) use earlier draft names
> (`SWEEP_HIGH`, `SWEEP_LOW`, `FAILED_BREAK_HIGH`, `FAILED_BREAK_LOW`).
> The implemented names are `SWEEP_UP/DOWN` and `FAILED_BREAK_UP/DOWN` as shown above.
> The spec will be reconciled in a future revision.

Event types listed in the spec but **not yet implemented**:
`WICK_REJECTION_HIGH`, `WICK_REJECTION_LOW`, `BREAK_HIGH`, `BREAK_LOW`,
`ACCEPTED_BREAK_HIGH`, `ACCEPTED_BREAK_LOW`.

---

## Implemented Event Field Semantics

Current `EVENT_COLUMNS`: `Timestamp`, `EventType`, `Side`, `PriceLevel`, `SourceTF`,
`ReferenceSwingTs`, `ReferenceSwingPrice`, `Confidence`, `MetaJson`.

| Field | SWING_HIGH / SWING_LOW | SWEEP_UP / SWEEP_DOWN | FAILED_BREAK_UP / FAILED_BREAK_DOWN |
|-------|------------------------|----------------------|--------------------------------------|
| `Timestamp` | Swing confirmation timestamp (`ConfirmedAt` = swing bar start + 2×TF) | Sweep occurrence row timestamp | Failed-break confirmation timestamp (`FailedBreak_{TF}_ConfirmedTs`) |
| `PriceLevel` | Swing price (High[i] or Low[i]) | Reference swing price level | Reference swing price level |
| `ReferenceSwingTs` | Same as Timestamp (self-referential) | Timestamp of the confirmed swing that was swept | Timestamp of the **sweep** that triggered the break (ReferenceSweepTs), not the original swing |
| `ReferenceSwingPrice` | Same as PriceLevel | Reference swing price | Reference swing price |
| `Confidence` | `NA` (null) in Phase 1 | `NA` (null) in Phase 1 | `NA` (null) in Phase 1 |
| `MetaJson` | `NA` (null) in Phase 1 | `NA` (null) in Phase 1 | `NA` (null) in Phase 1 |

`Confidence` and `MetaJson` will be populated in a later phase when confidence scoring (Block 5)
and lifecycle metadata are implemented.

> **ReferenceSwingTs note for FAILED_BREAK events:** In the current implementation,
> `ReferenceSwingTs` holds the sweep timestamp (`ReferenceSweepTs`), not the original swing
> timestamp. This differs from the description in section 3.7. This will be clarified in a
> future schema revision.

---

## Anti-Lookahead Rules — Implementation

The following rules are enforced in current code (see also Section 6 for full specification):

1. **Swing confirmation delay** — Both H1 and H4 use a strict 3-bar local extremum
   (1 left / 1 right neighbor). A swing at TF bar `i` becomes known only after bar `i+1`
   fully closes. `ConfirmedAt = Timestamp_of_bar_i + 2 × TF_duration`
   (H1: +2h; H4: +8h from the swing bar start). `SwingHigh_{TF}_ConfirmedAt` stores
   this timestamp; no downstream layer sees the swing before it.

2. **Sweep references only confirmed swings** — `sweeps.py` reads only the `*_ConfirmedAt` columns.
   A swing candidate that has not yet been confirmed cannot be swept.

3. **Failed-break confirms forward in time** — `failed_breaks.py` scans forward from the sweep bar.
   It does not look ahead to determine the failed-break label at sweep time.

4. **Sweep direction mutual exclusivity** — If a single bar simultaneously breaches both a swing
   high and a swing low level on the same timeframe, the bar is treated as ambiguous and no
   sweep event is emitted for that timeframe (fail-closed).

5. **Swing events emitted once per confirmation** — `events.py` emits a swing event only when
   `SwingHigh_{TF}_ConfirmedAt` changes versus the previous row. Persistent "latest confirmed
   swing" columns do not cause repeated emission of the same swing.

6. **Rolling baselines are right-aligned** — `absorption.py` uses `rolling(window=20, min_periods=1)`
   with no centering. No future bars contaminate any rolling calculation.

---

## Future Scope Boundary

The following are **not** part of the implemented Phase 1 spec:

- Setup extraction / candidate generation
- Statistical edge validation (win rate, R-multiple distribution)
- Ruleset selection and strategy optimization
- Live execution decisions, order sizing, stop placement
- Advanced confidence scoring (Block 5 logic)
- Event lifecycle metadata (`event_id`, `parent_event_id`, `status`)
- Session context features (`session`, `minutes_from_eu_open`, `minutes_from_us_open`)
- Swing lifecycle states (`ACTIVE`, `TESTED`, `CONSUMED`) — modeled in spec, not yet in pipeline
- Parquet output format — current output is CSV
- MetaJson population

---

# Data Source

Input dataset is produced by the Shi Aggregator.

Input format: 1-minute CSV.

Columns:

Timestamp
Open
High
Low
Close
Volume
AggTrades
BuyQty
SellQty
VWAP
OpenInterest
FundingRate
LiqBuyQty
LiqSellQty
IsSynthetic

---

## Data Fields

### AggTrades

Number of Binance aggTrade messages received during the 1-minute bar.

Note:
This is not the exact number of exchange fills. Binance aggTrade stream
aggregates multiple executions into single messages.

AggTrades should therefore be interpreted as a proxy for trade activity
rather than a precise trade count.

### VWAP (1-minute)

Volume-weighted average traded price of the 1-minute candle.

Formula:

    VWAP = sum(price * qty) / sum(qty)

VWAP represents the average execution price of all trades during the bar.

If a candle contains no trades (synthetic candle), VWAP is set equal to Close.

## Data Quality / Special Cases

### IsSynthetic

Binary flag indicating whether the candle was generated without trades.

Values:
0 — normal candle (trades occurred)
1 — synthetic candle (no trades during the interval)

Synthetic candles are created using the last known price
(mark price or last trade price).

Analyzer modules may optionally exclude synthetic candles
from volatility or compression calculations.

## Data Limitations

### Execution Granularity

Order flow metrics (BuyQty, SellQty, Delta) are derived from Binance aggTrade.

The aggTrade stream aggregates multiple fills and therefore does not
preserve full fill-by-fill execution order.

These metrics are suitable for bar-level order flow analysis (1-minute),
but they should not be interpreted as footprint-grade execution tape.

## Interpretation Guidelines

### Aggressor vs Control

BuyQty and SellQty represent taker-aggressor volume.

They indicate which side initiated market orders but do not by themselves
indicate directional market control.

Directional interpretation must always be combined with price response
(close location, wick structure, and range behavior).

### Liquidation Context

LiqBuyQty and LiqSellQty are derived from the Binance forceOrder stream.

This stream reports observed liquidation events but does not guarantee
complete coverage of all market liquidations.

These values are intended as contextual signals rather than exact
measurements of liquidation volume.

---

# Dependencies

Actual pipeline computation order (see `analyzer/pipeline.py`):

1. Schema / Loader — input validation, UTC parsing
2. Base Metrics — per-bar derived metrics (Delta, CVD, etc.)
3. Structural Swings — H1/H4 delayed-confirmation swing detection
4. Sweeps — sweep detection against confirmed swing levels
5. Failed Breaks — forward-in-time failed-break confirmation from sweep state
6. Absorption / Context Features — rolling-ratio context layer
7. Event Normalization — normalized event table from materialized columns

Notes:

- Sweep detection requires confirmed swings to be materialized first.
- Failed-break detection requires sweep columns to be materialized first.
- Absorption layer operates independently of swing/sweep logic.
- Event normalization reads all materialized feature columns.

Planned (not yet in pipeline):

- Session context features
- Confidence scoring (Block 5)
- CVD divergence features
- Setup extraction

---

# 0. Output Format — LOCKED

Analyzer produces two datasets.

## Feature Table

One row per 1-minute candle.

Columns include the raw aggregator data plus derived metrics.

Base columns:

Timestamp
Open
High
Low
Close
Volume
AggTrades
BuyQty
SellQty
VWAP
OpenInterest
FundingRate
LiqBuyQty
LiqSellQty
IsSynthetic

Derived metrics are defined in Section 1.

---

## Event Table

One row per detected event.

Columns:

Timestamp
EventType
Side
PriceLevel
SourceTF
ReferenceSwingTs
ReferenceSwingPrice
Confidence
MetaJson

### Confidence

Confidence is a qualitative classification of event strength.

Allowed values:


low
medium
high


This allows filtering events by quality during backtesting.

---

# 1. Base Metrics — LOCKED

The following metrics are computed for every 1-minute bar.

### Delta


Delta = BuyQty - SellQty


---

### CVD (Cumulative Volume Delta)


CVD[t] = CVD[t-1] + Delta[t]
CVD[0] = Delta[0]


---

### DeltaPct


DeltaPct = Delta / Volume if Volume > 0
DeltaPct = 0 if Volume = 0


---

### BarRange


BarRange = High - Low


---

### BodySize


BodySize = abs(Close - Open)


---

### UpperWick


UpperWick = High - max(Open, Close)


---

### LowerWick


LowerWick = min(Open, Close) - Low


---

### CloseLocation

Normalized position of the close within the candle.


CloseLocation = (Close - Low) / BarRange if BarRange > 0
CloseLocation = 0.0 if BarRange = 0


Range:


0.0 = close at low
1.0 = close at high
0.5 = midpoint


---

### BodyToRange


BodyToRange = BodySize / BarRange if BarRange > 0
BodyToRange = 0 if BarRange = 0


---

### UpperWickToRange


UpperWickToRange = UpperWick / BarRange if BarRange > 0
UpperWickToRange = 0 if BarRange = 0


---

### LowerWickToRange


LowerWickToRange = LowerWick / BarRange if BarRange > 0
LowerWickToRange = 0 if BarRange = 0


---

### OI_Change


OI_Change = OpenInterest[t] - OpenInterest[t-1]
OI_Change[0] = NaN  (pandas .diff() first-row behavior)


This metric helps distinguish:

- price movement caused by **new positions opening**
- price movement caused by **position closures or liquidations**

---

### LiqTotal


LiqTotal = LiqBuyQty + LiqSellQty


Used as a quick indicator of liquidation activity within the bar.

---

### Session Context — Planned v1.1

> **Not implemented in Phase 1.** Columns `session`, `minutes_from_eu_open`,
> `minutes_from_us_open` are listed in `FEATURE_COLUMNS_PLANNED` in `schema.py`
> but are not computed by any current module.

Derived from timestamp. Ліквідність на BTC розподілена нерівномірно по сесіях.

#### session

    ASIA     = 00:00–07:00 UTC
    EU       = 07:00–13:30 UTC
    US       = 13:30–20:00 UTC
    LATE_US  = 20:00–00:00 UTC

#### minutes_from_eu_open

    minutes_from_eu_open = (ts - 07:00 UTC today) in minutes
    Може бути від'ємним (до відкриття) або додатнім (після)

#### minutes_from_us_open

    minutes_from_us_open = (ts - 13:30 UTC today) in minutes
    Може бути від'ємним або додатнім

#### Чому це важливо

Sweep success rate суттєво відрізняється по сесіях:

    Asia:  ~35–45% (тонка ліквідність, багато noise sweeps)
    EU:    ~55–60%
    US:    ~60–70% (максимальна ліквідність, справжні sweeps)

Sweep перед відкриттям сесії (12:45–13:30 UTC) — часто liquidity preparation
перед US імпульсом. Це безкоштовний контекст для бектесту.

Session features НЕ використовуються в Block 5 (confidence).
Це аналітичні поля для pattern × session дослідження у Фазі 3.

---

# 2. Swing Logic — LOCKED

## Задача

Визначити ключові структурні рівні (swing high / swing low) на H1 і H4 таймфреймах.
Ці рівні — основа для: sweep detection, failed break, distance_to_liquidity, точки входу.

---

## Агрегація таймфреймів

Дані збираються на 1m. H1 і H4 свічки будуються з них.

### H1 candle

    Open   = first 1m Open in hour
    High   = max(all 1m Highs in hour)
    Low    = min(all 1m Lows in hour)
    Close  = last 1m Close in hour
    Volume = sum(all 1m Volumes)
    BuyQty = sum(all 1m BuyQty)
    SellQty = sum(all 1m SellQty)

### H4 candle

Те саме, блоки по 4 години UTC:

    00-04, 04-08, 08-12, 12-16, 16-20, 20-24

### OI, FundingRate

Беремо останнє значення в блоці (snapshot на кінець періоду).

---

## Fractal Swing Detection — Implemented

> **Implementation note:** Current implementation (`analyzer/swings.py`) uses
> strict 3-bar local extremum for **both H1 and H4**. No ATR impulse filter is applied
> in Phase 1. ATR-based validation is planned for v1.1.

### Swing definition (current implementation)

Strict 3-bar local extremum on TF bars:

    swing_high at bar i:
      High[i] > High[i-1]  AND  High[i] > High[i+1]

    swing_low at bar i:
      Low[i] < Low[i-1]  AND  Low[i] < Low[i+1]

Both H1 and H4 use the same 1-left / 1-right rule (3-bar window).

### Confirmation timing (current implementation)

A swing at TF bar `i` becomes known only after bar `i+1` fully closes.

    ConfirmedAt = Timestamp_of_bar_i + 2 * TF_duration

Examples:

    H1 swing high at bar starting 10:00
    → bar i+1 closes at 12:00
    → ConfirmedAt = 12:00  (= 10:00 + 2h)

    H4 swing high at bar starting 00:00
    → bar i+1 closes at 08:00
    → ConfirmedAt = 08:00  (= 00:00 + 2 × 4h)

Until ConfirmedAt the swing does NOT exist for any downstream layer.

### Lookahead rule

    Swing confirmed at: ConfirmedAt (bar i+1 close time)
    Swing price:        High[i] or Low[i]

Це обов'язкове правило для чесного бектесту.
Порушення = lookahead bias = невалідні результати.

---

## Swing Validation (impulse filter) — Planned v1.1

> **Not implemented in Phase 1.** The ATR impulse filter below is a planned
> upgrade; Phase 1 emits all fractal swings without impulse validation.

Не кожен фрактал — значущий swing. Потрібен рух після точки.

    ATR_period = 14 (на відповідному ТФ)
    MIN_IMPULSE_ATR_MULT = 0.5  # калібрувальна змінна

### Swing high validated if:

    min(Low[i+1 ... i+N]) < High[i] - ATR_14 * MIN_IMPULSE_ATR_MULT

### Swing low validated if:

    max(High[i+1 ... i+N]) > Low[i] + ATR_14 * MIN_IMPULSE_ATR_MULT

Суть: після swing high ціна повинна відійти вниз хоча б на пів-ATR.
Інакше це не swing а шум.

---

## Swing Lifecycle — Planned v1.1

> **Not implemented in Phase 1.** The swing lifecycle state machine below
> (ACTIVE/TESTED/CONSUMED) is a planned upgrade. In Phase 1, confirmed swings
> have no lifecycle state — a confirmed swing persists as the "latest confirmed"
> level until superseded by a newer one. There is no CONSUMED transition.

Кожен swing має три стани:

    ACTIVE    — рівень визначений, ціна не доходила
    TESTED    — ціна торкнулась рівня але не пробила (wick touch)
    CONSUMED  — рівень пробитий close-ом на відповідному ТФ

### Правила переходу

ACTIVE → TESTED (тільки з ACTIVE, не повторюється):

    if swing_state == ACTIVE:
        Для swing high: High > swing_price AND Close < swing_price → state = TESTED
        Для swing low:  Low < swing_price AND Close > swing_price → state = TESTED

ACTIVE/TESTED → CONSUMED:

    Для swing high: Close > swing_price (на відповідному ТФ)
    Для swing low:  Close < swing_price (на відповідному ТФ)

CONSUMED swing більше не використовується для sweep detection.
Зберігається в історії для бектесту.

---

## Swing Output

### Feature table — implemented columns

Columns written by `analyzer/swings.py` (per TF: H1, H4):

    SwingHigh_{TF}_Price         # latest confirmed swing high price (NA if none yet)
    SwingHigh_{TF}_ConfirmedAt   # confirmation timestamp of latest swing high
    SwingLow_{TF}_Price          # latest confirmed swing low price (NA if none yet)
    SwingLow_{TF}_ConfirmedAt    # confirmation timestamp of latest swing low

These are "latest confirmed" columns — they carry the most recent confirmed swing
level forward on every 1m row until a newer swing is confirmed.

### Feature table — planned columns (v1.1)

> Not implemented in Phase 1.

    nearest_swing_high_H1             # ціна найближчого ACTIVE/TESTED swing high
    nearest_swing_low_H1              # ціна найближчого ACTIVE/TESTED swing low
    distance_to_swing_high_H1_pct     # (nearest_swing_high - Close) / Close * 100
    distance_to_swing_low_H1_pct      # (Close - nearest_swing_low) / Close * 100
    distance_to_swing_high_H1_atr     # (nearest_swing_high - Close) / ATR_H1
    distance_to_swing_low_H1_atr      # (Close - nearest_swing_low) / ATR_H1
    (same for H4)

### Event table — swing events

Кожен новий підтверджений swing записується як подія:

    EventType: SWING_HIGH або SWING_LOW
    SourceTF: H1 або H4
    PriceLevel: ціна swing
    Timestamp: ConfirmedAt timestamp
    Confidence: NA (Phase 1)

---

## Параметри v1.0

| Параметр | H1 | H4 | Status |
|---|---|---|---|
| Fractal window | 1 left, 1 right (3-bar) | 1 left, 1 right (3-bar) | ✅ Implemented |
| Confirmation delay | 2 × H1 = +2h from swing bar | 2 × H4 = +8h from swing bar | ✅ Implemented |
| ATR period | 14 | 14 | 🔜 Planned v1.1 |
| MIN_IMPULSE_ATR_MULT | 0.5 | 0.5 | 🔜 Planned v1.1 |
| Swing states (ACTIVE/TESTED/CONSUMED) | — | — | 🔜 Planned v1.1 |

---

## Обмеження v1.0

Не реалізуємо:

- Multi-touch scoring (скільки разів рівень тестувався)
- Swing strength ranking
- Cluster detection (кілька свінгів поруч = зона)
- Order block integration

Це все v1.1+ після бектесту.

---

# 3. Sweep Detection + Failed Break Logic — LOCKED

## Контекст

Sweep і failed break — це один ланцюг подій:

    swing рівень існує → ціна знімає рівень → або пробій прийнятий → або повернення назад (failed break)

Failed break без sweep не існує як окрема подія.
Цей блок описує повний ланцюг.

---

## 3.1 Definitions

> **Phase 1 scope:** In the current implementation sweeps are detected against
> the latest confirmed swing level (no lifecycle state checks). The `swing_state`
> references in definitions below describe the v1.1 planned model.

### Sweep

Факт зняття ліквідності за swing-рівнем.
Wick або bar high/low виходить за рівень.
Це НЕ сигнал сам по собі — це подія-кандидат.

Planned (v1.1): sweep тільки проти swing у стані `ACTIVE` або `TESTED`.
Phase 1: sweep проти будь-якого останнього confirmed swing рівня.

### Break

Close за рівнем на відповідному ТФ.
Це факт прийняття ціни за рівнем.

### Failed break

Спершу був break (close за рівнем), але протягом K барів
ціна повернулась назад і закрилась з правильного боку рівня.

### Accepted break

Break який утримався K барів.
Рівень вважається consumed.

### Wick rejection

Sweep без break — ціна пробила рівень wick-ом але close залишився
з правильного боку. Це формальний liquidity grab pattern.

    WICK_REJECTION_HIGH:
        High > swing_price + MIN_SWEEP_PENETRATION_TICKS * TICK_SIZE AND Close < swing_price

    WICK_REJECTION_LOW:
        Low < swing_price - MIN_SWEEP_PENETRATION_TICKS * TICK_SIZE AND Close > swing_price

Close повинен бути строго по правильну сторону рівня (не рівний).

---

## 3.2 Sweep Detection Rules — Implemented

> **Implementation:** `analyzer/sweeps.py`. The rules below reflect actual
> Phase 1 behavior, not the originally planned spec (no penetration threshold,
> no first-cross rule, no swing state check in Phase 1).

### Timeframe rule

    Sweep detection: evaluated on 1m bars
    Reference level: latest confirmed swing on H1 or H4

Sweep ловимо на 1m, бо sweep який прийшов і повернувся за 2-3 хвилини
не буде видно на H1/H4 close.

### Sweep high detected if (Phase 1):

    High > SwingHigh_{TF}_Price  (latest confirmed swing high is non-null)

### Sweep low detected if (Phase 1):

    Low < SwingLow_{TF}_Price  (latest confirmed swing low is non-null)

### Ambiguity rule (implemented)

If a single 1m bar simultaneously breaches both the confirmed high and low levels
for the same timeframe, the bar is treated as ambiguous:

    Both Sweep_{TF}_Up and Sweep_{TF}_Down = False (fail closed)
    Sweep_{TF}_Direction = NA

### Anti-lookahead

Sweep references only the `SwingHigh_{TF}_Price` and `SwingLow_{TF}_Price`
values already materialized on the current row (which carry only confirmed swings).
No unconfirmed swing candidate can be swept.

### Важливо

Sweep — це лише факт зняття ліквідності.
Volume spike, delta spike, OI spike — це фільтри якості,
які застосовуються пізніше (Блок 5: Event Labeling / Confidence).
Вони НЕ входять у базове визначення sweep.

### Planned (v1.1)

> Not in Phase 1 implementation:
>
> - Swing state check (ACTIVE/TESTED only)
> - Penetration threshold (`MIN_SWEEP_PENETRATION_TICKS`)
> - First-cross deduplication rule

---

## 3.3 Break Acceptance Rules

### Break high:

    Close > swing_price (на ТФ свінга)

### Break low:

    Close < swing_price (на ТФ свінга)

### Чому close а не wick

Wick пробої відбуваються постійно — це шум.
Тільки close за рівнем означає що ринок прийняв нову ціну.

---

## 3.4 Failed Break Rules — Implemented

> **Implementation:** `analyzer/failed_breaks.py`. Phase 1 uses a conservative
> pending-from-sweep model. The K-bar window, BREAK event, and ACCEPTED_BREAK
> lifecycle are planned for v1.1.

### Phase 1 failed-break model

    1. A sweep on bar T creates a pending candidate.
       No retroactive marking on bar T.

    2. For every subsequent bar T+n (n >= 1):
       - Upward sweep (Sweep_{TF}_Direction == "up"):
           failed if Close[T+n] < swept_level
       - Downward sweep (Sweep_{TF}_Direction == "down"):
           failed if Close[T+n] > swept_level

    3. First confirmation terminates the pending state.
       → FAILED_BREAK_UP or FAILED_BREAK_DOWN emitted.
       ConfirmedTs = Timestamp of confirming bar.

    4. No timeout — pending state persists until any reclaim close occurs.
       No accepted-break lifecycle in Phase 1.
       `confirmation_bars` parameter is reserved and currently ignored.

### Written columns

    FailedBreak_{TF}_Up             # bool: failed break up confirmed on this bar
    FailedBreak_{TF}_Down           # bool: failed break down confirmed on this bar
    FailedBreak_{TF}_Direction      # "up" / "down" / NA
    FailedBreak_{TF}_ReferenceLevel # swept price level
    FailedBreak_{TF}_ReferenceSweepTs  # timestamp of the triggering sweep bar
    FailedBreak_{TF}_ConfirmedTs    # timestamp of this bar (confirmation row)

### Planned (v1.1)

> Not in Phase 1 implementation:
>
> - K-bar window with timeout
> - Explicit BREAK (PENDING) event
> - ACCEPTED_BREAK lifecycle
> - Break timer tracking

---

## 3.5 Accepted Break Rules — Planned v1.1

> **Not implemented in Phase 1.** Accepted break lifecycle requires a K-bar
> window timer and swing lifecycle states, both planned for v1.1.

### Accepted break high:

    Був break high (Close > swing_price)
    Всі K наступних барів: Close > swing_price

    → подія ACCEPTED_BREAK_HIGH
    → swing state = CONSUMED

### Accepted break low:

    Був break low (Close < swing_price)
    Всі K наступних барів: Close < swing_price

    → подія ACCEPTED_BREAK_LOW
    → swing state = CONSUMED

---

## 3.6 Sweep-Break Lifecycle — Planned v1.1

> **Not the current implementation.** Phase 1 uses a conservative
> pending-from-sweep model (see Section 3.4). The full lifecycle diagram
> below (WICK_REJECTION, BREAK_DETECTED, ACCEPTED_BREAK, swing CONSUMED)
> describes the v1.1 planned architecture.

Повний ланцюг станів від sweep до результату:

    SWEEP_DETECTED
        ↓
    bar Close за рівнем?
        ├── НІ → WICK_REJECTION (liquidity grab)
        └── ТАК → BREAK_DETECTED
                    ↓
              K барів чекаємо
                    ├── повернувся назад → FAILED_BREAK
                    └── утримався → ACCEPTED_BREAK
                                    → swing = CONSUMED

### Timing

Sweep і break можуть відбутись на одному барі:

    High > swing_price AND Close > swing_price → одразу BREAK_DETECTED

Або sweep без break:

    High > swing_price AND Close < swing_price → WICK_REJECTION_HIGH

Це найсильніший сетап для стратегії — liquidity grab + rejection.

---

## 3.7 Sweep Output

### Feature table — implemented columns

    Sweep_{TF}_Up              # bool: upward sweep on this bar
    Sweep_{TF}_Down            # bool: downward sweep on this bar
    Sweep_{TF}_Direction       # "up" / "down" / NA
    Sweep_{TF}_ReferenceLevel  # swept swing price level (NA if no sweep)
    Sweep_{TF}_ReferenceTs     # ConfirmedAt timestamp of the referenced swing (NA if no sweep)

### Feature table — planned columns (v1.1)

> Not implemented in Phase 1.

    is_wick_rejection_high     # sweep high + close < swing_price
    is_wick_rejection_low      # sweep low + close > swing_price
    bars_since_last_sweep
    distance_to_last_sweep_atr

### Event table — implemented event types

**SWEEP_UP / SWEEP_DOWN** ✅ Implemented:

    EventType: SWEEP_UP or SWEEP_DOWN
    Side: "up" or "down"
    Timestamp: sweep bar Timestamp (row where Sweep_{TF}_Up/Down = True)
    PriceLevel: Sweep_{TF}_ReferenceLevel (swept swing price)
    SourceTF: H1 or H4
    ReferenceSwingTs: Sweep_{TF}_ReferenceTs (swing ConfirmedAt timestamp)
    ReferenceSwingPrice: same as PriceLevel
    Confidence: NA (Phase 1)
    MetaJson: NA (Phase 1)

**FAILED_BREAK_UP / FAILED_BREAK_DOWN** ✅ Implemented:

    EventType: FAILED_BREAK_UP or FAILED_BREAK_DOWN
    Side: "up" or "down"
    Timestamp: FailedBreak_{TF}_ConfirmedTs (confirmation bar timestamp)
    PriceLevel: FailedBreak_{TF}_ReferenceLevel
    SourceTF: H1 or H4
    ReferenceSwingTs: FailedBreak_{TF}_ReferenceSweepTs  ← sweep timestamp, not original swing
    ReferenceSwingPrice: same as PriceLevel
    Confidence: NA (Phase 1)
    MetaJson: NA (Phase 1)

### Event table — planned event types (v1.1)

> Not emitted in Phase 1.

    WICK_REJECTION_HIGH / WICK_REJECTION_LOW
    BREAK_HIGH / BREAK_LOW
    ACCEPTED_BREAK_HIGH / ACCEPTED_BREAK_LOW

---

## 3.8 Параметри v1.0

| Параметр | H1 | H4 | Status |
|---|---|---|---|
| Sweep detection TF | 1m bars | 1m bars | ✅ Implemented |
| Sweep trigger | `High > SwingHigh_{TF}_Price` | same | ✅ Implemented |
| Ambiguous double-breach | fail closed (no event) | same | ✅ Implemented |
| Failed break: pending-from-sweep | any later reclaim close | same | ✅ Implemented |
| TICK_SIZE | 0.10 | 0.10 | 🔜 Planned v1.1 |
| MIN_SWEEP_PENETRATION_TICKS | 2 | 2 | 🔜 Planned v1.1 |
| Sweep first cross dedup | prev High/Low <= swing_price | same | 🔜 Planned v1.1 |
| FAILED_BREAK_WINDOW (K) timeout | 3 | 3 | 🔜 Planned v1.1 |
| Break trigger (BREAK event) | Close > swing_price | same | 🔜 Planned v1.1 |
| Wick rejection | sweep + Close on right side | same | 🔜 Planned v1.1 |
| Accepted = hold close K bars | all K bars | same | 🔜 Planned v1.1 |

---

## 3.9 Edge cases

### Два свінги поруч

Якщо sweep знімає два рівні одночасно (bar High > swing1 AND > swing2),
генеруються ДВІ окремі sweep events. Кожна зі своїм reference swing.

### Sweep на одному ТФ, але не на іншому

Можливо: H1 sweep є, H4 ні (бо H4 swing вище).
Це нормально — events генеруються незалежно по ТФ.

### Break → Failed → повторний Break

Після FAILED_BREAK новий BREAK вимагає нового SWEEP event.

    SWEEP → BREAK → FAILED_BREAK
    ... ціна відійшла ...
    NEW SWEEP → NEW BREAK → ...

Без нового sweep — повторний break НЕ генерується.
Це запобігає циклу BREAK → FAILED → BREAK → FAILED на кожному барі.

Planned (v1.1): swing залишається ACTIVE/TESTED поки не буде ACCEPTED_BREAK.

---

## 3.10 Архітектурне рішення — Planned v1.1

> **Not the current implementation.** Phase 1 uses stateless per-bar
> annotation (pandas vectorized columns). The state-machine model below
> (`swing_registry`, `break_timers`) is planned for v1.1 when swing lifecycle
> states and K-bar timeout tracking are introduced.

Planned (v1.1) architecture:

    swing_registry     — всі ACTIVE/TESTED свінги з їх станами
    break_timers       — активні break events з countdown до K
    event_log          — історія всіх згенерованих events

---

## 3.11 Event types — Блок 3

### Implemented (Phase 1)

    SWEEP_UP              # upward sweep of confirmed swing high
    SWEEP_DOWN            # downward sweep of confirmed swing low
    FAILED_BREAK_UP       # upward sweep followed by close reclaim below level
    FAILED_BREAK_DOWN     # downward sweep followed by close reclaim above level

Also from Block 2 (swing layer):

    SWING_HIGH
    SWING_LOW

### Planned (v1.1+)

    WICK_REJECTION_HIGH
    WICK_REJECTION_LOW
    BREAK_HIGH
    BREAK_LOW
    ACCEPTED_BREAK_HIGH
    ACCEPTED_BREAK_LOW

---

## 3.12 Обмеження v1.0

Не реалізуємо:

- Volume spike як частину визначення sweep (це фільтр якості, Блок 5)
- OI change як частину визначення failed break
- Partial failed break (повернувся на 50% руху)
- Multi-timeframe confirmation (sweep на H1 + H4 одночасно як окремий тип)
- Sweep depth scoring (наскільки глибоко пробили як score)
- Liquidity clusters / stacked swings detection

Це все v1.1+ після бектесту.

---

## 3.13 Note: Liquidity Clusters (v1.1 scope)

Clustered liquidity is explicitly out of scope for v1.0.
All swings are treated as independent levels.

However, analyzer must preserve enough historical swing data
to allow future v1.1 clustering of nearby same-side swings across H1/H4.

### Що це означає для v1.0

У v1.0 ми НЕ:

- групуємо свінги в зони
- визначаємо cluster_high / cluster_low
- змінюємо логіку sweep на основі сусідніх свінгів

### Що закладаємо для v1.1

В feature table додаємо поля (рахуються, але не впливають на логіку v1.0):

    nearby_swing_count_H1           # кількість ACTIVE/TESTED swing high/low в радіусі 1 ATR_H1
    nearby_swing_count_H4           # те саме для H4
    nearest_next_swing_distance_atr # відстань до наступного найближчого свінга тієї ж сторони / ATR

В MetaJson sweep event додаємо:

    "nearby_swings": [
        {"price": 71270, "tf": "H1", "distance_atr": 0.3},
        {"price": 71305, "tf": "H4", "distance_atr": 0.7}
    ]

### Чому це важливо

Ринок часто знімає не один swing а серію:

    swing_1 swept → ціна йде далі → swing_2 swept → swing_3 swept → розворот

Система яка шортить після першого sweep може входити прямо в середину
недознятої ліквідності. Cluster detection у v1.1 вирішить цю проблему.

Але спочатку v1.0 повинен відповісти на базове питання:
чи працює модель swing → sweep → failed break взагалі.

---

## 3.15 Note: Retrospective Sweep Bias

Confirmed swings may produce retrospective sweep events
because swing confirmation occurs with delay N.

Приклад:

    10:00 — swing high candidate (H1 bar start)
    10:10 — ціна пробиває цей high (sweep)
    10:20 — reversal
    12:00 — swing confirmed (ConfirmedAt = 10:00 + 2×1h)

Analyzer записує sweep з timestamp 10:10, але на момент sweep
система ще не знала що це swing. Формально lookahead немає
(sweep записується ретроспективно після confirmation), але це
створює semantic bias — частина sweep подій існує тільки тому
що ми знаємо майбутнє підтвердження.

### Вплив на статистику

Backtest може показати sweep success rate ~60%+,
а live буде ~45%, бо частина sweep — ретроспективні.

### Рішення для v1.0

Приймаємо цей bias. Причини:

    - система використовує multi-factor confirmation (absorption, volume, confidence)
    - не є чистою swing-only системою
    - bias буде оцінений під час бектесту

### Рішення для v1.1

Можливі підходи:

    - Delayed sweep eligibility: sweep тільки після swing confirmation
    - Candidate swings: pre-confirmed рівні для раннього detection
    - Liquidity levels: рівні на основі recent highs/lows/equal levels, не тільки свінгів

---

## 3.16 Sweep Penetration Filter — Planned v1.1

> **Not implemented in Phase 1.** Phase 1 sweep detection uses a simple
> `High > confirmed_swing_level` rule with no penetration threshold.
> The filter below is planned for v1.1.

Не кожен прокол рівня — справжній sweep.
На крипторинку spread noise може створити High > swing_price
без реального зняття ліквідності.

### Проблема

    Сценарій A (true sweep): 15 BTC market buy → пробиває рівень на 3$
    Сценарій B (noise): 0.1 BTC → ціна торкнулась рівня + 0.1$

Обидва створюють High > swing_price, але тільки A — реальний sweep.

### Фільтр

    valid_sweep if:
        penetration >= MIN_SWEEP_PENETRATION_TICKS * TICK_SIZE

    penetration_high = High - swing_price
    penetration_low = swing_price - Low

| Parameter | Value | Тип |
|---|---|---|
| MIN_SWEEP_PENETRATION_TICKS | 2 | калібрувальний |

Для BTCUSDT: 2 ticks = $0.20. Мінімально, але прибирає spread noise.

### Чому не більше

Smart money часто проколюють рівень на 2-3 тики — саме щоб зняти
стопи не залишаючи слідів. Занадто великий penetration threshold
відфільтрує саме ці liquidity grabs.

### Взаємодія з TICK_SIZE

Цей фільтр замінює попередній TICK_SIZE filter у sweep detection.
Sweep detection rule стає:

    bar High > swing_price + MIN_SWEEP_PENETRATION_TICKS * TICK_SIZE

Замість:

    bar High > swing_price + TICK_SIZE

---

# 4. Absorption Detection — LOCKED

## 4.0 Implemented: Context Feature Layer v1

> `analyzer/absorption.py` — ✅ Implemented in Phase 1.

Phase 1 implements a deterministic rolling-ratio context layer.
This is a context-stress helper for research, not a calibrated ruleset
and not a trading signal.

Window: `CONTEXT_WINDOW = 20` bars. All rolling baselines are right-aligned
(no future leakage).

### Implemented features

| Column | Formula | Type |
|--------|---------|------|
| `RelVolume_20` | `Volume / rolling_mean(Volume, 20)` | float ratio |
| `DeltaAbsRatio_20` | `abs(Delta) / rolling_mean(abs(Delta), 20)` | float ratio |
| `OIChangeAbsRatio_20` | `abs(OI_Change) / rolling_mean(abs(OI_Change), 20)` | float ratio |
| `LiqTotalRatio_20` | `LiqTotal / rolling_mean(LiqTotal, 20)` | float ratio |
| `CtxRelVolumeSpike_v1` | `RelVolume_20 >= 1.5` | bool |
| `CtxDeltaSpike_v1` | `DeltaAbsRatio_20 >= 1.5` | bool |
| `CtxOISpike_v1` | `OIChangeAbsRatio_20 >= 1.5` | bool |
| `CtxLiqSpike_v1` | `LiqTotalRatio_20 >= 1.5` | bool |
| `CtxWickReclaim_v1` | `max(UpperWickToRange, LowerWickToRange) >= 0.4 AND BodyToRange <= 0.35` | bool |
| `AbsorptionScore_v1` | Additive sum of 5 context bool flags (0–5) | int |

### Scope

- Context only — does not open positions or generate entry signals
- Not yet a calibrated ruleset; spike threshold (1.5) is a research starting point
- Absorption does not generate event table rows in Phase 1
- Used as a context feature alongside sweep/failed-break events in research

---

## 4.1 Planned: Sell/Buy Absorption Detector

> The following sections 4.2–4.9 describe the **originally planned** per-bar
> sell/buy absorption detection logic (DeltaPct + CloseLocation + wick rules).
> This is **not implemented in Phase 1** — planned for v1.1.

4. Absorption Detection
Контекст

Absorption — це ситуація, коли агресивний потік ордерів не призводить до очікуваного руху ціни, що означає наявність великого пасивного контрагента.

Типові приклади:

агресивні продажі, але ціна не падає

агресивні покупки, але ціна не росте

Це означає, що хтось великий поглинає ринкові ордери лімітними заявками.

Absorption не є сигналом сам по собі, а контекстним фактором, який може посилювати події з Блоку 3:

sweep

wick rejection

failed break

4.1 Detection Scope

Absorption detection виконується на 1m таймфреймі, оскільки це явище мікроструктури ринку.

Detection не залежить від H1/H4 swing logic і працює незалежно від Block 2.

Проте у Block 5 absorption може використовуватись як confidence modifier для sweep / failed break подій.

4.2 Sell Absorption

Sell absorption виникає коли агресивні продавці не можуть проштовхнути ціну вниз.

Sell absorption detected if:
DeltaPct <= -DELTA_PCT_THRESHOLD
AND CloseLocation >= CLOSE_LOCATION_HIGH_THRESHOLD
AND LowerWickToRange >= LOWER_WICK_THRESHOLD
Інтерпретація

значна частина обсягу — агресивні продажі

але close бару у верхній частині свічки

і є помітна нижня тінь

Це означає, що нижчі ціни були поглинуті пасивними покупцями.

4.3 Buy Absorption

Buy absorption виникає коли агресивні покупці не можуть проштовхнути ціну вверх.

Buy absorption detected if:
DeltaPct >= DELTA_PCT_THRESHOLD
AND CloseLocation <= CLOSE_LOCATION_LOW_THRESHOLD
AND UpperWickToRange >= UPPER_WICK_THRESHOLD
Інтерпретація

значна частина обсягу — агресивні покупки

але close бару у нижній частині свічки

і є помітна верхня тінь

Це означає, що вищі ціни були поглинуті пасивними продавцями.

4.4 Threshold Parameters (v1.0)

Для першої версії фіксуємо стартові пороги.

Parameter	Value	Тип
DELTA_PCT_THRESHOLD	0.40	калібрувальний
CLOSE_LOCATION_HIGH_THRESHOLD	0.66	фіксований
CLOSE_LOCATION_LOW_THRESHOLD	0.34	фіксований
LOWER_WICK_THRESHOLD	0.30	фіксований
UPPER_WICK_THRESHOLD	0.30	фіксований
Пояснення

DeltaPct ≥ 0.40 означає значну агресію однієї сторони

CloseLocation ≥ 0.66 — close у верхній третині бару

CloseLocation ≤ 0.34 — close у нижній третині бару

wick ≥ 30% range — тінь достатньо значна

Пороги можуть бути відкалібровані після збору статистики.

4.5 Feature Table Output

У feature table додаються:

is_sell_absorption
is_buy_absorption

Тип: boolean

Ці поля дозволяють аналізувати absorption разом із sweep / failed break подіями.

4.6 Absorption Output

Absorption у v1.0 є feature-only, не event.

Записується в feature table:

    is_sell_absorption    # bool
    is_buy_absorption     # bool

Absorption НЕ генерує рядки в event table.
Причина: absorption відбувається часто і створить тисячі micro-events
які засмічують event table. Натомість absorption використовується
як confidence modifier в Block 5 через feature table lookup.
4.7 Relationship with Sweep Events

Absorption не змінює sweep detection rules.

Але може виступати контекстним сигналом.

Наприклад:

SWEEP_HIGH
+ SELL_ABSORPTION
→ stronger reversal probability

або

FAILED_BREAK_LOW
+ BUY_ABSORPTION
→ stronger long setup

Ці комбінації використовуються у Block 5: Event Labeling / Confidence scoring.

4.8 Context Handling Note

Absorption features у v1.0 визначаються незалежно від розташування відносно swing-рівнів.

Фільтри контексту, такі як:

distance to nearest swing

proximity to recent sweep

failed break context

trend / impulse location

навмисно не входять у Block 4 і будуть оброблятись у Block 5 (Event Labeling / Confidence).

Це зберігає Block 4 як чистий detector мікроструктури, без змішування з quality scoring.

4.9 Limitations (v1.0)

У першій версії не реалізуємо:

volume threshold як частину визначення absorption

multi-bar absorption patterns

rolling delta pressure

z-score normalization

orderbook imbalance

OI-based absorption

absorption scoring

swing-distance filter inside detection logic

Ці функції можуть бути додані у v1.1+ після бектесту.


# 5. Event Labeling / Confidence — LOCKED

> **Implementation status:** Confidence scoring is **not yet implemented** in Phase 1.
> All event rows currently carry `Confidence = NA` and `MetaJson = NA`.
> The logic described in sections 5.1–5.13 is the planned Phase 2 contract.

## Контекст

Після визначення базових подій:

    swing (Block 2)
    sweep / break / failed break (Block 3)
    absorption (Block 4)

Analyzer повинен визначити якість події.

Confidence classification дозволяє:

    - відрізняти сильні сетапи від шуму
    - фільтрувати події у бектесті
    - будувати стратегію поверх event stream

Confidence не змінює сам факт події, а лише оцінює її значущість.

---

## 5.1 Confidence Levels

Кожна подія у event table отримує поле Confidence.

Можливі значення:

    LOW
    MEDIUM
    HIGH

| Confidence | Значення |
|---|---|
| LOW | подія сталася, але контекст слабкий або відсутній |
| MEDIUM | нормальний сетап з одним підтвердженням |
| HIGH | сильний сетап з множинним підтвердженням order flow |

---

## 5.2 Confidence Factors

Confidence визначається на основі контекстних факторів.

Analyzer оцінює:

    1. Absorption context
    2. Volume spike
    3. Delta imbalance
    4. OI change context
    5. Liquidation activity
    6. Distance to swing

Ці фактори не змінюють detection logic, а лише впливають на оцінку події.

---

## 5.3 Absorption Context

Absorption поруч із liquidity event значно підсилює сигнал.

    SWEEP_HIGH + SELL_ABSORPTION → +1
    SWEEP_LOW + BUY_ABSORPTION → +1
    FAILED_BREAK_HIGH + SELL_ABSORPTION → +1
    FAILED_BREAK_LOW + BUY_ABSORPTION → +1
    WICK_REJECTION_HIGH + SELL_ABSORPTION → +1
    WICK_REJECTION_LOW + BUY_ABSORPTION → +1

Absorption враховується якщо відбулась на тому ж барі або протягом
попередніх ABSORPTION_LOOKBACK барів.

| Parameter | Value | Тип |
|---|---|---|
| ABSORPTION_LOOKBACK | 3 | фіксований (бари, 1m) |

Confidence effect: +1

---

## 5.4 Volume Spike

Великий обсяг під час sweep або failed break означає активну боротьбу за рівень.

    Volume spike detected if:
        Volume >= rolling_median_volume * VOLUME_SPIKE_MULT

| Parameter | Value | Тип |
|---|---|---|
| VOLUME_SPIKE_MULT | 1.5 | калібрувальний |
| VOLUME_ROLLING_WINDOW | 60 | фіксований (60 барів = 1 година на 1m) |

Rolling median рахується за останні VOLUME_ROLLING_WINDOW барів.

Confidence effect: +1

---

## 5.5 Delta Imbalance

Сильний directional delta підтверджує liquidity events.

    Delta confirmation detected if:
        abs(DeltaPct) >= DELTA_CONFIRMATION_THRESHOLD

Напрямок delta повинен бути узгоджений з напрямком події (side):

    Events з Side=SELL (SWEEP_HIGH, WICK_REJECTION_HIGH, FAILED_BREAK_HIGH):
        DeltaPct <= -DELTA_CONFIRMATION_THRESHOLD (агресивні продажі)

    Events з Side=BUY (SWEEP_LOW, WICK_REJECTION_LOW, FAILED_BREAK_LOW):
        DeltaPct >= DELTA_CONFIRMATION_THRESHOLD (агресивні покупки)

Правило єдине для всіх event types: delta must align with event direction.

| Parameter | Value | Тип |
|---|---|---|
| DELTA_CONFIRMATION_THRESHOLD | 0.50 | калібрувальний |

Confidence effect: +1

---

## 5.6 Open Interest Change

OI дозволяє розрізнити контекст руху ціни.

    OI_Change = OI[t] - OI[t-1]

| Scenario | Meaning |
|---|---|
| price down + OI up | new shorts opening |
| price down + OI down | long liquidations |
| price up + OI up | new longs opening |
| price up + OI down | short covering |

OI використовується як додатковий контекст для інтерпретації,
але НЕ додає/знімає confidence points у v1.0.
Записується в MetaJson для аналізу.

Note: OI_change зберігається в feature table і MetaJson для майбутніх
research features (v1.1+). Можливе використання: OI-based confirmation
як додатковий confidence factor, OI regime detection, position flow analysis.

Confidence effect: інформаційний, без впливу на score у v1.0.

---

## 5.7 Liquidation Context

Ліквідації підтверджують sweep — це каскад примусових закриттів.

    Liquidation spike detected if:
        LiqTotal >= LIQ_SPIKE_THRESHOLD

| Parameter | Value | Тип |
|---|---|---|
| LIQ_SPIKE_THRESHOLD | 0.10 BTC | калібрувальний (initial default) |

Note: rolling median-based rule не підходить, бо більшість хвилин
LiqTotal = 0. Тому використовуємо абсолютний поріг.
LIQ_SPIKE_THRESHOLD є калібрувальним параметром, не фіксованою істиною.
Initial default 0.10 BTC підлягає перегляду після збору статистики.

Confidence effect: +1

---

## 5.8 Distance to Swing Filter

Події далеко від свого reference swing менш значущі.

Для подій з ReferenceSwingPrice (sweep, break, failed break, wick rejection):

    Distance = abs(Close - ReferenceSwingPrice) / ATR на ТФ свінга

    Distance penalty applied if:
        Distance > DISTANCE_PENALTY_ATR

Для подій без reference swing (absorption):

    Distance = distance_to_nearest_swing_atr (будь-який ACTIVE/TESTED)

    Distance penalty applied if:
        Distance > DISTANCE_PENALTY_ATR

| Parameter | Value | Тип |
|---|---|---|
| DISTANCE_PENALTY_ATR | 2.0 | фіксований |

Confidence effect: -1

---

## 5.9 Confidence Calculation

Confidence визначається шляхом накопичення score.

### Base level

    base_score = 0 (LOW)

### Adjustments

    + absorption context:  +1
    + volume spike:        +1
    + delta confirmation:  +1
    + liquidation spike:   +1
    - distance from swing: -1

### Final classification

| Score | Confidence |
|---|---|
| <= 0 | LOW |
| 1 | MEDIUM |
| >= 2 | HIGH |

### Приклади

Sweep без підтвердження:

    score = 0 → LOW (шум, пропускаємо)

Sweep + volume spike:

    score = 1 → MEDIUM (нормальний сетап)

Sweep + volume spike + absorption + liq cascade:

    score = 3 → HIGH (сильний сетап)

Sweep + volume spike, але далеко від свінга:

    score = 1 + 1 - 1 = 1 → MEDIUM

---

## 5.10 Event Table Structure (final)

Подія у event table (naming відповідає Block 7 contract):

    event_id
    event_ts
    event_type
    status
    side
    source_tf
    price_level
    reference_swing_id
    confidence
    parent_event_id
    meta_json

### MetaJson example

    {
        "delta_pct": -0.52,
        "volume": 1450,
        "oi_change": 120,
        "liq_total": 0.35,
        "distance_to_swing_h1_atr": 0.3,
        "distance_to_swing_h4_atr": 0.8,
        "absorption": true,
        "volume_spike": true,
        "confidence_score": 3,
        "confidence_factors": ["absorption", "volume_spike", "delta", "liq_spike"]
    }

---

## 5.11 Parameters Summary (v1.0)

### Fixed (не змінюються до v1.1)

| Parameter | Value |
|---|---|
| ABSORPTION_LOOKBACK | 3 bars |
| VOLUME_ROLLING_WINDOW | 60 bars |
| DISTANCE_PENALTY_ATR | 2.0 ATR |
| Base confidence score | 0 (LOW) |

### Calibratable (підлягають калібруванню на реальних даних)

| Parameter | Initial default | Note |
|---|---|---|
| VOLUME_SPIKE_MULT | 1.5 | множник від rolling median |
| DELTA_CONFIRMATION_THRESHOLD | 0.50 | мінімальний abs(DeltaPct) |
| LIQ_SPIKE_THRESHOLD | 0.10 BTC | абсолютний поріг, не median-based |

Калібрувальні параметри переглядаються після збору 2-4 тижнів даних.
Зміна калібрувальних параметрів не вимагає зміни архітектури.

---

## 5.12 Architecture Principle

Confidence scoring не впливає на detection logic.

Detection залишається у:

    Block 2 — Swing
    Block 3 — Sweep / Break / Failed Break
    Block 4 — Absorption

Confidence лише оцінює силу події.

Це дозволяє:

    - змінювати scoring без зміни detection
    - проводити бектести з різними фільтрами
    - легко розширювати систему у v1.1+

---

## 5.13 Обмеження v1.0

Не реалізуємо:

- Machine learning scoring
- Cluster-based liquidity detection
- Multi-bar context scoring (rolling confidence)
- Orderbook imbalance
- Footprint pattern recognition
- Weighted confidence (різна вага для різних factors)
- Time-decay для confidence factors

Це все v1.1+ після збору статистики.

---

# 6. Anti-Lookahead Rules — LOCKED

## Мета

Забезпечити що всі метрики, події та сигнали розраховуються
тільки з даних, доступних на момент закриття поточної свічки.

Це гарантує:

    - backtest відповідає реальним умовам
    - analyzer не використовує майбутні дані
    - результати не завищують winrate

---

## 6.1 Основне правило

Analyzer працює тільки на закритих барах.

    На барі t дозволено використовувати: data[0 ... t]
    Заборонено використовувати: data[t+1 ... future]

Усі події мають timestamp = bar_close_time.

---

## 6.2 Swing confirmation delay

Both H1 and H4 use strict 3-bar local extremum (1 left / 1 right neighbor).
A swing at TF bar `i` is confirmed only after bar `i+1` fully closes.

    ConfirmedAt = Timestamp_of_bar_i + 2 × TF_duration

    H1: ConfirmedAt = swing_bar_start + 2h
    H4: ConfirmedAt = swing_bar_start + 8h

    swing_price = High[i] або Low[i]

Приклад:

    H1 swing high at bar starting 10:00
    bar i+1 closes at 12:00
    ConfirmedAt = 12:00

До ConfirmedAt цей swing НЕ ІСНУЄ для системи.

---

## 6.3 Sweep detection timing

Sweep визначається в момент закриття бару де відбувся wick.

Phase 1 (implemented):

    High[t] > SwingHigh_{TF}_Price   (confirmed level already on row)
    event_time = Timestamp[t]

Planned (v1.1):

    High[t] > swing_price + MIN_SWEEP_PENETRATION_TICKS * TICK_SIZE
    previous High[t-1] <= swing_price   ← first-cross dedup
    event_time = close_time[t]

Analyzer не може перевіряти наступні бари щоб вирішити чи це sweep.

---

## 6.4 Break detection timing — Planned v1.1

> **Not implemented in Phase 1.** Explicit BREAK events and the BREAK_HIGH/BREAK_LOW
> taxonomy are planned for v1.1. In Phase 1 a sweep directly creates a pending
> failed-break candidate with no intermediate BREAK event.

Break визначається тільки по close закритого бару.

    Close[t] > swing_price → BREAK_HIGH
    Close[t] < swing_price → BREAK_LOW

    event_time = close_time[t]

---

## 6.5 Failed / Accepted break resolution

Phase 1 (implemented): conservative pending-from-sweep model.

    Sweep on bar T → pending candidate (no explicit BREAK event)
    First later bar where Close reclaims through level → FAILED_BREAK confirmed
    No timeout — pending persists indefinitely until reclaim

Planned (v1.1): K-bar window with PENDING status and ACCEPTED_BREAK lifecycle.

    FAILED_BREAK_WINDOW = K = 3

    Break на барі t → status = PENDING
    Кожен наступний бар t+1, t+2, t+3 перевіряється по close
    Resolution timestamp = close_time[t + K]

    Accepted: всі K барів Close за рівнем
    Failed: хоча б один з K барів Close повернувся назад

---

## 6.6 Confidence calculation timing

Confidence розраховується тільки з даних на барі події.

Дозволено:

    Volume[t], DeltaPct[t], LiqTotal[t], distance_to_swing[t]

Заборонено:

    future_volume, future_delta, future_price

Confidence НЕ МОЖЕ змінюватися після створення події.

---

## 6.7 Rolling metrics

Rolling метрики використовують тільки попередні бари.

    rolling_median_volume = median(Volume[t-59 ... t])

Заборонено:

    centered windows
    future bars в rolling calculation

---

## 6.8 ATR calculation

ATR розраховується тільки з історії:

    ATR[t] = rolling_mean(TrueRange[t-13 ... t])

Заборонено:

    centered rolling windows
    ATR[t+1] або будь-які майбутні значення

---

## 6.9 Event immutability

Після створення event наступні поля НЕ МОЖУТЬ змінюватись:

    event_id
    event_type
    timestamp
    price_level
    confidence

Допускається лише додавання resolution event:

    BREAK (PENDING) → FAILED_BREAK або ACCEPTED_BREAK

Resolution — це НОВИЙ event, не модифікація старого.

---

## 6.10 Deterministic replay

Analyzer повинен бути детермінованим.

    analyzer.run(dataset) виконаний двічі на одному наборі даних
    → ідентичний результат: events.csv + features.csv

Це забезпечує:

    - коректність backtest
    - відтворюваність результатів
    - можливість порівняння між версіями параметрів

---

## 6.11 Заборонені практики

У v1.0 категорично заборонено:

    - centered rolling windows
    - future swing detection (swing існує до confirmation delay)
    - labeling using future price
    - dynamic confidence updates (зміна confidence після створення)
    - використання bar data до закриття бару

---

## 6.12 Known Look-Ahead Pitfalls

Типові помилки реалізації які створюють look-ahead bias
навіть при правильній специфікації.

### 1. ATR contamination

Деякі бібліотеки використовують centered window за замовчуванням.

    ЗАБОРОНЕНО: rolling(window=14, center=True)
    ДОЗВОЛЕНО:  rolling(window=14)

Перевірити при імплементації: pandas rolling за замовчуванням
використовує right-aligned window (правильно).

### 2. Swing indexing bug

Swing підтверджується на барі i + N, але часта помилка —
записати swing у масив на позиції i.

    НЕПРАВИЛЬНО: swings[i] = swing_high
    ПРАВИЛЬНО:   swings[i + N] = swing_high_confirmed

Інакше analyzer "знає" swing раніше ніж він підтвердився.

### 3. Failed break resolution leakage

Break має період спостереження K барів.

    НЕПРАВИЛЬНО:
        if any(close[t+1:t+K] < swing):
            event = FAILED_BREAK  # на барі t

    Це використовує майбутні бари в момент створення break.

    ПРАВИЛЬНО:
        bar t: create BREAK (status=PENDING)
        bar t+1: check close, update pending
        bar t+2: check close, update pending
        bar t+3: resolve → FAILED або ACCEPTED

Resolution створюється як окремий event на барі t+K.

### Чому ці три помилки критичні

Ці три помилки ламають 90% академічних backtest-ів:

    ATR contamination → занижені стопи
    Swing indexing → ранні входи
    Break resolution → завищений winrate

Результат: стратегія показує 65% winrate в backtest,
40% в live. Різниця — look-ahead bias.

---

## 6.13 Підсумок

Block 6 гарантує:

    NO LOOKAHEAD — жодних майбутніх даних
    NO FUTURE DATA — тільки закриті бари
    DETERMINISTIC EVENTS — відтворюваний результат
    IMMUTABLE EVENTS — створені події не змінюються

Це робить систему придатною для:

    - честного backtest
    - коректної статистичної валідації
    - переходу до live execution

---

# 7. Analyzer Output Contracts — LOCKED

> **Implementation status:** The Phase 1 pipeline writes CSV output
> (`analyzer_features.csv`, `analyzer_events.csv`) via `analyzer/io.py`.
> The Parquet format described in section 7.1 is planned for a later phase.
> The event table schema in sections 7.3–7.8 (`event_id`, `status`, `parent_event_id`, etc.)
> describes the planned downstream contract; the currently implemented event columns are
> documented in the "Implemented Event Field Semantics" section above.

## Мета

Визначити точний формат виходу Analyzer, щоб Backtester (Фаза 3)
міг працювати без додаткових трансформацій.
Це контракт між Analyzer і всіма downstream системами.

---

## 7.1 Output Files

Analyzer створює два primary datasets:

    features_1m.parquet
    events.parquet

Parquet — primary формат (типізація, стиснення, швидке читання).
CSV export — опціональний, для ручної інспекції.

---

## 7.2 Feature Table Contract

Один рядок = одна 1-minute свічка.

### Primary key

    ts  (bar close timestamp, UTC, unique)

### Rules

    - ts must be unique (no duplicate rows)
    - ts is bar close timestamp in UTC
    - no gaps allowed (minutes with no trades are emitted as synthetic candles and marked IsSynthetic=1)
    - columns order: raw fields first, then derived metrics

### Column list (повний, відповідає Blocks 1-5)

Raw (з aggregator):

    ts, open, high, low, close,
    volume, agg_trades, buy_qty, sell_qty, vwap,
    open_interest, funding_rate, liq_buy_qty, liq_sell_qty, is_synthetic

Base metrics (Block 1):

    delta, cvd, delta_pct,
    bar_range, body_size, upper_wick, lower_wick,
    close_location, body_to_range, upper_wick_to_range, lower_wick_to_range,
    oi_change, liq_total

Swing context (Block 2):

    nearest_swing_high_h1, nearest_swing_low_h1,
    distance_to_swing_high_h1_pct, distance_to_swing_low_h1_pct,
    distance_to_swing_high_h1_atr, distance_to_swing_low_h1_atr,
    nearest_swing_high_h4, nearest_swing_low_h4,
    distance_to_swing_high_h4_pct, distance_to_swing_low_h4_pct,
    distance_to_swing_high_h4_atr, distance_to_swing_low_h4_atr

Sweep context (Block 3):

    is_sweep_high, is_sweep_low,
    is_wick_rejection_high, is_wick_rejection_low,
    sweep_high_ref_price, sweep_low_ref_price,
    bars_since_last_sweep, distance_to_last_sweep_atr

Cluster prep (v1.1 future-proof, Block 3.14):

    nearby_swing_count_h1, nearby_swing_count_h4,
    nearest_next_swing_distance_atr

Absorption (Block 4):

    is_sell_absorption, is_buy_absorption

Session context (Block 1):

    session, minutes_from_eu_open, minutes_from_us_open

---

## 7.3 Event Table Contract — Planned downstream schema

> **Not the current Phase 1 event table.** The columns below (`event_id`,
> `status`, `reference_swing_id`, `parent_event_id`) describe the planned
> v1.1+ downstream contract. The current Phase 1 event table columns are
> documented in the "Implemented Event Field Semantics" section at the top of
> this spec: `Timestamp`, `EventType`, `Side`, `PriceLevel`, `SourceTF`,
> `ReferenceSwingTs`, `ReferenceSwingPrice`, `Confidence` (NA), `MetaJson` (NA).

Один рядок = одна detected подія.

### Event creation order

    1. event detected (Block 2/3/4 rules)
    2. confidence calculated (Block 5 rules, using current bar data only)
    3. event written with all fields including confidence

Confidence is assigned at event creation time. Not retroactively.

### Required columns

    event_id            # unique immutable identifier
    event_ts            # bar close timestamp UTC
    event_type          # enum (see Block 3.12)
    status              # PENDING або FINAL
    side                # BUY або SELL
    source_tf           # 1m, H1, H4
    price_level         # ціна події
    reference_swing_id  # ID свінга до якого прив'язана подія
    confidence          # LOW, MEDIUM, HIGH
    parent_event_id     # ID батьківської події (null якщо немає)
    meta_json           # JSON з snapshot полями

---

## 7.4 Event ID Rules

    - event_id must be unique across entire dataset
    - event_id must not change after creation
    - repeated analyzer runs on same dataset → identical event_ids

Формат event_id:

    {event_type}_{source_tf}_{timestamp_unix}

Приклад:

    SWEEP_HIGH_H1_1710200400

---

## 7.5 Swing ID Rules

Кожен confirmed swing отримує unique stable identifier.

    swing_id format: SWING_{side}_{tf}_{timestamp_unix}
    Приклад: SWING_HIGH_H1_1710180000

Rules:

    - swing_id must be unique
    - кожен sweep / break / failed / accepted event
      повинен мати reference_swing_id
    - swing_id не змінюється після confirmation

---

## 7.6 Event Status

    PENDING  — подія очікує resolution (break чекає K барів)
    FINAL    — подія завершена, статус не зміниться

Приклади:

    BREAK_HIGH           → PENDING (чекаємо K барів)
    FAILED_BREAK_HIGH    → FINAL
    ACCEPTED_BREAK_HIGH  → FINAL
    SWEEP_HIGH           → FINAL
    WICK_REJECTION_HIGH  → FINAL

---

## 7.7 Append-Only Rule

Event history — append-only.

    - минулі events НЕ переписуються
    - outcomes додаються як нові рядки
    - audit trail залишається intact

Приклад:

    row 1: BREAK_HIGH (PENDING)
    row 2: FAILED_BREAK_HIGH (FINAL, parent=row1.event_id)

Row 1 залишається в таблиці без змін.

---

## 7.8 Parent Event Links

Якщо подія є resolution попередньої:

    parent_event_id = event_id попередньої події

Приклади:

    SWEEP_HIGH            → parent_event_id = null
    BREAK_HIGH            → parent_event_id = null (або sweep event_id)
    FAILED_BREAK_HIGH     → parent_event_id = BREAK_HIGH event_id
    ACCEPTED_BREAK_HIGH   → parent_event_id = BREAK_HIGH event_id

---

## 7.9 Snapshot Fields

Event рядки зберігають metric snapshots з бару події.

В meta_json:

    {
        "delta_pct": -0.52,
        "volume": 1450,
        "oi_change": 120,
        "liq_total": 0.35,
        "close_location": 0.82,
        "confidence_score": 3,
        "confidence_factors": ["absorption", "volume_spike", "delta", "liq_spike"]
    }

Це дозволяє аналізувати контекст події без join з feature table.

---

## 7.10 Deterministic Replay Requirement

Analyzer must be deterministic.

    analyzer.run(dataset) executed twice on same data:
        → identical feature row count
        → identical event row count
        → identical event ordering
        → identical event_ids
        → identical confidence values

Якщо детермінізм порушений — це баг, не фіча.

---

## 7.11 Підсумок

Block 7 забезпечує:

    - чіткий контракт між Analyzer і Backtester
    - unique IDs для трейсабіліті подій
    - append-only event log для аудиту
    - parent-child зв'язки між подіями
    - deterministic replay для валідації
    - snapshot fields для standalone event analysis
