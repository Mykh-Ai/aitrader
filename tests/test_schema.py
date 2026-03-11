from analyzer.schema import (
    FEATURE_COLUMNS_IMPLEMENTED,
    FEATURE_COLUMNS_PHASE0,
    FEATURE_COLUMNS_PLANNED,
    NUMERIC_RAW_COLUMNS,
    REQUIRED_RAW_COLUMNS,
    missing_required_columns,
    non_numeric_required_columns,
)


def test_required_columns_exactly_15_fields():
    assert len(REQUIRED_RAW_COLUMNS) == 15
    assert REQUIRED_RAW_COLUMNS[0] == "Timestamp"
    assert REQUIRED_RAW_COLUMNS[-1] == "IsSynthetic"


def test_missing_required_columns_detects_missing_fields():
    cols = REQUIRED_RAW_COLUMNS[:-1]
    missing = missing_required_columns(cols)
    assert missing == ["IsSynthetic"]


def test_numeric_columns_contract_is_explicit():
    assert "Timestamp" not in NUMERIC_RAW_COLUMNS
    assert "IsSynthetic" not in NUMERIC_RAW_COLUMNS
    assert len(NUMERIC_RAW_COLUMNS) == 13


def test_non_numeric_required_columns_detects_missing_fields():
    cols = [c for c in REQUIRED_RAW_COLUMNS if c != "Volume"]
    missing = non_numeric_required_columns(cols)
    assert missing == ["Volume"]


def test_feature_contract_separates_implemented_vs_planned():
    assert set(FEATURE_COLUMNS_IMPLEMENTED).isdisjoint(FEATURE_COLUMNS_PLANNED)
    assert FEATURE_COLUMNS_PHASE0 == FEATURE_COLUMNS_IMPLEMENTED + FEATURE_COLUMNS_PLANNED
