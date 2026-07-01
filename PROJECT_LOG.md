# Project Log

Compact handoff log for AiTrader. This file is the index; detailed evidence remains in `research/canonical/` and generated outputs under `market_monitor_runs/`.

## Long Project Timeline

### Feed / Aggregator Foundation

- Representative commits: `3f9219e`, `1908ef8`
- Built the Binance BTCUSDT feed collector and fixed early candle/OI handling.
- Durable assets: `binance_aggregator_shi.py`, `feed/`, feed schema discipline.
- Current docs: `docs/FEED_CONTRACT_AND_SCHEMA_NOTES.md`

### Analyzer v1 Phase 1 - Feature And Event Primitives

- Representative commits: `c6b96fb`, `e4c3552`, `efb98c3`, `9ca9235`, `52ff959`
- Built strict feed contracts, base metrics, swing detection, sweep detection, failed-break detection, event normalization, and absorption/context features.
- Current status: low-level ideas may be audited for reuse, but Analyzer v1 is not active strategy logic.

### Analyzer v1 Phase 2 - Research Rows And Shortlists

- Representative commits: `0e233f3`, `72f60cd`, `93180bc`, `a916a2e`, `1f92822`, `fdee2af`, `d9b3946`
- Built setup extraction, enrichment, lifecycle annotations, outcomes, rankings, selections, shortlist exports, explanations, and research summaries.
- Current status: archived as evidence. It produced deterministic artifacts but promoted weak research objects.

### Backtester / Replay Infrastructure

- Representative commits: `a80e755`, `d9b8339`, `95fe1d6`, `2e0ab88`, `9f0a526`, `ae4ad02`, `2fd7cea`, `d780beb`, `2ed6107`, `4f25799`
- Built rulesets, replay engine, trade ledger, metrics, validation, robustness, promotion decisions, campaign orchestration, deterministic exit resolution, and placement contracts.
- Current status: legacy validation harness candidate. It may become useful again only after the Market Monitor candidate contract is explicit.

### Research Operations / H2 / Sprint 02-10

- Representative commits: `67f3819`, `5ac0cd6`, `dae7b63`, `6040e5b`, `3086f8f`, `23d1cc3`, `887e212`, `9ad4e53`
- Built weekly research operations, H2 impulse/reclaim investigations, recovered-feed validation, formal candidates, replay specs, and holdout tracking.
- Current status: negative evidence and archived context. The branch failed as a strategy path.

### Analyzer v1 Reset And Archive

- Representative commits: `928bcc6`, `d7de18a`, `e955d77`, `7611712`, `2c3f40d`
- Canonical docs:
  - `STAGE_1_FAILED_RESEARCH_SUMMARY.md`
  - `research/canonical/SHI_RESET_2026_05_ANALYZER_V1_VERDICT.md`
  - `research/canonical/ARCHIVE_MANIFEST_FAILED_ANALYZER_V1.csv`
- Result: Analyzer v1 and Sprint 02-10 were closed. The next architecture became BTC Market State Monitor.

### Market Monitor Foundation - SHI_RESET_01 To 36C

- Representative commits: `542ff83`, `3f390fe`, `2166eef`, `3c0c80f`, `e02ce23`, `a4f31d9`, `dbfe8ab`, `80a933c`, `cde8213`, `406e017`, `8e80d63`, `39f698f`, `c087007`
- Built Market Monitor skeleton, structure/liquidity zones, zone registry carry-forward, lifecycle event log, unresolved sweep candidates, post-sweep observations, batch research, scoring, label taxonomy, visible liquidity structure monitor, M15 registry, significant zone selector, and trader snapshot builder.
- Current status: active research foundation.

### Hidden Flow And Market State - SHI_RESET_37A To 37K

- Representative commits: `f66be3f`, `117c5b1`, `5744a14`, `5a7f862`, `4c9038d`, `c83564f`, `1d868e8`
- Canonical docs include:
  - `research/canonical/SHI_RESET_37_HIDDEN_FLOW_RESEARCH_LOG_2026_06_10.md`
  - `research/canonical/SHI_RESET_37E_FAILED_REGIME_CLASSIFICATION_AUDIT_2026_06_28.md`
  - `research/canonical/SHI_RESET_37F_REAL_DATE_REGIME_VALIDATION_2026_06_28.md`
  - `research/canonical/SHI_RESET_37K_LIVE_REPLAY_SETUP_TIMELINE_AUDIT_2026_06_29.md`
- Built hidden-flow research, episode context, market-structure state memory, classifier repair, and live replay setup timeline.
- Current status: active context lineage for the 38-chain.

## Recent SHI_RESET_38 Chain

### SHI_RESET_38A - Setup Replay Validation

- Canonical audit: `research/canonical/SHI_RESET_38A_SETUP_REPLAY_VALIDATION_AUDIT_2026_06_29.md`
- Run output root: `market_monitor_runs/SHI_RESET_38A_setup_replay_validation_v0/`
- Result: replay validation of existing 37K setup timeline rows.

### SHI_RESET_38B - ARMED Manual Review Pack

