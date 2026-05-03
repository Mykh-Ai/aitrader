# Short Reclaim Entry Delay Holdout Validation

Generated: 2026-05-03

## Scope

Pseudo-holdout / concentration validation for `entry_delay_1` using already generated timing diagnostic trades.
This is not a true unseen holdout; true holdout requires future analyzer runs after this decision.

## Key Read

- all `entry_delay_1`: trades=191, mean=0.00017416, median=0.00016674, sum=0.03326387
- late-half `entry_delay_1`: trades=95, mean=0.00023207, median=0.00015668, sum=0.02204640
- final-third `entry_delay_1`: trades=70, mean=0.00032079, median=0.00027329, sum=0.02245548
- paired all mean delta: 0.00014437, delay better share: 63.87%
- entry_delay_1 min leave-one-day-out sum: 0.02639593
- entry_delay_1 min leave-one-day-out mean: 0.00014424

## Interpretation

Use this as a stability check, not as promotion evidence. Passing this check means `entry_delay_1` deserves true future holdout; failing it means the in-sample improvement is likely concentrated or regime-specific.

The check is constructive but not conclusive. `entry_delay_1` improves the
paired baseline in all temporal splits:
- all pairs: delay better share `63.87%`, mean delta `+0.00014437`;
- early half: delay better share `66.67%`, mean delta `+0.00013144`;
- late-half pseudo-holdout: delay better share `61.05%`, mean delta
  `+0.00015744`;
- final-third pseudo-holdout: delay better share `65.71%`, mean delta
  `+0.00024355`.

Concentration is acceptable for a research candidate but still a warning for
promotion. Removing the best single day keeps `entry_delay_1` positive
(`sum=+0.02639593`), but removing the top three days leaves only
`sum=+0.01576928`, and cost `0.00010` turns that top-3-removed sum slightly
negative (`-0.00103072`).

Decision:
keep `entry_delay_1` as the only current executable candidate for this surface.
The next valid test is true future holdout on new analyzer days, with no new
parameter changes.

Summary CSV: `research/results/short_reclaim_entry_delay_holdout_validation_2026-05-03.csv`
Pair CSV: `research/results/short_reclaim_entry_delay_holdout_validation_pairs_2026-05-03.csv`
Leave-one-day-out CSV: `research/results/short_reclaim_entry_delay_holdout_validation_lodo_2026-05-03.csv`
