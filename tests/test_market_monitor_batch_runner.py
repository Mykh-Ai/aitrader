from pathlib import Path

import pandas as pd
import pytest

from market_monitor.batch_runner import (
    BATCH_BOUNDARY_STATEMENT,
    BatchResearchError,
    MANIFEST_COLUMNS,
    run_batch_research,
)


def test_discovers_filters_sorts_and_applies_max_days(tmp_path: Path):
    feed_dir = tmp_path / "feed"
    _write_feed(feed_dir / "2026-05-09.csv", "2026-05-09", close_base=100)
    _write_feed(feed_dir / "2026-05-07.csv", "2026-05-07", close_base=100)
    _write_feed(feed_dir / "2026-05-08.csv", "2026-05-08", close_base=100)
    (feed_dir / "notes.csv").write_text("not,a,daily,file\n", encoding="utf-8")
    output_dir = tmp_path / "batch"

    result = run_batch_research(
        feed_dir,
        output_dir,
        start_date="2026-05-07",
        end_date="2026-05-09",
        max_days=2,
        run_timestamp="2026-05-31T00:00:00Z",
    )

    manifest = pd.read_csv(result.manifest_path)
    assert manifest["date"].tolist() == ["2026-05-07", "2026-05-08"]
    assert manifest["status"].tolist() == ["PROCESSED", "PROCESSED"]
    assert result.processed_days == 2
    assert result.skipped_days == 0
    assert result.failed_days == 0


def test_runs_multiple_days_carries_registry_and_writes_batch_artifacts(tmp_path: Path):
    feed_dir = tmp_path / "feed"
    _write_feed(feed_dir / "2026-05-07.csv", "2026-05-07", close_base=100)
    _write_feed(feed_dir / "2026-05-08.csv", "2026-05-08", close_base=101)
    output_dir = tmp_path / "batch"

    result = run_batch_research(
        feed_dir,
        output_dir,
        start_date="2026-05-07",
        end_date="2026-05-08",
        run_timestamp="2026-05-31T00:00:00Z",
    )

    assert (output_dir / "daily" / "2026-05-07" / "market_summary.md").exists()
    assert (output_dir / "daily" / "2026-05-08" / "market_summary.md").exists()
    assert (output_dir / "daily" / "2026-05-07" / "market_move_groups.csv").exists()
    assert (output_dir / "daily" / "2026-05-08" / "market_move_groups.csv").exists()
    assert (output_dir / "batch_manifest.csv").exists()
    assert (output_dir / "batch_summary.md").exists()
    assert (output_dir / "research_summary" / "post_sweep_research_summary.md").exists()
    assert (output_dir / "research_summary" / "post_sweep_research_summary.csv").exists()
    assert (output_dir / "research_summary" / "post_sweep_group_summary.csv").exists()

    manifest = pd.read_csv(output_dir / "batch_manifest.csv")
    assert manifest.columns.tolist() == MANIFEST_COLUMNS
    assert pd.isna(manifest.loc[0, "registry_in"])
    assert manifest.loc[0, "registry_out"] == "daily/2026-05-07/liquidity_zone_registry.csv"
    assert manifest.loc[1, "registry_in"] == "daily/2026-05-07/liquidity_zone_registry.csv"
    assert manifest.loc[1, "registry_out"] == "daily/2026-05-08/liquidity_zone_registry.csv"
    summary = (output_dir / "batch_summary.md").read_text(encoding="utf-8")
    assert "- Grouped unresolved market moves:" in summary
    assert "- Multi-event market moves:" in summary
    assert "- Max group span minutes:" in summary
    assert "- Groups over configured window:" in summary
    assert result.daily_output_dirs == (
        output_dir / "daily" / "2026-05-07",
        output_dir / "daily" / "2026-05-08",
    )


def test_degraded_day_is_skipped_without_breaking_next_registry_carry(tmp_path: Path):
    feed_dir = tmp_path / "feed"
    _write_feed(feed_dir / "2026-05-07.csv", "2026-05-07", close_base=100)
    _write_feed(feed_dir / "2026-05-08.csv", "2026-05-08", close_base=100, degraded=True)
    _write_feed(feed_dir / "2026-05-09.csv", "2026-05-09", close_base=101)
    output_dir = tmp_path / "batch"

    result = run_batch_research(
        feed_dir,
        output_dir,
        start_date="2026-05-07",
        end_date="2026-05-09",
        run_timestamp="2026-05-31T00:00:00Z",
    )

    manifest = pd.read_csv(output_dir / "batch_manifest.csv")
    assert manifest["status"].tolist() == ["PROCESSED", "SKIPPED", "PROCESSED"]
    assert manifest.loc[1, "reason"] == "DEGRADED_DATA_EXCLUDED"
    assert manifest.loc[2, "registry_in"] == "daily/2026-05-07/liquidity_zone_registry.csv"
    assert result.processed_days == 2
    assert result.skipped_days == 1
    assert not (output_dir / "daily" / "2026-05-08" / "market_summary.md").exists()


