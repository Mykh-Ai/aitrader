# SHI RESET 37I Hidden-Flow Candidate Promotion Audit

Verdict: CANDIDATE_MODEL_MAPPED_BEFORE_SETUP_BUILDER

Scope: research-only audit of the existing hidden-flow candidate generation and promotion model. No Setup Builder is added here. No production execution logic, Backtester, Executor, orders, entries, exits, PnL, live-readiness, strategy promotion, or trading advice is introduced.

## Files Inspected

- `market_monitor/hidden_flow_research.py`
- Recent generated artifacts from:
  - `market_monitor_runs/SHI_RESET_37H_pre_0326_0900_monitor_view_audit_v0/hidden_flow_asof_0900`
  - `market_monitor_runs/SHI_RESET_37F_real_date_regime_validation_v0`
  - `market_monitor_runs/SHI_RESET_37E_live_sim_2026_06_02_0400`

## Existing Model Map

The hidden-flow model has three distinct layers:

1. Raw regime windows: written to `market_regime_windows.csv`.
2. Promoted hidden-flow candidates: written to `hidden_flow_candidates.csv`.
3. Future labels: written to `hidden_flow_future_labels.csv` and marked evaluation-only.

The manifest explicitly declares:

- `detection_features_use_future_data=false`
- `episode_context_uses_future_data=false`
- `future_labels_evaluation_only=true`
- `low_confidence_windows_retained_in_regime_csv=true`

## Raw Window Labeling

Each window is scored and assigned a `candidate_label`, `confidence`, `candidate_score`, and evidence fields. Raw labels include more than the promoted set:

- `HIDDEN_DISTRIBUTION_DOWN_CANDIDATE`
- `SELLER_ABSORPTION_CANDIDATE`
- `BUYER_ABSORPTION_CANDIDATE`
- `HIDDEN_ACCUMULATION_UP_CANDIDATE`
- `DOWNTREND_EXHAUSTION_CANDIDATE`
- `UPTREND_EXHAUSTION_CANDIDATE`
- `COMPRESSION_BEFORE_EXPANSION_CANDIDATE`
- `NORMALIZATION_AFTER_MARKDOWN`
- `NORMALIZATION_AFTER_MARKUP`
- `UNCLEAR_FLOW_ANOMALY`

Important behavior: raw windows are descriptive context, not automatically review candidates.

## First Promotion Gate

Before a raw window can enter `hidden_flow_candidates.csv`, it must satisfy a broad numeric mask:

- `pressure_without_progress_score >= 48`
- `price_progress_score >= 35`
- at least one of:
  - `zone_hold_score >= 20`
  - `compression_score >= 35`
  - `high_volume_low_range_score >= 65`

This means state-level context can be strong while no hidden-flow candidate is produced if the raw hidden-flow window does not meet this pressure/progress/zone-compression shape.

## Review Label Gate

The direct review label allowlist is narrow:

- `COMPRESSION_BEFORE_EXPANSION_CANDIDATE`
- `HIDDEN_DISTRIBUTION_DOWN_CANDIDATE`
- `SELLER_ABSORPTION_CANDIDATE`

The review confidence tier is also narrow:

- `HIGH`

Explicitly excluded:

- `UNCLEAR_FLOW_ANOMALY`

Consequence: bullish or countertrend raw labels such as `BUYER_ABSORPTION_CANDIDATE`, `HIDDEN_ACCUMULATION_UP_CANDIDATE`, and `DOWNTREND_EXHAUSTION_CANDIDATE` can be present in `market_regime_windows.csv` but are not direct promoted review labels.

## Linked Compression Exception

There is one promotion exception for compression:

- label must be `COMPRESSION_BEFORE_EXPANSION_CANDIDATE`
- confidence must be `HIGH` or `MEDIUM`
- trend direction must be `RANGE`
- nearest zone side must be `BUY_SIDE`
- zone context must be one of `inside_zone`, `near_upper_zone`, `between_zones`
- it must link to a prior `HIDDEN_DISTRIBUTION_DOWN_CANDIDATE` within the 72-hour lookback
- the prior distribution row must be `HIGH` confidence, `BUY_SIDE`, and in one of the same episode zone contexts

Consequence: compression near lower-side demand or seller-side zones is retained as raw context but generally not promoted through this linked-compression path.

## Episode Context Gate

After initial selection, candidates are enriched with 1D/3D/7D context reads. The current context read uses:

- `price_change_pct`
- `range_pct`
- `close_position`
- `delta_pct`

Episode review state is stricter than initial selection:

- Non-linked `HIDDEN_DISTRIBUTION_DOWN_CANDIDATE` becomes `CONTEXT_ONLY`.
- Non-linked unresolved candidates become `HIDE_UNRESOLVED`.
- Linked compression with unresolved episode read becomes `HIDE_UNRESOLVED`.
- Only linked compression with a resolved episode read becomes `PROMOTE`.

Visibility is then assigned only to `episode_review_state=PROMOTE`, grouped by linked prior window and episode read, capped at 20 visible rows.

Important consequence: a row can exist in `hidden_flow_candidates.csv` but still have `visible_for_review=false`. A row can also be strong in `market_regime_windows.csv` and never appear in `hidden_flow_candidates.csv`.

## Future Label Boundary

Future labels are generated only after candidates exist. They evaluate future windows and false-positive flags, but the manifest and function order keep them outside detection and episode context.

