# AiTrader / Strategy Shi
## Phase 2 Stabilization & Implementation Plan (v2.2)

### Purpose
Provide a structured roadmap to stabilize Phase 2 (Analyzer / Research pipeline), ensure reproducibility of analyzer runs, and prepare the system for controlled candidate harvesting and Phase 3 formalization.

Phase 2 is explicitly treated as a **research engine**, not a ruleset generator.

## Current Status Snapshot

- **P0 — DONE**
- **P1 — DONE**
- **P2 — DONE**
- **P3 — DONE**

**Implementation Plan Status: COMPLETED (2026-03-16)**

All phases of this plan have been implemented. The system now has a full working pipeline:

```
analyzer runs
  → Phase 2 harvesting
    → phase2_formalization_candidates.csv
      → phase2_formalization_review.csv
        → Phase 3 ruleset formalization
          → phase3_ruleset_draft.csv
            → phase3_ruleset_contract.csv
              → phase3_ruleset_mapping.csv
                → ruleset materialization (PHASE3_MAPPING_ONLY)
```

Technical capabilities delivered:

- evidence collection from multiple analyzer runs
- deterministic candidate selection
- formalization surface
- ruleset draft → contract → replay mapping chain
- explicit binding in backtester (PHASE3_MAPPING_ONLY mode)
- 356 tests passing — pipeline is stable and reproducible

Phase 2 now has:

- canonical analyzer run contract
- standardized `run_manifest.json`
- post-run artifact validation
- stabilized Phase 2 → Phase 3 bridge
- honesty metadata in shortlist and research summary
- ranking provenance via `RankingMethod`
- minimal setup provenance via `SourceTF`
- multi-day candidate harvesting
- controlled formalization candidate pipeline
- Phase 3 ruleset formalization chain

Current interpretation:

- Phase 2 is canonical and reproducible as a code/data pipeline
- Phase 2 is materially honest as a research surface
- Phase 2 → Phase 3 bridge is fully operational
- Phase 3 ruleset formalization is implemented and binding-ready
- Phase 2 remains a research / hypothesis-forming layer, not a generalized ruleset generator

---

# Core Architectural Principle

Phase 2 improvements must focus on making the system:

- reproducible
- versioned
- auditable
- statistically honest

NOT prematurely “smarter”.

Research → Harvesting → Candidate → Formalization

---

# Raw Data Handling (`raw.csv`)

## Key Principle

`raw.csv` must **never** be treated as the canonical source of raw bars.

Canonical raw lineage must always be derived from:

```text
run_manifest.json → input_feed_paths
```

`raw.csv` exists only as a **compatibility artifact**.

This prevents accidental coupling of Phase 3 to a physical file layout.

---

# Raw Source Resolution (Phase 3 Backtester)

Backtester must resolve raw bars using the following priority:

1. explicit `raw_path`
2. `run_manifest.json → input_feed_paths`
3. `artifact_dir/raw.csv` (fallback compatibility mode)

This keeps Phase 3 backward compatible while removing architectural dependence on `raw.csv`.

---

# Current Runtime Truth vs Target Contract

This document distinguishes explicitly between:

- **current runtime truth** — what current Analyzer runs actually produce today
- **target canonical contract** — the cleaned and stabilized contract to be introduced

The current runtime truth must not be silently rewritten in documentation as if it already were the target state.

---

# Current Runtime Truth (Observed Analyzer Artifact Surface)

Based on current Analyzer runs, the artifact surface is currently CSV-based and uses names such as:

- `analyzer_features.csv`
- `analyzer_events.csv`
- `analyzer_setups.csv`
- `analyzer_setup_outcomes.csv`
- `analyzer_setup_report.csv`
- `analyzer_setup_context_report.csv`
- `analyzer_setup_rankings.csv`
- `analyzer_setup_selections.csv`
- `analyzer_setup_shortlist.csv`
- `analyzer_setup_shortlist_explanations.csv`
- `analyzer_research_summary.csv`

