# Short Reclaim Context Filter Diagnostic

Generated: 2026-05-03

## Scope

Diagnostic only. No ruleset changes, no parameter search, no optimizer.
Population: deduplicated SHORT setups whose `SetupType` contains `RECLAIM` and which have setup outcomes.

## Baseline

- n: 606
- days: 40
- pos_rate: 55.45%
- mean_ret: 0.023367
- median_ret: 0.017452

## Pre-Registered Slice Results

- `high_stress_all3_ge_median`: n=197, days=35, pos_rate=59.39%, mean_ret=0.051113, median_ret=0.039601, positive_day_rate=68.57%, largest_day_share=7.61%
- `ctx_spike_count_ge2`: n=197, days=35, pos_rate=61.93%, mean_ret=0.071894, median_ret=0.041615, positive_day_rate=71.43%, largest_day_share=6.60%
- `absorption_high_ge3`: n=93, days=34, pos_rate=54.84%, mean_ret=0.058470, median_ret=0.030612, positive_day_rate=55.88%, largest_day_share=7.53%
- `absorption_low_le1`: n=409, days=36, pos_rate=52.32%, mean_ret=-0.000007, median_ret=0.007779, positive_day_rate=55.56%, largest_day_share=8.31%
- `liq_spike_true`: n=71, days=33, pos_rate=56.34%, mean_ret=0.065241, median_ret=0.035229, positive_day_rate=57.58%, largest_day_share=8.45%

## Interpretation

The diagnostic supports keeping the SHORT high-stress / multi-spike context as
a live research surface.

`ctx_spike_count_ge2` is the strongest pre-registered slice in this pass:
- same sample size as high-stress (`n=197`);
- better `pos_rate` than baseline (`61.93%` vs `55.45%`);
- better `mean_ret` than baseline (`0.071894` vs `0.023367`);
- better `median_ret` than baseline (`0.041615` vs `0.017452`);
- better MAE (`-0.073884` vs `-0.114947`);
- not concentrated in one day (`largest_day_share=6.60%`);
- positive on 71.43% of active days.

`high_stress_all3_ge_median` also improves baseline, but less cleanly than
`ctx_spike_count_ge2`.

`absorption_high_ge3` and `liq_spike_true` are weaker as standalone filters:
they improve mean/median returns but do not clearly improve day-level
stability enough to be first-choice filters.

`absorption_low_le1` is more useful as an avoid / downweight signal than as a
candidate entry filter: it has large `n=409`, lower `pos_rate=52.32%`, and
near-zero mean return.

There is an MFE outlier risk in the daily detail, especially around
`2026-03-15`, so MFE should not be the primary argument. The stronger evidence
is in `pos_rate`, `median_ret`, MAE improvement, and day distribution.

## Decision

Do not change production or broad rulesets.

The next justified step is a narrow parameterized filter experiment design for:
- SHORT reclaim only;
- context filter primary candidate: `ctx_spike_count_ge2`;
- comparison candidate: `high_stress_all3_ge_median`;
- avoid/downweight check: `absorption_low_le1`;
- no optimizer search.

Daily detail CSV: `research/results/short_reclaim_context_filter_diagnostic_daily_2026-05-03.csv`
