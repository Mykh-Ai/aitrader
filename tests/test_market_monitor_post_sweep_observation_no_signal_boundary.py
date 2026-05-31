import json
from pathlib import Path

import pandas as pd

from market_monitor.post_sweep_observation import build_post_sweep_observations
from market_monitor.summary import write_market_summary


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
}
FORBIDDEN_EVIDENCE_TERMS = {
    "signal",
    "entry",
    "exit",
    "order",
    "position",
    "leverage",
    "stop_loss",
    "take_profit",
    "risk",
    "pnl",
    "win",
    "loss",
    "rejected",
    "accepted",
    "failed_breakout",
    "accepted_breakout",
    "long",
    "short",
}


def test_post_sweep_observation_has_no_signal_order_position_or_result_fields():
    observation = build_post_sweep_observations(
        event_log=pd.DataFrame([_event_row()]),
        feed=_feed(),
        volume_delta_state=_volume_delta(),
    )

    assert {column.lower() for column in observation.columns}.isdisjoint(FORBIDDEN_COLUMNS)
    evidence_text = json.dumps(
        json.loads(observation.iloc[0]["evidence_json"]), sort_keys=True
    ).lower()
    assert all(term not in evidence_text for term in FORBIDDEN_EVIDENCE_TERMS)
    assert json.loads(observation.iloc[0]["evidence_json"])["reaction_verdict"] == "NOT_CLASSIFIED"


def test_market_summary_includes_post_sweep_observation_stats(tmp_path: Path):
    summary_path = tmp_path / "market_summary.md"

    write_market_summary(
        summary_path,
        feed=_feed(),
        liquidity_map=pd.DataFrame(),
        structure_levels=pd.DataFrame(),
        event_log=pd.DataFrame([_event_row()]),
        run_timestamp="2026-05-31T00:00:00Z",
        input_files=["synthetic.csv"],
        output_dir=tmp_path,
        observation_stats={
            "total": 2,
            "complete": 1,
            "incomplete": 1,
            "window_bars": 30,
        },
    )

    summary = summary_path.read_text(encoding="utf-8")
    assert "- Post-sweep observations: 2" in summary
    assert "- Complete post-sweep observations: 1" in summary
    assert "- Incomplete post-sweep observations: 1" in summary
    assert "- Observation window bars: 30" in summary


def _event_row():
    return {
        "event_id": "event_000003",
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
        "evidence_json": (
            '{"data_quality":"RAW","event_class":"LIQUIDITY_SWEEP_UNRESOLVED",'
            '"price_lower":100,"price_mid":105,"price_upper":110,'
            '"side":"BUY_SIDE","zone_id":"zone_000001","zone_type":"H1_LEVEL_HIGH_ZONE"}'
        ),
        "data_quality": "RAW",
    }


def _feed():
    rows = [
        _feed_row("2026-05-08T00:01:00Z", 125, 90, 120),
        _feed_row("2026-05-08T00:02:00Z", 130, 120, 125),
    ]
    return pd.DataFrame(rows)


def _feed_row(ts, high, low, close):
    return {
        "Timestamp": pd.Timestamp(ts),
        "OpenPrice": close,
        "HiPrice": high,
        "LowPrice": low,
        "ClosePrice": close,
        "TotalQty": 10,
        "Trades": 1,
        "BuyQty": 6,
        "SellQty": 4,
        "OpenInterest": 1000,
        "FundingRate": 0.0001,
        "DataQuality": "RAW",
        "SourceFile": "synthetic.csv",
    }


def _volume_delta():
    return pd.DataFrame(
        {
            "timestamp": ["2026-05-08T00:01:00Z", "2026-05-08T00:02:00Z"],
            "volume_zscore": [0.0, 2.0],
            "delta_zscore": [0.0, 2.0],
            "oi_change": [0.0, 0.0],
        }
    )
