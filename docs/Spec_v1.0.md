# Strategy Shi — Analyzer Spec v1.0

Status: Draft
Version: 1.0

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

Analyzer computation order:

1. Base Metrics
2. Swing Logic
3. Failed Break Detection
4. Absorption Detection
5. Event Labeling
6. Derived signals (e.g. CVD divergence)

Notes:

- CVD divergence requires swing detection.
- Failed break detection depends on swing levels.
- Absorption detection uses bar structure metrics.

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
CloseLocation = 0.5 if BarRange = 0


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
OI_Change[0] = 0


This metric helps distinguish:

- price movement caused by **new positions opening**
- price movement caused by **position closures or liquidations**

---

### LiqTotal


LiqTotal = LiqBuyQty + LiqSellQty


Used as a quick indicator of liquidation activity within the bar.

---

### Session Context

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

## Fractal Swing Detection

### H1 swing high

Свічка де High вище ніж High кожної з N свічок зліва і N свічок справа.

    swing_high[i] = True if:
      High[i] > High[j] for all j in [i-N, i-1] AND [i+1, i+N]

    swing_low[i] = True if:
      Low[i] < Low[j] for all j in [i-N, i-1] AND [i+1, i+N]

    H1: N = 3 (3 зліва, 3 справа)
    H4: N = 2 (2 зліва, 2 справа)

### Чому різні N

H4 свічок менше (6 на день vs 24 для H1).
N=3 на H4 означало б чекати 24 години на підтвердження — занадто повільно.
H1 з N=3 дає підтвердження через 3 години — прийнятно.

### Lookahead prevention

КРИТИЧНО: swing i підтверджується тільки після повного закриття свічки i+N.
До цього моменту swing НЕ існує для системи.

    Swing confirmed at: bar i+N close time
    Swing price: High[i] або Low[i]
    Swing timestamp: bar i timestamp (коли фактично був екстремум)

Це обов'язкове правило для чесного бектесту.
Порушення = lookahead bias = невалідні результати.

---

## Swing Validation (impulse filter)

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

## Swing Lifecycle

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

### Feature table — додаткові колонки

    nearest_swing_high_H1             # ціна найближчого ACTIVE/TESTED swing high
    nearest_swing_low_H1              # ціна найближчого ACTIVE/TESTED swing low
    distance_to_swing_high_H1_pct     # (nearest_swing_high - Close) / Close * 100
    distance_to_swing_low_H1_pct      # (Close - nearest_swing_low) / Close * 100
    distance_to_swing_high_H1_atr     # (nearest_swing_high - Close) / ATR_H1
    distance_to_swing_low_H1_atr      # (Close - nearest_swing_low) / ATR_H1
    nearest_swing_high_H4
    nearest_swing_low_H4
    distance_to_swing_high_H4_pct
    distance_to_swing_low_H4_pct
    distance_to_swing_high_H4_atr
    distance_to_swing_low_H4_atr

### Event table — swing events

Кожен новий підтверджений swing записується як подія:

    EventType: SWING_HIGH або SWING_LOW
    SourceTF: H1 або H4
    PriceLevel: ціна swing
    Confidence:
      high   — impulse > 1.0 * ATR
      medium — impulse > 0.5 * ATR

---

## Параметри v1.0

| Параметр | H1 | H4 | Тип |
|---|---|---|---|
| Fractal width (N) | 3 | 2 | фіксований |
| ATR period | 14 | 14 | фіксований |
| MIN_IMPULSE_ATR_MULT | 0.5 | 0.5 | калібрувальний |
| Confirmation bars | 3 | 2 | фіксований (= N) |
| Swing states | ACTIVE / TESTED / CONSUMED | те саме | фіксований |

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

### Sweep

Факт зняття ліквідності за swing-рівнем.
Wick або bar high/low виходить за рівень.
Це НЕ сигнал сам по собі — це подія-кандидат.

Sweep може виникати ТІЛЬКИ проти swing у стані:

    swing_state ∈ {ACTIVE, TESTED}

Якщо swing_state = CONSUMED — sweep подія НЕ генерується.

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

## 3.2 Sweep Detection Rules

Працює тільки з swing-рівнями у стані ACTIVE або TESTED.

### Timeframe правило

    Sweep detection: evaluated on 1m bars
    Reference level: swing defined on H1 or H4

Sweep ловимо на 1m, бо sweep який прийшов і повернувся за 2-3 хвилини
не буде видно на H1/H4 close. А для стратегії це саме ті моменти
які нас цікавлять — швидке зняття ліквідності з rejection.

### Tick tolerance

    TICK_SIZE = exchange_symbol_tick_size
    # BTCUSDT Binance Perp: 0.10
    # Береться з metadata символу, не хардкодиться

