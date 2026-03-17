# Strategy Shi — Backtesting Architecture v0.1

**Status:** Implemented baseline architecture companion  
**Phase:** 3 — Implemented baseline  
**Companion to:** `docs/Backtesting_Spec_v0.1.md` (normative behavior), `docs/Spec_v1.0.md` (Analyzer contract)

---

## 1. Purpose

This document defines the **module architecture**, **artifact flow**, and **interface contracts** for the implemented Backtesting baseline.

Its role is to make boundaries explicit and prevent hidden assumptions around replay semantics, determinism, lookahead handling, and promotion decisions.

---

## 2. Boundary with Analyzer

Analyzer (Phase 1–2) is complete as a research pipeline and produces deterministic CSV artifacts (features, events, setups, outcomes, reports, context reports, rankings, selections, shortlist, shortlist explanations, research summary).

Phase 3 Backtesting is a **separate subsystem** that:

- consumes Analyzer artifacts as inputs,
- does not mutate Analyzer outputs,
- does not own Analyzer feature/event generation,
- does not perform live execution or exchange integration.

Operationally, Analyzer answers: **"what happened and what looks promising in research"**.  
Backtester answers: **"what a deterministic tradable ruleset would have produced under replay + costs + acceptance policy"**.

---

## 3. Phase 3 interface contract

### 3.1 v0.1 default boundary mode

Backtester reads **pre-generated Analyzer artifacts** from an artifact directory.

- Default mode does **not** implicitly call `analyzer.pipeline.run()`.
- Analyzer generation and Backtester replay are separate run steps.

### 3.2 Required system-level inputs for a backtest run

A run contract must explicitly provide:

- `artifact_dir` (Analyzer CSV set),
- dataset/run range (date interval or dataset identifier),
- ruleset set identifier (or ruleset file),
- cost model version,
- replay semantics version,
- output directory.

### 3.3 Input assumptions and guardrails

Backtester assumes Analyzer artifacts already satisfy Analyzer schema/time guarantees from Phase 2. Before replay, Backtester validates required artifact presence and expected schemas.

---

## 4. Module architecture

Implemented Phase 3 package layout:

### `backtester/rulesets.py`
- **Responsibility:** Deterministic ruleset schema and ruleset materialization from research candidates (e.g., shortlist/research summary mapping).
- **Inputs:** Analyzer shortlist/research artifacts, explicit ruleset parameters.
- **Outputs:** Canonical ruleset table (`backtest_rulesets.csv`) + ruleset metadata for engine.
- **Non-responsibilities:** Replay simulation, cost execution, trade metrics, validation decisions.

Research-summary bridge contract (v0.1 hardening):
- `analyzer_research_summary.csv` may contain rich research rows that are not replayable hypotheses.
- Ruleset formalization must consume rows marked `FormalizationEligible = TRUE`.
- Replay semantics columns (`Direction`, `SetupType`, `EligibleEventTypes`) are required only for eligible rows.
- Non-eligible rows preserve research lineage but are intentionally excluded from ruleset generation.
- No-setups fallback is explicit: `SetupType` rows with `_LONG`/`_SHORT` suffix may remain eligible; `Direction` rows must fail loud because setup-family lineage is unavailable.

### `backtester/ruleset_validation.py`
- **Responsibility:** Deterministic Phase 4 pre-replay validation gate for `phase3_ruleset_mapping.csv` in `PHASE3_MAPPING_ONLY` execution.
- **Inputs:** Mapping artifact; optional contract (`phase3_ruleset_contract.csv`) and draft (`phase3_ruleset_draft.csv`) artifacts when available.
- **Outputs:** `phase4_ruleset_validation_summary.csv`, `phase4_ruleset_validation_details.csv`.
- **Non-responsibilities:** Auto-fixing mappings, status auto-promotion, heuristic contract repair.

### `backtester/engine.py`
- **Responsibility:** Time-ordered replay of bars/events using versioned replay semantics and cost model hooks.
- **Inputs:** Features/events/setup-level observables, canonical rulesets, replay semantics version, cost model version.
- **Outputs:** Executed trade intents/fills snapshot stream to ledger, equity path intermediates.
- **Non-responsibilities:** Statistical acceptance policy, promotion decisions, Analyzer generation.

### `backtester/ledger.py`
- **Responsibility:** Immutable append-only trade record construction from replay outputs.
- **Inputs:** Engine execution outputs (entries/exits/costs/timestamps/reasons).
- **Outputs:** `backtest_trades.csv` (trade ledger ground truth for downstream metrics).
- **Non-responsibilities:** Strategy logic, robustness inference, promotion gating.

