# Peak_Ai consolidated research — 2026-10-11

Branch: `codex/peak-ai-research-consolidated-2026-10-11`.
Canonical Monitor base: `064247c4e3081a02ef9fc227e333ae6ca8dc6cec`.

This repository contains the bounded H1/H4 research adapter, native lifecycle
changes with unchanged default behavior, tests, audits and completed run summaries.
The complete candidate/replay implementation, historical experiments and trade
ledgers are in [btc-orderflow-system](https://github.com/Mykh-Ai/btc-orderflow-system/tree/codex/peak-ai-research-consolidated-2026-10-11/research/PEAK_AI_RESEARCH_INDEX.md).

## Current result

[Corrected both-sign SHORT report](market_monitor_runs/PEAK_AI_H1_BOTH_SIGNS_V2/REPORT_UA.md)
and [run summary](market_monitor_runs/PEAK_AI_H1_BOTH_SIGNS_V2/SUMMARY.md).

Both raw delta signs trigger the SAME upper-zone / four-hour completed-H1 reclaim
SHORT rule. One shared candidate lifecycle and portfolio. 226 closed simulated
trades, net -1401.95 USDC after costs. Positive triggers: 151 / -995.77 USDC;
negative: 75 / -406.18 USDC. Both groups negative. No live promotion.

The earlier [positive-only run](market_monitor_runs/PEAK_AI_DELTA_H1_V1_v0/SUMMARY.md)
is preserved but was incomplete for the intended hypothesis. Its 210 trades and
-1242.08 USDC must not be presented as a both-sign test. See the
[scope correction audit](research/canonical/PEAK_AI_H1_BOTH_SIGNS_CORRECTION_AUDIT_2026_10_11.md).

Seven correction checks, 34 ledger checks, and exact equivalence of the original
400 positive-only candidates passed. The earlier adapter/native/Replay targeted
suite had 145 passing tests, and 250 timestamp-helper comparisons matched.

This is research using individual H1/H4 zones, not the complete Monitor 39A.
No production trading, protected feed data, Executor lifecycle, live orders,
services or canonical branch changes are included in this consolidation.
