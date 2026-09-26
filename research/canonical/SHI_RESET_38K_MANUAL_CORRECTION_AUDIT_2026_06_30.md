# SHI_RESET_38K_MANUAL_CORRECTION_AUDIT

Verdict: 38J_BROAD_WINDOW_AUTO_DEMOTION_NEEDS_CORRECTION

Scope: research-only manual correction audit for the 38J wider-window setup classification. This document does not add or modify trading signals, entries, exits, orders, Executor logic, Backtester logic, PnL, position sizing, live-readiness, or strategy promotion.

## Source Rows

Source artifact:

`market_monitor_runs/SHI_RESET_38J_wider_research_window_2026_05_23_to_2026_06_10_v0/wider_setup_classification.csv`

Rows under correction:

| setup_id | setup_formed_at | setup_type | trigger_status | source_time_precision | 38J_classification | policy_replay_allowed | 38J_reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| setup_000002 | 2026-05-26T16:59:00+00:00 | SELLER_DOMINANCE_RETEST_DOWN_SETUP | ARMED | RAW_REGIME_WINDOW_720M | LATE_LAST_WAGON | false | broad raw/source window; not immediate entry without local trigger |
| setup_000003 | 2026-05-27T05:59:00+00:00 | SELLER_DOMINANCE_RETEST_DOWN_SETUP | ARMED | RAW_REGIME_WINDOW_720M | LATE_LAST_WAGON | false | broad raw/source window; not immediate entry without local trigger |

## Correction: 2026-05-26T16:59Z

Current 38J classification:

- SELLER_DOMINANCE_RETEST_DOWN_SETUP
- ARMED
- RAW_REGIME_WINDOW_720M
- LATE_LAST_WAGON

Manual verdict:

- This was not a late-last-wagon setup.
- It appeared before a major downside move of approximately 13000 USD.
- Around 2026-05-26 14:00, the H1 candle made a clear sweep with visible volume.
- The H1 candle closed red with an upper wick.
- The next H1 candle closed near the lower edge of the channel.
- The 16:59 setup appeared after this local H1 sweep/rejection context.
- Therefore this row should be reviewed as `MAJOR_SHORT_TRIGGER_AFTER_H1_SWEEP` or `PRIMARY_DOWNSIDE_IMPULSE_TRIGGER`, not rejected as late.

Corrected classification:

- MAJOR_SHORT_TRIGGER_AFTER_H1_SWEEP

Action:

- Reclassify for manual/replay review.
- Mark broad-window auto-demotion as false for this row.
- Require precise trigger timing check around the H1 sweep/reclaim/fail sequence.

## Correction: 2026-05-27T05:59Z

Current 38J classification:

- SELLER_DOMINANCE_RETEST_DOWN_SETUP
- ARMED
- RAW_REGIME_WINDOW_720M
- LATE_LAST_WAGON

Manual verdict:

- This row cannot be classified as late-last-wagon by definition if the main downside move had not matured before it.
- It should be reviewed as follow-through / continuation short context after the 2026-05-26 trigger.
- Do not reject solely because of `RAW_REGIME_WINDOW_720M`.

Corrected classification:

- FOLLOW_THROUGH_OR_CONTINUATION_SHORT_REVIEW

Action:

- Review separately from the primary 2026-05-26 trigger.
- Determine whether it is a valid continuation entry, confirmation, or already too late after part of the move.

## Updated Conclusion

- 2026-05-26T16:59Z is one of the most important candidates in the 38J wider window.
- 2026-05-27T05:59Z is a continuation / follow-through review row.
- The 38J broad-window demotion rule needs correction before any wider replay summary is treated as final.

## Required 38K Rule Repair Direction

The 38J classifier treated `RAW_REGIME_WINDOW_720M` as enough to demote an ARMED row to `LATE_LAST_WAGON`. This is not safe when a broad raw regime window contains or follows a precise local H1 sweep / rejection / reclaim-fail sequence.

Required follow-up before replay summary:

- Do not automatically demote all `RAW_REGIME_WINDOW_720M` ARMED rows.
- Add a local trigger evidence override for H1 sweep/rejection context.
- Preserve broad-window context as source metadata, not as an automatic rejection reason.
- Split primary downside impulse trigger review from continuation / follow-through review.
- Replay review must include `setup_000002` and `setup_000003`; they must not remain excluded solely by the 38J broad-window rule.

## Status

Status: 38K_REQUIRED_BEFORE_WIDER_REPLAY_SUMMARY

The generated 38J artifacts remain useful as raw evidence, but their `LATE_LAST_WAGON` classification for these two rows is superseded by this manual correction audit.