Current format for research summary is **CSV**, not JSON.

---

# Target Canonical Artifact Contract

Canonical artifacts are **Analyzer outputs plus manifest**.

## Target canonical analyzer run directory must contain

- `run_manifest.json`
- `analyzer_features.csv`
- `analyzer_events.csv`
- `analyzer_setups.csv`
- `analyzer_setup_outcomes.csv`
- `analyzer_setup_report.csv`
- `analyzer_setup_context_report.csv`
- `analyzer_setup_rankings.csv`
- `analyzer_setup_selections.csv`
- `analyzer_setup_shortlist.csv`
- `analyzer_setup_shortlist_explanations.csv`
- `analyzer_research_summary.csv`

Optional compatibility artifact:

- `raw.csv`

Canonical raw lineage source:

```text
run_manifest.json
```

---

# Manifest Schema (Recommended)

```text
run_manifest.json

run_id
run_date
date_range

input_feed_paths
input_feed_checksums

git_commit
git_branch

python_version

analyzer_schema_version
artifact_contract_version

artifact_paths
row_counts
artifact_hashes

status
```

Two separate versioning layers are required:

- **analyzer_schema_version** — structure of Analyzer tables
- **artifact_contract_version** — layout of run directory

These must evolve independently.

For real reproducibility, checksums / hashes are strongly recommended:

- `input_feed_checksums`
- `artifact_hashes`

---

# Definition of Canonical Analyzer Run

A canonical analyzer run is a run directory that:

- contains `run_manifest.json`
- passes artifact validation
- conforms to `artifact_contract_version`
- has reproducible raw lineage
- has `status = SUCCESS`
- contains all required canonical artifacts

Canonical runs are suitable for research aggregation and Phase 3 replay.

---

# P0 — Canonical Run Contract & Artifact Integrity

**Status: DONE**

Goal: ensure every analyzer run is reproducible and structurally valid.

Tasks:

- Define target canonical artifact contract
- Standardize `run_manifest.json`
- Add post-run validation
- Mark historical runs as canonical or non-canonical

### Completed

- target canonical artifact contract defined
- `run_manifest.json` standardized
- post-run validation implemented
- schema validation implemented
- timestamp monotonicity validation implemented
- canonical/non-canonical run discipline established
- incomplete historical run identified and removed from active corpus

## Post-Run Validation

Validation must include:

1. Artifact existence check
2. Row count validation
3. Header presence
4. **Schema validation**

```text
expected_columns == actual_columns
```

5. Timestamp monotonicity

```text
timestamps must be strictly increasing
```

### Outcome

Corrupted or incomplete runs no longer silently pass as usable Analyzer outputs.
Integrity is now enforced at run boundary rather than discovered late by downstream consumers.

---

## P0.x — Phase 2 → Phase 3 Bridge Hardening

**Status: DONE**

### Completed

#### P0.1 — Raw-feed resolution hardening

Phase 3 replay raw source resolution now follows this order:

1. explicit `raw_path`
2. `run_manifest.json → input_feed_paths`
3. `artifact_dir/raw.csv` (fallback compatibility mode)

This removed the old hidden dependency on `raw.csv` as the only practical replay source.

#### P0.2 — Fail-soft shortlist ingestion

Phase 3 no longer assumes every shortlist row is directly formalizable.

Current baseline auto-formalization supports only:

- `GroupType = Direction`
- `GroupType = SetupType`

Descriptive/context-only shortlist rows are skipped with structured warnings instead of causing fatal orchestration failure.

#### P0.3 — No-event replay contract

If replay produces zero events:

- `backtest_engine_events.csv` is still written as a valid header-only CSV
- orchestration can complete with:
  - `ruleset_count = 0`
  - `engine_event_count = 0`
  - `trade_count = 0`

This makes no-event runs valid controlled outcomes rather than corrupted pipeline states.

### Outcome

Phase 2 → Phase 3 bridge is now operational and materially more robust.

---

