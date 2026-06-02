import json
from pathlib import Path

import pandas as pd

from market_monitor.events import build_event_log
from market_monitor.summary import write_market_summary


REQUIRED_EVIDENCE_FIELDS = {
    "activity_evidence",
    "activity_passed",
    "candidate_evidence_status",
    "active_forward",
    "active_forward_role",
    "accepted_above_at",
    "accepted_below_at",
    "confidence_score",
    "confidence_tier",
    "consumed_at",
    "consumption_status",
    "data_quality",
    "delta_zscore",
    "event_class",
    "event_close",
    "event_high",
    "event_low",
    "event_timestamp",
    "excursion_abs",
    "excursion_passed",
    "first_seen_at",
    "failed_acceptance_count",
    "first_sweep_at",
    "min_excursion_abs",
    "oi_change",
    "pre_existing_zone",
    "price_lower",
    "price_mid",
    "price_upper",
    "reaction_status",
    "resweep_count",
    "side",
    "source_timeframes",
    "structural_zone_mode",
    "volume_zscore",
    "zone_behavior_state",
    "zone_id",
    "zone_core_lower",
    "zone_core_upper",
    "zone_outer_lower",
    "zone_outer_upper",
    "zone_type",
}


def test_unresolved_sweep_evidence_json_is_complete_and_deterministic():
    first = _event_log()
    second = _event_log()

    assert first.equals(second)
    unresolved = first[first["event_type"] == "LIQUIDITY_SWEEP_UNRESOLVED"].iloc[0]
    evidence = json.loads(unresolved["evidence_json"])

    assert set(evidence) == REQUIRED_EVIDENCE_FIELDS
    assert list(evidence.keys()) == sorted(evidence.keys())
    assert evidence["event_class"] == "LIQUIDITY_SWEEP_UNRESOLVED"
    assert evidence["pre_existing_zone"] is True
    assert evidence["excursion_abs"] == 15
    assert evidence["min_excursion_abs"] == 10
    assert evidence["excursion_passed"] is True
    assert evidence["activity_evidence"] == ["volume_zscore", "delta_zscore", "oi_change"]
    assert evidence["activity_passed"] is True
    assert evidence["candidate_evidence_status"] == "SUFFICIENT_UNRESOLVED"
    assert evidence["reaction_status"] == "UNRESOLVED"


def test_market_summary_includes_unresolved_sweep_stats(tmp_path: Path):
    event_log = _event_log()
    summary_path = tmp_path / "market_summary.md"

    write_market_summary(
        summary_path,
        feed=_feed(),
        liquidity_map=pd.DataFrame(),
        structure_levels=pd.DataFrame(),
        event_log=event_log,
        run_timestamp="2026-05-31T00:00:00Z",
        input_files=["synthetic.csv"],
        output_dir=tmp_path,
        event_stats={
            "total": 1,
            "by_type": (
                "LIQUIDITY_SWEEP_UNRESOLVED=1, "
                "LIQUIDITY_ZONE_CROSSED_UNCLASSIFIED=1"
            ),
            "approached": 0,
            "touched": 0,
            "crossed_unclassified": 1,
            "merged": 0,
            "expired": 0,
            "unresolved_sweep": 1,
            "unresolved_sweep_by_side": "BUY_SIDE=1, SELL_SIDE=0",
            "unresolved_sweep_by_data_quality": "RAW=1, RECOVERED_DEGRADED=0",
            "crossed_without_sweep_evidence": 0,
        },
    )

    summary = summary_path.read_text(encoding="utf-8")
    assert "- Unresolved liquidity sweep candidates: 1" in summary
    assert "- Unresolved sweep candidates by side: BUY_SIDE=1, SELL_SIDE=0" in summary
    assert (
        "- Unresolved sweep candidates by data quality: RAW=1, RECOVERED_DEGRADED=0"
        in summary
    )
    assert "- Crossed zones without sufficient sweep evidence: 0" in summary


def _event_log():
    feed = _feed()
    return build_event_log(
        registry=pd.DataFrame([_registry_row()]),
        feed=feed,
        volume_delta_state=pd.DataFrame(
            {
                "timestamp": ["2026-05-08T00:00:00Z", "2026-05-08T00:01:00Z"],
                "volume_zscore": [0.0, 2.0],
                "delta_zscore": [0.0, -2.0],
                "oi_change": [0.0, 5.0],
            }
        ),
    )


def _registry_row():
    return {
        "zone_id": "zone_000001",
        "first_seen_at": "2026-05-08T00:00:00Z",
        "last_seen_at": "2026-05-08T00:01:00Z",
        "last_updated_at": "2026-05-08T00:01:00Z",
        "side": "BUY_SIDE",
        "zone_type": "H1_SWING_HIGH_ZONE",
        "price_lower": 100,
        "price_upper": 110,
        "price_mid": 105,
        "source_level_ids": "level_000001",
        "source_timeframes": "H1",
        "status": "ACTIVE",
        "confidence_score": 65,
        "confidence_tier": "MEDIUM",
        "age_bars": 2,
        "age_days": 0,
        "touch_count": 0,
        "cross_count": 0,
        "active_days": 1,
        "last_touch_at": "",
        "last_cross_at": "",
        "merged_into_zone_id": "",
        "data_quality": "RAW",
        "invalidation_reason": "",
    }


def _feed():
    return pd.DataFrame(
        [
            _row("2026-05-08T00:00:00Z", high=95, low=90, close=92),
            _row("2026-05-08T00:01:00Z", high=125, low=90, close=120),
        ]
    )


def _row(ts, *, high, low, close):
    return {
        "Timestamp": pd.Timestamp(ts),
        "OpenPrice": close,
        "HiPrice": high,
        "LowPrice": low,
        "ClosePrice": close,
        "TotalQty": 10,
        "Trades": 1,
        "BuyQty": 5,
        "SellQty": 5,
        "OpenInterest": 1000,
        "FundingRate": 0.0001,
        "DataQuality": "RAW",
        "SourceFile": "synthetic.csv",
    }
