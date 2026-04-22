# Transition Analysis: Replay→Reject vs FE=0

**Date:** 2026-03-24 (updated with full VPS data)
**Commit:** c81e6ba (current repo state)
**Type:** Targeted research note — longitudinal transition regime
**Data source:** Full analyzer CSVs from VPS for all 9 runs

---

## A. Scope

### Group A: REPLAY→REJECT (3 runs)

| run_id | processed_at | source |
|--------|-------------|--------|
| 2026-03-15_to_2026-03-15_run_001 | 2026-03-22 | run_log.csv + VPS CSV |
| 2026-03-16_to_2026-03-16_run_001 | 2026-03-22 | run_log.csv + VPS CSV |
| 2026-03-17_to_2026-03-17_run_001 | 2026-03-22 | run_log.csv + VPS CSV |

All three reached full replay (backtester fan-out), all REJECT.

### Group B: FE=0 / NO_REPLAY (6 runs)

| run_id | processed_at | source |
|--------|-------------|--------|
| 2026-03-18_to_2026-03-18_run_001 | 2026-03-22 | run_log.csv + VPS CSV |
| 2026-03-19_to_2026-03-19_run_001 | 2026-03-22 | run_log.csv + VPS CSV |
| 2026-03-20_to_2026-03-20_run_001 | 2026-03-22 | run_log.csv + VPS CSV |
| 2026-03-21_to_2026-03-21_run_001 | 2026-03-22 | run_log.csv + VPS CSV |
| 2026-03-22_to_2026-03-22_run_001 | 2026-03-24 | probe_summary.csv + VPS CSV |
| 2026-03-23_to_2026-03-23_run_001 | 2026-03-24 | probe_summary.csv + VPS CSV |

These 6 runs form the consecutive `FormalizationEligible=0` streak
flagged by diagnostics.json.

**Boundary verification:** diagnostics.json explicitly states
`"6 consecutive runs with FormalizationEligible=0"`.
The first FE=0 run in this streak is 03-18; the last REPLAY→REJECT run is 03-17.
The transition boundary is **between 03-17 and 03-18**.

**Why these runs:** Group A = all runs from weekly cycle 2026-03-22 that reached
replay. Group B = full consecutive FE=0 streak including current cycle runs.

---

## B. Funnel evidence

### B.1. Funnel summary table

| run_dir | run_date | group | setups | LONG | SHORT | shortlist_rows | FE_rows | replay_status | derived_runs | final_decision |
|---------|----------|-------|--------|------|-------|----------------|---------|---------------|-------------|----------------|
| 03-15_run_001 | 03-15 | REPLAY_REJECT | 48 | 11 | 37 | 27 | 4 | REPLAYED | 4 | REJECT |
| 03-16_run_001 | 03-16 | REPLAY_REJECT | 46 | 11 | 35 | 17 | 2 | REPLAYED | 2 | REJECT |
| 03-17_run_001 | 03-17 | REPLAY_REJECT | 30 | 21 | 9 | 17 | 2 | REPLAYED | 2 | REJECT |
| 03-18_run_001 | 03-18 | FE0 | **1** | 1 | 0 | 0 | 0 | SKIPPED | 0 | NO_REPLAYABLE_RULESETS |
| 03-19_run_001 | 03-19 | FE0 | **1** | 0 | 1 | 0 | 0 | SKIPPED | 0 | NO_REPLAYABLE_RULESETS |
| 03-20_run_001 | 03-20 | FE0 | **1** | 1 | 0 | 0 | 0 | SKIPPED | 0 | NO_REPLAYABLE_RULESETS |
| 03-21_run_001 | 03-21 | FE0 | **2** | 1 | 1 | 0 | 0 | SKIPPED | 0 | NO_REPLAYABLE_RULESETS |
| 03-22_run_001 | 03-22 | FE0 | **1** | 0 | 1 | 0 | 0 | SKIPPED | 0 | NO_REPLAYABLE_RULESETS |
| 03-23_run_001 | 03-23 | FE0 | **3** | 1 | 2 | 0 | 0 | SKIPPED | 0 | NO_REPLAYABLE_RULESETS |

Setup count drop: **30-48 → 1-3**. This is the primary transition signal.

