from pathlib import Path

from analyzer.base_metrics import add_base_metrics
from analyzer.loader import load_raw_csv


def test_base_metrics_stub_returns_copy():
    df = load_raw_csv(Path(__file__).parent / "fixtures" / "sample_raw_minimal.csv")
    out = add_base_metrics(df)

    assert out.equals(df)
    assert out is not df
