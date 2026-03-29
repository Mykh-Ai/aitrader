# H2 Reclaim Durability Predictors

**Date:** 2026-03-29
**Analyst:** Shi research cycle
**Status:** observational only — read-only analysis, no code changes, no replay

---

## 1. Scope

**Data window:** 2026-03-18 → 2026-03-29 (12 days)

**Artifact source:** `local_runs/h2_bounded/<date>/` — per-day analyzer runs

**Setup types:** `IMPULSE_FADE_RECLAIM_LONG_V1`, `IMPULSE_FADE_RECLAIM_SHORT_V1`

**Total H2 setups:** 315 (LONG: 168 / SHORT: 147)

**Target label:** `H2_Post6Label_v1`
- `RECLAIM_HELD` = 116 setups (36.8%)
- `RECLAIM_FAILED` = 199 setups (63.2%)

**At-entry features examined:**
- Binary: `CtxLiqSpike_v1`, `CtxDeltaSpike_v1`, `CtxWickReclaim_v1`
- Ordinal: `AbsorptionScore_v1` (0–4)
- Numeric: `RelVolume_20`, `DeltaAbsRatio_20`, `OIChangeAbsRatio_20`, `LiqTotalRatio_20`
- Context: `Session` (ASIA / EU / US)

**Reference summary CSV:** `research/results/h2_reclaim_durability_predictors_2026-03-29.csv`

---

## 2. Executive verdict

At least two at-entry features show meaningful association with `RECLAIM_HELD`,
particularly in the SHORT direction.

**`CtxLiqSpike_v1 = True`** is the strongest single-feature signal:
held rate 63.6% for SHORT (n=22) vs 33.6% baseline SHORT (n=125) — **+30pp gap**.
Sample is borderline (n=22) but the magnitude is not subtle.

**`AbsorptionScore_v1 = HIGH (3+)`** is the second candidate:
held rate 63.0% for SHORT (n=27) vs 19.4% for AbsScore=MID — a **+44pp gap** vs MID,
and +16pp vs aggregate SHORT baseline.
Granular breakdown reveals a non-linear U-shape: score=1 is the worst cell (15.9% SHORT held rate).

These two features are **not independent** — HIGH absorption scores correlate heavily
with CtxLiqSpike and CtxDeltaSpike: at score=4 (SHORT), 100% have LiqTotalRatio>0
and DeltaSpike rate is near-total. They measure overlapping phenomena.

Both candidates are **filter hypothesis candidates** — but not yet actionable.
Samples are limited (n=22–27 for the "good" cells).
Both need 3–4x more data before interpretation can shift from "candidate" to "evidence."

**Negative predictor also found:** `AbsorptionScore_v1 = 1` is a reliable AVOID signal
for SHORT (15.9% held rate, n=44). This is below coin-flip for durability.

`CtxWickReclaim_v1` is unreliable at current sample sizes (n≤13, inverted, discard).
`RelVolume_20` shows flat held rate (HIGH 0.369 vs LOW 0.367 — effectively zero signal).
`OIChangeAbsRatio_20` is similarly flat (+1.5pp — noise).

---

## 3. Aggregate held vs failed baseline

| Subpop   | N   | HELD_rate | Baseline for comparison |
|----------|-----|-----------|------------------------|
| ALL      | 315 | 36.8%     | —                      |
| LONG     | 168 | 35.7%     | —                      |
| SHORT    | 147 | 38.1%     | —                      |

---

## 4. Single-feature analysis

### 4.1 CtxLiqSpike_v1

| Feature val | Subpop | N   | HELD_rate | Delta vs no-spike |
|-------------|--------|-----|-----------|-------------------|
| True        | ALL    | 42  | 59.5%     | +26.2pp           |
| False       | ALL    | 273 | 33.3%     | —                 |
| True        | LONG   | 20  | 55.0%     | +21.9pp           |
| False       | LONG   | 148 | 33.1%     | —                 |
| True        | SHORT  | 22  | **63.6%** | **+30.0pp**       |
| False       | SHORT  | 125 | 33.6%     | —                 |

CtxLiqSpike=True is rare (42/315 = 13.3%). When present, held rate nearly doubles.
Effect is stronger for SHORT than LONG (+30pp vs +22pp).
Caveat: n=22 for SHORT_LiqSpike=True is borderline. Direction is clear, magnitude uncertain.

### 4.2 CtxDeltaSpike_v1

| Feature val | Subpop | N   | HELD_rate | Delta vs no-spike |
|-------------|--------|-----|-----------|-------------------|
| True        | ALL    | 99  | 43.4%     | +9.6pp            |
| False       | ALL    | 216 | 33.8%     | —                 |
| True        | LONG   | 57  | 38.6%     | +4.4pp            |
| False       | LONG   | 111 | 34.2%     | —                 |
| True        | SHORT  | 42  | **50.0%** | **+16.7pp**       |
| False       | SHORT  | 105 | 33.3%     | —                 |