### B.2. Selections profile per run

#### Group A: REPLAY→REJECT

| run | SELECT | REVIEW | REJECT | STRONG_POS | POS_BORDER | NON_POS | LOW_SAMPLE | median_score | max_score | delta_pos>0 | MinSampleTrue |
|-----|--------|--------|--------|------------|------------|---------|------------|-------------|-----------|-------------|---------------|
| 03-15 | 14 | 13 | 5 | 14 | 13 | 4 | 1 | 0.087 | 0.288 | 17/32 | 31/32 |
| 03-16 | 9 | 8 | 15 | 9 | 8 | 15 | 0 | 0.003 | 0.529 | 16/32 | 32/32 |
| 03-17 | 13 | 4 | 14 | 13 | 4 | 11 | 3 | 0.002 | 0.393 | 15/31 | 28/31 |

#### Group B: FE=0

| run | SELECT | REVIEW | REJECT | STRONG_POS | POS_BORDER | NON_POS | LOW_SAMPLE | median_score | max_score | delta_pos>0 | MinSampleTrue |
|-----|--------|--------|--------|------------|------------|---------|------------|-------------|-----------|-------------|---------------|
| 03-18 | 0 | 0 | **9** | 0 | 0 | 0 | **9** | -0.003 | -0.003 | 0/9 | **0/9** |
| 03-19 | 0 | 0 | **9** | 0 | 0 | 0 | **9** | -0.015 | -0.015 | 0/9 | **0/9** |
| 03-20 | 0 | 0 | **9** | 0 | 0 | 0 | **9** | 0.006 | 0.006 | 0/9 | **0/9** |
| 03-21 | 0 | 0 | **17** | 0 | 0 | 0 | **17** | 0.004 | 0.005 | 0/17 | **0/17** |
| 03-22 | 0 | 0 | **9** | 0 | 0 | 0 | **9** | 0.005 | 0.005 | 0/9 | **0/9** |
| 03-23 | 0 | 0 | **28** | 0 | 0 | 0 | **28** | 0.352 | 0.359 | 15/28 | **0/28** |

**Key contrast:**
- Group A: 84-97% of ranking rows pass MinSamplePassed. Mixed SELECT/REVIEW/REJECT.
- Group B: **0% pass MinSamplePassed.** 100% REJECT LOW_SAMPLE. Zero exceptions across 81 total selection rows.
- Run 03-23 is notable: high scores (max 0.359) and 15/28 positive delta — but still 100% LOW_SAMPLE because SampleCount=1-2 across all groups.

### B.3. Direction/SetupType rankings detail

#### Group A: the groups that produce FE=True

| run | GroupType | GroupValue | SampleCount | RankingScore | Label | MinSample | Selection |
|-----|-----------|------------|-------------|-------------|-------|-----------|-----------|
| 03-15 | Direction | LONG | 11 | 0.283 | TOP | True | SELECT |
| 03-15 | Direction | SHORT | 37 | 0.026 | TOP | True | REVIEW |
| 03-15 | SetupType | FB_RECLAIM_LONG | 11 | 0.283 | TOP | True | SELECT |
| 03-15 | SetupType | FB_RECLAIM_SHORT | 37 | 0.026 | TOP | True | REVIEW |
| 03-16 | Direction | LONG | 11 | 0.220 | TOP | True | SELECT |
| 03-16 | Direction | SHORT | 35 | -0.067 | WEAK | True | REJECT |
| 03-16 | SetupType | FB_RECLAIM_LONG | 11 | 0.220 | TOP | True | SELECT |
| 03-16 | SetupType | FB_RECLAIM_SHORT | 35 | -0.067 | WEAK | True | REJECT |
| 03-17 | Direction | LONG | 21 | -0.059 | WEAK | True | REJECT |
| 03-17 | Direction | SHORT | 9 | 0.145 | TOP | True | SELECT |
| 03-17 | SetupType | FB_RECLAIM_LONG | 21 | -0.059 | WEAK | True | REJECT |
| 03-17 | SetupType | FB_RECLAIM_SHORT | 9 | 0.145 | TOP | True | SELECT |

