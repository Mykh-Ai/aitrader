# Research Log

Chronological decision log for Shi research operations.

This file records operational research decisions: what we decided to do next,
why, and what is explicitly out of scope. Strategic accumulated context stays in
`research/findings/shi_research_program_context.md`.

---

## 2026-05-03 - H1 reject decomposition before filter experiments

Decision:
Do not close broad H1 failed-break/reclaim yet, and do not tune parameters
blindly. Run a reject decomposition audit first.

Why:
Broad H1 failed-break/reclaim replay families repeatedly reached replay but
ended in `REJECT` / `validation_status=FAIL`. The cause is not yet known: the
failure may come from the signal itself, entry timing, SL/TP placement,
validation gates, low sample, direction/regime mixing, or unstable replay
behavior. At the same time, short-side high-stress / multi-spike reclaim remains
a live observational surface on the expanded sample.

Scope:
- Diagnostic only, not optimizer.
- First decompose existing `REJECT` / `FAIL` outcomes:
  - trade count and resolved/unresolved split
  - direction and ruleset family
  - validation and robustness status
  - win/pos rate where available
  - mean/median return or expectancy where available
  - dead reject vs live-but-bad vs unstable vs low-sample
- Do not change rulesets or parameters yet.
- Do not run broad parameter search.

Next:
Create and run `research/scripts/reject_decomposition_audit.py`.

Conditional next:
If audit shows non-zero but mixed/unstable surface, then run targeted SHORT
reclaim context diagnostic using pre-registered filters:
- SHORT only
- failed-break/reclaim family only
- high-stress all 3 >= median
- >=2 context spikes active
- `AbsorptionScore_v1` high / low
- liquidation spike if available

Result:
Completed `research/scripts/reject_decomposition_audit.py`.
The latest routine window is not a pure dead reject: ruleset-scope rows are
mostly `LIVE_BUT_NEGATIVE`, `LIVE_BUT_UNSTABLE`, and one
`VALIDATION_GATE_FAIL`. This means H1 should not be closed as dead, but broad
rulesets should not be tuned blindly.

Completed `research/scripts/short_reclaim_context_filter_diagnostic.py`.
The strongest pre-registered SHORT context slice is `ctx_spike_count_ge2`
(`n=197`, `pos_rate=61.93%`, `mean_ret=0.071894`,
`median_ret=0.041615`, `largest_day_share=6.60%`). This supports designing a
narrow filter experiment, not changing production or broad rulesets.

Next:
Design a parameterized filter experiment for SHORT reclaim with
`ctx_spike_count_ge2` as the primary candidate and
`high_stress_all3_ge_median` as comparison.

Result:
Completed `research/scripts/short_reclaim_context_replay_experiment.py`.
The narrow replay experiment kept all slices in `REJECT` under the current
per-run gate, but the campaign-level comparison improved only for
`ctx_spike_count_ge2`:
- baseline: `751` resolved trades, weighted mean ~= `-0.000024`,
  positive-run rate `43.18%`;
- `ctx_spike_count_ge2`: `236` resolved trades, weighted mean ~= `+0.000046`,
  positive-run rate `61.54%`;
- `high_stress_all3_ge_median`: weighted mean ~= `-0.000024`;
- `absorption_low_le1`: weighted mean ~= `-0.000056`.

Decision:
Do not promote and do not change broad H1. Keep `ctx_spike_count_ge2` as the
primary research candidate for pooled / campaign-level validation design.
Drop `high_stress_all3_ge_median` as primary candidate for now. Treat
`absorption_low_le1` as avoid/downweight candidate.

Result:
Completed `research/scripts/short_reclaim_pooled_validation.py`.
After deduplication by `source_setup_id`, `ctx_spike_count_ge2` remains better
than fair SHORT reclaim baseline on the same active days, but it is too thin for
any trading interpretation:
- `ctx_spike_count_ge2`: `191` trades, `34` days, pos rate `48.69%`,
  mean `+0.00002978`, median `-0.00001265`, sum `+0.00568846`;
- fair baseline on ctx-active days: `570` trades, pos rate `41.40%`,
  mean `-0.00002355`, median `-0.00006433`;
- cost stress kills the ctx mean at roughly `0.00005` per trade.

Decision:
Keep `ctx_spike_count_ge2` as a research surface only. It is not robust enough
for promotion. Next question is why observational fixed-horizon quality does
not survive deterministic replay.

Result:
Completed `research/scripts/short_reclaim_replay_mismatch_audit.py`.
For the same `191` deduplicated `ctx_spike_count_ge2` setups:
- analyzer fixed-horizon outcome pos rate is `62.83%`;
- replay trade pos rate is `48.69%`;
- `47` setups are outcome-positive but replay-negative;
- `20` setups are outcome-negative but replay-positive;
- mean fixed-horizon outcome is `+0.00075743`, but mean replay return is only
  `+0.00002978`;
