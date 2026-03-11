from pathlib import Path

from analyzer.loader import load_raw_csv
from analyzer.sweeps import detect_sweeps


def test_sweeps_stub_returns_copy():
    df = load_raw_csv(Path(__file__).parent / "fixtures" / "sample_raw_with_gap.csv")
    out = detect_sweeps(df)
    assert out.equals(df)
    assert out is not df
