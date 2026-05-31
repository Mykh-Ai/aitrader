from pathlib import Path

import pandas as pd

from market_monitor.post_sweep_observation import POST_SWEEP_OBSERVATION_COLUMNS
from market_monitor.research_summary import (
    GROUP_SUMMARY_COLUMNS,
    ROW_SUMMARY_COLUMNS,
    build_post_sweep_research_summary,
)


def test_research_summary_loads_multiple_run_dirs_and_writes_outputs(tmp_path: Path):
    run_a = _write_run(tmp_path / "run_a", side="BUY_SIDE", observation_id="observation_000001")
    run_b = _write_run(tmp_path / "run_b", side="SELL_SIDE", observation_id="observation_000002")
    output_dir = tmp_path / "summary"

    result = build_post_sweep_research_summary(
        [run_b, run_a],
        output_dir,
        run_timestamp="2026-05-31T00:00:00Z",
    )

    assert result.observation_count == 2
    assert result.complete_count == 2
    assert result.incomplete_count == 0
    assert result.event_counts_by_type["LIQUIDITY_SWEEP_UNRESOLVED"] == 2
    assert (output_dir / "post_sweep_research_summary.md").exists()
    assert (output_dir / "post_sweep_research_summary.csv").exists()
    assert (output_dir / "post_sweep_group_summary.csv").exists()

    rows = pd.read_csv(output_dir / "post_sweep_research_summary.csv")
    assert rows.columns.tolist() == ROW_SUMMARY_COLUMNS
    assert rows["source_run_dir"].tolist() == [str(run_a), str(run_b)]
    assert rows["market_move_id"].tolist() == [
        "move_20260508_000100_BUY_SIDE_000001",
        "move_20260508_000100_SELL_SIDE_000001",
    ]
    assert rows["market_move_role"].tolist() == ["PRIMARY", "PRIMARY"]
    assert rows["group_span_minutes"].tolist() == [0, 0]
    assert rows["grouping_window_mode"].tolist() == [
        "ANCHORED_FIXED_WINDOW",
        "ANCHORED_FIXED_WINDOW",
    ]

    groups = pd.read_csv(output_dir / "post_sweep_group_summary.csv")
    assert groups.columns.tolist() == GROUP_SUMMARY_COLUMNS
    assert "ALL" in groups["group_type"].tolist()
    assert set(groups[groups["group_type"] == "side"]["group_value"]) == {"BUY_SIDE", "SELL_SIDE"}
    assert "MEDIUM" in groups[groups["group_type"] == "confidence_tier"]["group_value"].tolist()
    assert "PRIMARY" in groups[groups["group_type"] == "market_move_role"]["group_value"].tolist()
    markdown = (output_dir / "post_sweep_research_summary.md").read_text(encoding="utf-8")
    assert "- Grouped unresolved market moves: 2" in markdown
    assert "- Multi-event market moves: 0" in markdown
    assert "- Max group span minutes: 0" in markdown
    assert "- Groups over configured window: 0" in markdown
    assert "- Grouping window mode: ANCHORED_FIXED_WINDOW=2" in markdown


def test_research_summary_handles_missing_and_header_only_observation_files(tmp_path: Path):
    missing = tmp_path / "missing_obs"
    missing.mkdir()
    header_only = tmp_path / "header_only"
    header_only.mkdir()
    pd.DataFrame(columns=POST_SWEEP_OBSERVATION_COLUMNS).to_csv(
        header_only / "post_sweep_observation.csv", index=False
    )
    output_dir = tmp_path / "summary"

    result = build_post_sweep_research_summary(
        [missing, header_only],
        output_dir,
        run_timestamp="2026-05-31T00:00:00Z",
    )

    assert result.observation_count == 0
    assert result.warnings == (f"Missing post_sweep_observation.csv in {missing}",)
    rows = pd.read_csv(output_dir / "post_sweep_research_summary.csv")
    groups = pd.read_csv(output_dir / "post_sweep_group_summary.csv")
    markdown = (output_dir / "post_sweep_research_summary.md").read_text(encoding="utf-8")
    assert rows.empty
    assert rows.columns.tolist() == ROW_SUMMARY_COLUMNS
    assert groups.loc[0, "group_type"] == "ALL"
    assert groups.loc[0, "observation_count"] == 0
    assert "Observation rows loaded: 0" in markdown
    assert "Missing post_sweep_observation.csv" in markdown


