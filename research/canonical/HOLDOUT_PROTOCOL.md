# HOLDOUT_PROTOCOL

Contract freeze timestamp: `2026-05-17T11:12:14.334104+00:00`

## Candidate IDs

- `CAND_SHORT_CTX_SPIKE_GE2_ENTRY_DELAY_1`
- `CAND_SHORT_IMPULSE_FADE_DEEP_RECLAIM_GT_0_6`

## Already-Seen Data

- All data, Analyzer artifacts, Backtester outputs, sidecar diagnostics, and recovered-gap reruns inspected before the freeze timestamp.
- This includes primary/recovered data through the current local project state on 2026-05-17.
- Recovered gap data is valid for data repair and pooled replay, but it is not true holdout.

## True Holdout

- True holdout starts only after the Sprint 03 freeze timestamp.
- Any day analyzed, used in candidate_events, or discussed before freeze is not holdout.
- Holdout data must come from clean feed or explicitly accepted recovered source with degraded fields documented.

## Minimum Evidence

- >= 25 post-holdout trades.
- >= 10 independent post-holdout trade-days.
- Positive net after cost stress 0.00015.
- 0.00020 stress failure is allowed only as WAIT_FOR_EXECUTION_COST_REVIEW, never PROMOTE.
- Source concentration PASS.
- Same-bar ambiguity cleared.

## No-Tuning Rule

- No threshold, entry delay, stop, target, expiry, feature definition, or filter may be changed after freeze based on holdout results.
- A changed rule becomes a new candidate and restarts the holdout clock.

## Verdict Rules

- `PROMOTE`: all gates pass, including true holdout.
- `WAIT`: formal mapping exists but holdout/cost/source/same-bar gates are incomplete or mixed.
- `REJECT`: hard cost gate fails or evidence is negative under frozen rule.
- `BLOCKED`: mapping, stop/exit, no-lookahead, or replay contract is invalid.

Phase 4 Bridge remains closed until this protocol passes. Executor/live remain prohibited.
