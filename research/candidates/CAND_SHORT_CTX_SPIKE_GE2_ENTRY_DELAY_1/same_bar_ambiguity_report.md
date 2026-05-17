# Same-Bar Ambiguity Report

Candidate: `CAND_SHORT_CTX_SPIKE_GE2_ENTRY_DELAY_1`

Status: `FAIL / NOT_EVALUATED_FOR_PROMOTION`

The timing diagnostic source includes trade outcomes and holding bars but does not expose same-bar collision or target/stop ordering fields for the frozen `entry_delay_1` candidate.

Aggregate recovered Backtester replay uses `SAME_BAR_CONSERVATIVE_V0_1`, but this candidate still needs true-holdout replay with explicit same-bar ambiguity accounting.

Required next action: true-holdout replay must emit same-bar collision/ordering diagnostics before this candidate can enter Phase 4 review.

