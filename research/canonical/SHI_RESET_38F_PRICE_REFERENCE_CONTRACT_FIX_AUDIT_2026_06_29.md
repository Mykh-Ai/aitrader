# SHI RESET 38F Price Reference Contract Fix Audit

Scope: price reference contract fix in replay/review layers. This change does not modify setup detection logic, does not change setup selection rules, and does not add Backtester execution logic, Executor logic, orders, entries/exits, PnL, position sizing, live-readiness, or strategy promotion.

## Files Changed

- `market_monitor/setup_builder.py`
- `market_monitor/setup_replay_validation.py`
- `market_monitor/armed_setup_review_pack.py`

## Contract Change

- `setup_reference_level` = structural/reference level emitted by Setup Builder.
- `actual_setup_price` = actual M1 feed price at `setup_formed_at`.
- `tradable_entry_anchor` = price anchor used by replay MFE/MAE calculations.
- `target_reference` = target/zone reference.
- `stop_reference` = invalidation/stop reference.
- `entry_reference_level` remains only as a deprecated compatibility alias where needed for older outputs/tests.

The key correction is that structural reference levels are no longer treated as tradable entry anchors in replay/review calculations.

## Primary Fixed Case

Affected setup:

- `setup_formed_at`: `2026-06-25T11:59:00Z`
- `setup_type`: `SUPPLY_SWEEP_RECLAIM_DOWN_SETUP`
- Old `entry_reference_level` / new `setup_reference_level`: `59628.3709`
- `actual_setup_price`: `61244.7`
- `tradable_entry_anchor`: `61244.7`
- `stop_reference`: `61286.628`
- `target_reference`: `zone_000102:SELL_SIDE:59500.93465-59560.46535`

This fixes the 38E finding: `59628.3709` was not inside the setup M1 bar or source H1 window, so it must not be treated as a tradable entry price.

## Verification

- Focused tests: `12 passed`
- Full suite: `688 passed, 11 warnings`
- Sample expansion: false
- Setup detection changes: false
- Regenerated 38A replay artifacts: true
- Regenerated 38B manual-review artifacts and chart data: true

Manual CSV check for `2026-06-25T11:59:00Z` confirmed:

- `setup_reference_level = 59628.3709`
- `actual_setup_price = 61244.7`
- `tradable_entry_anchor = 61244.7`

## Grep Check

`entry_reference_level` remains only as a deprecated alias/backward-compatibility field. Replay MFE/MAE now uses `tradable_entry_anchor`, which is derived from actual M1 setup price when available.

## Governance

- Backtester used: false
- Executor used: false
- Orders used: false
- Entries/exits used: false
- PnL used: false
- Position sizing used: false
- Live-readiness claim: false
- Strategy promotion: false

## Verdict

SHI_RESET_38F_PRICE_REFERENCE_CONTRACT_FIX_AUDIT_V0_CREATED