- exit mix is `STOP:93`, `TARGET:84`, `EXPIRY:14`.

Interpretation:
The raw short-reclaim / multi-spike context signal exists in fixed-horizon
outcomes, but current replay entry/SL/TP/expiry semantics extract almost none
of it. The next diagnostic should audit placement and exit mechanics for the
47 outcome-positive/replay-negative setups before changing rulesets.

Result:
Completed `research/scripts/short_reclaim_exit_placement_audit.py`.
For the `47` outcome-positive/replay-negative setups:
- exits are `STOP:42`, `EXPIRY:5`;
- median holding is `1` bar;
- `74.47%` exit within `3` bars;
- fixed-horizon MFE reaches the current target distance in `89.36%` of cases,
  but fixed-horizon adverse movement also reaches the current stop distance in
  `42.55%`.

Result:
Completed `research/scripts/short_reclaim_path_order_audit.py`.
Raw-feed path order over the same `47` mismatch setups shows:
- activation first events: `STOP_FIRST:38`, `SAME_BAR:2`, `NONE:7`;
- setup-window first events: `STOP_FIRST:38`, `SAME_BAR:2`, `NONE:7`;
- `setup_target_before_stop_share=0.00%`;
- `setup_stop_before_target_share=80.85%`;
- `target_after_replay_exit_share=44.68%`;
- median activation stop offset is `0` bars, median target offset is `4` bars.

Decision:
This is not evidence for simply widening targets or promoting the current
ruleset. The replay collapse is mainly a timing / stop-before-move problem.
The next diagnostic should be a pre-registered entry-delay / confirmation /
stop-survival experiment on `ctx_spike_count_ge2`, still diagnostic-only and
compared to the same fair baseline.

Result:
Completed `research/scripts/short_reclaim_timing_survival_diagnostic.py`.
Pre-registered variants over the same `ctx_spike_count_ge2` replay surface:
- `baseline_current`: `191` trades, pos rate `48.69%`, mean `+0.00002978`,
  median `-0.00001265`, sum `+0.00568846`, max drawdown `-0.01288895`;
- `entry_delay_1`: `191` trades, pos rate `61.26%`, mean `+0.00017416`,
  median `+0.00016674`, sum `+0.03326394`, max drawdown `-0.00702553`;
- `entry_delay_2`: `191` trades, pos rate `58.64%`, mean `+0.00002879`,
  median `+0.00008501`, max drawdown `-0.02067334`;
- `survival_confirm_1`: `122` trades, pos rate `50.00%`, mean `+0.00013756`,
  median `+0.00002484`;
- `favorable_close_confirm_1`: `94` trades, pos rate `50.00%`,
  mean `+0.00016087`, median `+0.00002799`.

Cost read:
Baseline turns negative at cost `0.00005`. `entry_delay_1` remains positive at
cost `0.00015` and turns negative around `0.00020`.

Decision:
Do not promote. All completed per-run validations still `FAIL`, promotions are
still `REJECT`, and robustness remains mostly `UNSTABLE`. However, `entry_delay_1`
is the first executable-semantics variant that materially improves replay on the
same sample without reducing trade count. Next step should be a stricter
holdout / source-concentration / cost-aware validation for `entry_delay_1`, not
additional parameter search.

Result:
Completed `research/scripts/short_reclaim_entry_delay_holdout_validation.py`.
This is a pseudo-holdout / concentration check over already generated timing
diagnostic trades, not a true unseen holdout.

Key reads:
- all `entry_delay_1`: `191` trades, mean `+0.00017416`, median
  `+0.00016674`, sum `+0.03326387`;
- late-half pseudo-holdout: `95` trades, mean `+0.00023207`, median
  `+0.00015668`, sum `+0.02204640`;
- final-third pseudo-holdout: `70` trades, mean `+0.00032079`, median
  `+0.00027329`, sum `+0.02245548`;
- paired all-sample mean delta vs baseline is `+0.00014437`; delay is better in
  `63.87%` of matched setup pairs;
- delay remains better in early half, late half, and final third paired splits;
- leave-one-day-out remains gross-positive even when omitting the best day;
- dropping the top 3 days leaves gross sum positive (`+0.01576928`) but cost
  `0.00010` turns that top-3-removed sum slightly negative (`-0.00103072`).

Decision:
Keep `entry_delay_1` as the only current executable candidate for
`SHORT reclaim + ctx_spike_count_ge2`. Do not tune additional parameters yet.
The next valid evidence step is true future holdout on new analyzer days with
the candidate frozen.
