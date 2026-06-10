# SHI RESET 37 Hidden Flow Research Log

Date: 2026-06-10

Status: research-only Market Monitor evidence log.

This document records the SHI_RESET_37 hidden-flow review work and the discussion conclusions. It is not a trading strategy specification, not Backtester evidence, not Executor input, and not a live-readiness claim.

## Git State At Time Of Log

- Current branch: `codex/SHI_RESET_37C_prune_hidden_flow_labels_v0`
- `origin/main` contains:
  - `SHI_RESET_36B` significant zone selector merge.
  - `SHI_RESET_36C` trader snapshot builder merge.
  - `SHI_RESET_37A` hidden flow research merge.
- Local branch contains one unmerged/unpushed commit:
  - `169ecd4 Prune hidden flow review labels`
- Local 37C diff versus `origin/main`:
  - `market_monitor/hidden_flow_research.py`
  - `tests/test_hidden_flow_research.py`
- Working tree source status was clean before writing this log.

## Scope Boundary

All SHI_RESET_37 work remains Market Monitor research infrastructure.

It does not add:

- trading signals;
- entries;
- exits;
- PnL;
- orders;
- Executor logic;
- Backtester campaigns;
- live-readiness;
- edge-validation claims.

Future outcome labels used in audit artifacts are post-factum diagnostics only. They must not be used to generate candidate labels.

## What SHI_RESET_37A Added

SHI_RESET_37A added hidden-flow research detection for Market Monitor review. It surfaced windows where effort/result, delta, OI, zone context, and local trend context suggested possible hidden accumulation, hidden distribution, compression, or absorption behavior.

SHI_RESET_37A was merged into `main` and pushed.

Important limitation: raw hidden-flow labels were too broad for trader review. The output contained too many low-confidence or unclear candidates to use directly.

## What SHI_RESET_37C Prunes

SHI_RESET_37C keeps only high-priority review labels in `hidden_flow_candidates.csv`:

- `COMPRESSION_BEFORE_EXPANSION_CANDIDATE`
- `HIDDEN_DISTRIBUTION_DOWN_CANDIDATE`
- `SELLER_ABSORPTION_CANDIDATE`

Low-confidence, unclear, and unproven directional labels remain in `market_regime_windows.csv` for audit, but are not promoted to the review candidate file.

Current local 37C commit:

- `169ecd4 Prune hidden flow review labels`

Full test result previously recorded for 37C:

- `667 passed, 11 warnings`

37C is not merged and not pushed at the time of this log.

## Whole-Feed Validation Findings

Whole-feed audit was run across usable feed segments while excluding the known feed outage window.

Before 37C pruning, promoted HIGH candidates across the audited feed were:

- total promoted HIGH candidates: `37`
- `COMPRESSION_BEFORE_EXPANSION_CANDIDATE`: `13`
- `HIDDEN_DISTRIBUTION_DOWN_CANDIDATE`: `8`
- `BUYER_ABSORPTION_CANDIDATE`: `7`
- `HIDDEN_ACCUMULATION_UP_CANDIDATE`: `3`
- `SELLER_ABSORPTION_CANDIDATE`: `3`
- `DOWNTREND_EXHAUSTION_CANDIDATE`: `3`

After 37C pruning:

- promoted review candidates: `24`
- `COMPRESSION_BEFORE_EXPANSION_CANDIDATE`: `13`
- `HIDDEN_DISTRIBUTION_DOWN_CANDIDATE`: `8`
- `SELLER_ABSORPTION_CANDIDATE`: `3`
- disallowed promoted labels: `0`
- promoted confidence: all `HIGH`

Important conclusion: `COMPRESSION_BEFORE_EXPANSION_CANDIDATE` is not directional by itself. It identifies compression / energy build, but direction depends on higher-timeframe context and local zone behavior.

## Episode Link Audit

An audit-only link check was run for this pattern:

`HIDDEN_DISTRIBUTION_DOWN_CANDIDATE` -> within 72h -> `COMPRESSION_BEFORE_EXPANSION_CANDIDATE`

Strict link criteria:

