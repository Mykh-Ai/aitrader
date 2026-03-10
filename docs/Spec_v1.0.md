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
Trades
BuyQty
SellQty
OpenInterest
FundingRate
LiqBuyQty
LiqSellQty

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

# 0. Output Format

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
Trades
BuyQty
SellQty
OpenInterest
FundingRate
LiqBuyQty
LiqSellQty

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

# 1. Base Metrics

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

# 2. Swing Logic

TBD

---

# 3. Failed Break Logic

TBD

---

# 4. Absorption Detection

TBD

---

# 5. Event Labeling

TBD
