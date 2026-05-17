# Same-Bar Ambiguity Report

Candidate: `CAND_SHORT_IMPULSE_FADE_DEEP_RECLAIM_GT_0_6`

Status: `FAIL / NOT_EVALUATED_FOR_PROMOTION`

The candidate source is a sidecar diagnostic slice. The candidate-level source files do not expose same-bar collision or target/stop ordering fields.

Aggregate recovered Backtester replay uses `SAME_BAR_CONSERVATIVE_V0_1`, but this candidate is not yet materialized as an official Phase 3 mapping. Therefore same-bar ambiguity is not cleared for promotion.

Required next action: build a frozen candidate replay output that includes same-bar collision/ordering fields or an explicit statement that no same-bar target/stop ambiguity exists under the conservative policy.

