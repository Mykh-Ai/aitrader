# Short Reclaim Context Replay Experiment

Generated: 2026-05-03

## Scope

Narrow replay experiment over temporary filtered analyzer artifacts.
No core Analyzer/Backtester code or production behavior was changed.

## Results

- `baseline_short_reclaim`: completed=44, skipped=2, failed=1, trades=751, resolved=751, mean_run_return=-0.000010, positive_run_rate=43.18%, promotion=REJECT:44, validation=FAIL:44, robustness=FRAGILE:12;UNSTABLE:32
- `ctx_spike_count_ge2`: completed=39, skipped=7, failed=1, trades=236, resolved=236, mean_run_return=0.000019, positive_run_rate=61.54%, promotion=REJECT:39, validation=FAIL:39, robustness=FRAGILE:10;UNSTABLE:29
- `high_stress_all3_ge_median`: completed=39, skipped=7, failed=1, trades=244, resolved=244, mean_run_return=-0.000026, positive_run_rate=43.59%, promotion=REJECT:39, validation=FAIL:39, robustness=FRAGILE:6;UNSTABLE:33
- `absorption_low_le1`: completed=40, skipped=6, failed=1, trades=515, resolved=515, mean_run_return=-0.000029, positive_run_rate=37.50%, promotion=REJECT:40, validation=FAIL:40, robustness=FRAGILE:14;UNSTABLE:26

Weighted trade-return view from per-run outputs:
- `baseline_short_reclaim`: weighted mean ~= `-0.000024`
- `ctx_spike_count_ge2`: weighted mean ~= `+0.000046`
- `high_stress_all3_ge_median`: weighted mean ~= `-0.000024`
- `absorption_low_le1`: weighted mean ~= `-0.000056`

The one failed run in each slice is `2026-03-12_to_2026-03-12_run_003`;
failure reason: raw feed path was unavailable for that historical local run.
It does not affect the current routine-window result interpretation.

## Interpretation

The replay experiment confirms the observational ranking direction:
`ctx_spike_count_ge2` is the only tested slice that improved replay-level
aggregate return profile versus baseline.

Compared with baseline:
- fewer trades (`236` vs `751`);
- all trades resolved (`236`, unresolved `0`);
- better mean/median run return;
- higher positive-run rate (`61.54%` vs `43.18%`);
- lower largest-run concentration (`5.51%` vs `6.26%`);
- still all `REJECT` under current per-run promotion gate.

`high_stress_all3_ge_median` did not survive replay as a useful comparator in
this pass. It was worse than baseline on aggregate mean/median run return and
positive-run rate.

`absorption_low_le1` behaved like an avoid/downweight slice: larger sample,
negative aggregate return, and weak positive-run rate.

## Gate Caveat

Do not overread the per-run `REJECT` labels here. The experiment intentionally
uses a single explicit mapping per filtered artifact, so source concentration is
structurally `max_share=1.0` and many per-day samples are small. That makes the
standard daily promotion gate useful as a warning, but not a final answer for
this campaign-style filter experiment.

The meaningful read is campaign-level comparison:
`ctx_spike_count_ge2` improves baseline but remains a small, fragile research
surface. It is not a production signal.

## Decision

Do not change broad H1 rulesets and do not promote.

Keep `ctx_spike_count_ge2` as the primary candidate for a next-stage pooled /
campaign-level validation design. Drop `high_stress_all3_ge_median` as a primary
candidate for now. Treat `absorption_low_le1` as an avoid/downweight candidate.

## Interpretation Guardrails

- This is a research replay experiment, not a live-trading signal.
- Filtered artifact directories normalize selected setup types to one experiment setup family.
- Compare against baseline before considering any persistent ruleset changes.
- Per-run details: `research/results/short_reclaim_context_replay_experiment_runs_2026-05-03.csv`
