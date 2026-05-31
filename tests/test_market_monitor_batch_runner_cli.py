from pathlib import Path

import pandas as pd

from market_monitor.run_batch_research import main


def test_batch_research_cli_writes_outputs(tmp_path: Path):
    feed_dir = tmp_path / "feed"
    _write_feed(feed_dir / "2026-05-07.csv", "2026-05-07")
    output_dir = tmp_path / "batch"

    assert main(
        [
            "--feed-dir",
            str(feed_dir),
            "--output",
            str(output_dir),
            "--start-date",
            "2026-05-07",
            "--end-date",
            "2026-05-07",
            "--run-timestamp",
            "2026-05-31T00:00:00Z",
        ]
    ) == 0

    manifest = pd.read_csv(output_dir / "batch_manifest.csv")
    assert manifest.loc[0, "status"] == "PROCESSED"
    assert (output_dir / "batch_summary.md").exists()
    assert (output_dir / "research_summary" / "post_sweep_group_summary.csv").exists()


def test_batch_research_cli_returns_nonzero_for_no_files(tmp_path: Path):
    feed_dir = tmp_path / "feed"
    feed_dir.mkdir()

    assert main(
        [
            "--feed-dir",
            str(feed_dir),
            "--output",
            str(tmp_path / "batch"),
            "--run-timestamp",
            "2026-05-31T00:00:00Z",
        ]
    ) == 2


def _write_feed(path: Path, day: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "Timestamp,Open,High,Low,Close,Volume,AggTrades,BuyQty,SellQty,OpenInterest,FundingRate,IsSynthetic",
                f"{day}T00:00:00Z,100,101,99,100,100,10,60,40,1000,0.0001,0",
                f"{day}T07:59:00Z,100,110,98,101,100,11,60,40,1001,0.0001,0",
                f"{day}T08:00:00Z,101,102,97,100,100,12,60,40,1002,0.0001,0",
                f"{day}T15:59:00Z,100,106,92,99,100,13,60,40,1003,0.0001,0",
                f"{day}T16:00:00Z,99,103,98,100,100,14,60,40,1004,0.0001,0",
                f"{day}T23:59:00Z,100,104,96,100,100,15,60,40,1005,0.0001,0",
            ]
        ),
        encoding="utf-8",
    )
