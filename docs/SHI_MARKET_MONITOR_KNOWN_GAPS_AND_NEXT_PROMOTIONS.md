# SHI Market Monitor Known Gaps And Next Promotions

Status: post-review backlog after SHI_RESET_39A

The 39A master audit was reviewed before the bounded v39A snapshot promotion on 2026-09-11. The items below remain unimplemented backlog and are not edge or live-readiness claims.

## Promotion Order

| Priority | Promotion candidate | Current gap | Acceptance evidence required before implementation |
| --- | --- | --- | --- |
| 1 | Level lifecycle memory | Zone registry has substantial memory, but no single per-level state machine is consumed by setup_builder from formation through invalidation. | Written transition table, deterministic timestamps, closed-candle semantics, de-duplication rules, and explicit mapping from existing registry fields. |
| 2 | Sweep sequence classifier using the next 1-3 H1 candles | Penetration and close-back subsets exist, but one canonical `touch -> penetration -> candidate -> final classification` engine does not. | Control cases for confirmed reclaim, accepted break, unresolved expiry, and noise; no one-case tuning. |
| 3 | Counter-sweep invalidation | The opposing sequence can invalidate a directional setup in manual review, but current code has no canonical transition. | Both-direction examples, ordering rules, same-window conflict policy, and a fail-closed result. |
| 4 | Accepted break versus reclaim classifier | Acceptance metrics and reclaim detection live in separate layers. | Explicit H1 close count/window, boundary semantics, accepted-break and reclaim controls, and state carry-forward. |
| 5 | Support/resistance blocker for setup_builder | setup_builder can emit a context near opposing structure that is not visible in selected_zones. | Full-inventory query contract, direction symmetry, distance semantics, and controls for `SHORT_INTO_MAJOR_SUPPORT` / `LONG_INTO_MAJOR_RESISTANCE`. |
| 6 | Target resolver using market_structure_levels | Current resolver searches visible selected zones and returns unresolved when no directional zone exists. | Directional full-level query, level eligibility/lifecycle filters, deterministic nearest valid target, and unresolved behavior. |
| 7 | LAST_WAGON / last-wagon prior-move maturity | No code measures how mature the preceding move is or how little clean space remains. | Distance, duration, impulse, opposing-structure space, and multiple positive/negative controls. |
| 8 | Minimum structural risk / meaningful R validation | Small risk can make TP1 mechanically easy without proving structural quality. | Risk anchored to valid structure, BTC-distance and volatility context, target geometry, and separation from outcome labels. |
| 9 | Local sequence direction override versus broad market state | Broad `market_state` can conflict with a newer local failed-break/reclaim sequence. | Bounded precedence rules, confidence thresholds, countertrend flagging, and fail-closed ambiguity. |

## Constraints For Any Future Promotion

- Start from the 39A terminology and evidence classes.
- Do not source candidates from the 38S 227-row discovery stream.
- Do not treat 38T/38U post-generation labels as ready-made filters.
- Regenerate 38V/38W lineage after current target-resolution semantics before using old target fields.
- Preserve chronological stop/TP1 ordering from reusable policy code and 38W1 evidence.
- Keep recovered/degraded provenance explicit.
- Add code and tests only in the separately reviewed promotion task.
- Do not activate old Analyzer, old Backtester, Executor, orders, PnL, position sizing, or live-readiness.

## Review Gate

The next project action is review of:

- `research/canonical/SHI_RESET_39A_MASTER_RESEARCH_TO_MONITOR_ALIGNMENT_AUDIT_2026_07_02.md`;
- `research/canonical/SHI_RESET_39A_CONTROL_CASE_LEDGER_2026_07_02.csv`;
- `research/canonical/SHI_RESET_39A_RESEARCH_TO_CODE_DECISION_MATRIX_2026_07_02.csv`;
- `docs/SHI_MARKET_MONITOR_TERMINOLOGY_AND_EVENT_LIFECYCLE.md`;
- this backlog.

For each additional promotion, select one narrow item and scope it separately with causal control cases.