- compression confidence: `MEDIUM` or `HIGH`
- compression trend direction: `RANGE`
- nearest side: `BUY_SIDE`
- compression zone context: `inside_zone`, `near_upper_zone`, or `between_zones`

Audit outputs:

- `market_monitor_runs/SHI_RESET_37C_episode_link_audit/distribution_to_compression_links.csv`
- `market_monitor_runs/SHI_RESET_37C_episode_link_audit/distribution_to_compression_links_summary.md`
- `market_monitor_runs/SHI_RESET_37C_episode_link_audit/episode_context_1_3_7.csv`
- `market_monitor_runs/SHI_RESET_37C_episode_link_audit/episode_context_1_3_7_summary.md`

Link audit findings:

- total linked rows: `33`
- unique compression starts: `29`
- linked prior distribution candidates: `6`
- linked compression confidence: all `MEDIUM`
- 720m post-factum labels:
  - `UP_CONTINUATION`: `12`
  - `DOWN_CONTINUATION`: `14`
  - `CHOP_OR_UNCLEAR`: `7`
- 1440m post-factum labels:
  - `UP_CONTINUATION`: `19`
  - `DOWN_CONTINUATION`: `14`

Read: the sequence supports an episode hypothesis, not a trading rule.

## Situations Reviewed

### 2026-03-13 / 2026-03-14

Early feed-context case.

Observed chain:

- prior `HIDDEN_DISTRIBUTION_DOWN_CANDIDATE`
- followed by `COMPRESSION_BEFORE_EXPANSION_CANDIDATE`
- zone context around `BUY_SIDE`
- subsequent upside continuation in the available future audit window

Interpretation:

- useful as an early example;
- limited because it is near the beginning of the available audited feed context;
- should not be over-weighted.

### 2026-04-11 / 2026-04-12 / 2026-04-13

Key constructive example.

Validated current artifact row:

- `2026-04-11T00:00:00+00:00` -> `2026-04-11T23:59:00+00:00`
- `HIDDEN_DISTRIBUTION_DOWN_CANDIDATE`
- confidence: `HIGH`
- trend context: `RANGE`
- prior trend: `UP`
- zone context: `near_upper_zone`
- nearest side: `BUY_SIDE`
- `delta_pct=0.0438`
- `open_interest_change=1598.95`

Additional overlapping row:

- `2026-04-10T21:00:00+00:00` -> `2026-04-11T20:59:00+00:00`
- `HIDDEN_DISTRIBUTION_DOWN_CANDIDATE`
- confidence: `HIGH`
- zone context: `inside_zone`
- nearest side: `BUY_SIDE`

Compression followed on 2026-04-12 / 2026-04-13 near or inside `BUY_SIDE` zones.

1D / 3D / 7D context before the 2026-04-12/13 compression episode:

- 1D: `DOWN -2.53%`
- 3D: `RANGE -0.28%`
- 7D: `UP +6.44%`

Post-factum audit:

- linked compression rows: `8`
- 720m: `5 UP_CONTINUATION`, `3 CHOP_OR_UNCLEAR`
- 1440m: `8 UP_CONTINUATION`

Interpretation:

`PULLBACK_ABSORBED_IN_UPTREND_COMPRESSION`

This is the best reviewed example of a local corrective move / hidden distribution being absorbed within a higher-timeframe up context, followed by compression and upside continuation.

### 2026-05-12 / 2026-05-13

Range / rejection example.

Prior distribution context:

- `near_upper_zone`
- `BUY_SIDE`

Compression context:

- `inside_zone/BUY_SIDE`: `3`
- `between_zones/BUY_SIDE`: `1`

1D / 3D / 7D context:

- 1D: `RANGE -0.23%`
- 3D: `RANGE +0.41%`
- 7D: `RANGE +0.02%`

The 7D context uses recovered feed for the known 2026-04-23 17:05 -> 2026-05-06 22:51 outage window where available. It is still read as range / balance, not trend.

Post-factum audit:

- 720m: `4 DOWN_CONTINUATION`
- 1440m: `4 DOWN_CONTINUATION`

Interpretation:

`RANGE_UPPER_DISTRIBUTION_REJECTION`

