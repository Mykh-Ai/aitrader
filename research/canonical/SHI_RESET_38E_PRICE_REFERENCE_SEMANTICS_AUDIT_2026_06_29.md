# SHI RESET 38E Price Reference Semantics Audit

Scope: research-only audit. No sample expansion, no setup detection changes, no Setup Builder changes, no Backtester execution logic, no Executor, no orders, no entries/exits, no PnL, no position sizing, no live-readiness, and no strategy promotion.

Output root: `market_monitor_runs/SHI_RESET_38E_price_reference_semantics_audit_v0`

Required outputs:

- `price_reference_semantics_audit.csv`
- `price_reference_semantics_summary.md`

## Primary Finding Verified

Affected setup:

- `setup_id`: `setup_000006`
- `setup_formed_at`: `2026-06-25T11:59:00Z`
- `setup_type`: `SUPPLY_SWEEP_RECLAIM_DOWN_SETUP`
- `sequence_role`: `CORRECTION_END_ENTRY_SETUP`
- 38D `entry_reference_level`: `59628.3709`

Actual M1 feed row at setup time:

- Open: `61239.10`
- High: `61249.70`
- Low: `61234.20`
- Close: `61244.70`
- VWAP: `61240.04`

H1 source window `2026-06-25T11:00:00Z -> 2026-06-25T11:59:00Z`:

- Open: `61257.0`
- High: `61395.3`
- Low: `61033.5`
- Close: `61244.7`

Checks:

- `59628.3709` touched in setup M1 bar: `false`
- `59628.3709` touched in source H1 window: `false`
- `59628.3709` touched after setup: `true`
- First later touch: `2026-06-25T13:47:00Z`
- `59628.3709` was inside later `08:00 -> 15:00` episode range: `true`

## Interpretation

`59628.3709` was not tradable at setup formation. It was not inside the setup M1 range and not inside the 11:00-11:59 source-window range. Therefore the field named `entry_reference_level` is misnamed or semantically overloaded.

For this affected row, the level behaves as a lower reference / target-side structure level, not an actual entry anchor.

## Stop Reference Note

`61395.3` is the H1/source-window high. It can be used as context, but it must not automatically be treated as a structural swing stop. A future policy replay needs explicit stop-reference typing, for example:

- `SOURCE_WINDOW_HIGH_CONTEXT`
- `CONFIRMED_SWING_HIGH`
- `STRUCTURAL_INVALIDATION_LEVEL`

## Required Conclusions

1. `entry_reference_level` is misnamed or semantically overloaded.
2. For `2026-06-25T11:59Z`, `59628.3709` is not a tradable entry price.
3. `61395.3` is the H1/source-window high, not necessarily structural swing stop.
4. Future policy replay must use actual setup price or explicit trigger price as entry anchor.
5. Existing 38D R-style interpretation for affected rows must be marked invalid until price references are fixed.

## Impact On 38D

The 38D row for this setup used:

- `policy_name`: `SWING_STOP_POLICY`
- `entry_reference_level`: `59628.3709`
- `policy_invalidation_reference`: `61395.3`
- `policy_outcome_label`: `SWING_STOP_INVALIDATION`

Because the entry anchor was not a tradable setup-time price, the R-style interpretation for this row is invalid. The descriptive path facts remain useful, but the policy result must not be treated as a management result until entry-reference semantics are fixed.

## Governance Check

- Sample expansion: false
- Setup detection changed: false
- Setup Builder changed: false
- Backtester execution logic added: false
- Executor added: false
- Orders added: false
- Entries/exits added: false
- PnL added: false
- Position sizing added: false
- Live-readiness added: false
- Strategy promotion added: false

## Verdict

SHI_RESET_38E_PRICE_REFERENCE_SEMANTICS_AUDIT_V0_CREATED
