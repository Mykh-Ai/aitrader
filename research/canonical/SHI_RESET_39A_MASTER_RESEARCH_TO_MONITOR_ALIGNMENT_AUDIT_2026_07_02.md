# SHI RESET 39A Master Research-To-Monitor Alignment Audit

Verdict: `PASS / DOCUMENTATION_ALIGNMENT_CREATED`

Date: 2026-07-02

Reviewed checkout: `f87cf33787de96bbe3acd39af0d506666a3b9e6a` plus the visible working-tree 38X target-reference change in `market_monitor/setup_builder.py` and its tests. This 39A task did not modify either source file.

## Scope And Governance

This is the canonical master alignment audit for the 38S/38T/38U/38V/38W/38W1/38X/38Y research chain and the current reusable Market Monitor architecture.

It is documentation/audit only. It does not change trading logic, add filters, modify feed data, activate Analyzer or Backtester, add Executor behavior, claim PnL, prove edge, or establish live readiness. No new code promotion should occur until this audit is reviewed.

## Evidence Classes

| Evidence class | Meaning |
| --- | --- |
| `CODE_CONFIRMED` | Directly visible in current reusable `market_monitor/` or related replay/policy code. |
| `RUN_ARTIFACT_CONFIRMED` | Directly visible in generated 38S-38Y outputs; not automatically reusable code. |
| `CANONICAL_DOC_CONFIRMED` | Directly stated in an existing file under `research/canonical/`. |
| `MANUAL_REVIEW_CONCLUSION` | Preserved chart/chat/manual interpretation that is not current code behavior. |
| `NOT_VERIFIED` | Missing or not provable from the reviewed files. `NOT_FOUND` names a missing path. |

Classes are not interchangeable. In particular, run scripts under `market_monitor_runs/` are not reusable monitor modules, and manual interpretations are not setup-builder behavior.

## Artifact Availability And Confidence

| Requested evidence | Availability | Classification and use |
| --- | --- | --- |
| 38S canonical audits | FOUND | `CANONICAL_DOC_CONFIRMED` plus run artifacts. |
| 38T canonical audit | FOUND | `CANONICAL_DOC_CONFIRMED` plus run artifacts. |
| `research/canonical/*38U*` | `NOT_FOUND` | 38U conclusions are `RUN_ARTIFACT_CONFIRMED` only in this checkout. Existing docs that name a canonical 38U file are stale pointers. |
| `research/canonical/*38V*` | `NOT_FOUND` | 38V conclusions are `RUN_ARTIFACT_CONFIRMED`. |
| `research/canonical/*38W*` / `*38W1*` | `NOT_FOUND` | 38W/38W1 conclusions are `RUN_ARTIFACT_CONFIRMED`. |
| `research/canonical/*38X*` | `NOT_FOUND` | 38X findings are run-artifact evidence plus current visible code/test state. |
| `research/canonical/*38Y*` | `NOT_FOUND` | 38Y is a documentation run artifact, not a canonical audit. |
| requested `market_monitor_runs/SHI_RESET_38W1_corrected_conclusions_v0/` | `NOT_FOUND` | The verified available root is `market_monitor_runs/SHI_RESET_38W1_fix_chronological_tp1_stop_labels_v0/`. |

No missing canonical artifact was reconstructed from memory.

## Current Architecture

The current research chain is:

`feed -> normalized Market Monitor feed -> structure levels -> liquidity zones -> zone registry/carry-forward -> event log and post-sweep observation -> significant-zone selection -> hidden-flow windows -> market_structure_state -> setup_builder context rows -> optional qualified H1 sequence/stage gates -> replay/policy evidence -> run-specific QC/manual review`

