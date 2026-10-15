from pathlib import Path

import pandas as pd

from market_monitor.run_market_monitor import main
from market_monitor.outputs import REQUIRED_CSV_SCHEMAS


def test_runner_creates_required_output_files_with_exact_headers(tmp_path: Path):
    input_file = _write_sample_feed(tmp_path)
    output_dir = tmp_path / "out"

    assert main(
        [
            "--input",
            str(input_file),
            "--output",
            str(output_dir),
            "--run-timestamp",
            "2026-05-31T00:00:00Z",
        ]
    ) == 0

    for filename, columns in REQUIRED_CSV_SCHEMAS.items():
        output_file = output_dir / filename
        assert output_file.exists()
        assert pd.read_csv(output_file).columns.tolist() == columns
    volume_delta = pd.read_csv(output_dir / "volume_delta_state.csv")
    assert volume_delta["liq_buy_qty"].tolist() == [1.0, 0.5, 0.0]
    assert volume_delta["liq_sell_qty"].tolist() == [2.0, 0.0, 0.25]
    assert volume_delta["liq_total_qty"].tolist() == [3.0, 0.5, 0.25]
    assert volume_delta["liquidation_data_available"].tolist() == [True, True, True]
    assert (output_dir / "market_summary.md").exists()


def _write_sample_feed(tmp_path: Path) -> Path:
    input_file = tmp_path / "feed.csv"
    input_file.write_text(
        "\n".join(
            [
                "Timestamp,Open,High,Low,Close,Volume,AggTrades,BuyQty,SellQty,OpenInterest,FundingRate,LiqBuyQty,LiqSellQty,IsSynthetic",
                "2025-01-01T00:00:00Z,100,101,99,100.5,10,5,6,4,1000,0.0001,1.0,2.0,0",
                "2025-01-01T00:01:00Z,100.5,102,100,101.5,12,7,7,5,1001,0.0001,0.5,0.0,0",
                "2025-01-02T00:00:00Z,101.5,103,101,102.5,15,9,9,6,1003,0.0001,0.0,0.25,0",
            ]
        ),
        encoding="utf-8",
    )
    return input_file