### `backtester/metrics.py`
- **Responsibility:** Deterministic trade/equity/drawdown metric aggregation.
- **Inputs:** Trade ledger.
- **Outputs:** `backtest_trade_metrics.csv`, `backtest_equity_curve.csv`, `backtest_drawdown.csv`.
- **Non-responsibilities:** Replaying market history, changing trade facts, pass/fail policy.

### `backtester/validation.py`
- **Responsibility:** Acceptance checks against declared minimum criteria (sample, expectancy, drawdown, etc. once finalized).
- **Inputs:** Trade metrics, run manifest context, validation policy version.
- **Outputs:** `backtest_validation_summary.csv`.
- **Non-responsibilities:** Robustness perturbations, final promotion state ownership.

### `backtester/robustness.py`
- **Responsibility:** Out-of-sample / walk-forward / perturbation evaluations (versioned methods once locked).
- **Inputs:** Rulesets, replay engine interface, baseline run artifacts, robustness config.
- **Outputs:** `backtest_robustness_summary.csv`.
- **Non-responsibilities:** Baseline deterministic replay semantics ownership, final promotion arbitration.

### `backtester/promotion.py`
- **Responsibility:** Final promote/review/reject decisioning based on validation + robustness outputs.
- **Inputs:** Validation summary, robustness summary, promotion policy version.
- **Outputs:** `backtest_promotion_decisions.csv`.
- **Non-responsibilities:** Computing replay facts, editing trade ledger, live execution triggers.

### `backtester/orchestrator.py`
- **Responsibility:** End-to-end Phase 3 orchestration over pre-generated Analyzer artifacts.
- **Inputs:** Analyzer artifact directory + run controls (ruleset mode, variants, model ids, semantics version).
- **Outputs:** Full baseline artifact set + `backtest_orchestration_manifest.json`.
- **Non-responsibilities:** Analyzer generation, live execution authorization.
- **Phase 4 gate behavior:** In `PHASE3_MAPPING_ONLY`, runs `ruleset_validation.py` after mapping load and before replay; replay is blocked unless exactly one mapping row is `VALID`/replay-eligible.

### `backtester/campaign.py`
- **Responsibility:** Deterministic batch orchestration over multiple analyzer artifact directories by delegating each run to `run_backtester(...)`.
- **Inputs:** Ordered artifact dir list + shared run controls.
- **Outputs:** `backtest_campaign_manifest.json`, `backtest_campaign_run_index.csv`, `backtest_campaign_summary.csv`.
- **Non-responsibilities:** Replay semantics ownership, ruleset optimization, winner selection, auto-promotion.

### `backtester/experiment_registry.py`
- **Responsibility:** Append-only Phase 5 experiment journal for completed runs.
- **Inputs:** Existing per-run artifacts (`backtest_orchestration_manifest.json`, `backtest_run_manifest.json`, ruleset/validation/promotion CSVs).
- **Outputs:** `phase5_experiment_registry.csv` (one appended row per completed run).
- **Non-responsibilities:** Replay blocking, artifact mutation, cross-experiment ranking logic.

---

## 5. Artifact flow

High-level dataflow:

`Analyzer artifacts`  
`→ ruleset definitions`  
`→ Phase 4 ruleset validation gate (mapping-only path)`  
`→ replay engine`  
`→ trade ledger`  
`→ trade metrics`  
`→ validation`  
`→ robustness`  
`→ promotion decisions`  
`→ registry / campaign summary (optional Phase 5 observational layer)`

Implemented baseline artifacts:

- `backtest_rulesets.csv`
- `backtest_engine_events.csv`
- `backtest_run_manifest.json`
- `backtest_trades.csv`
- `backtest_trade_metrics.csv`
- `backtest_equity_curve.csv`
- `backtest_drawdown.csv`
- `backtest_exit_reason_summary.csv`
- `backtest_validation_summary.csv`
- `backtest_validation_details.csv`
- `backtest_robustness_summary.csv`
- `backtest_robustness_details.csv`
- `backtest_promotion_decisions.csv`
- `backtest_promotion_details.csv`
- `backtest_orchestration_manifest.json`
- `phase4_ruleset_validation_summary.csv` (mapping-only mode)
- `phase4_ruleset_validation_details.csv` (mapping-only mode)

Manifest model is currently two-layered:

