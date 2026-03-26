# Rule Candidate Audit Methodology

This document defines how replayed rules are classified, stored, archived, and revisited.
It is registry-oriented and applies after replay. It does not change Analyzer, Backtester,
replay logic, validation logic, robustness logic, or promotion logic.

## 1. Candidate Classes After Replay

Use one of these post-replay classes:

- `DEAD_REJECT`
- `REPLAYED_BUT_INCONCLUSIVE`
- `CONCEPTUALLY_WEAK_REJECT`

Working meaning:

- `DEAD_REJECT`: no meaningful replay surface, no archival value beyond registry tracking.
- `REPLAYED_BUT_INCONCLUSIVE`: rule reached replay, produced non-zero replay surface, but failed to establish a positive candidate.
- `CONCEPTUALLY_WEAK_REJECT`: rule reached replay or review depth, but evidence suggests the concept itself is weak, not merely undersampled.

## 2. Storage Policy

`research/rule_candidate_registry.csv` is the single registry for replayed rules.

Storage rules:

- all replayed rules must be recorded in the registry;
- a separate rule finding document is created only for:
  - `REPLAYED_BUT_INCONCLUSIVE`, or
  - `STRATEGICALLY_INTERESTING` cases;
- rule finding documents are stored in `research/findings/rules/`.

Operational interpretation:

- registry entry is mandatory for every replayed rule;
- finding file is selective, not automatic;
- archival value does not imply positive edge.

## 3. Revisit Policy

A ruleset may be placed into a future re-run bucket only if all of the following hold:

- `trade_count > 0`;
- replay surface was non-zero;
- the rule does not look fully empty;
- the future replay will be run on a larger data base;
- the ruleset logic remains unchanged between runs.

Revisit means evidence expansion only. It does not authorize local rule tuning.

## 4. Prohibitions

Do not:

- tune a ruleset to escape a local `REJECT`;
- confuse archival value with edge;
- treat `REPLAYED_BUT_INCONCLUSIVE` as a positive candidate;
- move such rules into execution-ready vocabulary.

## 5. Registry Role

The registry is the authoritative list of replayed rules and their current archival status.
Rule-level finding files are supporting notes, not substitutes for the registry.
