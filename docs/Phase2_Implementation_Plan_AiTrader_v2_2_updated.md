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

All planned phases (P0–P3) are complete. The system is ready for:

1. **Phase 3 backtesting** — validate edge on 6-month historical data using materialized rulesets
2. **Phase 4 execution** — live trading via Spot Margin API (after backtesting validation)

```text
Phase 2 implementation plan is fully delivered.
Pipeline is stable, reproducible, and binding-ready for Phase 3 backtesting.
```

---

# Implementation Priority

| Priority | Focus | Status |
|--------|-------|--------|
| P0 | Canonical run contract, manifest, validation | DONE |
| P1 | Research honesty, ranking transparency | DONE |
| P2 | Structural & context hardening | DONE |
| P3 | Formalization candidate | DONE |

---

# Final Principle

Phase 2 prioritized:

- reproducibility
- statistical honesty
- versioned research outputs

over premature trading logic complexity.

All objectives delivered. Pipeline proceeds to Phase 3 backtesting.
