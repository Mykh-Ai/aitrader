# Short Reclaim Path Order Audit

Generated: 2026-05-03

## Key Read

- mismatch trades: 47
- activation first events: NONE:7;SAME_BAR:2;STOP_FIRST:38
- setup-window first events: NONE:7;SAME_BAR:2;STOP_FIRST:38
- activation target hit share: 48.94%
- setup target hit share: 48.94%
- setup target before stop share: 0.00%
- target after replay exit share: 44.68%
- median setup target offset: 4.00
- median activation stop offset: 0.00

## Interpretation

This audit checks raw-feed order for the outcome-positive / replay-negative mismatches. `activation` starts at replay entry activation; `setup-window` matches analyzer fixed-horizon semantics by starting after `SetupBarTs`.

The mismatch set does not show a hidden target-first path. In `80.85%` of the
47 mismatch trades, stop comes before target; another `4.26%` are same-bar
collisions, and the rest have no stop/target hit in the 12-bar window. Target
is hit in only `48.94%` of the mismatch set and is after replay exit in
`44.68%`.

Conclusion:
the replay collapse is primarily a timing / stop-before-move issue. The next
diagnostic should test whether the candidate needs an entry-delay / confirmation
or stop-survival rule. Do not treat this as evidence for simply widening target
or promoting the current ruleset.

Summary CSV: `/opt/aitrader/research/results/short_reclaim_path_order_audit_2026-05-03.csv`
Detail CSV: `/opt/aitrader/research/results/short_reclaim_path_order_audit_details_2026-05-03.csv`
