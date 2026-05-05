# FAILED_BREAK_RECLAIM_H4 Detector Root-Cause Audit - 2026-05-04

Scope: root-cause audit of detector behavior behind `FAILED_BREAK_RECLAIM_H4_EXTENDED_V1` after reconciliation showed replay arithmetic exists but manual review discarded 37/37 events. This audit does not change strategy logic, Analyzer behavior, Backtester behavior, stops, targets, or optimization parameters.

## Direct Answers

1. **Detector valid relative to intended H4 3-candle false-break/reclaim? `INVALID`.** The implemented detector does not contain explicit H4 Candle A / Candle B / Candle C logic. It detects 1m raw-bar sweeps and 1m raw-bar reclaim closes against a latest confirmed H4 swing level.
2. **Patch or discard current EXTENDED_V1? `Discard as evidence for this intended setup-class`.** Do not use current `FAILED_BREAK_RECLAIM_EXTENDED_V1` backtester/MFE results as evidence for the intended H4 3-candle formation. If the idea is still desired, build a new detector with explicit H4 A/B/C semantics rather than patching conclusions around this artifact.
3. **Functions responsible for the 37 timestamps:** `build_failed_break_reclaim_replay_bridge()` / `_build_failed_break_reclaim_variant()` run the pipeline; `annotate_swings()` creates latest H4 swing levels; `detect_sweeps()` marks 1m crosses of those levels; `detect_failed_breaks()` confirms 1m closes back through the level; `build_events()` emits `FAILED_BREAK_*`; `extract_setup_candidates()` sets `SetupBarTs` to that 1m event timestamp; `_resolve_activation_ts()` and `run_replay_engine()` make entry the next raw bar open.
4. **Can previous R/MFE be trusted for this class? `No, not as evidence for the intended H4 class`.** The arithmetic is reproducible, but it is measuring a different detector object and is distorted by micro risk distances and 1m same-bar/micro target behavior.

## Intended Formation Checked Against Code

Intended H4 short requires: Candle A H4 base, Candle B H4 sweeps Candle A high, Candle C H4 closes back below reclaim boundary, then 1m entry search after Candle C. Intended long mirrors this around lows.

The current code path does not model that sequence. `analyzer/swings.py` builds H1/H4 bars only to derive delayed confirmed swing levels. After that, `analyzer/sweeps.py` evaluates every raw row with `High > latest H4 swing high` or `Low < latest H4 swing low`; `analyzer/failed_breaks.py` then confirms when a later raw row close crosses back through the level within `confirmation_bars=60`. These are minute-feed events carrying `SourceTF=H4`, not H4 candle objects.

## Function Map

| Stage | Function | File | Behavior relevant to root cause |
|---|---|---|---|
| Variant config | `FAILED_BREAK_RECLAIM_EXTENDED_V1` | `analyzer/research_variants.py:60` | Sets `confirmation_bars=60`; this is 60 raw bars in the current pipeline, not 60 H4 bars and not a Candle C rule. |
| Pipeline bridge | `build_failed_break_reclaim_replay_bridge()` | `analyzer/research_replay_bridge.py:132` | Runs features -> swings -> sweeps -> failed breaks -> events -> setups for replay-compatible artifacts. |
| Sidecar pipeline | `_build_failed_break_reclaim_variant()` | `analyzer/research_variants.py:70` | Same detector sequence for research-only variant outputs. |
| H4 level source | `annotate_swings()` | `analyzer/swings.py:136` | Resamples to `4h` only to create delayed confirmed swing high/low levels, then attaches latest level to every raw row. |
| Sweep detector | `detect_sweeps()` / `_annotate_tf_sweeps()` | `analyzer/sweeps.py:118` | Marks raw-row crosses against latest H4 swing levels; no H4 Candle B object is required. |
| Reclaim detector | `detect_failed_breaks()` / `_annotate_tf_failed_breaks()` | `analyzer/failed_breaks.py:36` | Maintains pending sweep state and confirms on later raw-row `Close` reclaiming the level; no H4 Candle C close is required. |
| Event materialization | `build_events()` | `analyzer/events.py:186` | Emits `FAILED_BREAK_UP/DOWN` at raw-row confirmation timestamp with `SourceTF=H4`. |
| Setup materialization | `extract_setup_candidates()` | `analyzer/setups.py:128` | Maps failed-break events into setup rows and sets `DetectedAt`, `SetupBarTs`, and `ReferenceEventTs` equal to event timestamp. |
| Entry activation | `_resolve_activation_ts()` | `backtester/placement.py:97` | Selects first raw timestamp greater than `SetupBarTs`; with 1m feed this is `setup_ts + 1 minute`. |
| Replay entry | `run_replay_engine()` | `backtester/engine.py:387` | Enforces `NEXT_BAR_OPEN` and activates pending entry on the next raw bar. |
| Stop/target placement | `_materialize_one()` | `backtester/placement.py:159` | Reference stop is `ReferenceLevel`; risk is `abs(next_open - ReferenceLevel)`; target is fixed `1.5R`. |
| Same-bar policy | `ConservativeSameBarPolicy` | `backtester/engine.py:149` | Same-bar collision policy returns `UNRESOLVED`; ledger outcomes can still be dominated by tiny 1m target/stop touches outside collision rows. |

