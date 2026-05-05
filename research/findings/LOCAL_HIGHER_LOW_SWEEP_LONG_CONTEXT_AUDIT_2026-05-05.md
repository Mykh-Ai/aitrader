# LOCAL HIGHER LOW SWEEP LONG Context Audit

Date: 2026-05-05

Status: diagnostic context audit only. Not FIELD, not live strategy, not
execution-ready evidence.

Scope: `LOCAL_HIGHER_LOW_SWEEP` LONG focus rows `7`, `17`, `11`, `10`, `25`,
and `3` from `LOCAL_H4_RECLAIM_SWEEP_EXTREME_STOP_V1_BUFFER50`.

This audit does not run the Backtester, does not run the old
`FAILED_BREAK_RECLAIM` detector, and does not change detector logic.

## Summary Read

All six focus rows are sweeps of local higher lows, not sweeps of the prior
major structural low. In every case, the selected local level sits above the
lowest confirmed pivot low in the prior 30 H4 bars, and the sweep does not break
that major low.

The best-looking rows are not random tiny-risk artifacts. Rows `7`, `17`, `10`,
`25`, and `3` all catch real directional expansion. The main caveat is
clustering: row `11` is a duplicate/late continuation inside the same long
cluster as row `10`, and row `25` is the first row of a cluster that later emits
row `26`.

## Focus Rows

| row | entry_ts | cluster | classification | level | prior_major_low_30h4 | relation_to_major_low | sweep_depth | reclaim_distance | reclaim_body | prior_context | formation_read | entry_timing |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 7 | 2026-04-05 12:00 UTC | L03 | clean_reclaim | 66745.5 | 65676.1 | local level +1069.4 above major low; major low not swept | 170.0 | 227.2 | bullish, body 52.8% of H4 range | prior 12 H4 drift -221.2, prior 6 H4 drift -194.5 | pullback continuation after shallow local sweep | near start; 1.5R in 3.5h, 3R in 10.95h, 5R in 12.0h |
| 17 | 2026-04-13 04:00 UTC | L05 | clean_reclaim | 70566.5 | 67711.0 | local level +2855.5 above major low; major low not swept | 108.3 | 378.3 | bullish, body 34.8% of H4 range | prior 12 H4 drift -2206.5, prior 6 H4 drift -2302.5 | possible reversal / pullback-continuation after heavy selloff into local higher low | early enough but not instant; 1.5R in 10.57h, 3R in 15.27h, 5R in 18.23h |
| 11 | 2026-04-09 08:00 UTC | L04 | duplicate_same_move | 70671.6 | 66575.5 | local level +4096.1 above major low; major low not swept | 243.6 | 273.4 | bearish, body 3.8% of H4 range | prior 12 H4 drift +2214.9, prior 6 H4 drift -298.4 | continuation resample after row 10 already started the directional leg | late/duplicate; 1.5R in 7.55h, 3R in 13.12h, no 5R |
| 10 | 2026-04-07 20:00 UTC | L04 | clean_reclaim, clustered | 68227.5 | 65676.1 | local level +2551.4 above major low; major low not swept | 194.5 | 748.3 | bullish, body 82.2% of H4 range | prior 12 H4 drift +866.2, prior 6 H4 drift -1784.0 | strong reclaim from pullback low; first signal in later multi-row long cluster | near start; 1.5R in 2.1h, 3R in 3.35h, no 5R |
| 25 | 2026-04-22 00:00 UTC | L08 | clean_reclaim, clustered | 75433.1 | 73256.8 | local level +2176.3 above major low; major low not swept | 77.9 | 855.1 | bullish, body 89.4% of H4 range | prior 12 H4 drift +70.6, prior 6 H4 drift -1263.9 | strong V-style reclaim after pullback in ongoing up-leg | near start of new impulse; 1.5R in 5.27h, 3R in 15.5h, no 5R |
| 3 | 2026-03-31 16:00 UTC | L02 | clean_reclaim | 66200.1 | 64918.2 | local level +1281.9 above major low; major low not swept | 262.1 | 499.9 | bullish but weak body, 3.4% of H4 range | prior 12 H4 drift -128.5, prior 6 H4 drift -999.2 | countertrend bounce / possible early reversal after local sweep | starts quickly; 1.5R in 0.68h, 3R in 14.73h, no 5R |

## Row Notes

### Row 7

This is one of the cleanest local higher-low cases. The market was drifting down
into a local sweep, but the selected level was still far above the previous
major low. The reclaim candle is bullish and reasonably decisive, and the
directional leg begins soon after entry. This is a pullback-continuation
formation, not a structural-bottom false break.

### Row 17

This row comes after a sharp H4 selloff, with the selected local low still far
above the previous major low. It looks more like a reversal attempt from a local
higher-low shelf than a main structural reclaim. The signal is not instant, but
the expansion is real: 5R arrives within roughly 18.2 hours without a stop touch
first.

### Row 11

This is the weakest focus example as independent evidence. It is in cluster
`L04`, after row `10` already captured the cleaner start of the directional leg.
The reclaim candle is bearish and very small-bodied. It still expands, but the
context says duplicate continuation rather than a fresh setup. Under a
first-candidate-only cluster rule, this row should not count.

### Row 10

This is the first and best member of cluster `L04`. The prior H4 context is a
strong pullback inside a broader upside transition. The reclaim candle is large
and bullish, and 3R is reached quickly. It is a valid local higher-low
continuation/reversal diagnostic example, but later rows in the same long move
should be treated as duplicates unless repeat-entry rules are explicitly
defined.

### Row 25

This is a strong V-style local reclaim. The reclaim candle is large, bullish,
and closes far above the swept local level. It is near the start of the next
directional leg and reaches 3R, but it is also the first member of cluster `L08`;
row `26` follows as a poor risk-too-large repeat. Count row `25` if using
first-candidate-only cluster logic, but do not count row `26`.

### Row 3

This row follows a local sweep above the prior major low after a short-term
decline. The H4 reclaim candle has a weak body relative to range, so visually it
is less clean than rows `7`, `10`, `17`, and `25`. The next move still expands
quickly to 1.5R and later to 3R. Classify it as an early countertrend bounce or
possible reversal, not as a clean structural reclaim.

## Formation Pattern

The common formation is:

1. A prior major low remains intact.
2. Price forms a local higher low.
3. Price sweeps that local higher low without sweeping the major low.
4. H4 closes back above the local level.
5. Expansion often follows when the reclaim is early in a new directional leg.

This is a distinct setup family from main structural H4 false-break/reclaim. The
working name should remain local/internal, for example
`LOCAL_HIGHER_LOW_SWEEP_RECLAIM`, until a formal contract is drafted.

## Cluster Implication

Rows `10` and `11` show why row-level results are inflated. Row `10` is the
early signal; row `11` is a later continuation resample in the same directional
cluster. Row `25` is acceptable as the first row of cluster `L08`, while later
cluster members should be excluded unless repeat entries become an explicit
research question.

For future diagnostics, count only the first candidate per same-direction
impulse cluster before evaluating expectancy.

## Verdict

The best local higher-low LONG rows are real market formations, but they are not
main structural-low sweeps. The useful surface appears to be pullback
continuation / local reversal after a higher-low sweep, especially when the
reclaim candle is decisive and the entry is early in the next directional leg.

This deserves another diagnostic pass with cluster de-duplication frozen. It is
not ready for a formal ruleset draft or any FIELD/live interpretation.