def test_research_summary_outputs_are_deterministic(tmp_path: Path):
    run_dir = _write_run(tmp_path / "run", side="BUY_SIDE", observation_id="observation_000001")
    out_a = tmp_path / "out_a"
    out_b = tmp_path / "out_b"

    build_post_sweep_research_summary([run_dir], out_a, run_timestamp="2026-05-31T00:00:00Z")
    build_post_sweep_research_summary([run_dir], out_b, run_timestamp="2026-05-31T00:00:00Z")

    for filename in [
        "post_sweep_research_summary.md",
        "post_sweep_research_summary.csv",
        "post_sweep_group_summary.csv",
    ]:
        assert (out_a / filename).read_text(encoding="utf-8") == (
            out_b / filename
        ).read_text(encoding="utf-8")


def _write_run(path: Path, *, side: str, observation_id: str) -> Path:
    path.mkdir(parents=True)
    event_id = observation_id.replace("observation", "event")
    pd.DataFrame([_observation_row(observation_id, event_id, side)]).to_csv(
        path / "post_sweep_observation.csv", index=False
    )
    pd.DataFrame([_event_row(event_id, side)]).to_csv(path / "event_log.csv", index=False)
    return path


def _observation_row(observation_id: str, event_id: str, side: str) -> dict[str, object]:
    row = {column: "" for column in POST_SWEEP_OBSERVATION_COLUMNS}
    row.update(
        {
            "observation_id": observation_id,
            "source_event_id": event_id,
            "source_event_timestamp": "2026-05-08T00:01:00Z",
            "market_move_id": f"move_20260508_000100_{side}_000001",
            "market_move_role": "PRIMARY",
            "market_move_event_count": 1,
            "group_start_timestamp": "2026-05-08T00:01:00Z",
            "group_end_timestamp": "2026-05-08T00:01:00Z",
            "group_span_minutes": 0,
            "grouping_window_mode": "ANCHORED_FIXED_WINDOW",
            "zone_id": "zone_000001",
            "side": side,
            "zone_type": "H1_LEVEL_ZONE",
            "zone_price_lower": 100,
            "zone_price_upper": 110,
            "zone_price_mid": 105,
            "observation_bars_expected": 30,
            "observation_bars_available": 30,
            "observation_complete": True,
            "max_high_after_event": 130,
            "min_low_after_event": 95,
            "close_at_window_end": 106,
            "max_excursion_beyond_zone": 20,
            "max_return_inside_zone": 15,
            "bars_inside_zone": 29,
            "bars_above_zone": 1,
            "bars_below_zone": 0 if side == "BUY_SIDE" else 1,
            "net_close_change_abs": 12,
            "net_close_change_pct": 0.2,
            "post_volume_sum": 100,
            "post_buy_qty_sum": 55,
            "post_sell_qty_sum": 45,
            "post_delta_sum": 10,
            "post_delta_pct": 0.1,
            "post_trades_sum": 20,
            "post_oi_change": 3,
            "post_max_volume_zscore": 2,
            "post_max_abs_delta_zscore": 3,
            "data_quality": "RAW",
        }
    )
    return row


def _event_row(event_id: str, side: str) -> dict[str, object]:
    return {
        "event_id": event_id,
        "event_timestamp": "2026-05-08T00:01:00Z",
        "event_type": "LIQUIDITY_SWEEP_UNRESOLVED",
        "zone_id": "zone_000001",
        "side": side,
        "price_before": 95,
        "event_high": 125,
        "event_low": 90,
        "event_close": 120,
        "excursion_abs": 15,
        "excursion_atr": 0,
        "volume_zscore": 2,
        "delta_zscore": 2,
        "oi_change": 1,
        "reaction_status": "UNRESOLVED",
        "market_move_id": f"move_20260508_000100_{side}_000001",
        "market_move_role": "PRIMARY",
        "market_move_event_count": 1,
        "group_start_timestamp": "2026-05-08T00:01:00Z",
        "group_end_timestamp": "2026-05-08T00:01:00Z",
        "group_span_minutes": 0,
        "grouping_window_mode": "ANCHORED_FIXED_WINDOW",
        "evidence_json": (
            '{"confidence_tier":"MEDIUM","source_timeframes":"H1",'
            '"event_class":"LIQUIDITY_SWEEP_UNRESOLVED"}'
        ),
        "data_quality": "RAW",
    }
