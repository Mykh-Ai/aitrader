# Peak_Ai delta-triggered H1 v1 implementation audit

Date: 2026-10-11. Research-only. User explicitly requested implementation of a
new-delta-first experiment with a four-hour H1 confirmation window.
Canonical base fetched and ancestry checked:
`064247c4e3081a02ef9fc227e333ae6ca8dc6cec`, containing both required 39A and 38G
ancestors. Task branch: `codex/peak-ai-delta-h1-v1`.

## Scope

`market_monitor/closed_structure_adapter.py` provides a bounded H1/H4 research
inventory over the supplied completed-minute feed. It reuses native confirmed
swing geometry, single-reference zone construction, lifecycle and significance
scoring. H1 LR=2 / H4 LR=1 references become available at the CLOSE of their
final confirming candle. Complete, contiguous confirmation evidence is required.
The adapter converts availability labels to the native OPEN-label geometry.

The adapter deliberately preserves individual reference identity and boundaries;
it does not implement merged zone, M15, session, pattern, hidden-flow or full
v39A snapshot semantics. A crossed reference may be considered for research even
if the forward display map hides it. No visible-seven cap is applied. This is
not a trading-policy promotion of the native selector or setup_builder.

`zone_registry.py` gains opt-in `closed_htf_only` handling. Default callers retain
their previous behavior. Three timestamp loops avoid iterrows with identical
results; 250 randomized comparisons against the base implementation passed.

Candidate lifecycle and replay integration live in the separate
btc-orderflow-system research branch `codex/peak-ai-delta-h1-replay-v1`, based on
`84fcb9ec257dd2c28b04ff6149b48b52d628fdca`:
`research/peak_ai_delta_h1/PROTOCOL.md`, `engine.py`, and `run.py`.

## Feed and authority

All prices, quantity deltas and structural references in this campaign use the
same normalized legacy Spot archive. Futures liquidations are not a filter;
they are unavailable in these normalized inputs. No SHI Futures price feed is
mixed into the hypothesis. No protected feed/ or feed_recovered/ files changed.

The user-scoped research bridge uses Scout Replay, not the retired Analyzer-v1
candidate source or legacy AiTrader Backtester campaign. No Executor, orders,
position-sizing runtime, production deployment or live promotion was added.

## Verification

- 145 targeted tests passed, including existing Scout Replay, native selector,
  registry and HTF lifecycle tests plus the new candidate and adapter tests.
- Prefix equivalence covers both reference publication and native as-of scores.
- Strict H1 close, exact four-hour deadline, repeated-delta timer behavior,
  missing data, end-of-data censoring and structural stop verification tested.
- Checkpoint restore produces identical candidates, events and seed audit to an
  uninterrupted run.
- Completed campaign evidence and limitations belong in the run summary under
  `market_monitor_runs/PEAK_AI_DELTA_H1_V1_v0/`; absence of a summary is not success.
- Initial 2026-10-10 process did not preserve a completed result. The 2026-10-11
  restart adds checkpointing; the previous incomplete artifacts are retained.

## Interpretation boundary

This tests a newly specified research family. It does not validate the full
Monitor, prove the marginal contribution of delta, or establish out-of-sample
edge. A without-delta control and unused-period test are separate remaining
research tasks. A negative result must not be hidden or retuned in place.

## Completed historical result — 2026-10-11

Implementation commits: Monitor `fbcdce2`, Scout Replay `94abe8f`. Completed run: 400 confirmed candidates, 210 closed simulated portfolio trades, net **-1242.08 USDC**, PF 0.563; doubled-slippage net -1352.95 USDC. Gross was already negative (-193.75 USDC). All 41 ledger checks passed, in addition to the 145 tests and 250 parity checks. See `market_monitor_runs/PEAK_AI_DELTA_H1_V1_v0/SUMMARY.md` and `REPORT_UA.md`. This bounded SHORT adapter failed this historical test; no LONG, unused-period validation or without-delta control was performed. Review sequence semantics before specifying any new experiment. No live promotion.
