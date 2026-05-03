# Short Reclaim Timing Survival Diagnostic

Generated: 2026-05-03

## Scope

Diagnostic-only replay experiment over the existing `ctx_spike_count_ge2` surface.
Variants are pre-registered entry/confirmation transforms materialized as temporary analyzer artifacts.
Backtester core replay semantics are unchanged.

## Results

- `baseline_current`: trades=191, pos_rate=48.69%, mean=0.00002978, median=-0.00001265, sum=0.00568846, max_dd=-0.01288895, exits=EXPIRY:14;STOP:93;TARGET:84
- `entry_delay_1`: trades=191, pos_rate=61.26%, mean=0.00017416, median=0.00016674, sum=0.03326394, max_dd=-0.00702553, exits=EXPIRY:20;STOP:94;TARGET:77
- `entry_delay_2`: trades=191, pos_rate=58.64%, mean=0.00002879, median=0.00008501, sum=0.00549847, max_dd=-0.02067334, exits=EXPIRY:30;STOP:106;TARGET:55
- `survival_confirm_1`: trades=122, pos_rate=50.00%, mean=0.00013756, median=0.00002484, sum=0.01678283, max_dd=-0.01043900, exits=EXPIRY:20;STOP:50;TARGET:52
- `favorable_close_confirm_1`: trades=94, pos_rate=50.00%, mean=0.00016087, median=0.00002799, sum=0.01512205, max_dd=-0.00858429, exits=EXPIRY:18;STOP:37;TARGET:39

## Interpretation Guardrails

- This is not optimizer output and not a production signal.
- Any improvement must be compared against `baseline_current` and still survive costs, concentration, and sample checks.
- Delay variants shift `SetupBarTs`; stop remains the original `ReferenceLevel`.

## Read

`entry_delay_1` is the only variant that materially improves the baseline
without reducing sample size: `191` trades, pos_rate `61.26%`, mean
`+0.00017416`, median `+0.00016674`, sum `+0.03326394`, max drawdown
`-0.00702553`. Baseline on the same surface is `48.69%`, mean `+0.00002978`,
median `-0.00001265`, sum `+0.00568846`, max drawdown `-0.01288895`.

Cost stress remains research-only but is materially better than baseline:
baseline turns negative by cost `0.00005`, while `entry_delay_1` remains
positive through cost `0.00015` and turns negative around `0.00020`.

This does not promote the strategy. All completed per-run validation rows remain
`FAIL`, promotion remains `REJECT`, and robustness is mostly `UNSTABLE`. The
result does, however, confirm the previous path-order diagnosis: timing matters
more than target tweaking on this surface.

Summary CSV: `/opt/aitrader/research/results/short_reclaim_timing_survival_diagnostic_2026-05-03.csv`
Run CSV: `/opt/aitrader/research/results/short_reclaim_timing_survival_diagnostic_runs_2026-05-03.csv`
Detail CSV: `/opt/aitrader/research/results/short_reclaim_timing_survival_diagnostic_trades_2026-05-03.csv`
Cost CSV: `research/results/short_reclaim_timing_survival_diagnostic_costs_2026-05-03.csv`
