# Rule Finding Verdict

`RULESET_REPORT_SETUPTYPE_FAILED_BREAK_RECLAIM_LONG_V1_LONG_BASE` reached replay and produced a non-zero trade surface, but the replay result was not strong enough to survive review.
Recorded outcome:
- `trade_count=6`
- `validation=FAIL`
- `robustness=FRAGILE`
- `promotion=REJECT`

This is not a positive candidate. It is also not a dead reject.
Current classification: `REPLAYED_BUT_INCONCLUSIVE`.

## Source Lineage

Known source window:
- `2026-03-18_to_2026-03-22`

Known context from project findings:
- the window restored limited replayability after a daily `FormalizationEligible=0` streak;
- `shortlist_rows=4`, `FormalizationEligible=2`, `replayable_rulesets_count=2`.

Unknown / not asserted here:
- `SourceRunDir = UNKNOWN`
- exact derived run directory = `UNKNOWN`

## Why This Rule Matters

This ruleset matters because it was not filtered out before replay. It reached the replay stage, opened trades, and therefore has archival value as a concrete research case. That archival value does not imply edge.

## Replay Outcome

Replay produced `6` trades, then failed downstream review:
- validation failed;
- robustness was marked fragile;
- promotion decision was reject.

The correct reading is narrow: replay happened, but evidence remained insufficient.

## Candidate Classification

Candidate class: `REPLAYED_BUT_INCONCLUSIVE`.

Why this class:
- replay was real;
- replay surface was non-zero;
- the rule was not empty;
- the result still failed to establish a positive candidate.

Why not `DEAD_REJECT`:
- `trade_count > 0`
- non-zero replay surface existed

Why not positive:
- `validation=FAIL`
- `robustness=FRAGILE`
- `promotion=REJECT`

## Archive Verdict

Archive verdict: `ARCHIVE_AND_REVISIT_ON_LARGER_BASE`.

This means:
- keep the ruleset in the replayed-rule registry;
- keep this rule-level finding as an archival note;
- do not tune the ruleset against this local reject;
- do not present it as edge or execution-ready logic.

## What Is Closed

Closed on current evidence:
- this ruleset is not a positive candidate;
- this ruleset is not execution-ready;
- this ruleset is not a dead reject;
- current replay evidence is insufficient for promotion.

## What Remains Open

Still open:
- whether the same unchanged ruleset keeps non-zero replay surface on a larger history;
- whether a larger base keeps the result inconclusive or reveals a conceptually weak reject;
- whether the source lineage clusters around a narrow regime that does not generalize.

## Revisit Condition

Revisit only if all of the following remain true:
- larger replay base is available;
- ruleset logic is unchanged;
- replay is repeated as evidence expansion, not local tuning;
- the purpose is archival reassessment, not positive reinterpretation.

## Relationship to Project Verdicts

This note is subordinate to project-level findings and does not replace them.

Direct relationships:
- `research/verdicts/2026-03_first_project_verdict.md`
- `research/findings/2026-03_transition_replay_reject_to_fe0.md`
- `research/findings/2026-03_reclaim_context_asymmetry_phase_conditioned.md`

Project-level conclusion remains unchanged: multi-day accumulation can restore replayability, but it has not established promotable edge. This rule-level note isolates one replayed ruleset inside that broader project verdict.

Among the two replayed rulesets in this follow-up,  
`RULESET_REPORT_SETUPTYPE_FAILED_BREAK_RECLAIM_LONG_V1_LONG_BASE`
was the more informative rejection case.

It remained a REJECT and did not demonstrate edge,
but unlike the direction-only long ruleset (`trade_count=0`),
it produced a non-zero replay surface (`trade_count=6`).
For project discipline, this means it should not be interpreted as a positive candidate,
but it also should not be collapsed into the same bucket as a dead reject.
It is better treated as a replayed-but-inconclusive archival candidate,
worth future re-evaluation on a larger evidence base without changing its logic.