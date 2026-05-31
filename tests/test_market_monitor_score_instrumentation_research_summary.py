import json
from pathlib import Path

import pandas as pd

from market_monitor.post_sweep_observation import POST_SWEEP_OBSERVATION_COLUMNS
from market_monitor.research_summary import ROW_SUMMARY_COLUMNS, build_post_sweep_research_summary
from market_monitor.score_instrumentation import SCORE_INSTRUMENTATION_COLUMNS


def test_research_summary_propagates_score_instrumentation_from_event_evidence(
    tmp_path: Path,
):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    pd.DataFrame([_observation_row()]).to_csv(
        run_dir / "post_sweep_observation.csv", index=False
    )
    pd.DataFrame([_event_row()]).to_csv(run_dir / "event_log.csv", index=False)
    output_dir = tmp_path / "summary"

    build_post_sweep_research_summary(
        [run_dir],
        output_dir,
        run_timestamp="2026-05-31T00:00:00Z",
    )

    rows = pd.read_csv(output_dir / "post_sweep_research_summary.csv")
    groups = pd.read_csv(output_dir / "post_sweep_group_summary.csv")
    assert rows.columns.tolist() == ROW_SUMMARY_COLUMNS
    assert all(column in rows.columns for column in SCORE_INSTRUMENTATION_COLUMNS)
    assert rows.loc[0, "confidence_score"] == 100
    assert rows.loc[0, "confidence_tier"] == "HIGH"
    assert rows.loc[0, "source_level_count"] == 3
    assert bool(rows.loc[0, "has_h4_source"]) is True
    assert "has_h4_source" in groups["group_type"].tolist()
    assert "source_level_count_bucket" in groups["group_type"].tolist()
    assert "zone_width_pct_bucket" in groups["group_type"].tolist()


def _observation_row():
    row = {column: "" for column in POST_SWEEP_OBSERVATION_COLUMNS}
    row.update(
        {
            "observation_id": "observation_000001",
            "source_event_id": "event_000001",
            "source_event_timestamp": "2026-05-08T00:01:00Z",
            "zone_id": "zone_000001",
            "side": "BUY_SIDE",
            "zone_type": "CLUSTERED_BUY_SIDE_ZONE",
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


def _event_row():
    evidence = {
        "confidence_score": 100,
        "confidence_tier": "HIGH",
        "source_timeframes": "CLUSTER|H1|H4|SESSION",
        "score_components_json": json.dumps(
            {"final_confidence_score": 100}, sort_keys=True, separators=(",", ":")
        ),
        "source_level_count": 3,
        "cluster_member_count": 3,
        "zone_width": 10,
        "zone_width_pct": 9.5238095238,
        "has_h1_source": True,
        "has_h4_source": True,
        "has_session_source": True,
        "has_equal_level_source": False,
        "has_pdh_pdl_source": False,
    }
    return {
        "event_id": "event_000001",
        "event_timestamp": "2026-05-08T00:01:00Z",
        "event_type": "LIQUIDITY_SWEEP_UNRESOLVED",
        "zone_id": "zone_000001",
        "side": "BUY_SIDE",
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
        "evidence_json": json.dumps(evidence, sort_keys=True, separators=(",", ":")),
        "data_quality": "RAW",
    }
