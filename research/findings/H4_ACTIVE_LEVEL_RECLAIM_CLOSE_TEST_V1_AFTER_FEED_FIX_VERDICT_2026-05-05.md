# H4 Active-Level Reclaim-Close Test V1 After-Feed-Fix Verdict

Date: 2026-05-05

Status: consolidated research verdict. Diagnostic only. Not FIELD, not live
strategy, not execution-ready evidence.

This verdict consolidates the recent standalone
`H4_ACTIVE_LEVEL_RECLAIM_CLOSE_TEST_V1` reruns after the `2026-03-29` feed fix.
It does not use `FAILED_BREAK_RECLAIM_EXTENDED_V1`, does not run the legacy
failed-break detector, and does not run the Backtester.

## Feed Fix Status

- `feed/2026-03-29.csv` was replaced with a complete feed file.
- Raw close-labeled file inventory: `1440` rows, `0` missing raw minutes,
  `0` duplicate raw timestamps.
- Analyzer canonical timestamps remain open-labeled after normalization:
  `Timestamp = FeedTimestampUTC - 1 minute`.
- The after-feed-fix diagnostic window has candidate entries through
  `2026-04-23 00:00:00 UTC`; 96h forward diagnostics require coverage through
  `2026-04-27 00:00:00 UTC`.

## Registry-Aware Rerun

- Candidates after registry patch and feed fix: `12`.
- Direction split: `9 SHORT`, `3 LONG`.
- `promoted_from_pending`: `3`.
- Row 8 SHORT remained.
- Old row 13 SHORT remained as new row 12.
- LONG row 5 returned after the feed fix as a `promoted_from_pending` level.

The registry patch remains the correct lifecycle direction: confirmed levels
that appear while an active same-side level is occupied must be retained in a
pending queue and promoted deterministically after sweep, clear, or expiry. The
pre-registry one-slot behavior lost relevant internal/pending levels.

## Compressed Buffer350 Diagnostic

- Candidates: `12`.
- `diagnostic_trade_allowed`: `6`.
- `buffer_was_compressed`: `3`.
- This remains a stop/risk diagnostic over the same detector candidates, not a
  promotion rule and not a fitted parameter claim.

## Structural Audit

Heuristic used for the audit: classify an active level as structural only if it
is the highest confirmed pivot high for SHORT, or lowest confirmed pivot low for
LONG, among confirmed pivots in the prior `30` H4 bars at sweep time.

- SHORT: `9/9` candidates classified as `MAIN_STRUCTURAL_HIGH_SWEEP`.
- LONG row 1 classified as `MAIN_STRUCTURAL_LOW_SWEEP`.
- LONG rows 5 and 10 classified as `LOCAL_HIGHER_LOW_SWEEP`.

The key long-side issue remains active-level quality: the detector can open on a
local higher-low sweep while a lower structural low in the same context was not
swept. Those local higher-low cases may be a separate pattern, but they are not
evidence for strict main structural H4 false-break/reclaim.

## Verdict

- `FAILED_BREAK_RECLAIM_EXTENDED_V1` / old H4 failed-break arithmetic remains
  quarantined as evidence for this setup class.
- `H4_ACTIVE_LEVEL_RECLAIM_CLOSE_TEST_V1` remains standalone diagnostic only.
- The SHORT main-structural bucket remains the only continuing research surface
  from this rerun.
- LONG main-structural evidence is insufficient: only one main structural LONG
  candidate survived this audit lens.
- LONG local higher-low cases must be split into a separate bucket before any
  further interpretation.
- No Backtester, FIELD, production, or live execution claims are supported.

## Next Research Boundary

The next valid step is not parameter fitting. It is a structural-level contract
decision: whether the detector should require active highs/lows to be the
highest/lowest confirmed pivot over a fixed H4 context window, and whether local
higher-low / lower-high sweeps should become their own explicit diagnostic
pattern.
