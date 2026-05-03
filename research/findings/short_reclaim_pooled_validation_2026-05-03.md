# Short Reclaim Pooled Validation

Generated: 2026-05-03

## Scope

Campaign-level validation over trade ledgers from the narrow replay experiment.
Trades are deduplicated by `source_setup_id` per slice to remove same-day rerun duplicates.

## Key Read

- `ctx_spike_count_ge2` dedup trades: 191
- `ctx_spike_count_ge2` pos_rate: 48.69%
- `ctx_spike_count_ge2` mean_return: 0.00002978
- `ctx_spike_count_ge2` median_return: -0.00001265
- `ctx_spike_count_ge2` max_drawdown: -0.01288895
- fair baseline on ctx active days mean_return: -0.00002355

## Cost Sensitivity

- cost `0.00000000`: mean=0.00002978, median=-0.00001265, pos_rate=48.69%
- cost `0.00002500`: mean=0.00000478, median=-0.00003765, pos_rate=47.12%
- cost `0.00005000`: mean=-0.00002022, median=-0.00006265, pos_rate=44.50%
- cost `0.00010000`: mean=-0.00007022, median=-0.00011265, pos_rate=42.41%
- cost `0.00020000`: mean=-0.00017022, median=-0.00021265, pos_rate=36.13%
- cost `0.00050000`: mean=-0.00047022, median=-0.00051265, pos_rate=23.04%

## Interpretation

This validates whether the candidate survives pooled comparison and simple cost stress.
It is still research-only: no exchange costs, slippage, execution constraints, or production controls are implemented here.

Summary CSV: `/tmp/short_reclaim_pooled_validation_2026-05-03.csv`
Cost CSV: `/tmp/short_reclaim_pooled_validation_costs_2026-05-03.csv`
