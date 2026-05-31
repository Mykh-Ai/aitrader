from pathlib import Path

import pandas as pd

from market_monitor.post_sweep_observation import POST_SWEEP_OBSERVATION_COLUMNS
from market_monitor.run_research_summary import main


def test_research_summary_cli_writes_outputs(tmp_path: Path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    pd.DataFrame([_observation_row()]).to_csv(
        run_dir / "post_sweep_observation.csv", index=False
    )
    output_dir = tmp_path / "summary"

    assert main(
        [
            "--input-dir",
            str(run_dir),
            "--output",
            str(output_dir),
            "--run-timestamp",
            "2026-05-31T00:00:00Z",
        ]
    ) == 0

    assert (output_dir / "post_sweep_research_summary.md").exists()
    assert (output_dir / "post_sweep_research_summary.csv").exists()
    assert (output_dir / "post_sweep_group_summary.csv").exists()


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
