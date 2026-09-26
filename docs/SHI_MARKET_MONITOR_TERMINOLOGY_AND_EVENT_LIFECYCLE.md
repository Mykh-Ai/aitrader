# SHI Market Monitor Terminology And Event Lifecycle

Status: canonical terminology target after SHI_RESET_39A

This document defines research terminology. It does not claim that every term is implemented in current code. Current implementation status is stated explicitly.

## Governing Rule

A sweep is a sequence, not a candle.

The first candle can show a touch or penetration. It cannot by itself decide whether the market rejected the level, accepted beyond it, reversed through a counter-sweep, or merely produced local noise. Final classification uses subsequent closed candles, normally the next 1-3 H1 candles for the current research contract.

## Lifecycle Terms

| Term | Definition | Current status |
| --- | --- | --- |
| `LEVEL_TOUCH` | Price reaches a level/zone boundary without a meaningful excursion through the far side. A touch is interaction evidence, not a setup. | Partial equivalent `LIQUIDITY_ZONE_TOUCHED` is `CODE_CONFIRMED`. |
| `LEVEL_PENETRATION` | Price trades meaningfully beyond the referenced boundary. It records geometry only; direction is not yet confirmed. | Crossed/unresolved observations are `CODE_CONFIRMED`; this canonical name is a 39A target term. |
| `SWEEP_CANDIDATE` | A level penetration that has sufficient reference, age, reaction, penetration, wick, or related evidence to enter a confirmation window. It is not yet a confirmed sweep. | Qualified-H1 preconditions are partially `CODE_CONFIRMED`; the exact lifecycle state is not unified. |
| `CONFIRMED_SWEEP_RECLAIM` | A sweep candidate followed by a close back through the level within the confirmation window, with the local sequence still directionally valid. | Close-back detection is `CODE_CONFIRMED`; counter-sweep-aware final classification is not implemented. |
| `FAILED_BREAK_RECLAIM` | A failed attempt to break/accept beyond a level, followed by a close back to the prior side. This is the structural interpretation of a confirmed reclaim; it still does not guarantee a setup. | Partial close-back subset is `CODE_CONFIRMED`. |
| `ACCEPTED_BREAKDOWN` | Price penetrates support and subsequent closed candles remain/accept below it instead of reclaiming. | Acceptance metrics exist in zone registry, but no unified setup-consumed classifier exists. |
| `ACCEPTED_BREAKOUT` | Price penetrates resistance and subsequent closed candles remain/accept above it instead of reclaiming. | Acceptance metrics and a broad builder context type exist, but no unified lifecycle classifier exists. |
| `COUNTER_SWEEP_INVALIDATION` | During the confirmation window, price sweeps the opposing side or produces an opposite failed-break sequence that invalidates or reverses the earlier directional setup interpretation. | `MANUAL_REVIEW_CONCLUSION`; not current reusable behavior. |
| `RETEST_REACTION` | After reclaim or accepted break, price revisits the level/zone and responds away from it. | Touch/reaction metrics exist; the unified lifecycle transition is partial. |
| `LEVEL_CONFIRMED_BY_REACTION` | Repeated, separated retest reactions increase confidence that the level is behaviorally meaningful. | `MANUAL_REVIEW_CONCLUSION`; registry counts exist but are not this builder gate. |
| `LEVEL_STRENGTHENED` | New valid reactions add evidence without acceptance through the level. Strength is contextual and must not grow from duplicate/noisy touches. | Not a unified current state; promotion candidate. |
| `LEVEL_WEAKENED` | Repeated penetrations, time spent through/inside, failed reactions, or consumption reduce confidence before final invalidation. | Consumption/chop metrics are partial `CODE_CONFIRMED`; unified state is missing. |
| `LEVEL_INVALIDATED` | The level is no longer valid for the intended directional role because acceptance, consumption, expiry, or a structurally contradictory transition has occurred. | Registry invalidation/expiry exists; setup-consumed lifecycle invalidation is partial. |

## Setup-Context Terms

| Term | Definition | Current status |
| --- | --- | --- |
| `LAST_WAGON` / `PRIOR_MOVE_MATURITY` | A candidate appears late after a material directional move, leaving limited clean distance before opposing structure or making continuation structurally mature. It must be measured from prior move distance, duration, and remaining space, not assigned from one visual impression. | `MANUAL_REVIEW_CONCLUSION`; not implemented. |
| `SHORT_INTO_MAJOR_SUPPORT` | A short context whose entry/review area is too close to meaningful support for the proposed risk/target path. The blocker must be checked against the full eligible structure inventory, not only visible snapshot zones. | Gap confirmed; blocker rule not implemented. |
| `LONG_INTO_MAJOR_RESISTANCE` | A long context whose entry/review area is too close to meaningful resistance for the proposed risk/target path. The blocker must be checked against the full eligible structure inventory, not only visible snapshot zones. | Gap confirmed; blocker rule not implemented. |

## Sequence Decision Model

1. `LEVEL_TOUCH`: record interaction.
2. `LEVEL_PENETRATION`: record excursion through the boundary.
3. `SWEEP_CANDIDATE`: open a bounded confirmation window only if reference and penetration quality are sufficient.
4. Inspect the next 1-3 closed H1 candles:
   - close back through the level with no counter invalidation -> `CONFIRMED_SWEEP_RECLAIM` / `FAILED_BREAK_RECLAIM`;
   - continued closes beyond support -> `ACCEPTED_BREAKDOWN`;
   - continued closes beyond resistance -> `ACCEPTED_BREAKOUT`;
   - opposing sequence inside the window -> `COUNTER_SWEEP_INVALIDATION`;
   - insufficient evidence -> remain unresolved or expire without setup promotion.
5. Later returns may create `RETEST_REACTION`, `LEVEL_CONFIRMED_BY_REACTION`, strengthening, weakening, or invalidation.

## Current Boundary

Current code implements pieces of this model across zone registry, event log, qualified H1 sweep/reclaim, setup_builder, and replay. It does not yet implement this document as one reusable lifecycle engine. Therefore these terms must not be backfilled into historical rows as if they were already emitted.