Sweep вважається тільки якщо ціна реально пробила рівень, а не торкнулась.

### Sweep high detected if:

    swing_state in (ACTIVE, TESTED)
    bar High > swing_price + MIN_SWEEP_PENETRATION_TICKS * TICK_SIZE
    previous bar High <= swing_price       ← first cross rule

### Sweep low detected if:

    swing_state in (ACTIVE, TESTED)
    bar Low < swing_price - MIN_SWEEP_PENETRATION_TICKS * TICK_SIZE
    previous bar Low >= swing_price        ← first cross rule

### First cross rule

Sweep event генерується ТІЛЬКИ на першому барі де рівень перетнутий.
Якщо наступний бар теж High > swing_price — повторний sweep НЕ генерується.
Це запобігає дублікатам events при тривалому знаходженні за рівнем.

### Важливо

Sweep — це лише факт зняття ліквідності.
Volume spike, delta spike, OI spike — це фільтри якості,
які застосовуються пізніше (Блок 5: Event Labeling / Confidence).
Вони НЕ входять у базове визначення sweep.

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

## 3.4 Failed Break Rules

Після того як break зафіксований, починається timer.

### Failed break high:

    Був break high (Close > swing_price)
    Протягом наступних K барів (на ТФ свінга):
      хоча б один bar Close < swing_price

    → подія FAILED_BREAK_HIGH

### Failed break low:

    Був break low (Close < swing_price)
    Протягом наступних K барів (на ТФ свінга):
      хоча б один bar Close > swing_price

    → подія FAILED_BREAK_LOW

### K parameter:

    FAILED_BREAK_WINDOW = 3  # named constant

    H1: K = 3 бари (3 години)
    H4: K = 3 бари (12 годин)

### Чому K = 3

Занадто мало (1-2) — багато noise, кожен відкат буде "failed break".
Занадто багато (5+) — запізно, трейд вже пропущений.
K = 3 — баланс між швидкістю і надійністю.
Для v1.0 фіксуємо, калібруємо після бектесту.

---

## 3.5 Accepted Break Rules

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

## 3.6 Sweep-Break Lifecycle

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

### Feature table — додаткові колонки

    is_sweep_high              # bool: чи є sweep high на поточному барі
    is_sweep_low               # bool: чи є sweep low на поточному барі
    is_wick_rejection_high     # bool: sweep high + close < swing_price
    is_wick_rejection_low      # bool: sweep low + close > swing_price
    sweep_high_ref_price       # ціна свінга який знімається (0 якщо немає)
    sweep_low_ref_price        # ціна свінга який знімається (0 якщо немає)
    bars_since_last_sweep      # скільки барів пройшло з останнього sweep
    distance_to_last_sweep_atr # (Close - last_sweep_price) / ATR_H1, exhaustion signal

### Event table — events

Тип SWEEP:

    EventType: SWEEP_HIGH або SWEEP_LOW
    Side: BUY або SELL
    PriceLevel: ціна sweep (bar High або Low)
    SourceTF: H1 або H4
    ReferenceSwingTs: timestamp свінга який знято
    ReferenceSwingPrice: ціна свінга
    Confidence: визначається пізніше (Блок 5)
    MetaJson: {
        "sweep_depth": High - swing_price (наскільки пробили),
        "penetration_ticks": sweep_depth / TICK_SIZE,
        "bar_close_location": CloseLocation,
        "volume": Volume,
        "delta": Delta
    }

Тип WICK_REJECTION:

    EventType: WICK_REJECTION_HIGH або WICK_REJECTION_LOW
    Side: BUY або SELL
    PriceLevel: ціна свінга
    SourceTF: H1 або H4
    ReferenceSwingTs: timestamp свінга
    ReferenceSwingPrice: ціна свінга
    Confidence: визначається пізніше (Блок 5)
    MetaJson: {
        "sweep_depth": наскільки пробили,
        "rejection_wick": UpperWick або LowerWick,
        "bar_close_location": CloseLocation,
        "volume": Volume,
        "delta": Delta
    }

Тип FAILED_BREAK:

    EventType: FAILED_BREAK_HIGH або FAILED_BREAK_LOW
    Side: BUY або SELL
    PriceLevel: ціна свінга
    SourceTF: H1 або H4
    ReferenceSwingTs: timestamp свінга
    ReferenceSwingPrice: ціна свінга
    Confidence: визначається пізніше (Блок 5)
    MetaJson: {
        "break_bar_ts": timestamp бару який зробив break,
        "failed_at_bar": номер бару на якому повернулось (1-K),
        "return_close": ціна close бару повернення
    }

