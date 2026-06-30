# SHI_RESET_38O_SEQUENCE_WINDOW_QUALIFIED_H1_REPLAY_AUDIT

Verdict: PASS / PRIMARY_SEQUENCE_FOUND_FOR_2026_05_26

Scope: research-only sequence-window qualified H1 replay. This audit does not rewrite 38J, 38K, 38L, or 38N artifacts and does not add Executor logic, orders, live trading, entries/exits, PnL, position sizing, live-readiness, Backtester execution logic, or strategy promotion.

## Inputs

- Corrected 38J classification view:
  `market_monitor_runs/SHI_RESET_38J_wider_research_window_2026_05_23_to_2026_06_10_v0/wider_setup_classification_corrected.csv`
- 38M qualified H1 sweep/reclaim contract
- 38N exact-anchor replay outputs
- Feed: `feed/`
- Window: `2026-05-23T00:00:00Z -> 2026-06-10T23:59:00Z`

## Outputs

Output root:

`market_monitor_runs/SHI_RESET_38O_sequence_window_qualified_h1_replay_v0`

Files:

- `sequence_window_qualified_h1_events.csv`
- `sequence_window_setup_links.csv`
- `sequence_window_vs_manual_verdicts.csv`
- `sequence_window_summary.md`
- `sequence_window_manifest.json`

## Method

38O treats `setup_formed_at` as the setup review timestamp, not necessarily the sweep candle timestamp.

For each setup row:

- search the previous 8 completed H1 candles through `setup_formed_at`
- evaluate each H1 close through the 38M qualified H1 sweep/reclaim contract
- allow reclaim confirmation within 1-3 completed H1 bars after the sweep
- link a qualified sequence back to the setup if the reclaim happened before setup review time
- keep `entry_candidate_ts` as the reclaim/rejection close timestamp

## Run Counts

- Setup rows evaluated: 9
- H1 candidate evaluations: 81
- Qualified sequence links: 1
- Valid sequence links for setup: 1

Manual match status counts:

- `MATCH`: 1
- `MATCH_CONTROL`: 2
- `NO_MANUAL_VERDICT`: 5
- `NO_QUALIFIED_SEQUENCE_FOR_CONTINUATION_REVIEW`: 1

## Focus Case Results

| setup_id | setup_formed_at | corrected_research_classification | qualified_sequence_found | qualified_h1_sweep_ts | reclaim_h1_close_ts | entry_candidate_ts | entry_candidate_price | sequence_age_h1_bars_at_setup | valid | manual_match_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| setup_000002 | 2026-05-26T16:59:00+00:00 | MAJOR_SHORT_TRIGGER_AFTER_H1_SWEEP | true | 2026-05-26T14:59:00Z | 2026-05-26T15:59:00Z | 2026-05-26T15:59:00Z | 76476.8 | 1.0 | true | MATCH |
| setup_000003 | 2026-05-27T05:59:00+00:00 | FOLLOW_THROUGH_OR_CONTINUATION_SHORT_REVIEW | false |  |  |  |  |  | false | NO_QUALIFIED_SEQUENCE_FOR_CONTINUATION_REVIEW |
| setup_000005 | 2026-06-01T00:59:00+00:00 | FAILED_RECLAIM_TRIGGER_CANDIDATE | false |  |  |  |  |  | false | NO_MANUAL_VERDICT |
| setup_000008 | 2026-06-05T16:59:00+00:00 | LATE_LAST_WAGON | false |  |  |  |  |  | false | MATCH_CONTROL |
| setup_000009 | 2026-06-09T17:59:00+00:00 | PRE_TRIGGER_CONTEXT_OR_FAILED_CONTINUATION_REVIEW | false |  |  |  |  |  | false | MATCH_CONTROL |

## 2026-05-26T16:59Z Primary Sequence

38O confirms the 38K manual thesis for `setup_000002`:

- setup review timestamp: `2026-05-26T16:59:00Z`
- sequence window: `2026-05-26T08:59:00Z -> 2026-05-26T16:59:00Z`
- qualified H1 sweep timestamp: `2026-05-26T14:59:00Z`
- qualified failed reclaim timestamp: `2026-05-26T15:59:00Z`
- entry candidate timestamp: `2026-05-26T15:59:00Z`
- entry candidate price: `76476.8`
- swept level: `77351.6565`
- swept level type: `ACTIVE_STRUCTURAL_LIQUIDITY_ZONE`
- sweep H1 high: `78077.1`
- sweep H1 low: `76682.3`
- sweep H1 close: `76923.1`
- sweep H1 volume: `32813.911`
- sweep volume ratio: `9.619656`
- level age H1 bars: `10`
- reaction_abs: `807.8565`
- penetration_abs: `725.4435`
- wick quality: `true`
- reclaim bar number after sweep: `1`
- setup review lag: `1.0` H1 bars

This is sequence-linked evidence, not exact-anchor evidence. It corrects the 38N limitation.

## Negative / Control Cases

`2026-05-27T05:59Z`:

- no qualified sequence in the 8-H1 lookback
- remains follow-through / continuation review only
- not a primary trigger under 38M/38O

`2026-06-01T00:59Z`:

- no qualified sequence found
- prior 38J failed-reclaim classification is not confirmed by 38O
- needs separate review before replay interpretation

`2026-06-05T16:59Z`:

- no qualified sequence found
- manual LATE_LAST_WAGON / control demotion is supported

`2026-06-09T17:59Z`:

- no raw sweep in sequence window
- manual failed-continuation / pre-trigger-control demotion is supported

## Conclusion

38O proves that sequence-window replay is necessary and materially changes the interpretation of the 38J window:

- 38N exact-anchor replay was too narrow.
- 38O finds the qualified H1 sweep/reclaim sequence before the `2026-05-26T16:59Z` setup review timestamp.
- The entry candidate timestamp remains the reclaim confirmation close (`2026-05-26T15:59Z`), not the later setup review timestamp and not broad context time.
- Raw sweep still cannot promote without the 38M qualified H1 conditions.

Status: READY_FOR_REPLAY_POLICY_REVIEW_ON_SEQUENCE_LINKED_CANDIDATES
