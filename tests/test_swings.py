from pathlib import Path

from analyzer.loader import load_raw_csv
from analyzer.swings import annotate_swings


def test_swings_stub_returns_copy():
    df = load_raw_csv(Path(__file__).parent / "fixtures" / "sample_raw_minimal.csv")
    out = annotate_swings(df)
    assert out.equals(df)
    assert out is not df