CtxDeltaSpike has a moderate SHORT-specific effect. +16.7pp with adequate sample (n=42).
But it's the "weaker version" of the LiqSpike signal (more common, less specific).

### 4.3 CtxWickReclaim_v1 — DISCARD

Very low prevalence (n=13 ALL, n=6 SHORT), and the association is **inverted**
(held rate 7.7% ALL vs 38.1% without). Inverse likely spurious given n=13.
Cannot interpret. Discard for now.

### 4.4 AbsorptionScore_v1 — non-linear, U-shaped

Granular per-score breakdown:

| Score | N_ALL | HeldRate_ALL | N_SHORT | HeldRate_SHORT |
|-------|-------|--------------|---------|----------------|
| 0     | 118   | 42.4%        | 58      | 46.6%          |
| 1     | 101   | 22.8%        | 44      | **15.9%**      |
| 2     | 39    | 28.2%        | 18      | 27.8%          |
| 3     | 38    | 44.7%        | 18      | 50.0%          |
| 4     | 19    | **78.9%**    | 9       | **88.9%** LOW_SAMPLE |

**Critical non-linear pattern:**
- Score=0 (no absorption signals): moderate held rate (46.6% SHORT) — "quiet setup"
- Score=1 (one weak signal): WORST held rate (15.9% SHORT) — "partial signal = false reclaim"
- Score=4 (all signals confirmed): near-perfect durability (88.9% SHORT) — but n=9, LOW_SAMPLE

The U-shape is NOT monotonic. Score=1 acts as a negative predictor, score=4 as a strong positive.

**Structural explanation for U-shape:**
- Score=0 setups have zero LiqSpike, zero DeltaSpike, zero LiqRatio
  → quiet compressed market, reclaim meets no resistance, holds by default
- Score=1 setups show partial activity (LiqTotalRatio starts appearing, DeltaSpike=27%)
  → "noisy threshold" — some opposing force present but not confirmed quality
  → creates contested reclaims that fail
- Score=4 setups have confirmed liquidity events:
  at score=4 (SHORT), 100% have LiqTotalRatio>0, DeltaSpike near-certain
  → full liquidity event confirmation → reclaim is decisive, highly durable

This explains why CtxLiqSpike and AbsorptionScore are correlated:
AbsorptionScore is effectively a composite of the same signals.

### 4.5 LiqTotalRatio_20

| Value   | Subpop | N   | HELD_rate |
|---------|--------|-----|-----------|
| NONZERO | ALL    | 89  | 49.4%     |
| ZERO    | ALL    | 226 | 31.9%     |
| NONZERO | SHORT  | 40  | 47.5%     |
| ZERO    | SHORT  | 107 | 34.6%     |

+17.5pp gap (ALL) / +12.9pp gap (SHORT). Moderate but consistent.
When any liquidation flow is present, durability improves — overlaps with LiqSpike signal.

### 4.6 RelVolume_20 / OIChangeAbsRatio_20 — flat, no signal

| Feature         | Tier | ALL HeldRate | SHORT HeldRate | Delta |
|-----------------|------|--------------|----------------|-------|
| RelVolume_20    | HIGH | 36.9%        | 36.8%          | flat  |
| RelVolume_20    | LOW  | 36.7%        | 39.2%          | flat  |
| OIChangeAbsRatio| HIGH | 37.6%        | 37.8%          | flat  |
| OIChangeAbsRatio| LOW  | 36.1%        | 38.4%          | flat  |

Relative volume and OI change show zero predictive value for reclaim durability.
These measure activity level, not quality — consistent with finding that durability
depends on liquidity event type, not raw volume.

---

## 5. SHORT-specific analysis

### 5.1 Session effect on SHORT held rate

| Session | N_SHORT | HELD_rate |
|---------|---------|-----------|
| ASIA    | 66      | 34.8%     |
| EU      | 39      | 35.9%     |
| US      | 42      | **45.2%** |

US session produces +10.4pp held rate vs ASIA for SHORT.
Effect is real but moderate — session is a secondary factor, not primary.

### 5.2 Combined SHORT feature slices

