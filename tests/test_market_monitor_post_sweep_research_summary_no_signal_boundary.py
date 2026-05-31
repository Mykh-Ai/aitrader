from pathlib import Path

import pandas as pd

from market_monitor.post_sweep_observation import POST_SWEEP_OBSERVATION_COLUMNS
from market_monitor.research_summary import (
    BOUNDARY_STATEMENT,
    build_post_sweep_research_summary,
)


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


def test_research_summary_has_no_signal_order_position_or_classification_columns(tmp_path: Path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    pd.DataFrame([_observation_row()]).to_csv(
        run_dir / "post_sweep_observation.csv", index=False
    )
    output_dir = tmp_path / "summary"

    build_post_sweep_research_summary(
        [run_dir],
        output_dir,
        run_timestamp="2026-05-31T00:00:00Z",
    )

    row_summary = pd.read_csv(output_dir / "post_sweep_research_summary.csv")
    group_summary = pd.read_csv(output_dir / "post_sweep_group_summary.csv")
    assert {column.lower() for column in row_summary.columns}.isdisjoint(FORBIDDEN_COLUMNS)
    assert {column.lower() for column in group_summary.columns}.isdisjoint(FORBIDDEN_COLUMNS)


def test_research_summary_markdown_has_boundary_and_small_sample_warnings(tmp_path: Path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    pd.DataFrame([_observation_row()]).to_csv(
        run_dir / "post_sweep_observation.csv", index=False
    )
    output_dir = tmp_path / "summary"

    build_post_sweep_research_summary(
        [run_dir],
        output_dir,
        run_timestamp="2026-05-31T00:00:00Z",
    )

    markdown = (output_dir / "post_sweep_research_summary.md").read_text(encoding="utf-8")
    assert BOUNDARY_STATEMENT in markdown
    assert "Sample size is below 30 observations" in markdown
    assert "Sample size is below 100 observations" in markdown
    outside_boundary = markdown.replace(BOUNDARY_STATEMENT, "")
    assert "rejected/accepted" not in outside_boundary.lower()
    assert "pnl" not in outside_boundary.lower()
    assert "buy" not in outside_boundary.lower()
    assert "sell" not in outside_boundary.lower()


def _observation_row():
    row = {column: "" for column in POST_SWEEP_OBSERVATION_COLUMNS}
    row.update(
        {
            "observation_id": "observation_000001",
            "source_event_id": "event_000001",
            "source_event_timestamp": "2026-05-08T00:01:00Z",
            "zone_id": "zone_000001",
            "side": "BUY_SIDE",
            "zone_type": "H1_LEVEL_ZONE",
            "zone_price_lower": 100,
            "zone_price_upper": 110,
            "zone_price_mid": 105,
            "observation_bars_expected": 30,
            "observation_bars_available": 30,
            "observation_complete": True,
            "max_excursion_beyond_zone": 20,
            "max_return_inside_zone": 15,
            "bars_inside_zone": 29,
            "bars_above_zone": 1,
            "bars_below_zone": 0,
            "net_close_change_pct": 0.2,
            "post_delta_pct": 0.1,
            "post_oi_change": 3,
            "post_max_volume_zscore": 2,
            "post_max_abs_delta_zscore": 3,
            "data_quality": "RAW",
        }
    )
    return row