FE rows per run:
- 03-15: 4 FE (LONG SELECT + SHORT REVIEW → both directions eligible)
- 03-16: 2 FE (only LONG SELECT; SHORT REJECT NON_POSITIVE_EDGE)
- 03-17: 2 FE (only SHORT SELECT; LONG REJECT NON_POSITIVE_EDGE — direction flipped)

#### Group B: the groups that block FE

| run | GroupType | GroupValue | SampleCount | RankingScore | Label | MinSample | Selection |
|-----|-----------|------------|-------------|-------------|-------|-----------|-----------|
| 03-18 | Direction | LONG | **1** | -0.003 | LOW_SAMPLE | False | REJECT |
| 03-18 | SetupType | FB_RECLAIM_LONG | **1** | -0.003 | LOW_SAMPLE | False | REJECT |
| 03-19 | Direction | SHORT | **1** | -0.015 | LOW_SAMPLE | False | REJECT |
| 03-19 | SetupType | FB_RECLAIM_SHORT | **1** | -0.015 | LOW_SAMPLE | False | REJECT |
| 03-20 | Direction | LONG | **1** | 0.006 | LOW_SAMPLE | False | REJECT |
| 03-20 | SetupType | FB_RECLAIM_LONG | **1** | 0.006 | LOW_SAMPLE | False | REJECT |
| 03-21 | Direction | LONG | **1** | 0.005 | LOW_SAMPLE | False | REJECT |
| 03-21 | Direction | SHORT | **1** | 0.003 | LOW_SAMPLE | False | REJECT |
| 03-21 | SetupType | FB_RECLAIM_LONG | **1** | 0.005 | LOW_SAMPLE | False | REJECT |
| 03-21 | SetupType | FB_RECLAIM_SHORT | **1** | 0.003 | LOW_SAMPLE | False | REJECT |
| 03-22 | Direction | SHORT | **1** | 0.005 | LOW_SAMPLE | False | REJECT |
| 03-22 | SetupType | FB_RECLAIM_SHORT | **1** | 0.005 | LOW_SAMPLE | False | REJECT |
| 03-23 | Direction | LONG | **1** | 0.352 | LOW_SAMPLE | False | REJECT |
| 03-23 | Direction | SHORT | **2** | -0.167 | LOW_SAMPLE | False | REJECT |
| 03-23 | SetupType | FB_RECLAIM_LONG | **1** | 0.352 | LOW_SAMPLE | False | REJECT |
| 03-23 | SetupType | FB_RECLAIM_SHORT | **2** | -0.167 | LOW_SAMPLE | False | REJECT |

**Pattern is absolute:** Every Direction/SetupType group in Group B has SampleCount 1-2.
MIN_SAMPLE_COUNT=5 is unreachable. The sample gate is not borderline — it is not close.

### B.4. Shortlist / formalization evidence

| run | shortlist_rows | research_summary_rows | FE=True rows | shortlist GroupTypes |
|-----|----------------|----------------------|-------------|---------------------|
| 03-15 | 27 | 27 | 4 | Direction, SetupType, LifecycleStatus, OutcomeStatus, 9 context types |
| 03-16 | 17 | 17 | 2 | Direction, SetupType, LifecycleStatus, OutcomeStatus, 9 context types |
| 03-17 | 17 | 17 | 2 | Direction, SetupType, LifecycleStatus, OutcomeStatus, 9 context types |
| 03-18 | **0** | **0** | 0 | — |
| 03-19 | **0** | **0** | 0 | — |
| 03-20 | **0** | **0** | 0 | — |
| 03-21 | **0** | **0** | 0 | — |
| 03-22 | **0** | **0** | 0 | — |
| 03-23 | **0** | **0** | 0 | — |

Group A FE=True rows detail (from research_summary):

**03-15 (4 FE rows):**
- Direction LONG → FAILED_BREAK_RECLAIM → FAILED_BREAK_DOWN (P1, SELECT, score=0.283)
- SetupType FB_RECLAIM_LONG → LONG (P1, SELECT, score=0.283)
- Direction SHORT → FAILED_BREAK_RECLAIM → FAILED_BREAK_UP (P2, REVIEW, score=0.026)
- SetupType FB_RECLAIM_SHORT → SHORT (P2, REVIEW, score=0.026)