def test_degraded_day_can_be_included_explicitly(tmp_path: Path):
    feed_dir = tmp_path / "feed"
    _write_feed(feed_dir / "2026-05-08.csv", "2026-05-08", close_base=100, degraded=True)
    output_dir = tmp_path / "batch"

    result = run_batch_research(
        feed_dir,
        output_dir,
        include_degraded=True,
        run_timestamp="2026-05-31T00:00:00Z",
    )

    manifest = pd.read_csv(result.manifest_path)
    assert manifest.loc[0, "status"] == "PROCESSED"
    assert manifest.loc[0, "data_quality_summary"] == "RECOVERED_DEGRADED=6"
    assert "Degraded days processed: 1" in result.summary_path.read_text(encoding="utf-8")


def test_missing_files_inside_explicit_range_fail_fast_with_manifest(tmp_path: Path):
    feed_dir = tmp_path / "feed"
    _write_feed(feed_dir / "2026-05-07.csv", "2026-05-07", close_base=100)
    output_dir = tmp_path / "batch"

    with pytest.raises(BatchResearchError, match="No feed file found for 2026-05-08"):
        run_batch_research(
            feed_dir,
            output_dir,
            start_date="2026-05-07",
            end_date="2026-05-08",
            run_timestamp="2026-05-31T00:00:00Z",
        )

    manifest = pd.read_csv(output_dir / "batch_manifest.csv")
    assert manifest["status"].tolist() == ["PROCESSED", "FAILED"]
    assert manifest.loc[1, "reason"] == "NO_FILE"


def test_no_files_found_has_clear_error_and_empty_artifacts(tmp_path: Path):
    feed_dir = tmp_path / "feed"
    feed_dir.mkdir()
    output_dir = tmp_path / "batch"

    with pytest.raises(BatchResearchError, match="No daily feed CSV files found"):
        run_batch_research(
            feed_dir,
            output_dir,
            run_timestamp="2026-05-31T00:00:00Z",
        )

    assert pd.read_csv(output_dir / "batch_manifest.csv").empty
    assert (output_dir / "research_summary" / "post_sweep_research_summary.csv").exists()


def test_outputs_are_deterministic_for_identical_batch_rerun(tmp_path: Path):
    feed_dir = tmp_path / "feed"
    _write_feed(feed_dir / "2026-05-07.csv", "2026-05-07", close_base=100)
    _write_feed(feed_dir / "2026-05-08.csv", "2026-05-08", close_base=101)
    output_dir = tmp_path / "batch"

    run_batch_research(feed_dir, output_dir, run_timestamp="2026-05-31T00:00:00Z")
    first_manifest = (output_dir / "batch_manifest.csv").read_text(encoding="utf-8")
    first_summary = (output_dir / "batch_summary.md").read_text(encoding="utf-8")
    first_research = (
        output_dir / "research_summary" / "post_sweep_research_summary.csv"
    ).read_text(encoding="utf-8")

    run_batch_research(feed_dir, output_dir, run_timestamp="2026-05-31T00:00:00Z")

    assert (output_dir / "batch_manifest.csv").read_text(encoding="utf-8") == first_manifest
    assert (output_dir / "batch_summary.md").read_text(encoding="utf-8") == first_summary
    assert (
        output_dir / "research_summary" / "post_sweep_research_summary.csv"
    ).read_text(encoding="utf-8") == first_research


def _write_feed(path: Path, day: str, *, close_base: float, degraded: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    synthetic = 1 if degraded else 0
    rows = [
        ("00:00:00", close_base, close_base + 1, close_base - 1, close_base),
        ("07:59:00", close_base, close_base + 10, close_base - 2, close_base + 1),
        ("08:00:00", close_base + 1, close_base + 2, close_base - 3, close_base),
        ("15:59:00", close_base, close_base + 6, close_base - 8, close_base - 1),
        ("16:00:00", close_base - 1, close_base + 3, close_base - 2, close_base),
        ("23:59:00", close_base, close_base + 4, close_base - 4, close_base),
    ]
    lines = [
        "Timestamp,Open,High,Low,Close,Volume,AggTrades,BuyQty,SellQty,OpenInterest,FundingRate,IsSynthetic"
    ]
    for idx, (time, open_, high, low, close) in enumerate(rows):
        lines.append(
            f"{day}T{time}Z,{open_},{high},{low},{close},100,{10 + idx},60,40,{1000 + idx},0.0001,{synthetic}"
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def test_batch_boundary_statement_is_exact():
    assert BATCH_BOUNDARY_STATEMENT == (
        "This batch research summary is descriptive only. It does not classify "
        "trade outcomes, does not generate trading signals, does not "
        "define entries/exits, does not calculate PnL, and does not trigger "
        "Backtester or Executor behavior."
    )
