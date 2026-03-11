# Analyzer v1.0 Phase 0 Audit Report

## A) Current raw feed schema observed
Observed from `binance_aggregator_shi.py` CSV header:

1. Timestamp
2. Open
3. High
4. Low
5. Close
6. Volume
7. AggTrades
8. BuyQty
9. SellQty
10. VWAP
11. OpenInterest
12. FundingRate
13. LiqBuyQty
14. LiqSellQty
15. IsSynthetic

## B) Spec sections that align
- Raw input columns in Spec `Data Source` match the aggregator header exactly.
- `IsSynthetic` semantics are explicitly documented in the spec and present in feed.
- Locked event base columns in section `0. Output Format — LOCKED` are usable for a Phase 0 event schema placeholder.
- Dependency order in `# Dependencies` aligns with planned pipeline wiring order.

## C) Spec sections that are ambiguous or not yet implementable
- Spec `# 7 Analyzer Output Contracts — LOCKED` introduces additional contract details (event IDs, statuses, append-only behavior) not yet concretely mapped to raw feed-only Phase 0 implementation.
- Tick-size-dependent sweep rules require symbol metadata source and retrieval contract (not defined inside Analyzer Phase 0 scope).
- Some sections describe calibration constants as "calibratable" but do not define source-of-truth config location for analyzer runtime.
- Session context is clearly defined formula-wise, but timezone/input assumptions for non-UTC feeds are not formalized as a strict contract (Phase 0 assumes UTC parsing).

## D) Proposed Analyzer contracts
- **Input contract (strict):** analyzer loader requires the 15 raw feed columns exactly and raises explicit error on missing columns.
- **Timestamp contract:** parse `Timestamp` to UTC datetime and sort ascending before downstream modules.
- **Pipeline contract:** `run(input_path, output_dir)` is the single entrypoint, executes module chain, saves `analyzer_features.csv` and `analyzer_events.csv`.
- **Feature contract (Phase 0):** pass-through raw rows now; derived columns are declared as placeholders in schema for Phase 1 implementation.
- **Event contract (Phase 0):** return empty event table with locked base event columns.
- **Lookahead posture:** module docstrings keep anti-lookahead as an explicit implementation constraint for future phases.

## E) Files created
- `analyzer/__init__.py`
- `analyzer/schema.py`
- `analyzer/loader.py`
- `analyzer/base_metrics.py`
- `analyzer/swings.py`
- `analyzer/sweeps.py`
- `analyzer/failed_breaks.py`
- `analyzer/absorption.py`
- `analyzer/events.py`
- `analyzer/io.py`
- `analyzer/pipeline.py`
- `docs/Analyzer_Phase0_Audit.md`

## F) Tests added
- `tests/test_schema.py`
- `tests/test_loader.py`
- `tests/test_base_metrics.py`
- `tests/test_swings.py`
- `tests/test_sweeps.py`
- `tests/test_failed_breaks.py`
- `tests/test_events.py`
- `tests/test_pipeline.py`
- `tests/fixtures/sample_raw_minimal.csv`
- `tests/fixtures/sample_raw_with_synthetic.csv`
- `tests/fixtures/sample_raw_with_gap.csv`

## G) Open questions / TODOs
1. Confirm whether Analyzer must implement full section 7 event identity fields in v1.0 or if base columns are sufficient for Phase 1.
2. Define where symbol tick size metadata is sourced (config, exchange client, or sidecar file).
3. Define runtime location/format for calibratable constants (YAML/ENV/Python module).
4. Confirm whether `Timestamp` is guaranteed UTC ISO format across all ingestion paths.
5. Confirm desired handling of duplicate timestamps (currently sorted only, not deduplicated).