**03-16 (2 FE rows):**
- Direction LONG → FAILED_BREAK_RECLAIM → FAILED_BREAK_DOWN (P1, SELECT, score=0.220)
- SetupType FB_RECLAIM_LONG → LONG (P1, SELECT, score=0.220)

**03-17 (2 FE rows):**
- Direction SHORT → FAILED_BREAK_RECLAIM → FAILED_BREAK_UP (P1, SELECT, score=0.145)
- SetupType FB_RECLAIM_SHORT → SHORT (P1, SELECT, score=0.145)

All FE=True rows: ConfidenceModelStatus=PROXY_RANKING_HEURISTIC,
ExecutableEntrySemanticsStatus=IMPLEMENTED_IN_BACKTEST_RULESET_V1.

### B.5. Replay evidence for REPLAY→REJECT group

From run_log.csv:

| run_id | FE rows | derived runs | outcome | notes |
|--------|---------|-------------|---------|-------|
| 03-15_run_001 | 4 | 4 | all REJECT | FAIL/UNSTABLE |
| 03-16_run_001 | 2 | 2 | all REJECT | FAIL/UNSTABLE |
| 03-17_run_001 | 2 | 2 | all REJECT | FAIL/UNSTABLE |

Reference from available backtest artifacts (run 03-12, same structural pattern):
- validation_status: FAIL (sample_sufficiency=FAIL, source_concentration=FAIL)
- robustness_status: UNSTABLE (all sub-checks NOT_EVALUATED due to no return basis)
- promotion_decision: REJECT (`validation_status == FAIL => REJECT`)

The replay failures are structural: single-day data windows produce small trade
counts, which fail sample sufficiency checks.

### B.6. Where the funnel breaks

```
Group A path:   setups(30-48) → rankings(28-32) → selections(mixed) → shortlist(17-27) → FE(2-4) → replay → REJECT
Group B path:   setups(1-3)   → rankings(9-28)  → selections(ALL REJECT LOW_SAMPLE) → shortlist(0) → ∅
                       ↑
                  BREAK POINT
```

---

## C. REPLAY→REJECT vs FE=0: systematic differences

### C.1. Quantitative contrast

| metric | Group A (03-15/16/17) | Group B (03-18→23) | ratio |
|--------|----------------------|---------------------|-------|
| mean setups/run | 41.3 | 1.5 | **27.5x** |
| total setups | 124 | 9 | 13.8x |
| max SampleCount (Direction) | 37 | 2 | 18.5x |
| min SampleCount (Direction) | 9 | 1 | 9x |
| MinSamplePassed rate | 96% (91/95) | **0%** (0/81) | ∞ |
| SELECT rate | 38% (36/95) | **0%** (0/81) | ∞ |
| shortlist rows total | 61 | **0** | ∞ |
| FE rows total | 8 | **0** | ∞ |

### C.2. What differs within Group A

- 03-15: Both directions eligible (LONG SELECT + SHORT REVIEW)
- 03-16: Only LONG eligible (SHORT NON_POSITIVE_EDGE)
- 03-17: Only SHORT eligible, direction dominance flipped (LONG=21 setups but WEAK)

This shows the edge signal is unstable across directions even when setup volume is high.
The formalization gate filters correctly — weak directions don't reach replay.

### C.3. Run 03-23: near-miss or noise?

Run 03-23 has notably higher scores (max 0.359, 15/28 positive delta) than other
FE=0 runs. With 3 setups it's the "richest" FE=0 day. But SampleCount for
Direction LONG = 1, SHORT = 2 — still 60-80% below MIN_SAMPLE_COUNT=5.
This is not a borderline miss; it's a structural impossibility with single-day windows
producing 1-3 setups.

---

## D. Interpretation

### Primary finding: structural event drought

The transition from REPLAY→REJECT to FE=0 is caused by a **drop in setup
generation rate from ~40/day to ~1.5/day** starting 03-18.

Both groups were processed with identical pipeline code (same commit, same thresholds).
No rule change, no gate change. The input data changed.

With 1-3 setups per day, every ranking group has SampleCount 1-2.
`MIN_SAMPLE_COUNT=5` makes shortlist entry structurally impossible.
This is not a borderline gate — it's a 60-80% deficit.

