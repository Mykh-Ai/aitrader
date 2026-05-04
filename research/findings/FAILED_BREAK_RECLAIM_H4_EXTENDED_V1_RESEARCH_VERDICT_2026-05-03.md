# FAILED_BREAK_RECLAIM H4 EXTENDED_V1 Research Verdict - 2026-05-03

Status: `PROMOTE_TO_DEDICATED_RESEARCH_CANDIDATE`

Execution readiness: `NO`

This memo freezes the current research read for failed-break/reclaim H4 setups
from the EXTENDED_V1 sidecar. It is research evidence only. It is not a live or
execution-ready trading rule.

## Scope

- Source: `FAILED_BREAK_RECLAIM_EXTENDED_V1`
- SourceTF: `H4` only
- confirmation_bars: `60`
- Window: `2026-03-30_to_2026-05-02`
- Forward coverage: full `5760` bars for all main-test setups
- H4 sample: `37` trades
- Entry convention: `NEXT_BAR_OPEN`
- TP model in replay: `FIXED_R_MULTIPLE:1.5`
- Representative expiry: `BARS_AFTER_ACTIVATION:4320`
- Stop models reviewed:
  - `REFERENCE_LEVEL_HARD_STOP`
  - `SWEEP_EXTREME_HARD_STOP`

Primary evidence:
- `research/results/failed_break_reclaim_extended_structural_matrix_2026-03-30_to_2026-05-02/`
- `research/results/failed_break_reclaim_h4_mfe_r_diagnostic_2026-03-30_to_2026-05-02/`

## H4 Replay Metrics

`REFERENCE_LEVEL_HARD_STOP`:
- Trades: `37`
- TP / SL / Expiry: `23 / 14 / 0`
- Winrate: `0.621622`
- NetR: `20.5`
- MeanR: `0.554054`
- MedianR: `1.5`
- Average hold bars: `6.783784`
- Median hold bars: `1.0`
- Average risk distance: `58.794595`
- Median risk distance: `35.7`
- Same-bar exits: `13`
- Same-bar collisions: `9`

`SWEEP_EXTREME_HARD_STOP`:
- Trades: `37`
- TP / SL / Expiry: `22 / 15 / 0`
- Winrate: `0.594595`
- NetR: `18.0`
- MeanR: `0.486486`
- MedianR: `1.5`
- Average hold bars: `71.459459`
- Median hold bars: `15.0`
- Average risk distance: `190.664865`
- Median risk distance: `183.0`
- Same-bar exits: `2`
- Same-bar collisions: `0`

## H1 Contrast

At the same representative expiry:
- H1 with `REFERENCE_LEVEL_HARD_STOP`: `116` trades, NetR `4.0`, MeanR
  `0.034483`, MedianR `-1.0`.
- H1 with `SWEEP_EXTREME_HARD_STOP`: `116` trades, NetR `-8.5`, MeanR
  `-0.073276`, MedianR `-1.0`.

H1 is weak in this research slice and should be deferred unless later evidence
contradicts this read.

## MFE_R Findings

The H4 setups produced favorable excursion beyond the fixed `1.5R` target, but
this is diagnostic MFE only, not an executable TP result.

`REFERENCE_LEVEL_HARD_STOP`:
- `MFE_R >= 1.5`: `37/37`
- `MFE_R >= 2`: `37/37`
- `MFE_R >= 3`: `37/37`
- `MFE_R >= 5`: `36/37`
- `MFE_R >= 10`: `31/37`
- Median MFE_R: `42.644178`
- P75 MFE_R: `128.515152`
- P90 MFE_R: `426.618182`
- Median time to best MFE: `2659` bars

`SWEEP_EXTREME_HARD_STOP`:
- `MFE_R >= 1.5`: `34/37`
- `MFE_R >= 2`: `34/37`
- `MFE_R >= 3`: `34/37`
- `MFE_R >= 5`: `29/37`
- `MFE_R >= 10`: `23/37`
- Median MFE_R: `12.411209`
- P75 MFE_R: `23.753653`
- P90 MFE_R: `36.754302`
- Median time to best MFE: `2659` bars

Same-bar-clean MFE diagnostic subset:
- Reference strict-clean: `15` trades, median MFE_R `26.453386`
- Sweep strict-clean: `35` trades, median MFE_R `11.578393`

## Caveats

Same-bar caveat:
- Reference-level stop has material same-bar exposure: `13/37` same-bar exits
  and `9/37` same-bar collisions.
- Sweep-extreme stop is cleaner on this axis: `2/37` same-bar exits and `0`
  same-bar collisions.

SL-before-MFE caveat:
- Reference: `15/37` had SL before MFE `2R`; `8/37` had same-bar SL/2R
  collision.
- Sweep: `17/37` had SL before MFE `2R`; `0/37` had same-bar SL/2R
  collision.

Interpretation caveat:
- The large reference-stop MFE_R numbers are inflated by smaller risk distances.
- MFE_R should not be treated as an executable target result unless bar-order and
  same-bar ambiguity are explicitly handled.

## Current Bottlenecks

1. Same-bar handling for reference-level stop.
2. Stop / TP interaction for sweep-extreme stop with fixed `1.5R`.
3. Entry timing: many setups show later favorable excursion, but SL ordering can
   invalidate the path first.
4. Exit-shape design: fixed `1.5R` may be too micro for H4 continuation, while
   raw MFE diagnostics alone are not enough to promote an executable model.
5. H1 setup quality is weak relative to H4 in this sample.

## Verdict

Promote H4-only failed-break/reclaim EXTENDED_V1 to a dedicated research
candidate.

Do not promote it to execution. Do not auto-promote the baseline. Do not mix it
into existing shortlist, selection, or production-like workflows.

The research signal is concentrated in H4, remains positive under both
reference-level and sweep-extreme stop models, and survives strict same-bar
diagnostic filtering at least directionally. The signal is not yet robust enough
for execution claims because same-bar ambiguity and SL-before-MFE ordering remain
material.

## Recommended Next Steps

1. Create a dedicated H4 research ruleset candidate that excludes H1 by design.
2. Keep `confirmation_bars=60` frozen for the next test.
3. Test H4 entry timing variants before tuning filters:
   - delay after reclaim confirmation;
   - require survival beyond immediate stop-touch zone;
   - compare against the same H4 baseline.
4. Test exit-shape variants as diagnostics:
   - larger fixed R targets;
   - partial / trailing diagnostics;
   - time-based exit after favorable excursion.
5. Keep both stop models in research:
   - reference stop as micro-risk diagnostic;
   - sweep-extreme stop as sweep-logic invalidation.
6. Run the next candidate on a true future holdout before any promotion beyond
   research-candidate status.
