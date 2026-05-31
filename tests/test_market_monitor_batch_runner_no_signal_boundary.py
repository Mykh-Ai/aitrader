from pathlib import Path

import pandas as pd

from market_monitor.batch_runner import BATCH_BOUNDARY_STATEMENT, run_batch_research
from market_monitor.research_summary import BOUNDARY_STATEMENT as RESEARCH_BOUNDARY_STATEMENT


FORBIDDEN_COLUMNS = {
    "signal",
    "entry",
    "exit",
    "order",
    "position",
    "position_size",
    "leverage",
    "stop_loss",
    "take_profit",
    "risk",
    "pnl",
    "win",
    "loss",
    "rejected",
    "accepted",
}

FORBIDDEN_TERMS = {
    "buy",
    "sell",
    "long",
    "short",
    "entry",
    "exit",
    "stop loss",
    "take profit",
    "pnl",
    "profit",
    "loss",
    "win",
    "rejected sweep",
    "accepted sweep",
    "failed breakout",
    "accepted breakout",
    "signal",
}


def test_batch_outputs_do_not_add_signal_order_position_pnl_or_classification_fields(
    tmp_path: Path,
):
    feed_dir = tmp_path / "feed"
    _write_feed(feed_dir / "2026-05-07.csv", "2026-05-07")
    output_dir = tmp_path / "batch"

    run_batch_research(feed_dir, output_dir, run_timestamp="2026-05-31T00:00:00Z")

    for csv_path in [
        output_dir / "batch_manifest.csv",
        output_dir / "research_summary" / "post_sweep_research_summary.csv",
        output_dir / "research_summary" / "post_sweep_group_summary.csv",
    ]:
        columns = {column.lower() for column in pd.read_csv(csv_path).columns}
        assert columns.isdisjoint(FORBIDDEN_COLUMNS)


def test_batch_markdown_keeps_action_result_terms_only_in_negative_boundary_statement(
    tmp_path: Path,
):
    feed_dir = tmp_path / "feed"
    _write_feed(feed_dir / "2026-05-07.csv", "2026-05-07")
    output_dir = tmp_path / "batch"

    run_batch_research(feed_dir, output_dir, run_timestamp="2026-05-31T00:00:00Z")

    for markdown_path, boundary in [
        (output_dir / "batch_summary.md", BATCH_BOUNDARY_STATEMENT),
        (
            output_dir / "research_summary" / "post_sweep_research_summary.md",
            RESEARCH_BOUNDARY_STATEMENT,
        ),
    ]:
        text = markdown_path.read_text(encoding="utf-8")
        assert boundary in text
        check_text = text.replace(boundary, "").lower()
        for term in FORBIDDEN_TERMS:
            assert term not in check_text


def test_market_monitor_runs_is_ignored_not_a_batch_artifact_contract():
    gitignore = Path(".gitignore").read_text(encoding="utf-8")
    assert "market_monitor_runs/" in gitignore


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