- Canonical audit: `research/canonical/SHI_RESET_38B_ARMED_SETUP_MANUAL_REVIEW_AUDIT_2026_06_29.md`
- Run output root: `market_monitor_runs/SHI_RESET_38B_armed_setup_manual_review_pack_v0/`
- Result: built manual review pack for ARMED setup rows.

### SHI_RESET_38C - ARMED Manual Verdict And Sequence Audit

- Canonical audit: `research/canonical/SHI_RESET_38C_ARMED_MANUAL_VERDICT_AND_SEQUENCE_AUDIT_2026_06_29.md`
- Run output root: `market_monitor_runs/SHI_RESET_38C_armed_manual_verdict_and_sequence_audit_v0/`
- Result: recorded manual chart-review verdicts for 9 ARMED setup rows and classified sequence roles.
- Next implication: replay outcome alone is insufficient; future review must split by sequence role.

### SHI_RESET_38D To 38I - Policy, Price Reference, Live-Like Replay, Stops

- Canonical audits:
  - `research/canonical/SHI_RESET_38D_POLICY_REPLAY_VARIANTS_AUDIT_2026_06_29.md`
  - `research/canonical/SHI_RESET_38E_PRICE_REFERENCE_SEMANTICS_AUDIT_2026_06_29.md`
  - `research/canonical/SHI_RESET_38F_PRICE_REFERENCE_CONTRACT_FIX_AUDIT_2026_06_29.md`
  - `research/canonical/SHI_RESET_38G_LIVE_LIKE_BAR_BY_BAR_STATE_REPLAY_AUDIT_2026_06_29.md`
  - `research/canonical/SHI_RESET_38H_STRUCTURAL_SWING_STOP_RESOLVER_AUDIT_2026_06_29.md`
  - `research/canonical/SHI_RESET_38I_POLICY_REPLAY_FIXED_ANCHORS_STRUCTURAL_STOPS_AUDIT_2026_06_29.md`
  - `research/canonical/SHI_RESET_38I_TP1_BE_EVENT_ORDER_FIX_AUDIT_2026_06_29.md`
- Run output roots include:
  - `market_monitor_runs/SHI_RESET_38D_policy_replay_variants_v0/`
  - `market_monitor_runs/SHI_RESET_38G_live_like_bar_by_bar_state_replay_v0/`
  - `market_monitor_runs/SHI_RESET_38H_structural_swing_stop_resolver_v0/`
  - `market_monitor_runs/SHI_RESET_38I_policy_replay_fixed_anchors_structural_stops_v0/`
- Result: clarified policy variants, fixed setup price semantics, added live-like bar-by-bar replay, resolved structural stops, and fixed TP1/BE event ordering.

### SHI_RESET_38J To 38O - Wider Window And Qualified H1 Sequence

- Canonical audits:
  - `research/canonical/SHI_RESET_38J_WIDER_RESEARCH_WINDOW_2026_05_23_TO_2026_06_10_AUDIT_2026_06_29.md`
  - `research/canonical/SHI_RESET_38K_MANUAL_CORRECTION_AUDIT_2026_06_30.md`
  - `research/canonical/SHI_RESET_38M_SWEEP_RECLAIM_DEFINITION_AUDIT_2026_06_30.md`
  - `research/canonical/SHI_RESET_38M_QUALIFIED_H1_SWEEP_RECLAIM_CONTRACT_2026_06_30.md`
  - `research/canonical/SHI_RESET_38N_QUALIFIED_H1_SWEEP_RECLAIM_REPLAY_ON_38J_WINDOW_AUDIT_2026_06_30.md`
  - `research/canonical/SHI_RESET_38O_SEQUENCE_WINDOW_QUALIFIED_H1_REPLAY_AUDIT_2026_06_30.md`
- Run output roots include:
  - `market_monitor_runs/SHI_RESET_38J_wider_research_window_2026_05_23_to_2026_06_10_v0/`
  - `market_monitor_runs/SHI_RESET_38N_qualified_h1_sweep_reclaim_replay_on_38j_window_v0/`
  - `market_monitor_runs/SHI_RESET_38O_sequence_window_qualified_h1_replay_v0/`
- Result: separated raw sweep from qualified H1 sweep/reclaim and confirmed the 2026-05-26 sequence-window trigger.

### SHI_RESET_38P / 38Q - Stage Gate And Stop Anchor Correction

- Commit: `31ba79f Add stage gate replay and fix sequence stop anchoring`
- Canonical audits:
  - `research/canonical/SHI_RESET_38P_FULL_WINDOW_STAGE_GATE_REPLAY_AUDIT_2026_06_30.md`
  - `research/canonical/SHI_RESET_38P_TP1_BE_DIRECTIONAL_ACTIVATION_FIX_AUDIT_2026_06_30.md`
  - `research/canonical/SHI_RESET_38Q_SEQUENCE_LINKED_STOP_ANCHOR_FIX_AUDIT_2026_06_30.md`
