# SHI RESET 39A — Master Research-to-Monitor Alignment Audit

Date: 2026-07-02
Task: SHI_RESET_39A_MASTER_RESEARCH_TO_MONITOR_ALIGNMENT_AUDIT_V0
Scope: documentation / audit only

## 0. Hard boundary

This audit is a canonical alignment document only.

It does not change trading logic, feed data, market_monitor behavior, Executor behavior, old analyzer behavior, or old backtester behavior. It does not promote any setup, pattern, replay result, shortlist row, or manual chart interpretation into strategy/edge/live-readiness.

Current project state after this audit:

- active candidates: NONE
- replay candidates: NONE
- holdout candidates: NONE
- Executor/live: FORBIDDEN
- Phase 4 / execution-design readiness: NOT OPEN
- old analyzer/: LEGACY / FAILED / READ-ONLY
- old backtester/: LEGACY / AUDIT REQUIRED / NOT ACTIVE FOR CURRENT MONITOR
- setup_builder: context candidate generator only, not a final setup engine

## 1. Evidence classes

| Evidence class | Meaning |
|---|---|
| CODE_CONFIRMED | Directly visible in reusable market_monitor/setup_builder/replay/policy code available in the reviewed repo snapshot. |
| RUN_ARTIFACT_CONFIRMED | Visible in generated 38S/38T/38U/38V/38W/38W1/38X/38Y output files available to this audit. |
| CANONICAL_DOC_CONFIRMED | Already stated in existing canonical docs. |
| MANUAL_REVIEW_CONCLUSION | Chart/manual/chat-level interpretation preserved for future design, but not current code behavior. |
| NOT_VERIFIED | Referenced by task or discussion but not found/provable from available files. |

Do not collapse these classes. A run artifact is not reusable code. A manual conclusion is not code behavior. A research replay is not live readiness.

## 2. Availability / missing artifact ledger

