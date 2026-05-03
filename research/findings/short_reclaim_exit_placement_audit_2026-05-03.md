# Short Reclaim Exit Placement Audit

Generated: 2026-05-03

## Key Read

- mismatch trades: 47
- mismatch exits: EXPIRY:5;STOP:42
- mismatch same-bar collisions: 2
- mismatch median holding bars: 1.00000000
- mismatch horizon MFE reached target share: 89.36%
- mismatch horizon adverse reached stop share: 42.55%
- mismatch both target and stop in horizon share: 38.30%
- mismatch median MFE / target distance: 1.61028363
- mismatch median adverse / stop distance: 0.81342355

## Interpretation

This audit does not test new parameters. It profiles whether the replay collapse is explained by stop/target placement, same-bar collisions, expiry, or short holding time.
For mismatches, `horizon_mfe_reached_target_share` means the fixed-horizon analyzer path had enough favorable excursion to reach the current target at some point in the horizon. `horizon_adverse_reached_stop_share` means the fixed-horizon path also had enough adverse excursion to touch the current stop at some point.

Summary CSV: `/opt/aitrader/research/results/short_reclaim_exit_placement_audit_2026-05-03.csv`
Detail CSV: `/opt/aitrader/research/results/short_reclaim_exit_placement_audit_details_2026-05-03.csv`