The same local hidden-distribution/compression structure did not imply upside continuation because there was no higher-timeframe up context.

### 2026-05-21 / 2026-05-22

Bearish higher-context counterexample.

Prior candidate:

- `2026-05-20T18:00:00+00:00` -> `2026-05-21T05:59:00+00:00`
- `HIDDEN_DISTRIBUTION_DOWN_CANDIDATE`
- confidence: `HIGH`
- trend context: `UP`
- prior trend: `UP`
- zone context: `near_upper_zone`
- nearest side: `BUY_SIDE`
- `price_change_pct=0.307337`
- `delta_pct=0.045874`
- `open_interest_change=-357.57`
- `distribution_score=80.163`

Compression context:

- `near_upper_zone/BUY_SIDE`: `4`
- `between_zones/BUY_SIDE`: `1`

1D / 3D / 7D context:

- 1D: `RANGE -0.04%`
- 3D: `UP +1.48%`
- 7D: `DOWN -5.14%`

Post-factum audit:

- 720m: `5 DOWN_CONTINUATION`
- 1440m: `5 DOWN_CONTINUATION`

Interpretation:

`BEAR_MARKET_BOUNCE_REJECTED_AT_BUY_SIDE`

This is the clearest counterexample. Local context looked upward, but 7D context was down. The same `HIDDEN_DISTRIBUTION_DOWN_CANDIDATE HIGH + BUY_SIDE + compression` sequence resolved lower.

### 2026-05-25

Range rejection example.

Prior distribution context:

- `near_upper_zone/BUY_SIDE`: `2`
- `inside_zone/BUY_SIDE`: `1`

Compression context:

- `near_upper_zone/BUY_SIDE`: `2`
- `inside_zone/BUY_SIDE`: `1`

1D / 3D / 7D context:

- 1D: `RANGE +0.81%`
- 3D: `RANGE +0.02%`
- 7D: `RANGE +0.43%`

Post-factum audit:

- 720m: `3 DOWN_CONTINUATION`
- 1440m: `3 DOWN_CONTINUATION`

Interpretation:

`RANGE_UPPER_DISTRIBUTION_REJECTION`

## Main Research Conclusion

The local label is not enough.

The reviewed cases show that `7D` context must be considered before interpreting `HIDDEN_DISTRIBUTION_DOWN_CANDIDATE + BUY_SIDE + COMPRESSION`.

Working interpretation:

- `7D UP` + `1D DOWN pullback` + `BUY_SIDE compression` can read as:
  - `PULLBACK_ABSORBED_IN_UPTREND_COMPRESSION`
- `7D RANGE` + upper `BUY_SIDE` hidden distribution / compression can read as:
  - `RANGE_UPPER_DISTRIBUTION_REJECTION`
- `7D DOWN` + local bounce into upper `BUY_SIDE` hidden distribution / compression can read as:
  - `BEAR_MARKET_BOUNCE_REJECTED_AT_BUY_SIDE`

`RANGE` means balance / sideways context: price did not make a clean directional move in the measured window.

## What To Do Next

Recommended next task:

`SHI_RESET_37D_EPISODE_CONTEXT_CLASSIFIER`

Smallest useful scope:

1. Keep 37C pruning as candidate readability cleanup.
2. Add audit-visible `1D`, `3D`, and `7D` context columns for promoted hidden-flow review candidates.
3. Add a descriptive `episode_read` field for promoted candidates, with labels such as:
   - `PULLBACK_ABSORBED_IN_UPTREND_COMPRESSION`
   - `RANGE_UPPER_DISTRIBUTION_REJECTION`
   - `BEAR_MARKET_BOUNCE_REJECTED_AT_BUY_SIDE`
   - `UNRESOLVED_COMPRESSION_CONTEXT`
4. Keep future outcome labels audit-only.
5. Do not add trading signals, entries, exits, PnL, Backtester logic, Executor logic, live-readiness, or edge-validation claims.

Open merge decision before 37D:

- merge 37C first if the pruning behavior is accepted;
- then branch 37D from updated `main`;
- or keep 37C unmerged and include the same pruning in 37D only if the branch is intentionally being replaced.
