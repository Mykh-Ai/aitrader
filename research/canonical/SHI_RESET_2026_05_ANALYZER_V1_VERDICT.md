# SHI RESET 2026-05: Analyzer v1 Verdict

Date: 2026-05-17

## Verdict

Analyzer v1 is not suitable as the Shi market intelligence layer.

The Sprint 02-10 Analyzer/Backtester replay branch is closed as a failed research branch.

This is not a rejection of the false-break or liquidity-sweep concept. It is a rejection of the current implementation path.

## Findings

1. Analyzer v1 is not suitable as Shi market intelligence layer.
2. The failed-break/reclaim implementation was too primitive.
3. The 12-bar outcome logic was arbitrary research scaffolding, not market logic.
4. Liquidity sweep was not properly modeled.
5. Accumulation/distribution was not modeled.
6. Delta, volume, and OI were used as shallow context, not as integrated market state.
7. Sprint 02-10 replay research is closed.
8. Feed and data collection remain valid.
9. The next architecture must be a Market State Monitor, not a setup detector.
10. Live trading, Executor, and Phase 4 remain prohibited.

## Closed Branch

Closed branch scope:

- Analyzer v1 failed-break/reclaim setup detection;
- H1/H2/H4 setup replay families from Sprint 02-10;
- short/long candidate promotion work from this implementation;
- cost/same-bar/source-concentration replay attempts based on old setup surfaces;
- true-holdout attempts built on Analyzer v1 candidate mappings.

## Preserved Evidence

Summary-level evidence is archived under:

`research/archive/failed_analyzer_v1_branch/`

The archive keeps reports, candidate summaries, replay summaries, verdicts, and scripts without copying raw feed or full heavy generated noise.

## Still Valid

- Raw feed collection remains valid.
- `feed/` and `feed_recovered/` remain protected data assets.
- Data lineage, contamination inventory, and recovered-feed manifests remain valid.
- The test suite remains the executable safety contract.
- Aggregator code and Binance data collection remain useful infrastructure.

## New Direction

The next implementation must build a Market State Monitor.

The monitor must classify market structure, liquidity pools, sweep/stop-run events, volume/delta/OI behavior, accumulation/distribution, and post-event reactions.

No trading signal, Backtester promotion, Executor integration, or Phase 4 bridge is allowed in Market State Monitor v1.
