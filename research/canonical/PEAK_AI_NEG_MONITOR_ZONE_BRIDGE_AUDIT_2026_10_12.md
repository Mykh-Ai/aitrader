# Peak_Ai NEG / Market Monitor Zone Bridge Audit

Verdict: `DIAGNOSTIC_COMPLETE / DIRECT_PARITY_REJECTED / BRIDGE_REQUIRED`

Date: 2026-10-12

## Scope

This research-only audit answers two narrow questions:

1. how the saved Peak_Ai `NEG_H1_CONTROL` backtest obtained its levels without observed OI/liquidation inputs;
2. whether the same saved August NEG opportunities remain the same when the AiTrader Monitor feed and Monitor structural geometry are substituted.

The financial Backtester was not rerun. Stop/TP, execution, commission, slippage, sizing, and portfolio behavior were not changed. No production, Executor, DeltaScout, or Monitor logic was modified.

The user-directed exclusion is `2026-04-26` through `2026-05-09` inclusive. The diagnostic therefore starts with an explicit reset at `2026-05-10T00:00:00Z`; no row from the excluded period is used.

Run root:

`market_monitor_runs/PEAK_AI_NEG_MONITOR_ZONE_BRIDGE_JULY_CASE_v0/`

## Why The Old Backtest Had Levels Without OI Or Liquidations

The saved Peak_Ai experiment used `CLOSED_H1_H4_IMMUTABLE_REFERENCES_V1`. It built confirmed H1/H4 swing highs from price bars, converted each reference into a fixed-width structural zone, reconstructed its price lifecycle, scored it through the significant-zone scoring helper, and admitted only `MAJOR` or `PRIMARY` upper zones.

At a NEG seed the old candidate engine required:

- current price strictly above the frozen zone upper bound;
- a recent crossing above that bound;
- complete/non-synthetic price history for the relevant reference and crossing;
- the first completed H1 close within four hours strictly below the frozen lower bound.

OI and liquidations did not form the old level and did not participate in the adapter score. The adapter explicitly supplied compatibility `OpenInterest=0` and `FundingRate=0`; liquidations were absent. Therefore the prior H1/H4 levels were price/lifecycle levels, not derivatives-confirmed levels.

## Current Monitor Input Versus Current Level Pipeline

The AiTrader source feed contains observed `OpenInterest`, `FundingRate`, `LiqBuyQty`, and `LiqSellQty` outside degraded intervals.

Current reusable Monitor behavior is asymmetric:

- `OpenInterest` passes through `market_monitor.feed_adapter`, reaches volume/delta state, and can add OI evidence to significant-zone scores through event/post-sweep evidence;
- at the time of this diagnostic, `LiqBuyQty` and `LiqSellQty` were dropped by the adapter output contract;
- the selector therefore recorded `liquidations=not_available` and could not change zone geometry, bucket, or visibility because of liquidation evidence.

Superseding note, 2026-10-12: the reusable adapter now preserves liquidation quantities and exposes them in `volume_delta_state.csv` with an explicit availability flag. The production selector still does not score them. The separate five-delta research ablation is documented in `PEAK_AI_FIVE_DELTA_LEVEL_FLOW_ABLATION_AUDIT_2026_10_12.md`.

Consequently, merely replacing the old file with the enriched Monitor feed cannot make liquidation data alter `MAJOR`, `PRIMARY`, or `LOCAL_CONTEXT`. A separate tested adapter/event/scoring promotion would be required.

## Single Causal July Case

Case: `NEGH1_689c85eb5a98860654e5`

- old S0 / owning NEG seed: `2026-07-01T23:03:00Z`;
- old H1 confirmation: `2026-07-02T00:00:00Z`;
- old frozen zone: H4 `60243.863-60304.137`, `MAJOR`, score `90`;
- old source price recorded by the replay at S0: `60309.0` (above the old upper bound);
- Monitor-feed close at the same S0: `60288.4` (below the old upper bound).

The causal Monitor reconstruction used only rows from `2026-05-10T00:00:00Z` through S0. The excluded April/May interval contributed zero rows. The warm-up has one missing minute (`2026-05-18T19:31:00Z`) and 15 synthetic rows, so the result is explicitly `DEGRADED_PRE_CUTOFF_CONTEXT`, not a pristine live-like replay. The old H4 reference was available at `2026-06-26T04:00:00Z`, after the last synthetic warm-up row.

At S0 the current Monitor generated:

- 2,773 structure levels;
- 155 liquidity-zone candidates;
- 538 registry zones;
- 155 scored selector rows;
- 7 visible zones.

Bucket inventory:

