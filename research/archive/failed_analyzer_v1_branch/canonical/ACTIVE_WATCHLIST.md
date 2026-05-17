# ACTIVE_WATCHLIST

Last updated: 2026-05-17

Only two candidates remain on active/watch navigation after Sprint 03. Deep-reclaim short is rejected as a formal ruleset. H4 EXTENDED_V1 remains quarantined and is not watch evidence.

## 1. CAND_SHORT_CTX_SPIKE_GE2_ENTRY_DELAY_1

- Role: main validation candidate.
- Status: `ACTIVE_VALIDATION / WAIT`.
- Hypothesis: on the `ctx_spike_count >= 2` short reclaim surface, one-bar entry delay improves path order and reduces immediate adverse selection.
- Why still alive: Sprint 03 formal replay has 301 candidate events, 61 trade-days, no-lookahead PASS, source concentration PASS, and cost `0.00015` positive.
- Current evidence: cost `0.00000`, `0.00010`, and `0.00015` pass; cost `0.00020` fails and is an execution-risk warning.
- Weaknesses: true holdout has not started; same-bar ambiguity is 40/301 trades; `0.00020` stress is negative.
- Required next validation: true holdout only after Sprint 03 freeze commit `23d1cc3`, with unchanged mapper, `ctx_spike_count >= 2`, `entry_delay_1`, stop, exit, and cost model.
- Minimum promotion gates: >= 25 new holdout trades, >= 10 independent holdout trade-days, cost `0.00015` positive, same-bar not verdict-changing, source concentration PASS, no single-day PnL dominance, and no rule edits after freeze.
- Exact next replay action: run each new clean batch through Aggregator/feed update -> Analyzer -> unchanged Sprint 03 mapper -> append candidate events -> frozen replay -> cost stress -> holdout report.
- Exact reason why not live: no true holdout evidence exists, same-bar is not cleared, and `0.00020` cost stress fails.

## 2. CAND_LONG_IMPULSE_FADE_LATE_US_STRUCTURAL

- Role: passive watch.
- Status: `WATCH_ONLY`.
- Hypothesis: long-side H2 fade is not deep reclaim; it is late-US structural acceptance after impulse, expressed by `SetupCloseLocationInImpulseRange >= 0.75`, `entry_hour_16_23`, and `Impulse_BodyToRange > 0.75`.
- Why still alive: primary selector has 20 rows, 19 resolved return rows, and 13 trade-days; early behavior is constructive but below gate.
- Current evidence: diagnostic watch only; no formal Sprint 03 ruleset mapping.
- Weaknesses: small sample, one unresolved row, session-specific surface, no formal cost-aware Backtester replay, no same-bar clearance.
- Required next validation: continue passive forward evidence collection unchanged.
- Minimum promotion gates: formal mapping, true holdout, same-bar audit, cost stress, source concentration, and frozen stop/exit before any Phase 4 discussion.
- Exact next replay action: update forward watch only after clean Analyzer cycles; do not add predicates or tune selectors.
- Exact reason why not live: this is not a replayable strategy and has no promotion-grade evidence.