# P1 — Research Surface Honesty

**Status: DONE**

Goal: ensure research outputs do not overstate statistical strength.

Tasks:

- Separate descriptive slices from formalization candidates
- Mark research metrics as proxies
- Add explicit implemented-status metadata for major surfaces

Examples:

- confidence model
- accepted break semantics
- session/context assumptions
- executable entry semantics

These flags should exist not only as prose, but in one of the following forms:

- manifest metadata
- dedicated `research_surface_metadata`
- explicit downstream artifact fields

Add versioning fields to research artifacts.

### Completed

#### P1.1a — Honesty metadata in shortlist and research summary

Implemented:

##### `analyzer_setup_shortlist.csv`
- `SemanticClass`
- `FormalizationPath`

##### `analyzer_research_summary.csv`
- `OutcomeSemantics`

### Outcome

- baseline-direct rows are distinguishable from descriptive/context rows
- diagnostic-only rows are distinguishable from direct formalization sources
- outcome metrics are explicitly marked as research proxy semantics

#### P1.1b — Ranking provenance

Implemented:

- `RankingMethod`

### Outcome

- ranking method is now materialized in artifacts
- ranking score is no longer presented as a provenance-free scalar

`RankingComponents` was intentionally deferred to avoid duplicate payload and schema noise.

#### P1.2a — Minimal setup provenance

Implemented:

##### `analyzer_setups.csv`
- `SourceTF`

### Outcome

- timeframe provenance is now explicit in setup artifacts instead of being hidden only inside setup identity derivation

#### P1.3 — Implemented-status metadata

Implemented in `analyzer_research_summary.csv`:

- `ConfidenceModelStatus`
- `AcceptedBreakSemanticsStatus`
- `ContextFormalizationStatus`
- `ExecutableEntrySemanticsStatus`

### Outcome

- final research artifact now carries explicit semantic disclaimers for major surfaces
- Phase 2 research layer is harder to misread as a generalized executable ruleset layer

### What P1 completion does NOT mean

P1 completion does **not** mean that Phase 2 has become a generalized ruleset generator.

It means only that:

- research artifacts are more self-describing
- descriptive/context rows are harder to misread as direct executable candidates
- ranking provenance is explicit
- outcome semantics are explicitly marked as research proxy
- setup provenance is slightly more traceable
- major semantic limitations are surfaced explicitly in final research summary

Phase 2 should still be understood as a **research / hypothesis-forming layer**, not a fully generalized formalization engine.

---

# Ranking Layer Improvements

**Status: DONE**

Completed:

- Replaced opaque `CompositeScore` with `RankingScore` + `RankingMethod`
- `RankingComponents` intentionally deferred to avoid schema noise
- Ranking evolution supported without invalidating historical runs

---

# Setup Artifacts and Lineage

**Status: DONE**

Goal: make setup artifacts usable for downstream reasoning.

Completed:

- Setup artifacts are downstream-sufficient for review, formalization, and manual analysis
- Key lineage fields implemented: `source_event_type`, `source_event_ts`, `source_tf`, `reference_swing_ts`, `reference_level`, `setup_family_version`
- `setups.csv` does not duplicate all analyzer state — only provenance-critical fields

---

# P2 — Structural Layer Hardening

**Status: DONE**

Goal: reduce structural noise without rewriting baseline semantics.

Completed:

- failed_break timeout logic
- first-cross deduplication for sweeps
- penetration filters (versioned experiments)
- baseline semantics remain stable

---

# Context Layer Improvements

**Status: DONE**

Completed:

- Context scoring labeled as heuristic (`AbsorptionScore_v1`)
- Context fields implemented (`session`, `minutes_from_eu_open`, `minutes_from_us_open`)
- `ContextModelVersion` added to downstream artifacts

---

# Multi-Day Candidate Harvesting

**Status: DONE**

Goal: move from daily snapshots to accumulating research evidence.

Completed:

- Multi-day aggregation layer across canonical runs implemented
- Provenance tracking per aggregated row (`RunId`, `RunDate`, `AnalyzerVersion`, `ArtifactContractVersion`, `RankingMethod`, `SetupFamilyVersion`, `InputRawDate`)
- Stable lead qualification: candidates must appear in multiple runs

---

# P3 — Controlled Formalization Candidate

**Status: DONE**

Goal: produce a single well-defined candidate for Phase 3.

Completed:

1. Setup family selected via deterministic candidate selection
2. TF / direction slice confirmed from multi-day evidence
3. Multi-day evidence aggregated across canonical runs
4. Handoff artifacts produced:
   - `phase2_formalization_candidates.csv`
   - `phase2_formalization_review.csv`
5. Phase 3 ruleset formalization chain:
   - `phase3_ruleset_draft.csv`
   - `phase3_ruleset_contract.csv`
   - `phase3_ruleset_mapping.csv`
6. Explicit binding mode: `PHASE3_MAPPING_ONLY`

Candidate artifacts include:

- `FormalizationStatus` (CANDIDATE_UNDER_REVIEW)
- lineage and statistical basis
- known caveats
- readiness flag

---

# Next Stage After P0–P3

All original phases (P0–P3) are complete. Next implementation targets:

1. **Phase 4 — Ruleset Validation Layer** — mandatory validation gate before replay execution
2. **Phase 5 — Experiment Registry** — structured journal of all backtest/replay runs
3. **Backtesting** — validate edge on 6-month historical data using materialized rulesets
4. **Execution** — live trading via Spot Margin API (after backtesting validation)

```text
Pipeline order:
analyzer → formalization → ruleset → validation (Phase 4) → replay → registry (Phase 5)
```

---

# Implementation Priority

| Priority | Focus | Status |
|--------|-------|--------|
| P0 | Canonical run contract, manifest, validation | DONE |
| P1 | Research honesty, ranking transparency | DONE |
| P2 | Structural & context hardening | DONE |
| P3 | Formalization candidate | DONE |
| Phase 4 | Ruleset validation layer | BASELINE IMPLEMENTED (mapping-only pre-replay gate) |
| Phase 5 | Experiment registry / batch evaluation | TODO |

---

# Final Principle

Phase 2 prioritized:

- reproducibility
- statistical honesty
- versioned research outputs

over premature trading logic complexity.

---

# Phase 4 — Ruleset Validation Layer

## Purpose

Phase 4 introduces a mandatory deterministic validation layer between ruleset materialization and replay execution.

This validation layer prevents the following invalid states from entering replay/backtester execution:

- incomplete rulesets
- placeholder configuration values
- unresolved rule boundaries
- unresolved replay mappings
- incompatible replay semantics
- contract–mapping inconsistencies

The validation layer must evaluate materialized `RulesetRows` produced by the Phase 3 pipeline.

Phase 3 produces the following artifacts:

- `phase2_formalization_candidates.csv`
- `phase2_formalization_review.csv`
- `phase3_ruleset_draft.csv`
- `phase3_ruleset_contract.csv`
- `phase3_ruleset_mapping.csv`

Rulesets are materialized using `PHASE3_MAPPING_ONLY` mode.

Phase 4 ensures that these rulesets are safe and executable before replay is allowed to begin.

## Validation Categories

Validation must include all of the following categories:

1. Structural validation
2. Placeholder / unresolved detection
3. Status readiness validation
4. Replay semantics compatibility
5. Contract–mapping consistency validation
6. Cross-artifact integrity validation

All categories are mandatory. A ruleset is replay-eligible only if it passes every category.

## Structural Validation

The following fields must exist and must be non-empty in each materialized `RulesetRow`:

- `RulesetId`
- `SetupFamily`
- `Direction`
- `EligibleEventTypes`
- `ReplaySemanticsVersion`
- `EntryTriggerMapping`
- `EntryBoundaryMapping`
- `ExitBoundaryMapping`
- `RiskMapping`

Validation behavior:

- If any required field is missing, validation must fail.
- If any required field is present but empty/blank/null-equivalent, validation must fail.
- Field-level failure reasons must be emitted in `ValidationErrors`.

Failure modes in this category include:

- schema drift between mapping output and runtime expectations
- partially materialized rows
- empty executable mapping payloads

## Placeholder / Unresolved Detection

Validation must detect unresolved placeholder values in executable fields.

The following marker families must be treated as unresolved:

- `UNRESOLVED_*`
- `NOT_YET_*`
- `MANUAL_*`

If any unresolved marker appears in fields required for execution (including entry mapping, exit mapping, risk mapping, replay semantics, or any other runtime-critical mapping field), validation must fail.

This rule is critical because placeholder markers are valid during early formalization, but must never cross into runtime execution.

Failure modes in this category include:

- draft placeholders accidentally propagated into mapping output
- unresolved rule boundaries represented as temporary tokens
- unresolved replay mapping keys left for manual follow-up

## Status Gate Validation

Replay-eligible rulesets must satisfy strict readiness status gates.

`MappingStatus` must be:

- `READY`

`ReplayIntegrationStatus` must be:

- `READY_FOR_BINDING`

Validation behavior:

- Any value outside the allowed sets must fail validation.
- Missing status fields must fail validation.
- Case-variant or free-form status strings must fail validation unless explicitly normalized upstream.

Failure modes in this category include:

- mapping marked as draft but passed to replay
- integration not explicitly acknowledged
- stale status vocabularies from prior schema versions

## Replay Semantics Compatibility

Validation must ensure that `ReplaySemanticsVersion` is supported by the currently running backtester runtime.

Validation behavior:

- Unsupported semantics versions must fail validation.
- Missing semantics version declarations must fail validation.
- Semantics versions that are syntactically present but not registered in runtime-supported versions must fail validation.

Failure modes in this category include:

- mapped rulesets targeting deprecated semantics
- forward-declared semantics not yet implemented in runtime
- accidental runtime/artifact version skew

## Contract–Mapping Consistency Validation

Validation must ensure that the Phase 3 contract artifact and Phase 3 mapping artifact are logically consistent for each ruleset.

Required checks include:

- `SetupFamily` in mapping must match `SetupFamily` defined in contract.
- `Direction` must match between contract and mapping.
- `EligibleEventTypes` in mapping must not contradict contract definition.
- `MappingVersion` must correspond to the contract version.

Validation behavior:

- Any contract–mapping mismatch must fail validation.
- Missing contract references for mapped rows must fail validation.
- Duplicate or ambiguous contract linkage for a single `RulesetId` must fail validation.

Failure modes in this category include:

- mapping rows copied from a different setup family
- direction inversion between contract and mapping
- event eligibility widened or narrowed outside contract intent
- version drift between contract revision and mapping revision

## Cross-Artifact Integrity Validation

Validation must ensure that lineage and compatibility remain intact across draft, contract, and mapping artifacts.

Required checks include:

- `RulesetId` consistency across draft, contract, and mapping artifacts
- `ContractVersion` compatibility with `MappingVersion`
- `ReplaySemanticsVersion` compatibility with mapping layer declarations

Validation behavior:

- Any lineage break must fail validation.
- Missing upstream artifact linkage must fail validation.
- Orphan mapping rows without draft/contract lineage must fail validation.

Failure modes in this category include:

- ruleset identity reuse collisions
- contract/mapping pair assembled from different generation batches
- semantics declared in one artifact but omitted or contradicted in another

## Validation Output

The validation layer must produce a structured result with at least the following fields:

- `ValidationStatus`
- `ValidationErrors`

`ValidationStatus` allowed values:

- `VALID`
- `INVALID`
- `REVIEW_REQUIRED`

`ValidationErrors` requirements:

- must be a list of explicit failure reasons
- each reason must identify the failing category and rule
- each reason should include `RulesetId` and relevant field(s) when available

