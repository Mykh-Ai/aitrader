from pathlib import Path

import pandas as pd

from market_monitor.label_quality import build_label_quality_report


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
    "profit",
}

FORBIDDEN_VERDICTS = {
    "EDGE_CONFIRMED",
    "STRATEGY_READY",
    "BACKTEST_READY",
    "LIVE_READY",
}


def test_label_quality_outputs_have_no_signal_order_position_pnl_or_ready_verdicts(tmp_path: Path):
    batch = tmp_path / "batch"
    research = batch / "research_summary"
    research.mkdir(parents=True)
    pd.DataFrame([_row(idx) for idx in range(31)]).to_csv(
        research / "post_sweep_research_summary.csv", index=False
    )

    result = build_label_quality_report([batch], tmp_path / "quality")

    summary = pd.read_csv(result.summary_path)
    assert {column.lower() for column in summary.columns}.isdisjoint(FORBIDDEN_COLUMNS)
    assert set(summary["quality_verdict"]).isdisjoint(FORBIDDEN_VERDICTS)
    markdown = result.markdown_path.read_text(encoding="utf-8")
    assert all(verdict not in markdown for verdict in FORBIDDEN_VERDICTS)


def _row(idx: int) -> dict[str, object]:
    return {
        "taxonomy_version": "SWEEP_LABEL_TAXONOMY_V1",
        "sweep_label": "SWEEP_REJECTED",
        "label_reason": "returned_and_closed_inside_within_10_bars",
        "source_event_timestamp": f"2026-03-17T00:{idx % 60:02d}:00Z",
        "market_move_id": f"move_{idx:06d}",
        "market_move_role": "PRIMARY",
        "market_move_event_count": 1,
        "side": "BUY_SIDE",
        "confidence_tier": "HIGH",
        "source_timeframes": "H1",
        "precision_status": "PRECISE",
        "has_h4_source": False,
        "has_session_source": False,
        "zone_width": 100,
        "zone_width_pct": 0.2,
        "observation_complete": True,
        "observation_bars_expected": 30,
        "observation_bars_available": 30,
        "max_excursion_beyond_zone": 150,
        "max_return_inside_zone": 30,
        "bars_inside_zone": 10,
        "bars_above_zone": 1,
        "bars_below_zone": 0,
        "first_close_inside_at": f"2026-03-17T00:{(idx + 5) % 60:02d}:00Z",
        "post_delta_pct": 0.1,
        "post_oi_change": 5,
        "post_max_volume_zscore": 1.5,
        "post_max_abs_delta_zscore": 2.5,
        "data_quality": "RAW",
    }