- `backtest_run_manifest.json` — engine-level replay manifest.
- `backtest_orchestration_manifest.json` — orchestration-level run manifest spanning rulesets→promotion.

---

## 6. Responsibility split by concern

To avoid module sprawl, major concerns are assigned as follows:

- **Replay semantics:** `engine.py`
- **Cost application:** `engine.py` via explicit cost-model contract/version
- **Immutable trade records:** `ledger.py`
- **Aggregate trade statistics:** `metrics.py`
- **Acceptance checks:** `validation.py`
- **OOS / walk-forward / perturbation checks:** `robustness.py`
- **Final promote/review/reject state:** `promotion.py`
- **Run orchestration + boundary enforcement:** `orchestrator.py`

Cross-module rule: downstream modules may derive summaries from upstream facts, but may not rewrite replay/ledger facts.

---

## 7. Implemented baseline boundary

All core waves are implemented in baseline form:

- ruleset formalization,
- replay event generation,
- trade ledger materialization,
- metrics artifacts,
- validation artifacts,
- robustness artifacts,
- promotion artifacts,
- end-to-end orchestration.

Remaining work is hardening/completeness (economic return surface, richer stop/target resolution,
finalized thresholds), not absence of Phase 3 modules.

---

## 8. Determinism and anti-lookahead enforcement points

Architectural enforcement mapping:

- **Rulesets (`rulesets.py`)**
  - Rules may reference only Analyzer-observable fields available at replay timestamp.
  - No forward-dependent rule attributes.

- **Replay engine (`engine.py`)**
  - Enforces strict timestamp-ordered processing.
  - Enforces versioned same-bar/entry/exit replay semantics.
  - Applies costs deterministically through a versioned contract.

- **Ledger (`ledger.py`)**
  - Append-only immutable trade facts.
  - No retrospective edits after record materialization.

- **Metrics/Validation/Promotion (`metrics.py`, `validation.py`, `promotion.py`)**
  - Read-only over ledger/replay outputs.
  - Cannot override replay facts; only summarize and classify.

- **Run manifest (`backtest_run_manifest.json`)**
  - Captures semantics/cost/ruleset versions and input artifact lineage for reproducibility.

---

## 9. Known limitations carried into Phase 3

The following known constraints remain inherited and must be surfaced in interpretation (not silently normalized away):

1. **Execution-domain mismatch:** research data surface is futures-derived while intended production execution domain is Spot Margin.
   - Architecture impact: validation/robustness/promotion must treat this as external validity risk.

2. **Synthetic candle handling:** Analyzer includes synthetic bars for continuity but excludes them from structural event formation.
   - Architecture impact: engine consumes Analyzer outputs as produced; replay assumptions must not reinterpret Analyzer structural facts.

3. **Retrospective sweep bias caveat:** known caveat from current research surface.
   - Architecture impact: robustness/validation outputs must keep caveat visible in run summaries and promotion decisions.

4. **Unresolved trade handling is explicit:** baseline ledger can emit
   `NO_EXIT_RESOLVED_YET`, `UNRESOLVED`, `DEFERRED` with deterministic heuristic mapping.

5. **Equity/drawdown basis is non-monetary by default:** baseline uses `RESOLVED_TRADE_COUNT` basis.

6. **Validation and robustness thresholds are provisional heuristics:** status outputs are deterministic, but cutoffs/splits are interim.

7. **Perturbation is external-surface only:** robustness consumes an explicit perturbation artifact if provided.

8. **Regime robustness requires explicit labels:** otherwise regime check is `NOT_EVALUATED`.

9. **Promotion is not live authorization:** promotion outputs are execution-design progression only.

10. **Missing-scope promotion seam exists:** promotion may emit `robustness_status="MISSING"` and force `REVIEW` when robustness scope is absent.

Phase 3 architecture does not redesign these limitations in v0.1; it records where they affect decision confidence.

---

## 10. Open design decisions (unresolved)

The following must be explicitly locked in later design revisions before full implementation is complete:

- exact minimum trade count thresholds,
- exact statistical significance methodology,
- exact walk-forward mode,
- exact train/test window sizes,
- exact split policy,
- exact same-bar policy details (if not yet numerically versioned),
- exact fee/slippage values,
- exact acceptance and promotion threshold values,
- exact schema for run-manifest lineage hashes.

These are intentionally unresolved in v0.1 architecture to avoid fake precision.

---

## 11. Scope statement

This document is an architecture companion for Phase 3.  
It does not replace `docs/Backtesting_Spec_v0.1.md`, and it introduces no code, test, or runtime behavior changes.
