# Corrected H1 SHORT campaign — both delta signs

Completed 2026-10-11. Every raw DELTA_MIN/MAX can trigger the same upper-zone,
four-hour closed-H1 reclaim SHORT. Shared episode state and one portfolio.
Implementation 33f1cd9; query orchestration cd12223. Native adapter unchanged.

2846 raw deltas: 1417 positive, 1429 negative. 1217 armed episodes;
516 unique confirmations, 515 inside the decision interval.
226 filled and closed simulated trades; 289 blocked by a current position;
zero unresolved. Notional 3000 USDC; decisions March20-August17, exits to August19.

| Seed sign | Closed | Wins | Losses | Net USDC | PF |
|---|---:|---:|---:|---:|---:|
| Positive |151|49|102|-995.7669685134326|0.5175772944577245|
| Negative |75|33|42|-406.1783297306376|0.6489802406871614|
| Total |226|82|144|-1401.94529824407|0.5647801149386551|

Gross -273.10202769999677; commission 1008.9479051284632; slippage 119.89536541561.
Doubled slippage net -1521.84066365968 USDC. Closed-equity DD 1441.5946205714176.
Independent overlapping opportunities: 515 closed, net -2612.7512592766957;
positive -2157.5943354571496 and negative -455.156923819546 USDC.

Both sign groups are negative after costs in both saved modes. The grouped
portfolio results are contributions, not independently run sign-only strategies.
No profitable sign subgroup is established for this frozen rule on this history.

Seven new correction checks and 34 ledger checks passed; zero replay integrity
errors. Cached queries exactly reproduced all 400 original positive-only candidate
records and 2846 seed statuses. Actual complete query count verified at 2846.
An earlier marker overstated partial cache completeness (2838 actual); missing
queries were recovered BEFORE generation and replay. See VERIFICATION.json.

The original 210-trade v1 result is preserved but was incomplete for the user's
intended both-sign hypothesis. Full corrected ledgers are in btc-orderflow-system:
research/peak_ai_delta_h1_all_signs/results_v2.

Research limitations unchanged: individual H1/H4 adapter, not full Monitor 39A;
Spot normalized inputs; liquidations absent; no borrow-interest/order-book model,
no independent new holdout or without-delta control, and no production/live changes.
