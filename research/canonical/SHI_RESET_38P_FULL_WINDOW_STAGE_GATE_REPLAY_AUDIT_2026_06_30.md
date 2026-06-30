# SHI RESET 38P Full Window Stage-Gate Replay Audit

Verdict: RESEARCH_STAGE_GATE_REPLAY_COMPLETE

This audit records the 38P stage-gated full-window replay. The runner treats setup rows as review context by default and only allows policy replay after a valid qualified H1 failed-reclaim sequence link.

# SHI RESET 38P Full Window Stage-Gate Replay

Research-only replay. This is not live-ready and does not use Executor, orders, live trading, entries/exits modules, position sizing, or strategy promotion.

- Window: 2026-05-23 -> 2026-06-10
- Total setup rows found: 9
- Count by setup_type: {"DEMAND_SWEEP_RECLAIM_UP_SETUP": 1, "SELLER_DOMINANCE_RETEST_DOWN_SETUP": 7, "SUPPLY_SWEEP_RECLAIM_DOWN_SETUP": 1}
- Count by corrected_research_classification: {"FAILED_RECLAIM_TRIGGER_CANDIDATE": 1, "FOLLOW_THROUGH_OR_CONTINUATION_SHORT_REVIEW": 1, "LATE_LAST_WAGON": 1, "MAJOR_SHORT_TRIGGER_AFTER_H1_SWEEP": 1, "PRE_TRIGGER_CONTEXT": 1, "PRE_TRIGGER_CONTEXT_OR_FAILED_CONTINUATION_REVIEW": 1, "STRUCTURAL_RETEST_TRIGGER_CANDIDATE": 3}
- Count by final_stage_reached: {"STAGE_1_RAW_CONTEXT_OR_RAW_SWEEP": 8, "STAGE_5_POLICY_REPLAY_ALLOWED": 1}
- Count passing STAGE_1: 9
- Count passing STAGE_2: 1
- Count passing STAGE_3: 1
- Count passing STAGE_4: 1
- Count passing STAGE_5: 1
- Count failing each stage: {"STAGE_2_QUALIFIED_H1_SWEEP": 8}
- Policy replay outcomes: {"SELECTED_STOP_TARGET_POLICY::TARGET_BEFORE_SELECTED_STOP": 1, "TP1_BE_WITH_SELECTED_STOP_POLICY::TP1_THEN_BE": 1}
- 2026-05-26 sequence reproduced: true
- New sequence-linked candidates vs 38O: 0

## Sequence Valid Rows

| setup_id | setup_formed_at | corrected_research_classification | tradable_entry_anchor | final_stage_reached |
| --- | --- | --- | --- | --- |
| setup_000002 | 2026-05-26T16:59:00+00:00 | MAJOR_SHORT_TRIGGER_AFTER_H1_SWEEP | 76476.8 | STAGE_5_POLICY_REPLAY_ALLOWED |

## Policy Replay Allowed Rows

| setup_id | entry_candidate_ts | policy_name | policy_outcome_label | first_event | first_event_ts |
| --- | --- | --- | --- | --- | --- |
| setup_000002 | 2026-05-26T15:59:00Z | SELECTED_STOP_TARGET_POLICY | TARGET_BEFORE_SELECTED_STOP | TARGET | 2026-05-28T04:03:00Z |
| setup_000002 | 2026-05-26T15:59:00Z | TP1_BE_WITH_SELECTED_STOP_POLICY | TP1_THEN_BE | BE | 2026-05-26T16:23:00Z |

## Focus Rows

| setup_id | setup_formed_at | corrected_research_classification | final_stage_reached | stage_gate_status | stage_gate_reject_reason |
| --- | --- | --- | --- | --- | --- |
| setup_000002 | 2026-05-26T16:59:00+00:00 | MAJOR_SHORT_TRIGGER_AFTER_H1_SWEEP | STAGE_5_POLICY_REPLAY_ALLOWED | POLICY_REPLAY_ALLOWED |  |
| setup_000003 | 2026-05-27T05:59:00+00:00 | FOLLOW_THROUGH_OR_CONTINUATION_SHORT_REVIEW | STAGE_1_RAW_CONTEXT_OR_RAW_SWEEP | REJECTED_BEFORE_POLICY_REPLAY | no_qualified_h1_failed_reclaim_in_sequence_window: insufficient_prior_reaction\|close_strongly_held_beyond_level \|\| insufficient_prior_reaction\|close_strongly_held_beyond_level \|\| insufficient_prior_reaction\|close_strongly_held_beyond_level |
| setup_000005 | 2026-06-01T00:59:00+00:00 | FAILED_RECLAIM_TRIGGER_CANDIDATE | STAGE_1_RAW_CONTEXT_OR_RAW_SWEEP | REJECTED_BEFORE_POLICY_REPLAY | no_qualified_h1_failed_reclaim_in_sequence_window: level_too_young\|insufficient_prior_reaction\|close_strongly_held_beyond_level \|\| level_too_young\|insufficient_prior_reaction\|close_strongly_held_beyond_level \|\| level_too_young\|insufficient_prior_reaction\|close_strongly_held_beyond_level |
| setup_000008 | 2026-06-05T16:59:00+00:00 | LATE_LAST_WAGON | STAGE_1_RAW_CONTEXT_OR_RAW_SWEEP | REJECTED_BEFORE_POLICY_REPLAY | no_qualified_h1_failed_reclaim_in_sequence_window: level_too_young\|insufficient_prior_reaction\|close_strongly_held_beyond_level \|\| level_too_young\|insufficient_prior_reaction \|\| close_strongly_held_beyond_level |
| setup_000009 | 2026-06-09T17:59:00+00:00 | PRE_TRIGGER_CONTEXT_OR_FAILED_CONTINUATION_REVIEW | STAGE_1_RAW_CONTEXT_OR_RAW_SWEEP | REJECTED_BEFORE_POLICY_REPLAY | no_raw_sweep_in_sequence_window |

## Data Quality Notes

- Uses existing feed/ rows for 2026-05-23 through 2026-06-10.
- Future labels are not read by this runner.
- Historical 38J/38K/38L/38N/38O artifact roots are not rewritten.
- Raw sweep alone cannot pass to policy replay.