Тип BREAK (проміжна подія, для трекінгу):

    EventType: BREAK_HIGH або BREAK_LOW
    Side: BUY або SELL
    PriceLevel: ціна свінга
    SourceTF: H1 або H4
    ReferenceSwingTs: timestamp свінга
    ReferenceSwingPrice: ціна свінга
    Confidence: визначається після K барів
    MetaJson: {
        "break_close": ціна close бару break
    }

Тип ACCEPTED_BREAK:

    EventType: ACCEPTED_BREAK_HIGH або ACCEPTED_BREAK_LOW
    Side: BUY або SELL
    PriceLevel: ціна свінга
    SourceTF: H1 або H4
    ReferenceSwingTs: timestamp свінга
    ReferenceSwingPrice: ціна свінга
    Confidence: high (утримався K барів = сильний сигнал)
    MetaJson: {
        "break_bar_ts": timestamp початкового break,
        "hold_bars": K
    }

---

## 3.8 Параметри v1.0

| Параметр | H1 | H4 | Тип |
|---|---|---|---|
| FAILED_BREAK_WINDOW (K) | 3 | 3 | фіксований |
| TICK_SIZE | 0.10 | 0.10 | з metadata символу (BTCUSDT=0.10) |
| MIN_SWEEP_PENETRATION_TICKS | 2 | 2 | калібрувальний |
| Sweep trigger | High/Low > swing ± penetration | те саме | фіксований |
| Sweep first cross | prev High/Low <= swing_price | те саме | фіксований |
| Sweep detection TF | 1m bars | 1m bars | фіксований |
| Break trigger | Close > swing_price | те саме | фіксований |
| Wick rejection | sweep + Close строго по правильну сторону | те саме | фіксований |
| Failed = return close | будь-який з K барів | те саме | фіксований |
| Accepted = hold close | всі K барів | те саме | фіксований |
| New break after failed | вимагає нового sweep | те саме | фіксований |

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

Swing залишається ACTIVE/TESTED поки не буде ACCEPTED_BREAK.

---

## 3.10 Архітектурне рішення

Analyzer реалізується як event-driven state machine (варіант A).

Analyzer підтримує в пам'яті:

    swing_registry     — всі ACTIVE/TESTED свінги з їх станами
    break_timers       — активні break events з countdown до K
    event_log          — історія всіх згенерованих events

Stateless per-bar detection (варіант B) не підходить,
бо failed break вимагає трекінгу стану через K барів.

---

## 3.11 Повний список event types Блоку 3

    SWEEP_HIGH
    SWEEP_LOW
    WICK_REJECTION_HIGH
    WICK_REJECTION_LOW
    BREAK_HIGH
    BREAK_LOW
    FAILED_BREAK_HIGH
    FAILED_BREAK_LOW
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

    10:00 — swing high candidate (H1)
    10:10 — ціна пробиває цей high (sweep)
    10:20 — reversal
    13:00 — swing confirmed (N=3 bars)

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

## 3.16 Sweep Penetration Filter

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

Swing фрактали потребують правих барів для підтвердження.

    H1: fractal width N = 3, confirmation delay = 3 bars
    H4: fractal width N = 2, confirmation delay = 2 bars

    Swing на барі i підтверджується лише після закриття бару i + N.

    event_time = close_time[i + N]
    swing_price = High[i] або Low[i]

Приклад:

    H1 swing high candidate at 10:00
    N = 3, confirmation at 13:00
    event timestamp = 13:00

До 13:00 цей swing НЕ ІСНУЄ для системи.

---

## 6.3 Sweep detection timing

Sweep визначається в момент закриття бару де відбувся wick.

    High[t] > swing_price + MIN_SWEEP_PENETRATION_TICKS * TICK_SIZE
    previous High[t-1] <= swing_price

    event_time = close_time[t]

Analyzer не може перевіряти наступні бари щоб вирішити чи це sweep.

---

## 6.4 Break detection timing

Break визначається тільки по close закритого бару.

    Close[t] > swing_price → BREAK_HIGH
    Close[t] < swing_price → BREAK_LOW

    event_time = close_time[t]

Break event створюється одразу після закриття бару.

---

## 6.5 Failed / Accepted break resolution

Break подія має період спостереження K барів.

    FAILED_BREAK_WINDOW = K = 3

Правила:

    Break на барі t → status = PENDING
    Кожен наступний бар t+1, t+2, t+3 перевіряється по close
    Resolution timestamp = close_time[t + K]

    Accepted: всі K барів Close за рівнем
    Failed: хоча б один з K барів Close повернувся назад

До моменту t + K статус break = PENDING.
Pending events НЕ впливають на інші розрахунки.

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

## 7.3 Event Table Contract

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
