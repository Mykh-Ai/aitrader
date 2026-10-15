# Market Monitor Continuous Context and Gap Policy

Status: approved for implementation on
`codex/market-monitor-production-continuity-v1`, based on latest `origin/main`.

## Decision

A UTC daily CSV is a storage boundary, not a market-context boundary.
Historical Monitor calculations receive causal rows through their inclusive
cutoff, including required previous-day context. Rows after the cutoff are not
visible.

Warm-up calculation context is distinct from lifecycle progression. Only new
progression rows may update the zone registry, events, touches, crosses,
consumption, or counters.

Feed quality is represented per row and per exact rolling window. Recovered
source provenance and synthetic-row quality are distinct. Duplicates remain in
the input until diagnostics record them; downstream calculation uses a
deterministic deduplicated view.

Exact 5/15/30/60/240/1440-minute diagnostics report expected rows, rows used,
missing timestamps, duplicate rows, quality counts, and completion status.
Partial context is explicit and must not be presented as complete.

One synthetic or missing minute does not remove the rest of the trading day
from state progression.

## Governed feed selection

For the documented outage from `2026-04-23 17:05:00 UTC` through
`2026-05-06 22:51:00 UTC`, the daily recovered file is required and has
precedence. A missing required recovered file is an error; contaminated base
feed is never a fallback. Selected path, source class, and selection reason are
preserved in batch provenance.

Feed assets are read-only and are never copied or rewritten by this package.

## Compatibility boundary

Restored context may legitimately change midnight z-scores, first-minute OI
change, boundary structure, PDH/PDL, and registry interactions that were
previously lost. Existing zone definitions, event semantics, scoring, setup
semantics, and trading boundaries are unchanged.

Excluded: archived Peak-Ai H1/H4 research logic, liquidation promotion,
checkpoint redesign, Backtester, Executor, deployment, and feed mutation.