| Item | Availability | Evidence class | Notes |
|---|---:|---|---|
| GitHub `main` README / AGENTS / ACTIVE_DOCS / PROJECT_STATE / NEXT_TASK | FOUND | CANONICAL_DOC_CONFIRMED | GitHub `main` still stated reset/research-only boundaries. |
| GitHub `main` `PROJECT_LOG.md` | NOT_FOUND | NOT_VERIFIED | The file was requested for update, but was not present on GitHub `main`; this task creates it as a documentation log. |
| GitHub `main` `docs/SHI_MARKET_MONITOR_CURRENT_ARCHITECTURE.md` | NOT_FOUND | NOT_VERIFIED | Referenced by task, but absent from GitHub `main`; no facts inferred from that path. |
| Attached repository ZIP `Aitrader.zip` | FOUND | CANONICAL_DOC_CONFIRMED / RUN_ARTIFACT_CONFIRMED / CODE_CONFIRMED | Used as the available repo snapshot containing 38-chain docs/runs and current setup_builder code. |
| Attached `SHI_RESET_38W_full_feed_setup_builder_outcome_replay_v0.zip` | FOUND | RUN_ARTIFACT_CONFIRMED | Used for 38W replay file availability and summary-level evidence. |
| `research/canonical/*38S*` in attached repo snapshot | FOUND | CANONICAL_DOC_CONFIRMED | 38S docs exist in attached snapshot; not present on GitHub `main` search. |
| `research/canonical/*38T*` in attached repo snapshot | FOUND | CANONICAL_DOC_CONFIRMED | 38T quality-control audit exists in attached snapshot. |
| `research/canonical/*38U*` in attached repo snapshot | FOUND / untracked in local snapshot | CANONICAL_DOC_CONFIRMED with caveat | Present in attached snapshot but local git status showed it untracked; treat as available audit evidence, not merged canonical code state. |
| `research/canonical/*38V*` | NOT_FOUND in attached repo snapshot search | NOT_VERIFIED | No 38V canonical doc was found in the available attached snapshot search. |
| `research/canonical/*38W*` | Attached 38W run zip FOUND; canonical 38W doc not found in attached repo snapshot search | RUN_ARTIFACT_CONFIRMED / NOT_VERIFIED | 38W run output is available from attached zip; separate canonical 38W doc not verified. |
| `research/canonical/*38W1*` | NOT_FOUND in attached repo snapshot search | NOT_VERIFIED | 38W1 corrected conclusions are referenced by task/chat but not verified as a canonical file in the available snapshot. |
| `research/canonical/*38X*` | NOT_FOUND in attached repo snapshot search | NOT_VERIFIED | Referenced by task/chat, not proven from available files. |
| `research/canonical/*38Y*` | NOT_FOUND in attached repo snapshot search | NOT_VERIFIED | Referenced by task/chat, not proven from available files. |
| `market_monitor_runs/SHI_RESET_38S*` | FOUND in attached repo snapshot | RUN_ARTIFACT_CONFIRMED | Run directories available in attached snapshot. |
| `market_monitor_runs/SHI_RESET_38T*` | FOUND in attached repo snapshot | RUN_ARTIFACT_CONFIRMED | Run directory available in attached snapshot. |
| `market_monitor_runs/SHI_RESET_38U*` | FOUND in attached repo snapshot | RUN_ARTIFACT_CONFIRMED | Run directory available in attached snapshot. |
| `market_monitor_runs/SHI_RESET_38V_full_feed_38s_to_setup_builder_crosscheck_v0/` | NOT_FOUND in attached repo snapshot search | NOT_VERIFIED | Requested path was not found in the available snapshot search. |
| `market_monitor_runs/SHI_RESET_38W_full_feed_setup_builder_outcome_replay_v0/` | FOUND as attached zip | RUN_ARTIFACT_CONFIRMED | Available through the separate attached 38W zip. |
| `market_monitor_runs/SHI_RESET_38W1_corrected_conclusions_v0/` | NOT_FOUND in attached repo snapshot search | NOT_VERIFIED | Referenced by task/chat, not available as directory in attached snapshot search. |
| `market_monitor_runs/SHI_RESET_38X_up_side_stop_symmetry_and_replay_audit_v0/` | NOT_FOUND in attached repo snapshot search | NOT_VERIFIED | Referenced by task/chat, not available as directory in attached snapshot search. |
| `market_monitor_runs/SHI_RESET_38Y_research_audit_to_code_traceability_from_37d_v0/` | NOT_FOUND in attached repo snapshot search | NOT_VERIFIED | Referenced by task/chat, not available as directory in attached snapshot search. |

## 3. Current architecture

### 3.1 Aggregator / feed

Evidence class: CANONICAL_DOC_CONFIRMED

The project remains BTC Market State Monitor research infrastructure. The feed and recovered feed are core data-lineage assets. They are not modified by this audit.

Raw market data expectations remain descriptive: timestamped OHLCV/order-flow style rows plus available OI/funding/liquidation fields when present. This audit does not add, repair, synthesize, or backfill feed rows.

### 3.2 Base Market Monitor

Evidence class: CODE_CONFIRMED / CANONICAL_DOC_CONFIRMED

The current monitor sees pieces of market behavior:

- feed / OHLCV / volume / delta context;
- OI/funding/liquidation context where source fields exist;
- structure levels;
- liquidity zones;
- zone registry carry-forward;
- touches / crosses / events;
- market_structure_state outputs used downstream;
- selected zones and hidden-flow context used by setup_builder.

The monitor is still research infrastructure. It does not produce entries, exits, orders, position sizing, PnL, or live instructions.

### 3.3 Memory state

Evidence class: CODE_CONFIRMED / MANUAL_REVIEW_CONCLUSION

Current memory that exists:

- zone registry memory / carry-forward exists;
- market_structure_state exists and is used by setup_builder;
- selected-zones visibility exists as one effective downstream context source.

Current memory that remains incomplete:

- full per-level lifecycle memory is not complete: formed -> touched -> penetrated -> sweep candidate -> reclaim / accepted break -> retest -> strengthened/weakened/invalidated;
- level behavior is not yet promoted into a strict reusable lifecycle state machine;
- lower/upper supports or resistances can be hidden from the effective setup_builder context if they are not selected/promoted into the visible context used by builder.

### 3.4 Setup Builder

Evidence class: CODE_CONFIRMED / MANUAL_REVIEW_CONCLUSION

The current setup_builder is a downstream context candidate generator. It is not a full setup engine.

It uses market_structure_state timeline, market_regime_windows, selected_zones filtered by visibility, optional hidden_flow candidates if provided, pressure scores and contextual state labels.

It does not yet fully implement confirmed sweep as a sequence/lifecycle event, next 1-3 H1 confirmation after penetration, counter-sweep invalidation, accepted break vs reclaim lifecycle classifier, hard support/resistance blocker using all relevant market_structure_levels, target resolver beyond visible selected_zones, last-wagon / prior move maturity, minimum structural risk / meaningful R validation, full SL/TP/BE trade policy as strategy logic, or local sequence direction override versus broad market state.

Therefore: setup_builder rows are research candidates/context rows only. They are not trade candidates and are not live-ready.

### 3.5 Replay / policy layers

Evidence class: CODE_CONFIRMED / RUN_ARTIFACT_CONFIRMED / NOT_VERIFIED where 38W1 is referenced

Reusable replay/policy files exist in the market_monitor layer, including fixed-stop / policy replay tooling. 38W replay artifacts are available from the attached 38W zip. The task-level conclusion that 38W1 corrected TP1/stop chronology is preserved as a required conclusion, but the specific 38W1 directory/file was not found in the available snapshot and is therefore marked NOT_VERIFIED in this audit.

Micro-risk TP1 hits, especially 130-200 USD BTC risk, must not be treated as structural trade-quality evidence without minimum structural-risk validation. This is a preserved manual/research conclusion, not a current code-enforced rule.

## 4. Old analyzer and old backtester

Evidence class: CANONICAL_DOC_CONFIRMED

Old analyzer/ remains legacy / failed / read-only. It is not the active source of current 38-chain candidates. It must not be used to explain 38S/38T/38V/38W outputs as current architecture behavior.

Old backtester/ remains legacy / audit-required / possible future reusable parts only. It is not the active validation engine for current Market Monitor. Running old Backtester replay campaigns remains out of scope.

## 5. 38-chain alignment

### 5.1 38S / 38T / 38U

Evidence class: CANONICAL_DOC_CONFIRMED / RUN_ARTIFACT_CONFIRMED / MANUAL_REVIEW_CONCLUSION

38S/38T/38U are research/audit artifacts, not strategy code.

Preserved conclusions:

- 38S 227 rows were permissive discovery/context rows, not canonical setup_builder candidates.
- 38T/38S contain useful local sweep/reclaim research logic but overgenerate pseudo-sweeps.
- 38U specimen-like review was post-generation evidence review, not a pre-filter and not a live setup source.
- 31.05-like rows are weak pseudo-sweeps/local noise and should not become confirmed sweep events without lifecycle proof.
- 29.05-like and 09.06-like rows show useful local sweep/reclaim behavior, but require sequence/lifecycle classification before promotion.
- 38S/38T must not be used as source candidates without a stricter event lifecycle classifier.

### 5.2 38V / 38W / 38W1 / 38X / 38Y

Evidence class: RUN_ARTIFACT_CONFIRMED for attached 38W zip; NOT_VERIFIED for unavailable 38V/38W1/38X/38Y files/directories

38W outcome/policy replay artifacts are available from the attached 38W zip and are preserved as run-artifact evidence only. They are not edge proof and do not create live readiness.

38V, 38W1, 38X, and 38Y are referenced by the task and chat-level conclusions, but the requested directories/canonical files were not found in the available repository snapshot search. Their conclusions are therefore preserved only as MANUAL_REVIEW_CONCLUSION or NOT_VERIFIED unless later files are supplied.

