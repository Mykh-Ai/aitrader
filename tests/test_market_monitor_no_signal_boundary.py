from pathlib import Path

import pandas as pd

from market_monitor.config import BOUNDARY_STATEMENT
from market_monitor.outputs import REQUIRED_CSV_SCHEMAS
from market_monitor.run_market_monitor import main


PROHIBITED_COLUMNS = {
    "signal",
    "entry",
    "exit",
    "side_to_trade",
    "order",
    "position",
    "position_size",
    "leverage",
    "stop_loss",
    "take_profit",
    "risk",
}

PROHIBITED_SUMMARY_PHRASES = {
    "buy now",
    "sell now",
    "long",
    "short",
    "entry",
    "exit",
    "stop loss",
    "take profit",
    "position size",
    "leverage",
    "risk per trade",
    "execution instruction",
}

FUTURE_LABEL_COLUMNS = {
    "future_return",
    "forward_return",
    "outcome_12_bar",
    "outcome_12_bars",
    "twelve_bar_outcome",
    "future_label",
}


def test_outputs_do_not_produce_signal_order_position_or_future_label_fields(tmp_path: Path):
    output_dir = _run_monitor(tmp_path)

    for filename in REQUIRED_CSV_SCHEMAS:
        columns = {column.lower() for column in pd.read_csv(output_dir / filename).columns}
        assert columns.isdisjoint(PROHIBITED_COLUMNS)
        assert columns.isdisjoint(FUTURE_LABEL_COLUMNS)


def test_market_summary_uses_only_required_negative_boundary_language(tmp_path: Path):
    output_dir = _run_monitor(tmp_path)
    summary = (output_dir / "market_summary.md").read_text(encoding="utf-8")

    assert BOUNDARY_STATEMENT in summary
    check_text = summary.replace(BOUNDARY_STATEMENT, "").lower()
    for phrase in PROHIBITED_SUMMARY_PHRASES:
        assert phrase not in check_text


def _run_monitor(tmp_path: Path) -> Path:
    input_file = tmp_path / "feed.csv"
    input_file.write_text(
        "\n".join(
            [
                "Timestamp,Open,High,Low,Close,Volume,AggTrades,BuyQty,SellQty,OpenInterest,FundingRate",
                "2025-01-01T00:00:00Z,100,101,99,100.5,10,5,6,4,1000,0.0001",
                "2025-01-01T00:01:00Z,100.5,102,100,101.5,12,7,7,5,1001,0.0001",
            ]
        ),
        encoding="utf-8",
    )
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
    return output_dir

