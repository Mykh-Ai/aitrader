# H4 False-Break/Reclaim Research Contract v0.1

Status: research contract, not live execution design.

## Purpose

This contract freezes the intended H4 false-break/reclaim research semantics after
the Analyzer lifecycle audit.

It exists to prevent the future H4 setup class from inheriting legacy Analyzer
micro-lifecycle defaults or replay defaults by accident.

## Lifecycle Boundary

Analyzer `LifecycleStatus`, `InvalidatedAt`, and `ExpiredAt` are setup research
metadata. They are not trade expiry, not replay holding-period policy, and not a
silent replay gate for the H4 false-break/reclaim setup class.

`SETUP_TTL_BARS = 12` remains unchanged globally. In the current Analyzer baseline
it is the legacy diagnostic setup lifecycle window, counted in raw 1m bars.

## Quarantine Boundary

`FAILED_BREAK_RECLAIM_EXTENDED_V1` remains quarantined for the intended H4
false-break/reclaim setup class. It must not be used as evidence for
`H4_ACTIVE_LEVEL_RECLAIM_V1`.

Reason: the historical variant uses raw-bar timing assumptions that do not encode
the intended H4 active-level lifecycle contract.

## H4_ACTIVE_LEVEL_RECLAIM_V1 Contract

Future `H4_ACTIVE_LEVEL_RECLAIM_V1` rulesets must declare:

| Field | Value |
|---|---|
| `active_level_ttl_value` | `30` |
| `active_level_ttl_unit` | `H4_BARS` |
| `trade_expiry_model` | `BARS_AFTER_ACTIVATION:5760` |
| `stop_model` | `SWEEP_EXTREME_HARD_STOP` |

`REFERENCE_LEVEL_HARD_STOP` is forbidden as an evidence model for H4
false-break/reclaim. If sweep extremes are unavailable, the run must fail loudly
rather than fall back to `ReferenceLevel`.

## Replay Guard

Ruleset validation must reject `H4_ACTIVE_LEVEL_RECLAIM_V1` when:

- `expiry_model = BARS_AFTER_ACTIVATION:12`
- `expiry_model` differs from `BARS_AFTER_ACTIVATION:5760`
- `stop_model = REFERENCE_LEVEL_HARD_STOP`
- `stop_model` differs from `SWEEP_EXTREME_HARD_STOP`

This guard is a contract check only. It does not run a backtest and does not make
claims about field performance.
