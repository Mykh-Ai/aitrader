# ACTIVE_WATCHLIST

Last updated: 2026-05-16

## CAND_SHORT_IMPULSE_FADE_DEEP_RECLAIM_GT_0_6

- Status: `REJECT` under Sprint 03 formal mapping.
- Hypothesis: H2 short impulse fade works best when reclaim depth is real, specifically `ReclaimDepthToImpulseRange > 0.6`.
- Formal evidence: 14 formal candidate events, no-lookahead PASS, stop/exit frozen, but cost stress fails at every level including `0.00015`.
- Source concentration: FAIL, only 7 trade-days; largest day abs result share 0.409027 and top3 abs share 0.738923.
- Same-bar: PASS for ambiguity handling, but economic result remains negative.
- Exact next action: do not continue as primary active watch. Reopen only as a new pre-declared candidate, not by tuning threshold or adding filters after the REJECT.
- Exact reason why not live: formal replay hard cost gate fails and sample/concentration gates fail.

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
- Current evidence: Sprint 03 formal replay has 301 candidate events, 61 trade-days, no-lookahead PASS, source concentration PASS, and cost `0.00015` positive.
- Weaknesses: no true unseen holdout; cost `0.00020` fails; same-bar report is WAIT with 40/301 ambiguous trades.
- Required next validation: true future holdout on new clean Analyzer days with no parameter changes.
- Minimum promotion gates: global gates, plus cost sensitivity pass at realistic spot margin fee/slippage assumptions.
- Exact next replay action: run true future holdout after the Sprint 03 freeze timestamp with unchanged `ctx_spike_count >= 2` and `entry_delay_1`.
- Exact reason why not live: true holdout is not started, cost `0.00020` fails, and same-bar verdict remains WAIT.