## 6. Agreed terminology

Evidence class: MANUAL_REVIEW_CONCLUSION / PROMOTION_BACKLOG

Sweep-quality is not a gate. A raw level penetration is not yet a sweep. Sweep is not a candle. Sweep is a sequence.

Canonical event sequence:

1. The penetration candle creates `LEVEL_PENETRATION` / `SWEEP_CANDIDATE` only.
2. Final classification requires the next 1-3 H1 candles.
3. If following candles close beyond the broken level, classify as `ACCEPTED_BREAKDOWN` / `ACCEPTED_BREAKOUT`.
4. If following candles reclaim the level, classify as `FAILED_BREAK_RECLAIM` / `CONFIRMED_SWEEP_RECLAIM`.
5. If a counter-sweep appears inside the confirmation window, the previous directional setup can be invalidated or reversed.
6. A support sweep can be a valid event but still fail to become a long setup if the following sequence creates counter-sweep/seller response.

This terminology is expanded in `docs/SHI_MARKET_MONITOR_TERMINOLOGY_AND_EVENT_LIFECYCLE.md`.

## 7. Control-case conclusions

Evidence class: MANUAL_REVIEW_CONCLUSION unless otherwise noted in the ledger

The control-case ledger created with this audit is the canonical place to preserve case-level interpretation without presenting it as current code behavior.

High-level conclusions:

- 2026-05-26: valid upper sweep / failed breakout / DOWN continuation specimen.
- 2026-05-29 14:59: support sweep event with volume/wick/reaction, but not automatically a valid long setup because following sequence created counter-sweep/seller response.
- 2026-05-29 17:59-18:59: counter-sweep / seller response after failed UP continuation.
- 2026-05-31: pseudo-sweeps / local noise; should not become confirmed sweep events.
- 2026-06-01: accepted breakdown through 72.6K support zone; valid DOWN continuation case.
- 2026-06-05: late short into support / lower support plate not treated as effective Major blocker by setup_builder; small-R TP1 reaction is not structural trade-quality evidence.
- 2026-06-09: multi-H1 support sweep/reclaim around 61.15K; builder read it as DOWN, but local sequence is closer to UP support reclaim / failed breakdown.
- 2026-06-10: repeated retests/reactions around 61.15K confirming level behavior.

## 8. Implementation promotion candidates

Evidence class: MANUAL_REVIEW_CONCLUSION / PROMOTION_BACKLOG

These are documentation-only future candidates. They are not implemented by 39A and no tests are created for them here.

1. Level lifecycle memory.
2. Sweep sequence classifier with next 1-3 H1 confirmation.
3. Counter-sweep invalidation.
4. Accepted break vs reclaim classifier.
5. Support/resistance blocker for setup_builder.
6. Target resolver using market_structure_levels, not only visible selected_zones.
7. Last-wagon by prior move distance/maturity.
8. Minimum structural risk / meaningful R validation.
9. Local sequence direction override versus broad market state.

The detailed backlog is in `docs/SHI_MARKET_MONITOR_KNOWN_GAPS_AND_NEXT_PROMOTIONS.md`.

## 9. Final 39A verdict

Evidence class: CANONICAL_DOC_CONFIRMED / MANUAL_REVIEW_CONCLUSION

39A becomes the current source-of-truth alignment audit after review.

No new code promotion should happen until this audit is reviewed. The next promotion must first decide whether to implement the lifecycle/sweep terminology as code, and must not reuse 38S/38T rows directly as candidates.

Final state:

- documentation aligned around research-only Market Monitor;
- setup_builder remains context generator, not final setup engine;
- sweep must be redefined as sequence/lifecycle event before new setup logic is added;
- 38S 227 rows remain discovery-only;
- 38W/38W1-style replay evidence remains replay evidence, not edge proof;
- chat/manual conclusions are preserved separately from code-confirmed facts;
- missing/unavailable artifacts are explicitly marked NOT_FOUND / NOT_VERIFIED.
