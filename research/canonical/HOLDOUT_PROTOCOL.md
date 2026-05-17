# HOLDOUT_PROTOCOL

Last updated: 2026-05-17

## Freeze Point

- Freeze point: Sprint 03 commit `23d1cc3`.
- Contract freeze timestamp: `2026-05-17T11:12:14.334104+00:00`.
- Candidate: `CAND_SHORT_CTX_SPIKE_GE2_ENTRY_DELAY_1`.
- Rule version: `SPRINT03_CTX_GE2_ENTRY_DELAY_1_V1`, frozen from Sprint 03.
- No parameter changes after freeze.

## Frozen Rule Scope

- Candidate id: `CAND_SHORT_CTX_SPIKE_GE2_ENTRY_DELAY_1`.
- Side: `SHORT`.
- Core selector: `ctx_spike_count >= 2`.
- Entry timing: `entry_delay_1`.
- Stop model: `REFERENCE_LEVEL_HARD_STOP`.
- Exit model: `FIXED_R_MULTIPLE:1.5` plus `BARS_AFTER_ACTIVATION:12` expiry.
- Mapper: `research/scripts/sprint_03_formal_candidate_rulesets.py`.
- Existing mapped events are already-seen evidence, not holdout evidence.

## Already-Seen Data

- Already-seen data: everything before Sprint 03 freeze commit `23d1cc3`.
- This includes all primary/recovered feed rows, Analyzer artifacts, Backtester outputs, sidecar diagnostics, candidate events, replay summaries, and written findings inspected before the freeze.
- Recovered gap data is valid for data repair and pooled replay, but it is not true holdout.

## True Holdout

- True holdout: only data after Sprint 03 freeze commit `23d1cc3`.
- Holdout starts after the freeze point, not at the start of the recovered gap and not at any previously inspected date.
- Holdout data must come from clean feed or explicitly accepted recovered source with degraded fields documented.
- Every holdout batch must use the unchanged Sprint 03 mapper and unchanged stop/exit/cost model.

## Minimum Holdout Gates

- >= 25 new holdout trades.
- >= 10 independent holdout trade-days.
- Cost `0.00015` positive.
- Same-bar ambiguity not verdict-changing.
- Source concentration PASS.
- No single-day PnL dominance.
- No rule edits after freeze.

## Cost Verdict Rule

- Cost `0.00015` is the hard gate.
- Cost `0.00020` is a warning gate.
- If cost `0.00015` fails, verdict is `REJECT` or `WAIT`, never `PROMOTE`.
- If cost `0.00015` passes but cost `0.00020` fails, candidate can remain `WAIT`, but execution-readiness is blocked.

## Same-Bar Rule

- Same-bar ambiguity must be measured on every replay.
- Conservative policy remains the default: if stop and target are both possible in the same bar, count the conservative stop-first result.
- If optimistic/pessimistic/conservative treatment materially changes verdict, Phase 4 remains closed.
- If intrabar data is unavailable for ambiguous windows, same-bar is not cleared and promotion remains prohibited.

## Daily / Periodic Holdout Routine

1. Aggregator / feed update.
2. Analyzer run.
3. Sprint 03 mapper unchanged.
4. Append `candidate_events` for `CAND_SHORT_CTX_SPIKE_GE2_ENTRY_DELAY_1`.
5. Replay with frozen stop/exit.
6. Cost stress at `0.00000`, `0.00010`, `0.00015`, `0.00020`.
7. Update holdout report and `holdout_log.csv`.

## Verdict Rules

- `PROMOTE`: all holdout gates pass, same-bar is cleared, cost hard gate passes, source concentration passes, and no rule edits occurred after freeze.
- `WAIT_HOLDOUT_IN_PROGRESS`: formal rule exists but holdout sample is below gate.
- `WAIT_SAME_BAR_NOT_CLEARED`: economics remain constructive but same-bar ambiguity is not cleared.
- `REJECT_HOLDOUT_FAIL`: true holdout economics fail under the frozen rule.
- `REJECT_COST_FAIL`: cost `0.00015` fails under the frozen rule.
- `BLOCKED`: mapper, stop/exit, no-lookahead, or replay contract is invalid.

Until the gates pass:

- `PROMOTE` is prohibited.
- Phase 4 Bridge is closed.
- Executor/live trading are prohibited.
