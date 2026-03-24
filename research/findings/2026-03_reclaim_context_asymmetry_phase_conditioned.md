# Finding: Phase-Conditioned Reclaim Context Asymmetry

**Date:** 2026-03-24
**Status:** Research-only, phase-conditioned, NOT ruleset-ready
**Extends:** `2026-03_reclaim_context_asymmetry.md`
**Script:** `research/scripts/slice_by_regime.py`
**New dimension:** `PhaseHeuristicLabel` from `analyzer/day_regime_report.py`

---

## Question

Does the reclaim-context asymmetry (LONG low-stress, SHORT high-stress)
survive after stratification by PhaseHeuristicLabel?

Or is it an artifact of mixing structurally different market days?

---

## Data Basis

| Source | Value |
|--------|-------|
| Analyzer runs used | 11 runs across 11 unique days |
| Date range | 2026-03-12 to 2026-03-23 |
| Unique setups after dedup | 217 |
| LONG setups | 62 |
| SHORT setups | 155 |
| Phase buckets observed | MIXED (211 setups, 6 runs), ACCUMULATION (6 setups, 5 runs) |
| Methodology | Frozen from `2026-03_reclaim_context_asymmetry.md` — no slice logic change |

---

## Result

### Phase distribution

| phase | setups | LONG | SHORT | runs | date range |
|-------|--------|------|-------|------|------------|
| MIXED | 211 | 59 | 152 | 6 | 03-12→17, 03-23 |
| ACCUMULATION | 6 | 3 | 3 | 5 | 03-18→22 |

### Asymmetry survival

| hypothesis | ALL_PHASES | MIXED | ACCUMULATION |
|---|---|---|---|
| LONG low-stress > baseline | +10.6pp SUPPORTED | +10.1pp SUPPORTED | n=2, not evaluable |
| SHORT high-stress > baseline | +4.2pp SUPPORTED | +4.8pp SUPPORTED | n=1, not evaluable |

### MIXED bucket detail

| direction | slice | n | pos_rate | mean_ret | MFE | MAE |
|-----------|-------|---|----------|----------|-----|-----|
| LONG | baseline | 59 | 76.3% | +0.162% | 0.287% | -0.131% |
| LONG | low-stress (all 3 <= median) | 22 | 86.4% | +0.236% | 0.342% | -0.088% |
| LONG | high-stress (any 1 > median) | 37 | 70.3% | +0.117% | 0.254% | -0.156% |
| SHORT | baseline | 152 | 52.6% | -0.003% | 1.483% | -0.116% |
| SHORT | high-stress (all 3 >= median) | 47 | 57.4% | +0.022% | 2.312% | -0.087% |
| SHORT | low-stress (any 1 < median) | 105 | 50.5% | -0.014% | 1.113% | -0.129% |

---

## What is now closed

**Hypothesis "asymmetry is only a phase-mixing artifact" — not supported.**

The asymmetry exists within MIXED phase, which is the only bucket
with sufficient sample size. Phase stratification does not dissolve it.

---

## What remains open

- Whether asymmetry survives on a larger history (30+ days, multiple phase types).
- Whether other phase buckets (MOVEMENT, CORRECTION) show different behavior.
- Whether ACCUMULATION days can ever produce enough setups for inference.

---

## Important caveat

This is not a ruleset validation and not an execution decision.

- ACCUMULATION bucket (n=6) is statistically empty. Any numbers there are noise.
- MIXED bucket (n=211) is the only evaluable bucket. Results are directional, not confirmed.
- No claim that "low-stress LONG works" or "high-stress SHORT works" as tradeable rules.
- No claim that "ACCUMULATION days are untradeable."

---

## Limitations

1. **Only two phase buckets observed** (MIXED and ACCUMULATION). Other phases
   (MOVEMENT, CORRECTION) absent from this date range.
2. **ACCUMULATION bucket too small for any inference** — 6 setups across 5 days.
3. **MIXED bucket inherits all limitations from the original finding** —
   small sample, proxy outcome metric, median-split population dependence.
4. **12 days total.** Market regime may not be representative.
5. **PhaseHeuristicLabel is itself a heuristic** — thresholds are provisional,
   label semantics are descriptive naming only (per commit `f4b15e9`).
