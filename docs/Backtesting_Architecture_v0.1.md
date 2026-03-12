# Strategy Shi — Backtesting Architecture v0.1

**Status:** Draft architecture companion (design-only)  
**Phase:** 3 — Planned  
**Companion to:** `docs/Backtesting_Spec_v0.1.md` (normative behavior), `docs/Spec_v1.0.md` (Analyzer contract)

---

## 1. Purpose

This document defines the **module architecture**, **artifact flow**, and **interface contracts** for the planned Backtesting subsystem before implementation starts.

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

Planned Phase 3 package layout:

### `backtester/rulesets.py`
- **Responsibility:** Deterministic ruleset schema and ruleset materialization from research candidates (e.g., shortlist/research summary mapping).
- **Inputs:** Analyzer shortlist/research artifacts, explicit ruleset parameters.
- **Outputs:** Canonical ruleset table (`backtest_rulesets.csv`) + ruleset metadata for engine.
- **Non-responsibilities:** Replay simulation, cost execution, trade metrics, validation decisions.

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

---

## 5. Artifact flow

High-level dataflow:

`Analyzer artifacts`  
`→ ruleset definitions`  
`→ replay engine`  
`→ trade ledger`  
`→ trade metrics`  
`→ validation`  
`→ robustness`  
`→ promotion decisions`

Expected Phase 3 artifacts:

- `backtest_rulesets.csv`
- `backtest_trades.csv`
- `backtest_trade_metrics.csv`
- `backtest_equity_curve.csv`
- `backtest_drawdown.csv`
- `backtest_validation_summary.csv`
- `backtest_robustness_summary.csv`
- `backtest_promotion_decisions.csv`
- `backtest_run_manifest.json`

`backtest_run_manifest.json` is the run-level reproducibility anchor (input artifact refs, versions, dataset range, policy versions, output hashes/paths).

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

Cross-module rule: downstream modules may derive summaries from upstream facts, but may not rewrite replay/ledger facts.

---

## 7. Step 1 implementation boundary

Implementation sequencing for Phase 3 is explicitly staged:

### Step 1 (first implementation wave)

- implement ruleset schema,
- implement ruleset builder/mapping from Analyzer shortlist and research_summary artifacts (explicit source-lineage input boundary),
- emit `backtest_rulesets.csv` + run manifest skeleton,
- no replay engine yet,
- no trade ledger/metrics/validation/robustness/promotion yet.

### Later waves (planned)

- **Step 2:** replay engine + cost-model contract + ledger output,
- **Step 3:** metrics outputs (trade/equity/drawdown),
- **Step 4:** validation and robustness modules,
- **Step 5:** promotion decision layer.

This ordering keeps first delivery focused on deterministic hypothesis formalization before simulation complexity.

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