## Why H4 Timestamps Are Minute Timestamps

- Selected 37 H4 events have `entry_ts - setup_ts` unique values: `[1]` minute(s).
- H4 selected setup timestamps aligned exactly to 4h candle boundaries: `0/37`.
- This happens because `SourceTF=H4` identifies the reference swing/level lineage, not the timestamp granularity of the formation. `SetupBarTs` is the raw 1m bar where failed-break confirmation occurred.
- `entry_ts = setup_ts + 1 minute` because placement and engine use `NEXT_BAR_OPEN` on the next raw feed row.

## Why R And MFE Become Absurd

Reference-stop risk is `abs(entry_next_open - H4_reference_level)`. When a 1m close reclaims just across the level, next open can sit only cents/dollars away from that level. The target then becomes `entry +/- 1.5 * tiny_risk`, so backtester can count TP on very small 1m moves. MFE_R divides later favorable excursion by the same tiny risk distance, producing hundreds/thousands of R without proving a meaningful formation.

- Reference-stop H4 risk distance summary from replay rows: count `37`, min `0.2`, median `35.7`, max `278.0` dollars.
- Tiny-risk counts: `<=1` dollar `1`, `<=5` dollars `3`, `<=10` dollars `6`, `<=25` dollars `14`.
- Same-bar exposure in reference-stop H4 replay rows: SameBarExit `13/37`, SameBarCollision `9/37`.
- Holding bars distribution starts: `{0: 13, 1: 10, 2: 3, 3: 1, 4: 2, 5: 2, 8: 1, 11: 1, 15: 1, 28: 1, 51: 1, 101: 1}`; `0` means exit on entry bar.

Smallest reference-stop risk examples:

