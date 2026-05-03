# Reject Decomposition Audit

Generated: 2026-05-03
Source CSV: `research/results/reject_decomposition_audit_2026-05-03.csv`

## Summary

- Rows audited: 169
- Backtest runs: 35
- Derived runs: 10

## Promotion Decisions

- `REJECT`: 169

## Reject Classes

- `DEAD_REJECT`: 32
- `LIVE_BUT_NEGATIVE`: 39
- `LIVE_BUT_UNSTABLE`: 48
- `LIVE_UNRESOLVED_NO_RETURN`: 8
- `NO_RESOLVED_TRADES`: 36
- `VALIDATION_GATE_FAIL`: 6

## Directions

- `BOTH`: 26
- `LONG`: 6
- `NA`: 134
- `SHORT`: 3

## Scope Mix

- `ALL_TRADES`: 67
- `RESOLVED_ONLY`: 67
- `RULESET_REPORT_SETUPTYPE_FAILED_BREAK_RECLAIM_LONG_V1_LONG_BASE`: 6
- `RULESET_REPORT_SETUPTYPE_FAILED_BREAK_RECLAIM_SHORT_V1_SHORT_BASE`: 3
- `RULESET_REPORT_SETUPTYPE_IMPULSE_FADE_RECLAIM_LONG_V1_V1_BOTH_BASE`: 15
- `RULESET_REPORT_SETUPTYPE_IMPULSE_FADE_RECLAIM_SHORT_V1_V1_BOTH_BASE`: 11

## Ruleset-Scope Read

Ruleset-specific rows are more informative than aggregate `ALL_TRADES` /
`RESOLVED_ONLY` rows for deciding what failed.

Across ruleset scopes:
- `LIVE_BUT_UNSTABLE`: 16
- `LIVE_BUT_NEGATIVE`: 13
- `LIVE_UNRESOLVED_NO_RETURN`: 4
- `VALIDATION_GATE_FAIL`: 2

Direction / class split across ruleset scopes:
- `BOTH, LIVE_BUT_NEGATIVE`: 12
- `BOTH, LIVE_BUT_UNSTABLE`: 12
- `BOTH, VALIDATION_GATE_FAIL`: 2
- `LONG, LIVE_BUT_NEGATIVE`: 1
- `LONG, LIVE_BUT_UNSTABLE`: 2
- `LONG, LIVE_UNRESOLVED_NO_RETURN`: 3
- `SHORT, LIVE_BUT_UNSTABLE`: 2
- `SHORT, LIVE_UNRESOLVED_NO_RETURN`: 1

For the latest routine window (`2026-04-10 -> 2026-04-23`), ruleset-specific
rows show:
- `LIVE_BUT_NEGATIVE`: 7
- `LIVE_BUT_UNSTABLE`: 6
- `VALIDATION_GATE_FAIL`: 1

There are no ruleset-scope `DEAD_REJECT` rows in that latest routine window.
That matters: the broad H1/H2 reclaim families are not merely empty; they
produce trades, but the replay surface is either negative, unstable/fragile, or
blocked by validation gates.

## Interpretation

This audit does not support closing H1 as a dead signal. It also does not
support promoting or tuning broad H1.

The dominant failure mode is live-but-failing surface:
- some runs are live but negative;
- some runs have positive mean return but fail robustness as `UNSTABLE` or
  `FRAGILE`;
- a smaller number pass return direction superficially but fail validation,
  especially source concentration.

This means the next research question is not "does replay ever create trades?"
It does. The next question is whether the live surface is too mixed, too small,
or structurally mis-specified by current formalization / placement / validation.

The short-side high-stress / multi-spike reclaim surface remains relevant, but
it should be treated as a conditional follow-up, not as an immediate ruleset
change. A parameterized filter experiment is justified only if a targeted
diagnostic can show that it isolates the live-but-failing surface rather than
just fitting noise.

## Decision

Do not tune broad H1 parameters yet.

Proceed to a targeted SHORT reclaim context diagnostic only as a diagnostic
follow-up, with pre-registered filters and no optimizer search:
- SHORT only
- failed-break/reclaim family only
- high-stress all 3 >= median
- >=2 context spikes active
- `AbsorptionScore_v1` high / low
- liquidation spike if available

## Interpretation Guardrails

- This audit classifies existing replay artifacts only.
- It does not tune parameters and does not create a new ruleset.
- `LIVE_UNRESOLVED_NO_RETURN` means trades exist but resolved return evidence is absent.
- A filter experiment should only follow if non-zero surfaces are visible and the failure mode is not simply dead/no-sample.
