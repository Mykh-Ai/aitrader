# Peak_Ai Five-Delta Level Flow Ablation Audit

Verdict: `FLOW_EVIDENCE_REDUCES_LEVEL_INVENTORY / RESEARCH_ONLY / NOT_PROMOTED`

Date: 2026-10-12

## Question

Does a Market Monitor level inventory materially change when H1/H4/M15 swing geometry is required to have causal volume and derivatives evidence at the bar that formed the level?

This is not a Backtester run. The five saved NEG delta rows supply cutoff timestamps only. Their delta and volume values are not injected into Market Monitor. Every structure level, zone, price, volume, liquidation, and OI observation comes from `D:/Project_V/Aitrader/feed`.

## Scope And Causality

- Explicit post-outage reset: `2026-05-10T00:00:00Z`.
- Five evenly spaced August NEG cutoffs from the preserved old candidate cohort.
- Each snapshot consumes Monitor feed only through its cutoff.
- H1/H4/M15 geometry is built by the current `market_monitor.structure` and `market_monitor.liquidity_zones` code.
- A source bar is evaluated only after it is completed; no later touch is allowed to retroactively validate the level.
- H1/H4 candidates are limited to 3% from the cutoff price; M15 local context is limited to 1%.

The first attempted diagnostic used the maximum flow anomaly over the entire lifetime of a level. It over-admitted old levels because almost every long-lived level eventually encountered an unrelated spike. That method was rejected. The reported result evaluates only the completed source-timeframe bar that formed each level.

## Experimental Qualification

All thresholds are explicit research hypotheses, not promoted policy:

- volume evidence: source-bar `volume_z >= 2.0` versus the prior 20 completed bars of the same timeframe;
- directional liquidation evidence: source-bar z-score `>= 2.0`;
  - `BUY_SIDE` zone above price uses `LiqBuyQty` (short liquidation / market buy);
  - `SELL_SIDE` zone below price uses `LiqSellQty` (long liquidation / market sell);
- stricter OI confirmation tier: absolute source-bar OI-change z-score `>= 2.0`;
- H4+H1 confluence upgrades a qualified level to `MAJOR`, but cannot substitute for missing volume/liquidation evidence;
- H4-only or H1-only qualified levels are `PRIMARY`;
- M15-only qualified levels are `LOCAL_CONTEXT`.

The ablation stages are:

1. geometric structural candidates;
2. volume-only candidates, representing the result when liquidation and OI are unavailable;
3. volume plus directional liquidation;
4. volume plus directional liquidation plus OI, a stricter evidence tier.

## Results

| Cutoff UTC | Structural | Volume only | Volume + directional liquidation | + OI strict tier | Liquidation-qualified MAJOR | PRIMARY | LOCAL_CONTEXT |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-08-02 00:25 | 270 | 67 | 54 | 29 | 18 | 8 | 28 |
| 2026-08-04 07:35 | 277 | 62 | 51 | 32 | 19 | 12 | 20 |
| 2026-08-06 19:20 | 287 | 82 | 61 | 32 | 19 | 16 | 26 |
| 2026-08-08 20:49 | 195 | 55 | 41 | 27 | 11 | 13 | 17 |
| 2026-08-17 11:08 | 359 | 80 | 65 | 38 | 24 | 13 | 28 |
| **Total across snapshots** | **1,388** | **346** | **272** | **158** | **91** | **62** | **119** |

Effects across the five independent snapshots:

- volume-at-formation removed 1,042 of 1,388 geometric candidates (`75.1%`);
- directional liquidation removed another 74 of the 346 volume-confirmed candidates (`21.4%` of that stage);
- the strict OI tier retained 158 of 272 liquidation-confirmed candidates and removed 114 more;
- 91 of the 272 liquidation-confirmed zones had H4+H1 confluence and therefore received the experimental `MAJOR` grade.

## Interpretation

The user's concern is confirmed: H1/H4/M15 swing geometry alone massively overstates the number of meaningful levels. Volume produces the largest first reduction, and directional liquidation adds real discrimination beyond volume. OI adds a further strong separation, but this audit does not establish that OI must be a hard gate rather than a score/confirmation component.

Liquidation evidence changes the inventory, not merely the description. In these five snapshots the important set fell from 346 volume-only zones to 272 volume-plus-liquidation zones. Requiring OI as well produced a much tighter 158-zone tier.

The resulting counts are still too large for direct display or automatic entry use. A later promotion must separately define lifecycle freshness, duplicate/confluence collapse, side-aware ranking, and a visible-zone cap. Profitability and edge were not tested.

## Code Boundary

The reusable feed contract now preserves `LiqBuyQty` and `LiqSellQty`, and `volume_delta_state.csv` carries liquidation quantities plus an availability flag. The production `significant_zone_selector` has not been changed to use the experimental gate. The ablation lives only in the run script below.

## Artifacts

Run root: `market_monitor_runs/PEAK_AI_FIVE_DELTA_LEVEL_FLOW_ABLATION_v0/`

- `build_ablation.py`: deterministic five-cutoff causal ablation.
- `five_delta_summary.csv`: per-cutoff counts.
- `zone_evidence_ablation.csv`: zone-level source evidence and qualification flags.
- `manifest.json`: thresholds, semantics, feed hashes, and limitations.

## Verification

Targeted Monitor adapter/output/selector/event/observation tests: `19 passed in 2.23s`.
Full canonical regression: `721 passed, 11 warnings in 55.21s`.

No Backtester trades, exits, PnL, Executor behavior, or live policy were run or changed.
