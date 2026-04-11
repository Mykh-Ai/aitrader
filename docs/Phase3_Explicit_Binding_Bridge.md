# Phase 3 Explicit Binding Bridge

Status: proposed architectural bridge (docs-first)
Scope: Phase 3 replay-entry contract clarification

---

## 1) Problem statement

The repository already has:

- a working research-derived replay path,
- a strict mapping-only replay path (`PHASE3_MAPPING_ONLY`) that expects READY input,
- a machine-generated formalization chain that intentionally stops at PARTIAL /
  NOT_INTEGRATED when binding fields remain unresolved.

What is missing is a canonical transition layer from machine-generated partial
mapping to reviewed replay-ready binding.

## 2) Current gap

The gap is architectural, not a bug:

- Harvest/formalization produces mapping intent surfaces.
- Strict replay requires executable reviewed bindings.
- No canonical production workflow currently defines who promotes PARTIAL → READY,
  under what evidence, and with what audit metadata.

Therefore, failing strict replay on PARTIAL mapping is expected behavior.

## 3) Why this is a missing transition layer (not validator failure)

Validator and orchestrator are correctly strict:

- validator enforces READY-class executable fields and statuses;
- orchestrator blocks replay in mapping-only mode unless strict gate passes.

Relaxing that behavior would blur research artifacts and executable truth, reduce
auditability, and violate no-auto-promotion discipline.

## 4) Proposed bridge responsibilities

Introduce an explicit binding bridge layer with these responsibilities:

1. ingest machine-generated PARTIAL mapping artifact;
2. require explicit review of replay-critical mappings;
3. emit reviewed replay-ready binding artifact only after approval;
4. write append-only decision metadata with evidence references;
5. preserve lineage to draft/contract/mapping artifacts.

Non-responsibilities:

- no auto-repair of unresolved fields,
- no auto-promotion based on shortlist/research outputs,
- no changes to harvest defaults or validator thresholds.

## 5) Proposed artifact flow

Research-derived chain (existing):

`phase2_formalization_candidates.csv`
→ `phase2_formalization_review.csv`
→ `phase3_ruleset_draft.csv`
→ `phase3_ruleset_contract.csv`
→ `phase3_ruleset_mapping.csv` (machine-generated, can remain PARTIAL)

Explicit bridge (new canonical transition):

`phase3_ruleset_mapping.csv` (PARTIAL intent)
→ **explicit review/promotion step**
→ `phase3_ruleset_binding.csv` (reviewed executable binding; READY-only rows)
→ strict replay (`PHASE3_MAPPING_ONLY`)

## 6) Proposed statuses

Machine-generated mapping statuses (intent surface):

- `MappingStatus = PARTIAL` (allowed, non-executable)
- `ReplayIntegrationStatus = NOT_INTEGRATED` (allowed, non-executable)

Reviewed binding statuses (executable surface):

- `BindingDecisionStatus = READY` or `REJECTED`
- `ReplayIntegrationStatus = READY_FOR_BINDING` (required for strict replay)

## 7) READY minimum requirements

Before READY is allowed, binding must explicitly resolve at minimum:

- `EntryTriggerMapping`
- `EntryBoundaryMapping`
- `ExitBoundaryMapping`
- `RiskMapping`
- `ReplaySemanticsVersion`
- readiness / integration status fields

## 8) Minimal review metadata (audit trail)

Reviewed binding rows should include:

- `BindingDecisionStatus`
- `BindingApprovedAt`
- `BindingPolicyVersion`
- `EvidenceRef`
- `DecisionNote`

This metadata is minimal but sufficient for append-only audit and reproducibility.

## 9) Replay entry mode declaration

Replay manifests should carry:

- `ReplayEntryMode = RESEARCH_DERIVED` or
- `ReplayEntryMode = EXPLICIT_BINDING`

This prevents semantic mixing of baseline research replay and strict binding replay.

## 10) Intentionally manual / explicit steps

The following remains intentionally manual (or explicit workflow-driven):

- PARTIAL → READY promotion decision,
- policy/evidence judgment,
- approval timestamping and reviewer accountability.

## 11) What must NOT be automated

- auto-promotion from research outputs to READY binding,
- harvest-side emission of READY binding by default,
- validator rule weakening to accept unresolved mappings,
- orchestrator-side silent patching/repair of mapping artifacts.

## 12) Future implementation (separate from this docs patch)

Potential follow-up code changes (not part of current patch):

1. add a dedicated bridge module/CLI for reviewed binding generation;
2. add `phase3_ruleset_binding.csv` loader path in orchestrator for explicit mode;
3. add manifest field `ReplayEntryMode`;
4. add tests for bridge promotion audit metadata and strict-mode consumption.