### Secondary finding: the MIN_SAMPLE_COUNT gate is appropriate

The gate is protecting against noise. With 1 setup per direction,
there is no statistical basis for group-level claims. The system correctly
refuses to formalize groups it cannot evaluate.

Run 03-23 confirms this: high scores (0.352) mean nothing with n=1.
A single setup can show any score — it's pure noise.

### Tertiary finding: single-day windows create binary behavior

The system either generates enough structural events per day (→ 30+ setups,
rich funnel, FE>0) or it doesn't (→ 1-3 setups, empty funnel, FE=0).
There is no middle ground. The architecture is regime-binary, not regime-gradual.

**Interpretation: market regime shift (primary) with architectural amplification
(secondary). Not a pipeline bottleneck.**

---

## E. Research conclusion

**Bottleneck is before shortlist — at setup generation.**

The funnel breaks because single-day windows produce 1-3 setups during
low-activity market days. No downstream gate is relevant. The selections,
shortlist, and formalization logic never get a chance to act.

The pipeline is functioning as designed. The question is not "why does the
gate block?" but "why do low-activity days produce so few structural events?"

---

## F. Recommended next research action

**One narrow step:**

Re-run the analyzer for the FE=0 date range (03-18→03-23) with a **multi-day
sliding window** (e.g., 3-day or 5-day) instead of single-day windows.

Purpose: determine whether aggregating adjacent days accumulates enough
setups to cross MIN_SAMPLE_COUNT=5 and produce non-empty shortlists.

This answers: "Is the structural signal present but diluted across days,
or genuinely absent in this period?"

No production changes. No threshold tuning. One diagnostic experiment.

---

## G. Version / rule stability note

### Code state at analysis time
- Commit: `c81e6ba` (2026-03-24)
- Both processing cycles (2026-03-22 and 2026-03-24) used post-`f32ae46` code
  (confirmation_bars=5 change from 2026-03-16)

### Changes to key pipeline files during analysis period (2026-03-14→03-24)

| commit | date | file(s) | impact assessment |
|--------|------|---------|-------------------|
| f32ae46 | 03-16 | failed_breaks.py | Added 5-bar confirmation window. Tightens setup generation. **Applied equally to ALL runs** since all processed on 03-22 or later. |
| 9a6ed00 | 03-16 | sweeps.py (metadata only) | Observation-only penetration metadata. No behavioral change. |
| 59de9df | 03-16 | context features | Scope tightening. No effect on setup detection. |
| bda24d2 | 03-15 | research_summary.py | Metadata fields only. No gate logic change. |
| e2746c5 | 03-15 | shortlists.py | Honesty metadata. No gate logic change. |

**Critical finding:** No changes to `rankings.py`, `selections.py`, `thresholds.py`,
or the core selection/scoring logic between Group A and Group B processing.
The `confirmation_bars=5` change pre-dates both groups' processing.

**Rule-change cannot explain the transition.** Both groups processed with
identical pipeline logic. The difference is in the input data.

### Thresholds (unchanged throughout)
- `MIN_SAMPLE_COUNT = 5` (thresholds.py)
- `MIN_SELECTION_SCORE = 0.05` (selections.py)
- `MIN_POSITIVE_RATE_DELTA = 0.0` (selections.py)
- `SETUP_TTL_BARS = 12` (setups constant)
- `confirmation_bars = 5` (failed_breaks.py, post-f32ae46)

---

## H. Data sources

All data verified from actual VPS analyzer CSVs downloaded to
the local-only transition data archive. No inferred values remain.

| artifact | runs verified |
|----------|--------------|
| analyzer_setups.csv | all 9 |
| analyzer_setup_rankings.csv | all 9 |
| analyzer_setup_selections.csv | all 9 |
| analyzer_setup_shortlist.csv | all 9 |
| analyzer_research_summary.csv | all 9 |

Additional reference runs with full local data:
- `analyzer_runs/2026-03-12_to_2026-03-12_run_003` (33 setups, FE=2)
- `analyzer_runs/2026-03-14_to_2026-03-14_run_001` (51 setups, FE=0 — Direction LOW_SAMPLE/NON_POS)