- `MAJOR`: 73;
- `PRIMARY`: 32;
- `MINIMUM`: 29;
- `LOCAL_CONTEXT`: 5;
- `NOISE_HIDE_BY_DEFAULT`: 16.

The old H4 zone did not survive as the same Monitor upper zone. Only one current zone overlapped its price band: hidden `zone_000493`, a `SELL_SIDE` M15 swing-low `60201.98395-60262.21605`, bucket `MINIMUM`. No current `BUY_SIDE` `MAJOR`/`PRIMARY` zone had an upper bound below the S0 Monitor price, so the old SHORT admission condition would not arm at this timestamp.

The raw enriched feed at S0 did contain derivatives context:

- OI `104009.76`;
- minute `LiqSellQty=0.335`, `LiqBuyQty=0`;
- trailing 60-minute OI change `-1193.39`;
- trailing 60-minute liquidations: buy `5.013`, sell `4.65` BTC quantity.

Those liquidation values did not enter the current level pipeline. OI did contribute to several current selector scores.

## August Saved-Seed Comparison

The preserved NEG seed audit contains 920 NEG events after the `2026-05-10` reset. Every one of the 920 differs from the Monitor feed at the same timestamp in delta and/or volume. This proves the old raw delta stream and the Monitor feed are different source contracts. Exact re-detection parity is therefore impossible without defining a new Monitor-feed delta detector and threshold contract.

A second, explicitly counterfactual comparison retained the old timestamps as external trigger times and substituted the Monitor minute's delta/volume only to satisfy the unchanged engine input check. This method was subsequently rejected for parity interpretation because it mixes source contracts. It remains forensic evidence only and must not be used to claim which Monitor-native trades would open.

August result:

| Measure | Old saved cohort | Monitor-feed fixed-timestamp counterfactual |
| --- | ---: | ---: |
| Candidates | 26 | 26 |
| H1 swing-high candidates | 13 | 13 |
| H4 swing-high candidates | 13 | 13 |
| Exact candidate IDs in common | 0 | 0 |
| Owning seed IDs in common | 16 | 16 |
| Old-only owning seeds | 10 | - |
| New-only owning seeds | - | 10 |

For the 16 common owning seeds:

- all 16 retained the same H1 confirmation timestamp;
- 11 retained the same H1/H4 level type;
- zero retained exact zone bounds;
- zero retained the same candidate ID.

The equal total count `26` is therefore not parity. The membership and zone identities changed materially.

At the old NEG timestamps, Monitor-feed minute delta was negative 799 times and positive 121 times. Even the sign is not invariant across sources.

## Integration Decision

Do not inject the current seven visible zones directly into the old Peak_Ai backtester. That would mix three contracts:

1. old-source delta events;
2. Monitor-feed price/flow geometry;
3. a selector whose OI evidence is active but liquidation evidence is unavailable.

The correct integration boundary is a versioned `as_of_zone_query(cutoff_ts)` contract that returns the full eligible upper-zone inventory, immutable zone identity/bounds, availability time, lifecycle state, source families, score components, and explicit OI/liquidation availability. The Peak_Ai engine can then freeze one returned upper zone at the trigger and preserve its existing four-hour H1 close rule.

Before a new backtest is meaningful, define a Monitor-feed-native delta detector and freeze its thresholds. Then run candidate-generation parity first. Financial replay should be rerun only after that candidate contract is audited.

Liquidation-aware selection is a separate promotion. It must first carry liquidation fields through the adapter, define causal event/window features and units, add deterministic scoring/gating with tests, and prove that its use changes selection for stated reasons rather than merely adding data columns.

## Artifacts

- `case_summary.json`: single July case and raw OI/liquidation context.
- `feed_audit.json`: cutoff, hashes, coverage, exclusion, gaps, and synthetic rows.
- `visible_zones_at_s0.csv`: seven visible current Monitor zones.
- `zone_bridge_comparison.csv`: full 155-zone comparison to the old frozen zone.
- `monitor_daily/2026-07-01/`: causal Monitor outputs through S0.
- `significant_zone_selector/`: selector output and manifest.
- `august_parity/summary.json`: source mismatch and fixed-timestamp scope.
- `august_parity/parity_summary.csv`: high-level old/new set comparison.
- `august_parity/common_seed_comparison.csv`: 16 common owning seeds.
- `august_parity/cohort_changes.csv`: 10 old-only and 10 new-only owning seeds.
- `august_parity/comparison_analysis.json`: exact comparison counts.

## Verification

- `tests/test_market_monitor_feed_adapter.py`
- `tests/test_significant_zone_selector.py`
- `tests/test_market_monitor_zone_registry.py`
- `tests/test_market_monitor_liquidity_zone_semantics.py`
- Result: `21 passed in 4.86s`.

No financial Backtester run was performed.