Execution gate behavior:

- If `ValidationStatus == INVALID`, replay/backtester must fail loudly and stop execution.
- `REVIEW_REQUIRED` may be used only for non-executable policy checks; replay must not auto-proceed unless explicitly permitted by orchestration policy.
- Silent downgrade, silent coercion, or implicit auto-fix of invalid executable mappings is not permitted at this gate.

## Integration Point

The validation layer must run as a mandatory orchestration step after ruleset materialization and before replay execution.

Pipeline order:

`analyzer → formalization → ruleset draft → ruleset contract → ruleset mapping → ruleset materialization → ruleset validation → replay/backtesting`

Integration rules:

- Replay execution must never begin without validation.
- Validation is part of the deterministic execution contract, not an optional diagnostic.
- Validation outcomes must be recorded as orchestration artifacts/log events for auditability.

## Implementation Targets

Expected implementation components:

- `backtester/validation.py`
- `tests/test_backtester_validation.py`

Integration call site:

- `backtester/orchestrator.py`

Implementation requirements:

- Validation must execute automatically before replay execution begins.
- Orchestrator must enforce hard-gate behavior on invalid results.
- Validation logic must remain deterministic for identical artifact inputs.

---

# Phase 5 — Experiment Registry / Batch Evaluation Layer

## Purpose

Phase 5 introduces a structured experiment registry — an artifact journal of every backtest/replay run.

Without a registry, after 5–10 replay runs the following questions become unanswerable:

- which ruleset produced this result?
- was this the old or new version?
- which mapping was used?
- which cost model / same-bar policy?
- which run is better and why?

The registry solves this by providing a single filterable list of experiments with full lineage and short outcome summaries.

## Output Artifact

```
phase5_experiment_registry.csv
```

One row per experiment (backtest/replay run).

## Registry Fields

| Field | Description |
|-------|-------------|
| `ExperimentId` | Unique experiment identifier |
| `ExperimentLabel` | Short human-readable tag (e.g. "baseline_v1", "tight_stop_test") |
| `RunTimestamp` | When the experiment was executed |
| `DateRangeStart` | Input data start date |
| `DateRangeEnd` | Input data end date |
| `RulesetId` | Which ruleset was used |
| `RulesetContractVersion` | Contract version of the ruleset |
| `ReplaySemanticsVersion` | Replay semantics version |
| `MappingVersion` | Mapping version |
| `ValidationStatus` | Phase 4 validation result |
| `CostModelId` | Which cost model was applied |
| `SameBarPolicyId` | Same-bar execution policy |
| `InputArtifactDir` | Path to input artifacts |
| `BacktestRunDir` | Path to backtest output |
| `GitCommit` | Git commit hash for reproducibility |
| `DurationSeconds` | How long the run took |
| `TradeCount` | Total trades generated |
| `ResolvedTradeCount` | Trades that reached resolution |
| `ValidationSummaryStatus` | Aggregated validation outcome |
| `PromotionSummaryStatus` | Whether results qualify for promotion |
| `NetResult` | Short outcome metric |
| `Notes` | Free-text notes |

## Design Principles

- Registry only records facts — no aggregation, no comparison, no auto-promotion
- Append-only: each run adds a row, never modifies previous rows
- Deterministic: identical inputs must produce identical registry rows (except `RunTimestamp`, `DurationSeconds`)
- Lineage-complete: every registry row must link back to its full artifact chain

## What the Registry Does NOT Do

- No cross-experiment comparison logic (separate layer if needed)
- No auto-promotion of "best" results
- No modification of upstream artifacts
- No execution decisions — purely observational

## Implementation Targets

Expected implementation components:

- `backtester/experiment_registry.py`
- `tests/test_experiment_registry.py`

Integration call site:

- `backtester/orchestrator.py` — hook after run completion

Integration rules:

- Registry write must execute after every completed replay run (valid or invalid)
- Registry must not block or modify replay execution
- Registry artifacts must be preserved alongside backtest output