- Run output roots:
  - `market_monitor_runs/SHI_RESET_38P_full_window_stage_gate_replay_v0/`
  - `market_monitor_runs/SHI_RESET_38P_tp1_be_directional_activation_fix_v0/`
  - `market_monitor_runs/SHI_RESET_38Q_sequence_linked_stop_anchor_fix_v0/`
- Result: one 2026-05-26 row passed to policy replay; BE-before-TP semantics were fixed; invalid inside-sweep stop `76717.03935` was replaced with `78077.1`.

### SHI_RESET_38R - Sequence-Linked Candidate Evidence Pack

- Commit: `3c35a71 Record sequence-linked candidate evidence pack`
- Canonical audit: `research/canonical/SHI_RESET_38R_SEQUENCE_LINKED_CANDIDATE_EVIDENCE_PACK_AUDIT_2026_06_30.md`
- Run output root: `market_monitor_runs/SHI_RESET_38R_sequence_linked_candidate_evidence_pack_v0/`
- Result: packaged the first confirmed research specimen, `setup_000002` on 2026-05-26.
- Key path: H1 sweep `2026-05-26T14:59:00Z`, entry candidate/reclaim close `2026-05-26T15:59:00Z`, setup review `2026-05-26T16:59:00Z`, corrected stop `78077.1`, TP1 `74876.5`, target `72713.263462`, outcome `TP1_THEN_TARGET`.

### SHI_RESET_38S - Full-Feed Live-Like Setup Discovery Redo

- Commit: `c06ad73 Record full feed live-like discovery scan`
- Canonical audit: `research/canonical/SHI_RESET_38S_REDO_FULL_FEED_LIVE_LIKE_SETUP_DISCOVERY_AUDIT_2026_06_30.md`
- Run output root: `market_monitor_runs/SHI_RESET_38S_redo_full_feed_live_like_setup_discovery_v0/`
- Result: processed `2026-03-11T13:45:00Z -> 2026-06-28T23:59:00Z`, generated 227 setup/context rows, 140 sequence-linked policy-allowed candidates, and reproduced the 2026-05-26 specimen without using 38J rows.
- Next implication: required QC because all 227 rows became ARMED and both UP/DOWN contexts passed too easily.

### SHI_RESET_38T - Full-Feed Discovery Quality Control

- Commit: `434f10f Record full feed discovery quality control audit`
- Canonical audit: `research/canonical/SHI_RESET_38T_FULL_FEED_DISCOVERY_QUALITY_CONTROL_AUDIT_2026_06_30.md`
- Run output root: `market_monitor_runs/SHI_RESET_38T_full_feed_discovery_quality_control_v0/`
- Result: reviewed 227 setup rows and 140 policy-allowed candidates; found 8 specimen-like primary setup ids, 17 data-quality review candidates, 6 bad R-profile rejects, and 29 weak sweep rejects.
- Key conclusion: 38S redo is a permissive research scanner with overgeneration. 38T is quality-control evidence, not edge proof.
- Next implication: review 38T shortlist and tighten scanner/candidate contract before statistical interpretation or Backtester gating.
- Post-38U clarification: these rows are permissive discovery rows from a run artifact, not canonical `setup_builder` candidates.


### SHI_RESET_38U - Specimen-Like Candidate Evidence Review

- Canonical audit: `research/canonical/SHI_RESET_38U_SPECIMEN_LIKE_CANDIDATE_EVIDENCE_REVIEW_2026_07_01.md`
- Run output root: `market_monitor_runs/SHI_RESET_38U_specimen_like_candidate_evidence_review_v0/`
- Result: reviewed only the 8 38T `SPECIMEN_LIKE_PRIMARY_CANDIDATE` rows. Verdict counts: 1 `CANONICAL_MATCH_STRONG`, 6 `CANONICAL_MATCH_PARTIAL`, and 1 `SPECIMEN_LIKE_NUMERIC_ONLY`.
- Key conclusion: 2026-05-26 remains the only strong canonical research specimen; the other seven are partial or numeric relatives. This is partial repeatability and needs rule tightening.
- Next implication: 38V must compare the 227 38S discovery rows against canonical Market Monitor `setup_builder` output before broader statistical interpretation.

### SHI_RESET_DOCS_ARCHITECTURE_ALIGNMENT_POST_38U

- Canonical docs updated: `README.md`, `AGENTS.md`, `docs/ACTIVE_DOCS.md`, `research/canonical/PROJECT_STATE_CURRENT.md`, `NEXT_TASK_MARKET_MONITOR.md`, and `docs/SHI_MARKET_MONITOR_CURRENT_ARCHITECTURE.md`.
- Result: reclassified 38S 227 rows as permissive discovery/context rows generated by a run script under `market_monitor_runs/`, not by old Analyzer v1 and not by canonical `setup_builder.py`.
- Boundary preserved: Analyzer v1 remains legacy/read-only; Backtester remains future/audit-required; Executor remains future.
- Next task: `SHI_RESET_38V_FULL_FEED_38S_TO_SETUP_BUILDER_CROSSCHECK_V0`.

## Log Maintenance Rule

For every future SHI_RESET task, add a short entry here after the canonical audit is written. The entry should point to the commit, audit file, run-output directory, verification result, and next implication.