| Layer | Current behavior | Evidence class |
| --- | --- | --- |
| Feed adapter | Normalizes OHLC, quantity/volume, trades, BuyQty, SellQty, OI, funding, provenance, and timestamps. Missing numeric context fields are zero-filled. | `CODE_CONFIRMED` |
| Liquidation visibility | `visual_overlay.py` can display `LiqBuyQty`/`LiqSellQty` when present, but the base `feed_adapter.py` output does not carry those columns and current hidden-flow/selector artifacts mark liquidations unavailable. | `CODE_CONFIRMED`; 38V absence is `RUN_ARTIFACT_CONFIRMED` |
| Structure | Builds daily/session references, confirmed M15/H1/H4 swings, equal levels, and pattern-derived levels. | `CODE_CONFIRMED` |
| Liquidity and memory | Builds zones and carries a registry with touch/cross counts, first sweep, resweeps, acceptance timestamps, reaction/consumption state, and HTF lifecycle metrics. | `CODE_CONFIRMED` |
| Events | Emits approaches, touches, crossed-unclassified events, unresolved sweep observations, merges, expiry, and registry lifecycle updates. | `CODE_CONFIRMED` |
| Zone selection | Scores the full zone inventory, then exposes a bounded `visible_on_snapshot` subset. The 38V support run had 5,338 candidates but only 7 visible zones. | `CODE_CONFIRMED`; count is `RUN_ARTIFACT_CONFIRMED` |
| Hidden flow | Builds research windows/candidates from price, volume/delta, OI, funding, zone context, and state-like features; labels remain context, not setup proof. | `CODE_CONFIRMED` |
| Market structure state | Produces `market_state`, active support/resistance, candidate bias/strength, dominant side, and pressure/demand/supply scores used by setup_builder. | `CODE_CONFIRMED` |
| setup_builder | Generates research context candidates from state, regime/hidden-flow windows, visible zones, and pressure predicates. It requires later replay and forbids execution language. | `CODE_CONFIRMED` |
| Qualified H1 detector | Evaluates completed H1 penetration at meaningful references, age/separation, prior reaction, wick and close behavior; records volume ratio; searches the next 1-3 H1 bars for a close-back reclaim. | `CODE_CONFIRMED` |
| Replay/policy | Resolves research stops/targets and enforces event ordering, including stop-before-TP1 and ambiguous same-bar outcomes. | `CODE_CONFIRMED` |
| 38S/38T/38U/38V/38W/38W1/38Y scripts | Task-specific discovery, QC, crosscheck, replay correction, and traceability logic. | `RUN_ARTIFACT_CONFIRMED` |

## What The Monitor Sees And What It Does Not Yet Decide

The reusable monitor sees price, OHLCV/quantity, trade-side delta inputs, OI, funding, structural levels, zones, touches/crosses, partial zone lifecycle state, hidden-flow context, and broad market-state context. Liquidations are surface-dependent: supported by visual overlay when raw columns exist, but not carried through the base adapter/current hidden-flow pipeline.

The registry already has meaningful memory. Therefore the gap is not “no lifecycle exists.” The gap is the absence of one canonical, setup-consumed per-level event sequence that unifies:

`formed -> touched -> penetrated -> sweep candidate -> reclaimed or accepted break -> retested -> strengthened/weakened/invalidated`

Current registry states and M1 events do not yet provide that complete H1 sequence contract to setup_builder. This distinction is `CODE_CONFIRMED`.

## What setup_builder Actually Uses

`run_setup_builder()` directly loads:

- `market_structure_state_timeline.csv`;
- regime/hidden-flow windows;
- `selected_zones.csv`, filtered to `visible_on_snapshot=true`;
- optional promoted hidden-flow candidates.

It then evaluates broad state, dominant side, pressure scores, active support/resistance, raw window labels, close position, and directional target-zone availability. It can emit seller-dominance retest, supply sweep/reclaim, demand sweep/reclaim, and accepted-breakout context rows.

This is `CODE_CONFIRMED`. The correct architectural conclusion is that setup_builder is a context candidate generator, not a final setup engine.

The following are not complete setup-builder gates:

- confirmed sweep lifecycle sequence;
- counter-sweep invalidation;
- accepted break versus reclaim classification;
- prior-move maturity / last-wagon distance;
- minimum structural risk and meaningful R;
- full SL/TP/BE policy;
- all relevant support/resistance blockers from the full structure inventory;
- local sequence direction override against broad market state.

Because setup_builder receives only visible selected zones, a valid lower support or upper resistance can be absent from its effective context even when it exists elsewhere in `market_structure_levels` or the full zone inventory. The input-boundary mechanism is `CODE_CONFIRMED`; its impact on the 2026-06-05 control case remains a `MANUAL_REVIEW_CONCLUSION` supported by run-artifact symptoms.

## Sweep And Lifecycle Alignment

