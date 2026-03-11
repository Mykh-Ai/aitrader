from pathlib import Path

from analyzer.failed_breaks import detect_failed_breaks
from analyzer.loader import load_raw_csv


def test_failed_breaks_stub_returns_copy():
    df = load_raw_csv(Path(__file__).parent / "fixtures" / "sample_raw_with_gap.csv")
    out = detect_failed_breaks(df, confirmation_bars=3)
    assert out.equals(df)
    assert out is not df
