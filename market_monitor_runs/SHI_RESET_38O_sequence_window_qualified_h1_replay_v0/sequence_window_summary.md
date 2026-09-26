# SHI RESET 38O Sequence-Window Qualified H1 Replay

Research-only replay. Setup timestamp is treated as review time; qualified trigger time remains reclaim/rejection close time.

- Setup rows evaluated: 9
- Qualified sequence links: 1
- Valid sequence links for setup: 1
- Manual match status counts: {"MATCH": 1, "MATCH_CONTROL": 2, "NO_MANUAL_VERDICT": 5, "NO_QUALIFIED_SEQUENCE_FOR_CONTINUATION_REVIEW": 1}

## Focus Cases

| setup_id | setup_formed_at | corrected_research_classification | qualified_sequence_found | qualified_h1_sweep_ts | entry_candidate_ts | sequence_age_h1_bars_at_setup | sequence_valid_for_setup | manual_match_status | sequence_reject_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| setup_000002 | 2026-05-26T16:59:00+00:00 | MAJOR_SHORT_TRIGGER_AFTER_H1_SWEEP | true | 2026-05-26T14:59:00Z | 2026-05-26T15:59:00Z | 1.0 | true | MATCH |  |
| setup_000003 | 2026-05-27T05:59:00+00:00 | FOLLOW_THROUGH_OR_CONTINUATION_SHORT_REVIEW | false |  |  |  | false | NO_QUALIFIED_SEQUENCE_FOR_CONTINUATION_REVIEW | no_qualified_h1_failed_reclaim_in_sequence_window: insufficient_prior_reaction\|close_strongly_held_beyond_level \|\| insufficient_prior_reaction\|close_strongly_held_beyond_level \|\| insufficient_prior_reaction\|close_strongly_held_beyond_level |
| setup_000005 | 2026-06-01T00:59:00+00:00 | FAILED_RECLAIM_TRIGGER_CANDIDATE | false |  |  |  | false | NO_MANUAL_VERDICT | no_qualified_h1_failed_reclaim_in_sequence_window: level_too_young\|insufficient_prior_reaction\|close_strongly_held_beyond_level \|\| level_too_young\|insufficient_prior_reaction\|close_strongly_held_beyond_level \|\| level_too_young\|insufficient_prior_reaction\|close_strongly_held_beyond_level |
| setup_000008 | 2026-06-05T16:59:00+00:00 | LATE_LAST_WAGON | false |  |  |  | false | MATCH_CONTROL | no_qualified_h1_failed_reclaim_in_sequence_window: level_too_young\|insufficient_prior_reaction\|close_strongly_held_beyond_level \|\| level_too_young\|insufficient_prior_reaction \|\| close_strongly_held_beyond_level |
| setup_000009 | 2026-06-09T17:59:00+00:00 | PRE_TRIGGER_CONTEXT_OR_FAILED_CONTINUATION_REVIEW | false |  |  |  | false | MATCH_CONTROL | no_raw_sweep_in_sequence_window |

No Executor, orders, live trading, entries/exits, PnL, position sizing, live-readiness, or strategy promotion is used.
