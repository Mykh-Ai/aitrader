from pathlib import Path

from analyzer.events import build_events
from analyzer.loader import load_raw_csv
from analyzer.schema import EVENT_COLUMNS


def test_events_stub_returns_empty_table_with_contract_columns():
    df = load_raw_csv(Path(__file__).parent / "fixtures" / "sample_raw_minimal.csv")
    events = build_events(df)

    assert events.empty
    assert events.columns.tolist() == EVENT_COLUMNS
