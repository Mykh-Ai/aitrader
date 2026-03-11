from analyzer.schema import REQUIRED_RAW_COLUMNS, missing_required_columns


def test_required_columns_exactly_15_fields():
    assert len(REQUIRED_RAW_COLUMNS) == 15
    assert REQUIRED_RAW_COLUMNS[0] == "Timestamp"
    assert REQUIRED_RAW_COLUMNS[-1] == "IsSynthetic"


def test_missing_required_columns_detects_missing_fields():
    cols = REQUIRED_RAW_COLUMNS[:-1]
    missing = missing_required_columns(cols)
    assert missing == ["IsSynthetic"]
