# ACTIVE_WATCHLIST

Last updated: 2026-05-16

## CAND_SHORT_IMPULSE_FADE_DEEP_RECLAIM_GT_0_6

- Hypothesis: H2 short impulse fade works best when reclaim depth is real, specifically `ReclaimDepthToImpulseRange > 0.6`.
- Why still alive: 34 diagnostic trades show 70.59% `FULL_FADE`, 2.94% `NO_FADE`, positive PnL, and cluster-first checks do not erase the signal.
- Current evidence: frozen sidecar slice has 34 trades and 16 trade-days; cost stress report stays positive through `0.00020`; post-recovery support is still too small and not true holdout.
- Weaknesses: PnL concentration is high at trade level; top 2 winners equal 81.34% of total PnL in prior diagnostic. Same-bar audit is not promotion-grade.
- Required next validation: true forward accumulation on clean data with threshold frozen at `>0.6`.
- Minimum promotion gates: >=25 post-holdout trades, >=10 post-holdout trade-days, positive after cost stress, no single-day dominance, source concentration pass, same-bar pass.
- Exact next replay action: materialize the frozen contract as a candidate-specific deterministic replay/mapping, then run recovered and pooled replay on clean pre-gap plus recovered gap plus post-gap, without changing threshold.
- Exact reason why not live: no post-holdout sample, no formal cost model pass, no frozen stop/exit contract.

## CAND_LONG_IMPULSE_FADE_LATE_US_STRUCTURAL

- Hypothesis: long-side H2 fade is not deep reclaim; it is late-US structural acceptance after impulse, best expressed by `SetupCloseLocationInImpulseRange >= 0.75`, `entry_hour_16_23`, and `Impulse_BodyToRange > 0.75`.
- Why still alive: primary selector has 20 trades, 70.00% winrate, 75.00% `FULL_FADE`, 0 `NO_FADE`, and positive cluster-first behavior.
- Current evidence: primary selector has 20 rows, 19 resolved return rows, and 13 trade-days; 7 post-recovery trades across 4 post-recovery trade-days remain below promotion gate.
- Weaknesses: small support; one unresolved row; session-specific; child low-stress variant has only 18 trades; broad long filters are weak or negative.
- Required next validation: continue watch on new clean days with exactly the two frozen selectors from the 2026-05-15 watchlist.
- Minimum promotion gates: same global gates, plus selector must remain positive under 30m/60m/120m/240m/480m/1440m cluster-first.
- Exact next replay action: keep `contract.md` and `watch_status.md` unchanged, update `impulse_fade_long_forward_watchlist` after each clean Analyzer cycle, and do not add new predicates.
- Exact reason why not live: post-recovery support is 7 trades / 4 days and no formal ruleset/cost/same-bar validation exists.

## CAND_H4_FAILED_BREAK_RECLAIM_EXTENDED_V1

- Hypothesis: an explicit H4 false-break/reclaim formation may be useful, but current `FAILED_BREAK_RECLAIM_EXTENDED_V1` does not implement it.
- Why still alive: the conceptual H4 A/B/C formation remains a possible structural idea, not because current EXTENDED_V1 evidence is valid.
- Current evidence: current implementation produced 37 H4-lineage diagnostic trades, but root-cause audit says it is raw M1 failed-break against H4 level lineage, not H4 candle formation.
- Weaknesses: detector mismatch, micro risk distances, same-bar/micro target artifacts, zero-cost replay, contaminated broad artifact window.
- Required next validation: implement a new detector that materializes H4 Candle A/B/C timestamps, levels, reclaim close, and then a separate M1 entry-search phase.
- Minimum promotion gates: all global gates, plus minimum risk/fee viability and no micro-target evidence.
- Exact next replay action: do not replay current EXTENDED_V1 for promotion. Build new detector contract first, then replay from clean/recovered data.
- Exact reason why not live: current detector is invalid for the intended setup-class and current arithmetic is audit-only.

## CAND_SHORT_CTX_SPIKE_GE2_ENTRY_DELAY_1

- Hypothesis: on the `ctx_spike_count >= 2` short reclaim surface, one-bar entry delay improves path order and reduces immediate adverse selection.
- Why still alive: `entry_delay_1` keeps the full 191-trade sample and improves winrate from 48.69% to 61.26%, mean return from +0.00002978 to +0.00017416, and max drawdown from -0.01288895 to -0.00702553.
- Current evidence: pseudo-holdout and leave-one-day-out are constructive; Sprint 02 cost stress stays positive through `0.00015` and fails transparently at `0.00020`.
- Weaknesses: no true unseen holdout; top-3 day removal plus 0.00010 cost turns slightly negative; source window needs exact verification.
- Required next validation: true future holdout on new clean Analyzer days with no parameter changes.
- Minimum promotion gates: global gates, plus cost sensitivity pass at realistic spot margin fee/slippage assumptions.
- Exact next replay action: run true future holdout on the frozen `entry_delay_1` contract, compare against `baseline_current`, and publish paired deltas without changing `ctx_spike_count >= 2` or delay.
- Exact reason why not live: diagnostic-only transform, no true holdout, no execution-grade cost model, and official promotion remains `REJECT`.
