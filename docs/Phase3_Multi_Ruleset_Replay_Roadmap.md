# Phase 3 Extension — Multi-Ruleset Replay Orchestration Roadmap

## Status

Draft based on repository audit and confirmed code evidence.

## Purpose

This document defines the Phase 3 extension required to support canonical multi-ruleset replay without breaking the current baseline.

The goal is not to redesign the whole backtester stack. The goal is to resolve the confirmed contract seam between:

- ruleset formalization
- replay orchestration
- placement entry
- run-level artifact and registry summarization

This extension is intentionally narrow, conservative, and implementation-oriented.

---

## 1. Problem Statement

The current Phase 3 baseline contains a contract mismatch between formalization and replay execution.

Confirmed repository evidence shows:

- shortlist-based formalization in `backtester/rulesets.py` can legitimately produce **0..N canonical ruleset rows**
- `backtester/ruleset_validation.py` does **not** force this set to collapse to one row
- but replay entry at the `orchestrator -> placement` seam still behaves as:
  - **one replay run -> exactly one canonical ruleset**

As a result, canonical multi-ruleset output is already possible at the formalization layer, but current replay execution is not yet fully compatible with that cardinality.

This is not primarily an Analyzer problem and not primarily a ruleset-generation problem.

This is a **replay-run cardinality and orchestration problem**.

---

## 2. Confirmed Findings

### 2.1 What is **not** the primary seam

Audit evidence confirmed that the following layers are **not** the primary source of the current issue:

- `backtester/rulesets.py` in shortlist-based formalization modes
- `backtester/ruleset_validation.py`
- `backtester/engine.py`
- `backtester/ledger.py`
- `backtester/metrics.py`
- `backtester/validation.py`

Reason:

- formalization already supports multiple ruleset rows
- validation does not force cardinality down to one row
- downstream replay carriers already use `ruleset_id` as a scope key or grouping dimension

### 2.2 Where the actual seam exists

The real seam is confirmed in the following places.

#### A. `backtester/placement.py`
`materialize_stop_target_levels()` currently enforces a hard replay-entry contract:

- `rulesets_df` must contain **exactly one row**
- otherwise `PlacementContractError` is raised

This is the clearest hard boundary blocking canonical multi-ruleset replay inside one replay run.

#### B. `backtester/orchestrator.py`
In the `PHASE3_MAPPING_ONLY` path, orchestration already performs explicit narrowing:

- replay-eligible mapping rows must not exceed one row
- the flow is then narrowed to one `RulesetId`

So in mapping-only mode, single-ruleset policy is enforced even before placement.

#### C. `backtester/experiment_registry.py`
The registry does not forbid many completed runs overall, but current completed-run extraction represents one run as one summarized ruleset identity rather than a many-ruleset payload.

#### D. `backtester/campaign.py`
Campaign currently supports:

- **many artifact_dirs -> many backtest runs**

but not:

- **one analyzer artifact_dir -> many derived replay runs**

---

## 3. Root Cause

The root cause is not that the system cannot formalize multiple candidate rulesets.

The root cause is that:

> current replay-run contract still assumes one canonical ruleset per run at the orchestration -> placement seam.

In practical terms:

- the **formalization layer** already lives in `0..N rulesets`
- the **replay entry layer** still lives in `exactly 1 ruleset`
- the **run-level artifact and registry model** is still oriented around one completed run producing one summarized ruleset identity

This is therefore a **contract misalignment across layers**, not a single isolated bug.

---

## 4. Phase 3 Extension Decision

### Implementation status note

The baseline described in this roadmap is now the implemented Phase 3 replay behavior.
The roadmap remains useful as a contract/reference document, but the following points are no longer prospective only:

- `0` replayable rulesets fails loudly before placement
- `1` replayable ruleset preserves the existing single-run baseline
- `N > 1` replayable rulesets fan out into `N` derived isolated replay runs
- each derived run receives a one-row canonical ruleset input
- campaign/registry appends one fact row per completed derived run
- parent scope remains orchestration/lineage scope, not a synthetic merged replay result

### 4.1 Baseline decision for first implementation

Canonical multi-ruleset replay will **not** be introduced first as:

- one replay run containing many canonical rulesets

Instead, the first implementation baseline for this extension will be:

> **one analyzer artifact -> many derived isolated replay runs, one per canonical ruleset**

