# Peak_Ai delta H1 v1 — completed negative research result

Completed 2026-10-11. Implementation commits: Monitor fbcdce2; Scout Replay 94abe8f.
Frozen rule: raw DELTA_MAX, pre-existing significant H1/H4 upper zone, price above
zone at trigger, completed H1 close below its lower bound within four hours.
No PEAK_EMIT or future-labelled M2.6 entry filters.

2846 raw seeds; 1417 DELTA_MAX; 1429 DELTA_MIN retained but LONG out of scope.
836 armed episodes; 400 unique confirmed candidates; 210 closed simulated
portfolio trades; 190 candidates blocked by an existing position; zero unresolved.
Period: decisions 2026-03-20 through 2026-08-17; exits through 2026-08-19.
Fixed notional 3000 USDC. Net -1242.0843517226726 USDC; gross -193.74927090000068;
commission 937.471539964572; slippage 110.8635408581; PF 0.5626595771352179.
Doubled slippage net -1352.947892580773 USDC on the same 210 trades.
Independent overlapping replay: 400 closed; net -2334.6172763326067 USDC.

145 targeted tests, 250 timestamp-helper parity checks, checkpoint parity, and
41 completed-ledger checks passed. No integrity errors in either replay.

Scope: individual H1/H4 swing adapter, not full Monitor 39A. Prices/deltas/levels
use normalized legacy Spot feed; execution uses BTCUSDC Spot bars. Liquidations
are unavailable, not manufactured. Raw feed and protected data were not changed.
No independent holdout or without-delta control; no LONG test. See REPORT_UA.md.

Decision: this frozen version fails the historical test, including before costs.
Review representative complete sequences against intended level semantics before
any new hypothesis. Do not retune this run or promote it to production/live.
Full candidate, seed, zone and execution ledgers remain in the Scout Replay
research/peak_ai_delta_h1/results_v1_checkpointed directory.
