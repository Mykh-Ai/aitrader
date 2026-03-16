# AiTrader / Strategy Shi
## Phase 2 Stabilization & Implementation Plan (v2.2)

### Purpose
Provide a structured roadmap to stabilize Phase 2 (Analyzer / Research pipeline), ensure reproducibility of analyzer runs, and prepare the system for controlled candidate harvesting and Phase 3 formalization.

Phase 2 is explicitly treated as a **research engine**, not a ruleset generator.

## Current Status Snapshot

- **P0 — DONE**
- **P1 — DONE**
- **P2 — NOT STARTED**
- **P3 — NOT STARTED**

Phase 2 now has:

- canonical analyzer run contract
- standardized `run_manifest.json`
- post-run artifact validation
- stabilized Phase 2 → Phase 3 bridge
- honesty metadata in shortlist and research summary
- ranking provenance via `RankingMethod`
- minimal setup provenance via `SourceTF`

Current interpretation:

- Phase 2 is now canonical and reproducible as a code/data pipeline
- Phase 2 is materially more honest as a research surface
- Phase 2 is safer for Phase 3 handoff
- Phase 2 is still a research / hypothesis-forming layer, not a generalized ruleset generator

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

Avoid opaque single-number scores.

Replace:

```text
CompositeScore
```

with:

```text
RankingScore
RankingMethod
RankingComponents
```

Example:

```text
RankingMethod = heuristic_v1
RankingComponents =
    expectancy_component
    stability_component
    sample_size_component
```

This allows ranking evolution without invalidating historical runs.

---

# Setup Artifacts and Lineage

Goal: make setup artifacts usable for downstream reasoning.

Principle:

```text
setup artifacts must be downstream-sufficient
```

A setup row should contain enough information for:

- review
- Phase 3 formalization
- manual research analysis

without recomputing internal Analyzer logic.

However, `setups.csv` does **not** need to duplicate all analyzer state.

Key lineage fields:

```text
source_event_type
source_event_ts
source_tf

reference_swing_ts
reference_level

setup_family_version
```

---

# P2 — Structural Layer Hardening

Goal: reduce structural noise without rewriting baseline semantics.

Possible improvements:

- failed_break timeout logic
- first-cross deduplication for sweeps
- penetration filters

Important rule:

```text
penetration filters must be introduced as versioned experiments
```

Example:

```text
penetration_filter_v1
penetration_filter_v2
```

Baseline semantics must remain stable.

---

# Context Layer Improvements

Context scoring must be clearly labeled as heuristic.

Example:

```text
AbsorptionScore_v1
```

Additional context fields:

```text
session
minutes_from_eu_open
minutes_from_us_open
```

Add:

```text
ContextModelVersion
```

to downstream artifacts.

---

# Multi-Day Candidate Harvesting

Goal: move from daily snapshots to accumulating research evidence.

Tasks:

Create a multi-day aggregation layer across canonical runs.

Each aggregated row must track provenance:

```text
RunId
RunDate
AnalyzerVersion
ArtifactContractVersion
RankingMethod
SetupFamilyVersion
InputRawDate
```

Candidates must appear in multiple runs to qualify as stable leads.

---

# P3 — Controlled Formalization Candidate

Goal: produce a single well-defined candidate for Phase 3.

Steps:

1. Select one setup family
2. Select one TF / direction slice
3. Confirm multi-day evidence
4. Produce handoff artifact:

```text
phase2_formalization_candidates.csv
```

Candidate artifact should include explicit status, for example:

```text
CandidateStatus
```

or

```text
FormalizationStatus
```

This prevents ambiguity between:

- research lead
- candidate under review
- formalization-ready candidate

Candidate must include:

- lineage
- statistical basis
- known caveats
- readiness flag

---

# Next Stage After P0–P1

With P0 and P1 completed, the next work should move away from integrity / honesty hardening and toward one of:

1. multi-day research / candidate harvesting
2. explicit candidate formalization work
3. deeper setup/event lineage only if operational need appears
4. Phase 3 strategy candidate evaluation on larger evidence corpus

Recommended interpretation of current project state:

```text
Phase 2 is now stable enough to support disciplined multi-day research
and safer Phase 3 handoff, but should still be treated as a hypothesis-generation layer.
```

---

# Implementation Priority

| Priority | Focus |
|--------|-------|
| P0 | Canonical run contract, manifest, validation |
| P1 | Research honesty, ranking transparency |
| P2 | Structural & context hardening |
| P3 | Formalization candidate |

---

# Final Principle

Phase 2 must prioritize:

- reproducibility
- statistical honesty
- versioned research outputs

over premature trading logic complexity.