### 4.2 Why this path is chosen

This is the smallest safe path because it:

- preserves the current exact-one-row placement contract
- avoids immediate redesign of run-level artifact layout
- avoids first-order rewrites in engine, ledger, metrics, or validation
- aligns with the current registry model:
  - one completed run -> one fact row
- minimizes regression risk for the current single-ruleset baseline

This is a conservative extension, not a broad redesign.

---

## 5. Scope

### 5.1 In scope

This extension includes:

- replay-run cardinality policy
- orchestration fan-out at the Phase 3 replay boundary
- derived per-ruleset run materialization
- run-level lineage preservation
- campaign / registry alignment for derived runs
- regression-safe preservation of the existing single-ruleset path

### 5.2 Out of scope

This extension does **not** include:

- Analyzer logic changes
- shortlist generation logic changes
- formalization redesign in `rulesets.py`
- engine event model redesign
- ledger / metrics / validation core redesign
- promotion policy redesign
- auto-promotion
- registry aggregation
- live execution behavior
- Executor changes

---

## 6. Target Contract

After this extension, the target Phase 3 replay contract should be:

### 6.1 Formalization contract
`build_backtest_rulesets()` may produce **0..N canonical ruleset rows** in shortlist-based modes without forced narrowing.

### 6.2 Replay execution contract
Each canonical replayable ruleset row must be replayable as its own **derived isolated replay run**. A zero-ruleset outcome blocks replay before placement with an explicit failure, a one-ruleset outcome keeps the existing single-run path, and an `N > 1` outcome yields `N` derived runs.

### 6.3 Derived run identity contract
Each derived replay run must have deterministic lineage to:

- source analyzer artifact
- source `RulesetId`
- replay semantics version
- relevant policy/version identifiers

The parent run scope is lineage/orchestration scope only. Replay-completed units are the derived runs themselves; the parent is not a synthetic merged replay output. Where campaign identity is surfaced, `RunId` continues to point at the parent artifact slot, while derived replay identity is carried by the child `ExperimentId` / `RunDir`.

### 6.4 Placement compatibility contract
`placement.py` may preserve its current exact-one-row contract in the first implementation, provided orchestration supplies a one-row `rulesets_df` for each derived run.

### 6.5 Registry contract
Registry must record **one fact row per completed derived run**, without:

- aggregation across derived runs
- best-of selection
- promotion inference
- hidden run collapsing

Campaign/registry semantics remain append-only and observational: no aggregation, no best-of, and no auto-promotion across siblings derived from the same parent analyzer artifact.

---

## 7. Implementation Roadmap

## Step 0 — Contract Lock

Before code changes, the replay cardinality decision must be explicitly documented:

- canonical multi-ruleset replay in Phase 3 baseline is implemented through **derived isolated runs**
- not through one in-run many-ruleset replay bundle

Also lock the following:

- current placement exact-one-row contract remains valid in first implementation
- registry remains fact-only
- no auto-promotion
- no registry aggregation

### Deliverable
- this roadmap document
- a short Phase 3 extension note in `docs/Spec_v1.0.md`

---

## Step 1 — Orchestration Fan-Out

Add orchestration behavior so that one analyzer artifact may produce multiple replay invocations.

Expected behavior:

- if replayable ruleset count is `0`:
  - fail loudly before placement
- if replayable ruleset count is `1`:
  - preserve current single-run baseline behavior
- if replayable ruleset count is `N > 1`:
  - derive **one replay invocation per ruleset row**

### Required properties

- deterministic ordering
- deterministic per-ruleset run naming
- no silent dropping of valid replayable rows
- no implicit collapse to first row

### Deliverable
- fan-out replay policy
- deterministic derived-run invocation contract

---

## Step 2 — Per-Ruleset Derived Run Materialization

Each derived replay run must receive its own isolated output scope.

Minimum required artifacts per derived run:

- dedicated output directory
- one-row `backtest_rulesets.csv`
- dedicated orchestration manifest
- dedicated replay outputs

### Required lineage properties

Each derived run must clearly preserve:

- source analyzer artifact reference
- source `RulesetId`
- local derived run path / identifier

### Deliverable
- per-ruleset run directory structure
- per-ruleset artifact bundle contract

---

## Step 3 — Campaign Alignment

Extend campaign behavior so that one analyzer artifact may result in multiple derived replay runs without breaking current campaign semantics.

