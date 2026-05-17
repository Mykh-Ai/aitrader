# SAME_BAR_DE_RISK_PLAN

Candidate: `CAND_SHORT_CTX_SPIKE_GE2_ENTRY_DELAY_1`

Status: `ACTIVE_VALIDATION / WAIT`

Current Sprint 03 ambiguity: 40 / 301 trades, 13.29%.

## Level 1 - Conservative Policy

Use the existing conservative policy for every replay:

- If SL and TP are both possible in the same bar, count worst-case / stop-first.
- Treat this as the default result for registry and promotion-gate checks.
- Current conservative cost `0.00015` result is positive: `0.0123921046`.

Verdict rule:

- If conservative net at cost `0.00015` remains positive, the candidate can remain alive as `WAIT`.
- Conservative positivity alone is not enough for `PROMOTE` while same-bar ambiguity remains unresolved.

## Level 2 - Ambiguity Sensitivity

For each replay, calculate and store:

- `result_without_ambiguous_trades`
- `result_all_ambiguous_as_loss`
- `result_all_ambiguous_as_best_case`
- `current_conservative_result`

Decision rule:

- If the candidate only passes because ambiguous trades are included favorably, Phase 4 remains closed.
- If the verdict materially changes between conservative, pessimistic, and optimistic treatments, Phase 4 remains closed.
- If conservative result stays positive and pessimistic is not materially worse, candidate remains `WAIT` pending holdout.

## Level 3 - Intrabar Resolution

Check whether M1, trade-level, or lower-timeframe raw data exists for each ambiguous window.

- If intrabar data exists, run micro-replay for those windows using the frozen Sprint 03 stop/target/expiry.
- If intrabar data does not exist, record: `intrabar unavailable -> same-bar not cleared -> no promotion`.
- Intrabar resolution must not introduce a new entry condition, threshold, or exit parameter.

Promotion remains prohibited until same-bar ambiguity is either cleared or proven not verdict-changing under conservative and sensitivity tests.