| Feature / Value          | N   | HELD_rate | vs baseline 38.1% | Note        |
|--------------------------|-----|-----------|-------------------|-------------|
| SHORT × CtxLiqSpike=True | 22  | 63.6%     | +25.5pp           | borderline n|
| SHORT × AbsScore=HIGH    | 27  | 63.0%     | +24.9pp           |             |
| SHORT × CtxDeltaSpike=T  | 42  | 50.0%     | +11.9pp           |             |
| SHORT × AbsScore=LOW     | 58  | 46.6%     | +8.5pp            |             |
| SHORT × AbsScore=MID     | 62  | 19.4%     | −18.7pp           | AVOID signal|
| SHORT × US session       | 42  | 45.2%     | +7.1pp            |             |
| SHORT × US × DeltaSpike=T| 13  | 69.2%     | —                 | LOW_SAMPLE  |
| SHORT × US × LiqSpike=T  | 9   | 66.7%     | —                 | LOW_SAMPLE  |

**SHORT × AbsScore=MID is the strongest AVOID signal** (n=62, 19.4% held rate).
This is the most actionable finding: setups with AbsorptionScore=1-2 should be
deprioritized in future filter design.

---

## 6. Best predictor candidates

**Candidate A: CtxLiqSpike_v1 = True (SHORT-specific)**
- Effect: +30pp vs baseline SHORT
- Current sample (SHORT): n=22 — borderline
- Strength: highest rate among all single-feature slices (63.6%)
- Concern: rare event (13.3% prevalence) → limited setups per day

**Candidate B: AbsorptionScore_v1 = HIGH (3+) (SHORT-specific)**
- Effect: +24.9pp vs baseline SHORT
- Current sample (SHORT): n=27 — borderline but above 20
- Strength: 63.0% held rate, structurally consistent with Candidate A
  (score=4 = 88.9%, score=3 = 50.0%)
- Note: these are partially the same signal (AbsScore HIGH implies LiqSpike likely)

**Negative candidate: AbsorptionScore_v1 = 1 (AVOID)**
- Effect: −22.2pp vs baseline SHORT
- Sample (SHORT): n=44 — adequate
- 15.9% held rate = strong negative predictor for SHORT
- Actionable as exclusion criterion in future filter design

**What is NOT a candidate:**
- RelVolume_20: flat, zero signal
- OIChangeAbsRatio_20: flat, zero signal
- CtxWickReclaim_v1: LOW_SAMPLE + inverted, not interpretable
- Session alone: mild modifier, not standalone predictor

**Feature independence note:**
Candidates A and B are correlated — AbsorptionScore=HIGH implies CtxLiqSpike likely True,
and both measure the same underlying liquidity event quality.
They are not independent predictors; they are two views of one phenomenon:
**confirmed liquidity event at formation = durable reclaim**.

---

## 7. Strategic interpretation for Shi

**The at-entry predictor gap is partially closed.**

The research gap from the subslice review was:
"RECLAIM_HELD is real but post-hoc — what at-entry features predict it?"

The answer is: **liquidity event quality at formation**.

Specifically:
- When a SHORT setup forms with confirmed liquidity spike (`CtxLiqSpike_v1=True`
  or `AbsorptionScore=HIGH`), the reclaim is ~2x more likely to hold.
- When a SHORT setup forms with partial/weak activity (`AbsorptionScore=1`),
  the reclaim almost certainly fails (15.9% held rate, n=44).
- "Quiet" setups (AbsorptionScore=0, no spikes) have moderate durability (46.6%)
  — likely because compressed market provides no resistance.

This is conceptually consistent with the strategy thesis:
stronger liquidity event → more decisive mean reversion → more durable reclaim.

**However — the candidates are not yet filter-ready:**
- CtxLiqSpike=True for SHORT has n=22 — need n≥50 for confidence
- AbsScore=HIGH for SHORT has n=27 — same limitation
- Score=4 (best cell) has n=9 — cannot conclude anything

**What this changes:**
The question shifts from "is there a predictor?" (answered: probably yes)
to "is this predictor stable at scale?" (needs more data).

**What does NOT change:**
- H2 remains non-formalizable
- No code changes warranted
- No replay warranted
- Strategy stays in pure observation mode

---

## 8. Decision

**H2_FILTER_CANDIDATE_EMERGING**

Rationale: Two at-entry features (`CtxLiqSpike_v1`, `AbsorptionScore_v1=HIGH`)
show meaningful and structurally consistent association with RECLAIM_HELD in SHORT direction.
The effect is large enough (+25–30pp) to be unlikely pure noise at n=22–27,
but samples are insufficient for confident conclusions.
One strong negative predictor is identified (`AbsorptionScore=1`, n=44, −22pp).

---

## 9. Next step

Continue bounded H2 data collection on the next 2-week window
(target: 2026-04-01 → 2026-04-14) and re-run this predictor analysis
to check whether `CtxLiqSpike_v1=True` and `AbsorptionScore=HIGH` held rates
remain stable with n≥50 per SHORT cell.
No code changes. No replay. Read-only rerun of this same analysis script.