Campaign must support:

- preserving current many-artifact-dir behavior
- tracking multiple child replay runs under one analyzer lineage
- stable campaign manifest entries for derived runs

### Important constraint

The first patch must not turn campaign into a large planning framework.

Only a minimal safe extension is intended.

### Deliverable
- derived-run-compatible campaign behavior
- stable campaign manifest semantics

---

## Step 4 — Registry Alignment

Extend registry handling so that:

- one completed derived run -> one appended fact row

Registry must remain:

- append-only
- fact-oriented
- non-aggregating
- non-promoting

### Required registry lineage fields

A completed derived-run row must allow reconstruction of:

- source analyzer artifact
- derived replay run path
- `RulesetId`
- replay semantics version
- relevant policy/version identifiers

### Deliverable
- derived-run-compatible registry row contract
- preserved append-only semantics

---

## Step 5 — Tests

The implementation must be accompanied by regression and correctness tests.

### Required coverage

#### 5.1 Existing baseline
- one replayable ruleset -> current behavior remains unchanged

#### 5.2 Multi-ruleset shortlist case
- one analyzer artifact with `N > 1` replayable rulesets
- orchestration emits `N` isolated derived runs
- each derived run contains exactly one-row `backtest_rulesets.csv`

#### 5.3 Placement compatibility
- placement continues receiving one-row ruleset input
- valid derived-run flow does not raise `PlacementContractError`

#### 5.4 Registry behavior
- one completed derived run -> one registry row
- `N` derived runs -> `N` registry rows

#### 5.5 No silent collapse
- valid multi-ruleset inputs are not silently collapsed into one replay result unless explicitly configured by a future separate policy

### Deliverable
- regression coverage
- fan-out correctness tests
- lineage tests

---

## Step 6 — Documentation Alignment

After code and tests are in place, update documentation so that code and docs agree.

Update targets:

- `docs/Spec_v1.0.md`
- README / backtester operational docs
- artifact / registry documentation

### Required documentation outcome

Documentation must explicitly describe:

- derived replay runs
- per-ruleset lineage
- preserved single-ruleset baseline compatibility

### Deliverable
- documentation aligned with implementation
- no contradiction between code and spec

---

## 8. Acceptance Criteria

This extension is considered complete only if all conditions below are satisfied.

### 8.1 Functional
- shortlist-based formalization may produce more than one replayable ruleset
- one analyzer artifact with `N` replayable rulesets yields `N` isolated replay runs
- each derived replay run completes using a one-row canonical ruleset input

### 8.2 Compatibility
- current single-ruleset baseline remains valid
- placement exact-one-row contract is preserved in the first implementation
- engine / ledger / metrics do not require first-order redesign

### 8.3 Lineage
Every derived run must be traceable to:

- source analyzer artifact
- source `RulesetId`
- replay semantics version

### 8.4 Registry
- registry records one fact row per completed derived run
- no aggregation is introduced
- no auto-promotion is introduced

### 8.5 Safety
- no silent dropping of replayable rulesets
- no hidden cardinality collapse in shortlist-based replay flow

---

## 9. Non-Goals

The following are explicitly excluded from the first patch set:

- rewriting `rulesets.py`
- changing shortlist formalization semantics
- rewriting `engine.py`
- rewriting `ledger.py`
- rewriting `metrics.py`
- changing promotion semantics
- adding registry aggregation
- adding auto-promotion
- implementing true in-run many-ruleset placement
- changing Analyzer behavior

---

## 10. Open Questions

### 10.1 External replay unit
A separate product/contract decision is still required:

What is the externally visible replay unit?

- the parent analyzer artifact
- or each derived replay run

This cannot be resolved from code evidence alone.

### 10.2 Future of `PHASE3_MAPPING_ONLY`
A separate decision is still required:

Should `PHASE3_MAPPING_ONLY` remain a strict single-candidate baseline mode, or should it later gain many-derived-run behavior?

Current code is strict-single.
Future intended policy is not established by current code evidence.

---

## 11. Recommended Implementation Posture

Recommended engineering posture for this extension:

- small patches
- tests alongside code
- no wide refactor
- preserve current baseline where possible
- change orchestration boundary first
- revisit placement contract only if later needed

This extension should be treated as a **controlled replay-orchestration upgrade**, not as a broad backtester redesign.