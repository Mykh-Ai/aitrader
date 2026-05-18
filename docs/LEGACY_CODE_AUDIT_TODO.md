# Legacy Code Audit TODO

## A. analyzer/

Status: LEGACY / FAILED AS STRATEGY ANALYZER / NOT ACTIVE.

Potentially reusable:

- feed loading;
- schema checks;
- timestamp normalization;
- VWAP calculations;
- volume/delta base metrics;
- session labels;
- swing/level primitive code, only if audited.

Not reusable / do not continue:

- failed-break/reclaim setup logic;
- shallow sweep detector;
- arbitrary 12-bar outcome logic;
- old setup candidates;
- old shortlist logic;
- old promotion assumptions.

## B. backtester/

Status: LEGACY / POSSIBLY REUSABLE VALIDATION HARNESS / AUDIT REQUIRED.

Potentially reusable:

- deterministic replay skeleton;
- ledger;
- cost stress;
- same-bar policy;
- source concentration;
- promotion/rejection discipline.

Needs audit before reuse:

- entry contract;
- timestamp semantics;
- stop/target handling;
- one-position rule;
- compatibility with Market State events.

## C. aggregator/feed/

Status: KEEP / CORE ASSET.

`binance_aggregator_shi.py`, `feed/`, and `feed_recovered/` are retained as data-lineage assets. They are not evidence of an active trading strategy.

## D. research scripts

Status: ARCHIVED / NOT ACTIVE.

Old research scripts were moved out of active state into the failed Analyzer v1 archive package. They must not be used to continue Sprint 02-10 research.