Audit conclusion: the future-label path is not the reason 2026-03-26 or 2026-06-02 produced no promoted candidates. The limiting behavior is the candidate promotion and episode gates before future labels are built.

## Observed Case Impact

### 2026-03-26T09:00Z

The state layer showed seller-dominant context:

- `PULLBACK_RETEST_INSIDE_MAJOR_RESISTANCE`
- `dominant_side=SELLER`
- `seller_pressure_score=93.3`
- `buyer_response_score=5.7`
- `price_change_pct=-1.830115`
- `delta_pct=-6.420618`
- `close_position=0.1562`

Hidden-flow result:

- `hidden_flow_candidates.csv` was empty.
- `market_regime_windows.csv` contained 36 primary-window raw rows.
- Raw labels included `UNCLEAR_FLOW_ANOMALY`, `COMPRESSION_BEFORE_EXPANSION_CANDIDATE`, `DOWNTREND_EXHAUSTION_CANDIDATE`, `NORMALIZATION_AFTER_MARKDOWN`, and `NORMALIZATION_AFTER_MARKUP`.

Why no promoted candidate:

- The strongest raw countertrend/exhaustion label is not in the allowed review label set.
- Seller-dominant state context is not an input to hidden-flow promotion.
- The linked-compression exception is upper-zone distribution-to-compression specific and does not cover this seller-dominant state row.

### 2026-06-01 -> 2026-06-02T04:00Z

The state layer showed relevant context before cutoff:

- 2026-06-01: `MARKDOWN_ABOVE_SUPPORT`, `candidate_bias=DOWN`, `candidate_strength=HIGH`, `dominant_side=SELLER`.
- 2026-06-02 00:00-04:00: `CONTEXT_BELOW_RESISTANCE`, `candidate_bias=MIXED`, `candidate_strength=LOW`, `dominant_side=MIXED`.

Hidden-flow result:

- No promoted hidden-flow candidate inside the primary cutoff window.
- A promoted compression candidate existed before the context window, ending 2026-05-31T13:59:00Z, but not inside the primary 2026-06-01T00:00:00Z -> 2026-06-02T04:00:00Z window.

Why no primary-window promoted candidate:

- The hidden-flow promotion model is not state-context aware.
- Strong seller-dominant state rows do not create candidates unless hidden-flow raw windows independently satisfy promotion labels and episode rules.

## Model Strengths

- Clear separation between raw windows, candidates, and future labels.
- Future-label evaluation is not used for detection.
- Candidate labels avoid execution words and remain descriptive.
- Low-confidence and unclear windows are retained in `market_regime_windows.csv` for audit.
- The current promotion model is conservative and avoids promoting ambiguous flow.

## Model Gaps Relevant To Setup Builder

1. State context is not part of hidden-flow promotion.

   Market Structure State can identify seller dominance, failed continuation, markdown, or pullback/retest conditions, but these rows do not influence `hidden_flow_candidates.csv`.

2. Raw bullish/countertrend evidence is demoted.

   `BUYER_ABSORPTION_CANDIDATE`, `HIDDEN_ACCUMULATION_UP_CANDIDATE`, and `DOWNTREND_EXHAUSTION_CANDIDATE` can be raw labels but are not allowed direct review labels.

3. Raw seller-dominance continuation is not a setup candidate.

   `NORMALIZATION_AFTER_MARKDOWN` and seller-dominant state rows are context, not promoted hidden-flow candidates.

4. Linked compression is asymmetric.

   The linked-compression exception is oriented around `BUY_SIDE` upper-zone distribution-to-compression chains. It does not generalize to lower-zone demand reclaim, seller-dominance retest, or markdown continuation context.

5. `visible_for_review` is episode-chain gated.

   A candidate can be selected but hidden unless it becomes a promoted episode chain. This is appropriate for the current hidden-flow research model, but it means `hidden_flow_candidates.csv` is not a complete list of research review contexts.

## Implication For 37I Setup Builder Design

A Setup Builder should not replace hidden-flow promotion. It should sit downstream of existing artifacts and consume:

- Market Structure State rows as context.
- Raw `market_regime_windows.csv` rows as supporting flow evidence.
- Visible liquidity zones as level references.

It should create separate research-only setup candidates only when context plus level behavior plus raw-window evidence align. It must not reuse `hidden_flow_candidates.csv` emptiness as proof that no setup context existed.

Required separation for future implementation:

- Context: market state and raw hidden-flow evidence.
- Setup: replayable research candidate row.
- Trigger: research-only activation condition, not a live signal.
- Invalidation: descriptive level or condition for replay evaluation.
- Target reference: next relevant zone for future evaluation.

## Guardrails Before Implementation

- Do not modify hidden-flow promotion rules until a separate change request explicitly asks for that.
- Do not make Setup Builder depend only on `hidden_flow_candidates.csv`; it must inspect raw `market_regime_windows.csv`.
- Do not use future labels for setup detection.
- Do not output execution-like labels such as `OPEN_LONG`, `OPEN_SHORT`, `BUY_NOW`, `SELL_NOW`, `ENTRY_SIGNAL`, or `EXIT_SIGNAL`.
- Keep output language as `setup candidate` and `research-only trigger`.
- Keep Backtester, Executor, entries, exits, PnL, and live-readiness out of scope.
