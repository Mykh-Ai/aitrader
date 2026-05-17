# Failed Analyzer v1 Branch Archive

Archived: 2026-05-17

## What Was Tested

This archive preserves summary-level evidence from the Analyzer/Backtester research branch that ran through Sprint 02 to Sprint 10.

The branch tested failed-break/reclaim and related replay surfaces built on Analyzer v1 artifacts:

- close-around-level failed-break/reclaim setup detection;
- weak sweep and reclaim abstractions;
- arbitrary 12-bar forward outcome scaffolding;
- H1/H2/H4 replay formalization attempts;
- recovered-feed replay and cost/same-bar/source-concentration audits;
- BTC surface discovery, formal replay mapping, integrity checks, and true-holdout attempts.

## Why This Branch Is Closed

Analyzer v1 is closed as a failed research branch because it did not model the market state that Shi needs.

The implementation was too setup-centric and too shallow:

- failed-break/reclaim was detected as candle behavior around a level rather than as a liquidity event;
- sweep logic did not prove real liquidity removal;
- 12-bar outcome labels were research scaffolding, not market logic;
- volume, delta, OI, funding, and liquidation context were not integrated into a coherent state model;
- accumulation and distribution zones were not modeled;
- repeated replay and holdout work did not produce execution-ready evidence.

## What Remains Useful

The branch still leaves useful infrastructure and evidence:

- raw feed collection and data lineage remain valid;
- recovered-feed provenance and contamination handling remain useful;
- deterministic artifact discipline remains useful;
- backtester replay hygiene exposed cost sensitivity, same-bar ambiguity, and source-concentration risks;
- negative results are preserved as evidence against continuing this implementation.

## What Must Not Be Continued

Do not continue Sprint 02-10 replay research as the main path.

Do not:

- tune old failed-break/reclaim thresholds;
- promote old candidates;
- reopen Phase 4 from this branch;
- run Executor or live trading;
- treat recovered-data replay as promotion evidence;
- repeat the broad H1/H2/H4 replay loop without a new market-state model.

## Concept Status

The false-break / liquidity-sweep idea is not rejected.

Rejected is only the Analyzer v1 implementation and the replay branch built on it.

The concept must be rebuilt as liquidity event detection inside a Market State Monitor:

- detect actual liquidity pools;
- detect sweep/stop-run magnitude, speed, and volume;
- model post-sweep reaction;
- classify accumulation/distribution/expansion/chop states;
- only then evaluate whether a failed breakout or reclaim matters.

## Archive Layout

- `canonical/`: sprint reports, registry/state snapshots, data lineage summaries.
- `candidates/`: candidate-level verdicts, replay summaries, checklists, and audit summaries.
- `scripts/`: old branch scripts used for discovery, mapping, replay, and diagnostics.
- `results/`: summary-level result CSV/MD files only.
- `backtest_summaries/`: official replay summary artifacts without full heavy generated noise.
