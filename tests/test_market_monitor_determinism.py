from pathlib import Path

from market_monitor.outputs import REQUIRED_CSV_SCHEMAS
from market_monitor.run_market_monitor import main


def test_csv_outputs_are_deterministic_for_identical_input(tmp_path: Path):
    input_file = tmp_path / "feed.csv"
    input_file.write_text(
        "\n".join(
            [
                "Timestamp,Open,High,Low,Close,Volume,AggTrades,BuyQty,SellQty,OpenInterest,FundingRate",
                "2025-01-01T00:00:00Z,100,101,99,100.5,10,5,6,4,1000,0.0001",
                "2025-01-01T01:00:00Z,100.5,104,100,103.5,12,7,7,5,1001,0.0001",
                "2025-01-01T02:00:00Z,103.5,103.8,101,101.5,11,6,5,6,1000,0.0001",
                "2025-01-02T00:00:00Z,101.5,102,99.5,100,15,9,8,7,1002,0.0001",
            ]
        ),
        encoding="utf-8",
    )
    out_a = tmp_path / "out_a"
    out_b = tmp_path / "out_b"
    args = ["--input", str(input_file), "--run-timestamp", "2026-05-31T00:00:00Z"]

    assert main(args + ["--output", str(out_a)]) == 0
    assert main(args + ["--output", str(out_b)]) == 0

    for filename in REQUIRED_CSV_SCHEMAS:
        assert (out_a / filename).read_text(encoding="utf-8") == (
            out_b / filename
        ).read_text(encoding="utf-8")

