# SHI RESET 38E Price Reference Semantics Summary

Research-only audit of whether 38A/38D price reference fields were incorrectly treated as tradable entry prices.

## Primary Finding

For `2026-06-25T11:59:00Z` `SUPPLY_SWEEP_RECLAIM_DOWN_SETUP`:

- 38D `entry_reference_level`: `59628.3709`
- Actual M1 setup row:
  - Open: `61239.10`
  - High: `61249.70`
  - Low: `61234.20`
  - Close: `61244.70`
  - VWAP: `61240.04`
- H1 source window `2026-06-25T11:00:00Z -> 2026-06-25T11:59:00Z`:
  - Open: `61257.0`
  - High: `61395.3`
  - Low: `61033.5`
  - Close: `61244.7`
- `59628.3709` was not inside the setup M1 bar range.
- `59628.3709` was not inside the source H1 range.
- `59628.3709` was inside the later `08:00 -> 15:00` episode range and was first touched after setup at `2026-06-25T13:47:00Z`.

Therefore `59628.3709` must not be treated as a tradable entry price.

## Semantics

- `entry_reference_level` is misnamed or semantically overloaded.
- In this affected row it behaves like a lower reference / target-side structure level, not an executable setup entry anchor.
- `61395.3` is the H1/source-window high. It is useful context, but it is not necessarily a structural swing stop without a separate swing-stop resolver.

## Policy Replay Impact

- Existing 38D R-style interpretation for this affected row is invalid until price-reference semantics are fixed.
- Future policy replay must use actual setup price, setup-bar close/VWAP, or an explicit trigger price as the entry anchor.
- Stop references must be typed separately, for example `SOURCE_WINDOW_HIGH_CONTEXT`, `CONFIRMED_SWING_HIGH`, or `STRUCTURAL_INVALIDATION_LEVEL`.

## Governance

- Sample expansion: false
- Setup detection changed: false
- Setup Builder changed: false
- Backtester execution logic added: false
- Executor added: false
- Orders / entries / exits / PnL / position sizing added: false
- Live-readiness / strategy promotion: false

## Verdict

SHI_RESET_38E_PRICE_REFERENCE_SEMANTICS_AUDIT_V0_CREATED
