# NEXT TASK: SHI_RESET_39A_REVIEW_GATE

## Status

39A is now the required review gate before any new Market Monitor code promotion.

Read first:

- `research/canonical/SHI_RESET_39A_MASTER_RESEARCH_TO_MONITOR_ALIGNMENT_AUDIT_2026_07_02.md`
- `research/canonical/SHI_RESET_39A_CONTROL_CASE_LEDGER_2026_07_02.csv`
- `research/canonical/SHI_RESET_39A_RESEARCH_TO_CODE_DECISION_MATRIX_2026_07_02.csv`
- `docs/SHI_MARKET_MONITOR_TERMINOLOGY_AND_EVENT_LIFECYCLE.md`
- `docs/SHI_MARKET_MONITOR_KNOWN_GAPS_AND_NEXT_PROMOTIONS.md`

## Gate

No new code promotion should happen until 39A is reviewed.

## Current boundaries

- Market Monitor is research infrastructure only.
- `setup_builder` remains a context candidate generator, not a final setup engine.
- Sweep must be redefined as a sequence/lifecycle event before new setup logic is added.
- 38S 227 rows remain discovery material, not candidates.
- 38W1-style corrected replay evidence remains replay evidence, not edge proof.
- Chat/manual conclusions are preserved separately from code-confirmed facts.

## Next possible promotion candidates after review

Documentation-only backlog, not implemented here:

- level lifecycle memory;
- sweep sequence classifier with next 1-3 H1 confirmation;
- counter-sweep invalidation;
- accepted break vs reclaim classifier;
- support/resistance blocker for setup_builder;
- target resolver using market_structure_levels, not only visible selected_zones;
- last-wagon by prior move distance/maturity;
- minimum structural risk / meaningful R validation;
- local sequence direction override versus broad market state.

## Hard prohibitions

No Executor. No live. No orders. No PnL. No position sizing. No old analyzer activation. No old backtester activation. No strategy/edge/live-readiness claims.
