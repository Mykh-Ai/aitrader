# NEXT TASK: SELECT THE NEXT POST-39A MONITOR PROMOTION

## Canonical base — 2026-09-26

New Market Monitor work, including 39B/39C, MUST start from `canonical/market-monitor-39a`.
Do not start from old `main`, named 39A, or 38G. Follow `docs/CANONICAL_BASE.md`
and verify canonical ancestry before editing. Branch audit: `research/canonical/CANONICAL_BRANCH_AUDIT_2026_09_26.md`.
This base decision does not promote research into trading or live readiness.

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

## Separate user-scoped experiment — 2026-10-11

Peak_Ai delta-triggered H1 implementation is isolated from the canonical promotion backlog. Review its implementation audit and run evidence before interpreting results; no automatic promotion follows.

Peak_Ai delta-H1 v1 historical run completed: 210 simulated closed portfolio trades, net -1242.08 USDC; negative research result. Evidence: `market_monitor_runs/PEAK_AI_DELTA_H1_V1_v0/SUMMARY.md`. Review sequence semantics; no live promotion.

## 2026-10-11 — Correction: both delta signs trigger the same H1 SHORT setup

The prior Peak_Ai H1 v1 excluded negative deltas and was incomplete for the user's intended hypothesis. Correction audit: `research/canonical/PEAK_AI_H1_BOTH_SIGNS_CORRECTION_AUDIT_2026_10_11.md`. Both signs share the same SHORT rule, pending state and portfolio. Replay implementation: `33f1cd9`; native adapter unchanged. Corrected historical run completed: 226 closed simulated SHORT trades, net -1401.95 USDC; positive group -995.77 and negative group -406.18 USDC. Both groups negative. Evidence: `market_monitor_runs/PEAK_AI_H1_BOTH_SIGNS_V2/SUMMARY.md`. No live promotion.