The agreed terminology is canonicalized in `docs/SHI_MARKET_MONITOR_TERMINOLOGY_AND_EVENT_LIFECYCLE.md`.

Major decisions:

1. A raw level penetration is not a confirmed sweep. Evidence class: `CODE_CONFIRMED` in the raw-observation boundary and `MANUAL_REVIEW_CONCLUSION` for the broader terminology decision.
2. A sweep is a sequence, not one candle. The penetration candle creates `LEVEL_PENETRATION` / `SWEEP_CANDIDATE`; the next 1-3 closed H1 candles decide reclaim, accepted break, or invalidation. The current qualified detector implements a close-back subset, but not the full lifecycle vocabulary. Evidence class: `CODE_CONFIRMED` plus `MANUAL_REVIEW_CONCLUSION` for the expanded target contract.
3. A close that remains beyond the level belongs to accepted-break classification, not sweep confirmation. Evidence class: partial `CODE_CONFIRMED`; unified classifier is missing.
4. A counter-sweep inside the confirmation window can invalidate or reverse the earlier directional interpretation. Evidence class: `MANUAL_REVIEW_CONCLUSION`.
5. “Sweep quality” is not one current setup_builder gate. Several qualities exist in the H1 detector, while volume expansion is informational and 38T weak-sweep logic remains run-only. Evidence class: `CODE_CONFIRMED` and `RUN_ARTIFACT_CONFIRMED`.

## Research Chain Alignment

| Research stage | Preserved conclusion | Evidence class |
| --- | --- | --- |
| 38S | Produced 227 permissive discovery/context rows and 140 policy-allowed sequence rows from a run script; every discovery row was ARMED. They are not old Analyzer rows and are not canonical setup_builder candidates. | `CANONICAL_DOC_CONFIRMED`; counts also `RUN_ARTIFACT_CONFIRMED` |
| 38T | Post-generation QC found overgeneration, including 29 weak-sweep rejects, 6 bad-R rejects, 17 degraded-data review rows, and 8 specimen-like rows. Its rules are not pre-generation monitor filters. | `CANONICAL_DOC_CONFIRMED` |
| 38U | Reviewed only the 8 specimen-like rows: 1 strong, 6 partial, 1 numeric-only. It is post-generation evidence review, not a setup source. | `RUN_ARTIFACT_CONFIRMED`; canonical audit `NOT_FOUND` |
| 38V | Generated 51 setup_builder rows; only 10 of 227 38S rows matched by the crosscheck categories, with just 3 exact-time-and-type matches. The 2026-05-26 specimen survived. | `RUN_ARTIFACT_CONFIRMED` |
| 38W | Demonstrated that replay can observe reactions, but its original 51/51 TP1-quality reading was chronologically invalid. | `RUN_ARTIFACT_CONFIRMED` |
| 38W1 | Corrected chronology to 34 valid TP1-before-stop reactions, 17 stop-before-TP1 rows, and 2 target-before-stop continuations. This is corrected replay evidence, not edge proof. | `RUN_ARTIFACT_CONFIRMED` |
| 38X | Found directional target-reference fallback behavior and changed the currently visible setup_builder helper to return unresolved when no valid directional target exists. The 38W1 artifacts predate that correction and require regeneration before target interpretation. | current helper is `CODE_CONFIRMED`; audit counts are `RUN_ARTIFACT_CONFIRMED` |
| 38Y | Mapped reusable versus run-only logic and recorded missing canonical 38U-38W files. It is useful traceability evidence but remained a run artifact. | `RUN_ARTIFACT_CONFIRMED` |

## Replay, Risk, And Outcome Discipline

Chronological stop/TP1/target handling exists in reusable replay/policy code. A selected stop before TP1 is terminal; same-bar stop/TP1 is ambiguous rather than a rescued success. That is `CODE_CONFIRMED`.

38W1 is the corrected full-feed run evidence. It does not prove edge. Small-risk TP1 touches, especially roughly 130-200 USD BTC structural-risk distances, cannot establish structural setup quality without a minimum-risk and market-structure validation rule. The replay values are `RUN_ARTIFACT_CONFIRMED`; the structural-quality interpretation is `MANUAL_REVIEW_CONCLUSION` and is not implemented.

