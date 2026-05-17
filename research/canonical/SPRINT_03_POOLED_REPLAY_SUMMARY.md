# SPRINT_03_POOLED_REPLAY_SUMMARY

Date: 2026-05-17

## Scope

- Sprint: `SHI_SPRINT_03_FORMAL_RULESETS_AND_HOLDOUT_DESIGN`
- Output root: `backtest_runs/sprint_03_candidate_rulesets/`
- Mapper script: `research/scripts/sprint_03_formal_candidate_rulesets.py`
- Source Analyzer dirs used: 61 already-seen dirs, including recovered gap Analyzer artifacts.
- Phase 4: closed.
- Executor/live: prohibited.

## Formalization Result

| Candidate | Candidate events | No-lookahead | Stop/exit frozen | Verdict |
|---|---:|---|---|---|
| `CAND_SHORT_CTX_SPIKE_GE2_ENTRY_DELAY_1` | 301 | PASS | PASS | WAIT |
| `CAND_SHORT_IMPULSE_FADE_DEEP_RECLAIM_GT_0_6` | 14 | PASS | PASS | REJECT |

## Cost Stress

### CAND_SHORT_CTX_SPIKE_GE2_ENTRY_DELAY_1

| Cost | Trades | Net result | Winrate | Max drawdown | Profit factor | Status |
|---:|---:|---:|---:|---:|---:|---|
| 0.00000 | 301 | 0.0575368599 | 0.598007 | -0.0061264591 | 1.789267 | PASS |
| 0.00010 | 301 | 0.0274411088 | 0.528239 | -0.0087855288 | 1.318372 | PASS |
| 0.00015 | 301 | 0.0123921046 | 0.498339 | -0.0101360018 | 1.132430 | PASS |
| 0.00020 | 301 | -0.0026576521 | 0.445183 | -0.0124841490 | 0.973838 | FAIL |

Interpretation: hard gate `0.00015` passes, warning gate `0.00020` fails. This cannot be PROMOTE; maximum status is WAIT pending holdout and execution-cost review.

### CAND_SHORT_IMPULSE_FADE_DEEP_RECLAIM_GT_0_6

| Cost | Trades | Net result | Winrate | Max drawdown | Profit factor | Status |
|---:|---:|---:|---:|---:|---:|---|
| 0.00000 | 14 | -0.0002538167 | 0.571429 | -0.0019390443 | 0.939959 | FAIL |
| 0.00010 | 14 | -0.0016539120 | 0.500000 | -0.0020392432 | 0.662974 | FAIL |
| 0.00015 | 14 | -0.0023540122 | 0.428571 | -0.0022390657 | 0.556365 | FAIL |
| 0.00020 | 14 | -0.0030541475 | 0.428571 | -0.0028391926 | 0.464792 | FAIL |

Interpretation: hard gate `0.00015` fails. Under Sprint 03 formal mapping this candidate is REJECT, not WAIT.

## Source Concentration

| Candidate | Trade days | Largest day abs share | Top3 day abs share | Status |
|---|---:|---:|---:|---|
| `CAND_SHORT_CTX_SPIKE_GE2_ENTRY_DELAY_1` | 61 | 0.056238 | 0.149102 | PASS |
| `CAND_SHORT_IMPULSE_FADE_DEEP_RECLAIM_GT_0_6` | 7 | 0.409027 | 0.738923 | FAIL |

## Same-Bar Ambiguity

| Candidate | Total trades | Ambiguous | Ambiguous % | Pessimistic | Optimistic | Conservative | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| `CAND_SHORT_CTX_SPIKE_GE2_ENTRY_DELAY_1` | 301 | 40 | 13.29% | 0.0100437998 | 0.0134791115 | 0.0123921046 | WAIT |
| `CAND_SHORT_IMPULSE_FADE_DEEP_RECLAIM_GT_0_6` | 14 | 1 | 7.14% | -0.0023540122 | -0.0020438861 | -0.0023540122 | PASS |

## Holdout Status

True holdout is not completed. `research/canonical/HOLDOUT_PROTOCOL.md` defines the Sprint 03 freeze timestamp and states that all data already inspected before the freeze is already-seen, not true holdout.

## Final Sprint 03 Verdict

- `CAND_SHORT_CTX_SPIKE_GE2_ENTRY_DELAY_1`: WAIT. Formal mapping exists and hard cost gate passes, but true holdout is missing, 0.00020 fails, and same-bar ambiguity remains WAIT.
- `CAND_SHORT_IMPULSE_FADE_DEEP_RECLAIM_GT_0_6`: REJECT under formal Sprint 03 mapping. Hard cost gate fails, sample is only 14 trades / 7 days, and source concentration fails.

No candidate is PROMOTE. Phase 4 remains closed.

