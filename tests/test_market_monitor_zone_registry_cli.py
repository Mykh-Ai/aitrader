from pathlib import Path

import pandas as pd

from market_monitor.run_market_monitor import main


def test_runner_supports_registry_in_out_and_does_not_mutate_registry_in(tmp_path: Path):
    day1_input = _write_feed(tmp_path / "day1.csv", "2026-05-07", 100)
    day2_input = _write_feed(tmp_path / "day2.csv", "2026-05-08", 101)
    day1_out = tmp_path / "day1_out"
    day2_out = tmp_path / "day2_out"
    registry_1 = day1_out / "liquidity_zone_registry.csv"
    registry_2 = day2_out / "custom_registry.csv"

    assert main(
        [
            "--input",
            str(day1_input),
            "--output",
            str(day1_out),
            "--registry-out",
            str(registry_1),
            "--run-timestamp",
            "2026-05-31T00:00:00Z",
        ]
    ) == 0
    before = registry_1.read_text(encoding="utf-8")

    assert main(
        [
            "--input",
            str(day2_input),
            "--output",
            str(day2_out),
            "--registry-in",
            str(registry_1),
            "--registry-out",
            str(registry_2),
            "--run-timestamp",
            "2026-05-31T00:00:00Z",
        ]
    ) == 0

    assert registry_1.read_text(encoding="utf-8") == before
    assert registry_2.exists()
    assert (day2_out / "liquidity_zone_registry.csv").exists()
    summary = (day2_out / "market_summary.md").read_text(encoding="utf-8")
    assert f"Registry input: {registry_1}" in summary
    assert f"Registry output: {registry_2}" in summary
    assert len(pd.read_csv(registry_2)) >= len(pd.read_csv(registry_1))


def _write_feed(path: Path, day: str, close: float) -> Path:
    path.write_text(
        "\n".join(
            [
                "Timestamp,Open,High,Low,Close,Volume,AggTrades,BuyQty,SellQty,OpenInterest,FundingRate",
                f"{day}T00:00:00Z,{close},{close + 1},{close - 1},{close},10,1,5,5,1000,0.0001",
                f"{day}T08:00:00Z,{close},{close + 8},{close - 8},{close},10,1,5,5,1000,0.0001",
                f"{day}T16:00:00Z,{close},{close + 4},{close - 4},{close},10,1,5,5,1000,0.0001",
                f"{day}T23:59:00Z,{close},{close + 2},{close - 2},{close},10,1,5,5,1000,0.0001",
            ]
        ),
        encoding="utf-8",
    )
    return path
