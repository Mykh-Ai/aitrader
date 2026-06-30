# SHI_RESET_38N_QUALIFIED_H1_SWEEP_RECLAIM_REPLAY_ON_38J_WINDOW_AUDIT

Verdict: PARTIAL / SEQUENCE_WINDOW_REQUIRED

Scope: research-only replay of the 38J window through the 38M qualified H1 sweep/reclaim layer. No Executor, orders, live trading, entries/exits, PnL, position sizing, Backtester execution logic, live-readiness, or strategy promotion were introduced.

## Inputs

- 38J corrected classification view:
  `market_monitor_runs/SHI_RESET_38J_wider_research_window_2026_05_23_to_2026_06_10_v0/wider_setup_classification_corrected.csv`
- Feed:
  `feed/`
- Window:
  `2026-05-23 -> 2026-06-10`
- Qualified layer:
  `SHI_RESET_38M_QUALIFIED_H1_SWEEP_RECLAIM_V0`

## Outputs

Output root:

`market_monitor_runs/SHI_RESET_38N_qualified_h1_sweep_reclaim_replay_on_38j_window_v0`

Files:

- `qualified_h1_sweep_reclaim_events.csv`
- `qualified_h1_vs_manual_verdicts.csv`
- `qualified_h1_sweep_reclaim_summary.md`
- `qualified_h1_sweep_reclaim_manifest.json`

## Run Counts

- Setup rows evaluated: 9
- Raw H1 sweep rows at setup timestamp: 6
- Qualified H1 sweep rows at setup timestamp: 0
- Qualified H1 failed reclaim rows at setup timestamp: 0

Manual match status counts:

- `NO_MANUAL_VERDICT`: 5
- `MANUAL_EXPECTS_PRIMARY_TRIGGER_BUT_QUALIFIED_RECLAIM_MISSING`: 1
- `MATCH_REVIEW`: 1
- `MATCH_CONTROL`: 2

## Focus Case Results

| setup_id | setup_formed_at | manual_or_corrected_classification | raw_sweep | qualified_h1_sweep | qualified_h1_failed_reclaim | 38N status | reject reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| setup_000002 | 2026-05-26T16:59:00+00:00 | MAJOR_SHORT_TRIGGER_AFTER_H1_SWEEP | false | false | false | MANUAL_EXPECTS_PRIMARY_TRIGGER_BUT_QUALIFIED_RECLAIM_MISSING | no_raw_sweep_at_h1_close |
| setup_000003 | 2026-05-27T05:59:00+00:00 | FOLLOW_THROUGH_OR_CONTINUATION_SHORT_REVIEW | true | false | false | MATCH_REVIEW | insufficient_prior_reaction; close_strongly_held_beyond_level |
| setup_000005 | 2026-06-01T00:59:00+00:00 | no manual correction | true | false | false | NO_MANUAL_VERDICT | level_too_young; insufficient_prior_reaction; close_strongly_held_beyond_level |
| setup_000008 | 2026-06-05T16:59:00+00:00 | LATE_LAST_WAGON | true | false | false | MATCH_CONTROL | close_strongly_held_beyond_level |
| setup_000009 | 2026-06-09T17:59:00+00:00 | PRE_TRIGGER_CONTEXT_OR_FAILED_CONTINUATION_REVIEW | false | false | false | MATCH_CONTROL | no_raw_sweep_at_h1_close |

## Interpretation

38N proves that the strict 38M qualified H1 contract rejects all five focus rows when evaluated at the exact `setup_formed_at` H1 close.

That does not disprove the 38K manual verdict for `2026-05-26T16:59Z`. The manual verdict explicitly says the meaningful H1 sweep/rejection occurred around `2026-05-26 14:00`, and that the `16:59` setup appeared after that local sequence. Therefore an exact-timestamp sweep check is insufficient for this case.

Required next correction:

- Add a sequence-window replay that searches the H1 sweep / reclaim / fail sequence before the setup timestamp.
- For `2026-05-26T16:59Z`, inspect the H1 sequence around `2026-05-26 14:00 -> 2026-05-26 16:59`.
- Treat `setup_formed_at` as the setup review timestamp, not necessarily the sweep candle timestamp.
- The entry candidate timestamp, if qualified, must still be the reclaim/rejection confirmation timestamp, not broad context time.

## 38N Conclusion

- 38M contract works as a strict guard against raw sweep promotion.
- 38N exact-anchor replay is too narrow for manually identified sequence cases.
- `2026-06-05T16:59Z` and `2026-06-09T17:59Z` manual demotions are supported by the qualified layer as control / non-entry cases.
- `2026-05-27T05:59Z` remains review-only follow-through, not a qualified primary failed reclaim.
- `2026-05-26T16:59Z` requires sequence-window H1 analysis before the manual primary-trigger verdict can be accepted or rejected by code.

Status: 38O_SEQUENCE_WINDOW_QUALIFIED_H1_REPLAY_REQUIRED
