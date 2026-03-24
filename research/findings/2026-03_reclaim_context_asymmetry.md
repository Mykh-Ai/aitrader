# Finding: FAILED_BREAK_RECLAIM Context Asymmetry

**Date:** 2026-03-18
**Status:** Preliminary — NOT actionable, NOT a ruleset change
**Script:** `research/slice_analysis_reclaim_context.py`
**Result snapshot:** `research/results/reclaim_context_asymmetry_summary.csv`

---

## Objective

Test whether LONG and SHORT FAILED_BREAK_RECLAIM setups perform differently
depending on the market stress context at setup detection time.

Manual observation hypothesis (pre-analysis):
- LONG winners appeared in lower-stress / cleaner reclaim context
- SHORT winners appeared in higher-stress / more aggressive reclaim context

---

## Data Basis

| Source | Value |
|--------|-------|
| Analyzer runs used | 9 runs across 6 unique days |
| Date range | 2026-03-12 to 2026-03-17 |
| Raw rows loaded | 402 |
| After SetupId deduplication | 249 unique setups |
| LONG setups | 81 |
| SHORT setups | 168 |
| Outcome metric | `CloseReturn_Pct` (forward close-return over 12 bars) |
| MFE/MAE metric | `MFE_Pct`, `MAE_Pct` from `analyzer_setup_outcomes.csv` |

Deduplication note: runs 2026-03-14_run_002/003/004 are re-runs of the same day
with identical SetupIds. Kept first occurrence (earliest run by sort order).

---

## Slicing Logic

**Method:** Median split computed within each direction separately.
Cross-direction contamination in threshold selection is avoided.

### LONG — low-stress slice (all 3 conditions simultaneously)
```
AbsorptionScore_v1 <= median(LONG population)   [median = 1.000]
RelVolume_20       <= median(LONG population)   [median = 0.785]
LiqTotalRatio_20   <= median(LONG population)   [median = 0.000]
```

### SHORT — high-stress slice (all 3 conditions simultaneously)
```
AbsorptionScore_v1 >= median(SHORT population)  [median = 1.000]
RelVolume_20       >= median(SHORT population)  [median = 0.869]
DeltaAbsRatio_20   >= median(SHORT population)  [median = 0.552]
```

Field selection rationale: 3-field minimum coverage of the hypothesis without
overfitting. LONG uses LiqTotalRatio (liquidity activity) instead of DeltaAbsRatio
because manual observation flagged liq context as the key LONG differentiator.

---

## Results

### LONG (n=81)

| Slice | n | pos_rate | mean_ret | median_ret | MFE | MAE |
|-------|---|----------|----------|------------|-----|-----|
| baseline (all) | 81 | 67.9% | +0.125% | +0.108% | 0.263% | -0.132% |
| **low-stress (all 3 ≤ median)** | **28** | **85.7%** | **+0.230%** | **+0.228%** | **0.339%** | **-0.077%** |
| high-stress (any 1 > median) | 53 | 58.5% | +0.069% | +0.062% | 0.222% | -0.162% |
| zero ctx spikes | 30 | 80.0% | +0.159% | +0.144% | 0.291% | -0.117% |

### SHORT (n=168)

| Slice | n | pos_rate | mean_ret | median_ret | MFE | MAE |
|-------|---|----------|----------|------------|-----|-----|
| baseline (all) | 168 | 53.0% | +0.004% | +0.008% | 1.374% | -0.119% |
| **high-stress (all 3 ≥ median)** | **50** | **58.0%** | **+0.023%** | **+0.033%** | **2.187%** | **-0.090%** |
| low-stress (any 1 < median) | 118 | 50.8% | -0.004% | +0.001% | 1.030% | -0.131% |
| ≥2 ctx spikes active | 43 | 55.8% | +0.033% | +0.031% | 2.515% | -0.077% |

### Hypothesis verdict

| Hypothesis | Delta pos_rate | Delta mean_ret | Verdict |
|------------|---------------|----------------|---------|
| LONG: low-stress better | +17.8pp | +0.105% | **WEAKLY SUPPORTED** |
| SHORT: high-stress better | +5.0pp | +0.019% | **WEAKLY SUPPORTED** |

---

## Interpretation

**LONG signal is stronger:**
- +18pp pos_rate in low-stress slice vs baseline is directionally convincing
- MAE halved (-0.077% vs -0.132%) — setups move less against position
- MFE +29% — setups run further in intended direction
- High-stress LONG is the worst segment across all metrics

**SHORT signal is weaker on pos_rate but notable on MFE:**
- +5pp pos_rate modest
- HIGH-stress MFE = 2.19% vs 1.37% baseline (+59%) — setups go further when conditions match
- ≥2 ctx spikes: MFE = 2.51% — highest MFE in entire dataset
- This suggests high-stress SHORT setups have more potential if TP placement captures it

**Directional asymmetry exists:** LONG and SHORT should NOT share the same context
filter. This is the key structural observation from this finding.

---

## Limitations

1. **Sample too small for statistical significance.** LONG n=81, low-stress slice n=28.
   No p-values computed. This is exploratory, not confirmatory.
2. **Outcome metric is CloseReturn_Pct (12-bar forward close), not actual trade PnL.**
   Real trade outcomes depend on entry timing, SL placement, TP placement.
3. **6 days only (2026-03-12 to 2026-03-17).** Market regime may not be representative.
4. **Median split is population-dependent.** Thresholds will shift on a larger window.
   This is expected and correct — medians are within-direction by design.
5. **No cross-day stability check performed.** Individual day results may vary significantly.

---

## Next Step

**Repeat this exact analysis on a larger window (target: 30+ days).**

Rules for the repeat:
- Same script, same slice definitions, same field selections
- Do NOT adjust thresholds to fit new data
- Do NOT add new slice dimensions
- If finding persists directionally on 30+ days → graduate to ruleset parameter candidate
- If finding reverses or disappears → discard hypothesis

Do NOT convert to a ruleset filter until the larger-window repeat is complete.

---

## Follow-up

Extended by phase-conditioned analysis:
[`2026-03_reclaim_context_asymmetry_phase_conditioned.md`](2026-03_reclaim_context_asymmetry_phase_conditioned.md)

Result: asymmetry survives within MIXED phase bucket. Not a phase-mixing artifact.
