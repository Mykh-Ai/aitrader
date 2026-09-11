# NEXT TASK: SELECT THE NEXT POST-39A MONITOR PROMOTION

## Status

The 39A review is complete. On 2026-09-11, one bounded promotion added the
stateful v39A snapshot used as descriptive entry-time evidence by Executor's
LLM Trade Judge. It did not implement the unified level lifecycle, sweep
classifier, setup policy, trade management, or PnL logic.

## Review Set

- `research/canonical/SHI_RESET_39A_MASTER_RESEARCH_TO_MONITOR_ALIGNMENT_AUDIT_2026_07_02.md`
- `research/canonical/SHI_RESET_39A_CONTROL_CASE_LEDGER_2026_07_02.csv`
- `research/canonical/SHI_RESET_39A_RESEARCH_TO_CODE_DECISION_MATRIX_2026_07_02.csv`
- `docs/SHI_MARKET_MONITOR_TERMINOLOGY_AND_EVENT_LIFECYCLE.md`
- `docs/SHI_MARKET_MONITOR_KNOWN_GAPS_AND_NEXT_PROMOTIONS.md`

## Selection Questions

- Which one remaining gap has enough control cases for a bounded implementation?
- What causal acceptance evidence will distinguish useful context from extra prompt volume?
- How will the change preserve closed-candle cutoff, lineage, and state continuity?
- Which replay or offline dataset will test usefulness before any trading-policy change?

## Candidate Next Step

Select at most one item from the documented post-39A backlog. The leading
candidate remains a unified level lifecycle and next-1-3-H1 sequence classifier,
but it requires an explicit task and control cases before implementation.

## Boundary

Research-only. The deployed v39A snapshot is descriptive LLM evidence, not an
edge claim or authority over orders, live trading, PnL, position sizing, stops,
targets, or trailing.
