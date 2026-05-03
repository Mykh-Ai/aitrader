# Short Reclaim Replay Mismatch Audit

Generated: 2026-05-03

## Key Read

- joined trades: 191
- observational outcome pos_rate: 62.83%
- replay trade pos_rate: 48.69%
- outcome positive but replay negative: 47
- outcome negative but replay positive: 20
- mean close return: 0.00075743
- mean trade return: 0.00002978
- mean replay minus outcome: -0.00072765
- exits: EXPIRY:14;STOP:93;TARGET:84

## Interpretation

This audit measures the gap between fixed-horizon analyzer outcomes and deterministic replay returns for the same setup ids.
A large drop from outcome pos_rate to replay pos_rate points to entry/exit/placement semantics, not only raw signal quality.

The result keeps the research surface alive but blocks promotion. `ctx_spike_count_ge2`
looks materially better in analyzer fixed-horizon outcomes than in replay:
`62.83%` outcome-positive versus `48.69%` replay-positive. The `47`
outcome-positive/replay-negative setups are the next diagnostic target.

Next diagnostic:
- audit stop/target/expiry behavior for the `47` mismatch setups;
- compare stop distance, target distance, realized MFE/MAE before exit, and
  whether the replay exits before the fixed-horizon move appears;
- do this as placement/exit diagnosis, not broad parameter optimization.

Detail CSV: `/tmp/short_reclaim_replay_mismatch_audit_details_2026-05-03.csv`
