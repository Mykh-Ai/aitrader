# Same-Bar Ambiguity Report

Candidate: `CAND_LONG_IMPULSE_FADE_LATE_US_STRUCTURAL`

Status: `FAIL / NOT_EVALUATED_FOR_PROMOTION`

The long watchlist source is a sidecar diagnostic and does not expose same-bar collision or target/stop ordering fields. One primary-selector row is unresolved and has no `TradeReturnPct`.

Aggregate recovered Backtester replay uses `SAME_BAR_CONSERVATIVE_V0_1`, but this watch candidate is not an official Phase 3 mapping.

Required next action: continue watch unchanged, then replay only after a formal frozen mapping exists and same-bar ambiguity can be measured directly.