| setup_id | setup_ts | entry_ts | dir | entry | stop | target | risk_distance | R | replay_exit |
|---|---|---|---|---:|---:|---:|---:|---:|---|
| `a7041ce1f10fd1f3af817637` | 2026-04-05 06:28:00+00:00 | 2026-04-05 06:29:00+00:00 | long | 66745.7 | 66745.5 | 66746.0 | 0.2 | -1.0 | STOP |
| `0d25765ec7778c11c037cd24` | 2026-04-19 18:02:00+00:00 | 2026-04-19 18:03:00+00:00 | long | 74826.7 | 74824.3 | 74830.3 | 2.4 | -1.0 | STOP |
| `747855283015820c70664969` | 2026-04-21 08:53:00+00:00 | 2026-04-21 08:54:00+00:00 | short | 76526.1 | 76531.0 | 76518.75 | 4.9 | 1.5 | TARGET |
| `7d7d5ff4a49433f6625e6d11` | 2026-04-07 10:54:00+00:00 | 2026-04-07 10:55:00+00:00 | long | 68233.8 | 68227.5 | 68243.25 | 6.3 | -1.0 | STOP |
| `ee3a427c406780624a37e615` | 2026-04-07 20:37:00+00:00 | 2026-04-07 20:38:00+00:00 | short | 69210.9 | 69219.0 | 69198.75 | 8.1 | -1.0 | STOP |
| `a4b5b44714ca7e13a0dfd875` | 2026-04-15 08:07:00+00:00 | 2026-04-15 08:08:00+00:00 | long | 73775.9 | 73766.8 | 73789.55 | 9.1 | 1.5 | TARGET |
| `2b972c2d5c1154445cef48ed` | 2026-04-15 20:08:00+00:00 | 2026-04-15 20:09:00+00:00 | short | 74725.8 | 74739.2 | 74705.7 | 13.4 | 1.5 | TARGET |
| `84b4a773e173b42be1f3ea1f` | 2026-04-10 08:09:00+00:00 | 2026-04-10 08:10:00+00:00 | long | 71553.4 | 71539.9 | 71573.65 | 13.5 | 1.5 | TARGET |

These values are not suitable as Binance-executable evidence without explicit fee/slippage/min-distance gates. A `$0.20` or `$2.40` 1R on BTCUSDT is structurally incapable of supporting a meaningful fee/slippage-aware claim.

## Root Cause

The detector name and downstream research label imply an H4 false-break/reclaim setup-class, but implementation detects raw 1m failed-break events against latest confirmed H4 swing levels. This creates a semantic mismatch: the replay arithmetic is internally consistent for the implemented detector, but the implemented detector is not the intended H4 three-candle formation.

Consequences:

- `SourceTF=H4` is a level lineage label, not proof that Candle A/B/C occurred on closed H4 candles.
- `SetupBarTs` and `entry_ts` are minute timestamps by design of the current detector/engine path.
- Backtester TP can be achieved by micro moves around the H4 level, especially when reference-stop risk is tiny.
- MFE_R is mathematically inflated when risk distance is microscopic.
- Manual review rejecting 37/37 as no real continuation is consistent with this root cause.

## Audit Verdict

- **Detector validity:** invalid for intended H4 3-candle false-break/reclaim.
- **Current EXTENDED_V1 status:** discard/quarantine as evidence for this setup-class. Use only as historical artifact evidence of a flawed detector path.
- **Required future work if the idea remains useful:** implement a new explicit H4 A/B/C detector that materializes Candle A/B/C timestamps, prices, sweep boundary, reclaim close, and only then opens a separate 1m entry-search phase. Add minimum risk/fee/slippage viability gates before replay metrics are interpreted.
- **Trust in previous R/MFE:** do not trust as setup-class evidence. Trust only that the arithmetic is reproducible for the wrong object.

## Superseding Manual Review Note

After timezone-corrected visual review, the manual entry-review CSV has blank `outcome` cells and no longer supports reading rows as final visual discards. Two entries are now explicitly marked as `potential_after_resweep`: `2026-04-11 18:44:00+00:00` and `2026-04-15 20:09:00+00:00`. This does not change the code-level detector verdict above: current EXTENDED_V1 still does not implement explicit H4 Candle A/B/C logic.

## Source Artifacts Used

- `research/results/failed_break_reclaim_extended_structural_matrix_2026-03-30_to_2026-05-02/structural_matrix_all_trades.csv`
- `research/results/failed_break_reclaim_extended_large_window_prep_2026-03-10_to_2026-05-03/extended_v1_setups.csv`
- `research/results/failed_break_reclaim_h4_extended_v1_entry_review_2026-03-30_to_2026-05-02.csv`
- `analyzer/research_variants.py`
- `analyzer/research_replay_bridge.py`
- `analyzer/swings.py`
- `analyzer/sweeps.py`
- `analyzer/failed_breaks.py`
- `analyzer/events.py`
- `analyzer/setups.py`
- `backtester/placement.py`
- `backtester/engine.py`