## Control Cases

The detailed ledger is `SHI_RESET_39A_CONTROL_CASE_LEDGER_2026_07_02.csv`.

| Case | Aligned conclusion | Evidence class |
| --- | --- | --- |
| 2026-05-26 | Valid upper failed-break/reclaim research specimen with DOWN continuation; remains research evidence only. | `CANONICAL_DOC_CONFIRMED` |
| 2026-05-29 14:59 | Support penetration/reaction can be a valid event without becoming a valid long; following seller response must be classified first. | `MANUAL_REVIEW_CONCLUSION` |
| 2026-05-29 17:59-18:59 | Counter-sweep/seller response invalidates the earlier automatic UP continuation reading. | `MANUAL_REVIEW_CONCLUSION` |
| 2026-05-31 | Local crossings/unresolved sweeps are noisy pseudo-sweep controls and must not auto-promote. | `MANUAL_REVIEW_CONCLUSION` supported by run events and 38V rejections |
| 2026-06-01 | Accepted breakdown through the 72.6K support region is a DOWN continuation control, not a reclaim. | `MANUAL_REVIEW_CONCLUSION` |
| 2026-06-05 | Late short into support demonstrates the visible-zone blocker gap; small-R TP1 reaction is not structural-quality proof. | `MANUAL_REVIEW_CONCLUSION` with run-artifact replay values |
| 2026-06-09 | Local 61.15K support sequence is closer to failed breakdown/support reclaim than the broad-state DOWN builder row. | `MANUAL_REVIEW_CONCLUSION`; builder/replay disagreement is `RUN_ARTIFACT_CONFIRMED` |
| 2026-06-10 | Repeated reactions around 61.15K support strengthen the level-behavior interpretation but are not a coded setup rule. | `MANUAL_REVIEW_CONCLUSION` |

## Current Gaps

The following are confirmed gaps or conservative non-promotions:

- no unified level lifecycle consumed by setup_builder (`CODE_CONFIRMED`);
- no full accepted-break/reclaim/counter-sweep sequence classifier (`CODE_CONFIRMED`);
- visible-zone-only setup context can omit a structural blocker (`CODE_CONFIRMED`);
- target resolver does not query the full market-structure level inventory (`CODE_CONFIRMED`);
- no prior-move maturity / last-wagon gate (`CODE_CONFIRMED`);
- no minimum structural-risk gate (`CODE_CONFIRMED`);
- no local sequence direction override against broad market state (`CODE_CONFIRMED`);
- 38W1 full-feed correction is still run-script logic rather than one reusable full-feed replay module (`RUN_ARTIFACT_CONFIRMED`);
- canonical 38U-38Y audit files are absent (`NOT_VERIFIED` / `NOT_FOUND`).

## Documentation-Only Promotion Candidates

Promotion candidates are recorded in `docs/SHI_MARKET_MONITOR_KNOWN_GAPS_AND_NEXT_PROMOTIONS.md` and the decision matrix. They are backlog items only:

1. unified level lifecycle memory;
2. next-1-3-H1 sweep sequence classifier;
3. counter-sweep invalidation;
4. accepted break versus reclaim classification;
5. setup_builder structural blocker from the full level/zone inventory;
6. target resolver using market structure levels, not only visible zones;
7. last-wagon / prior-move maturity;
8. minimum structural risk and meaningful R validation;
9. local sequence direction override versus broad state.

No item was implemented or tested in 39A.

## Verification

- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q`: `718 passed, 11 warnings` in 51.65 seconds.
- The warnings are existing deprecation/future warnings in `binance_aggregator_shi.py` and `analyzer/events.py`; no test failed.
- Repository-integrity checks are recorded after the final documentation edit in `PROJECT_LOG.md`.

## Final Boundary Verdict

- setup_builder remains a context generator, not a final setup engine;
- sweep must be treated as a sequence/lifecycle event before new setup logic is added;
- 38S 227 rows remain discovery-only;
- 38W1 remains corrected replay evidence, not edge proof;
- manual/chat conclusions are preserved separately from code and run facts;
- Analyzer v1 remains legacy/read-only;
- Backtester remains inactive/audit-required;
- Executor/live/readiness/PnL/position sizing remain out of scope;
- no code or feed behavior changed in this audit.
