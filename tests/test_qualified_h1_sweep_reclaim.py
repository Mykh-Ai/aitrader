from __future__ import annotations

from pathlib import Path

import pandas as pd

from market_monitor.qualified_h1_sweep_reclaim import (
    detect_qualified_h1_sweep_reclaims,
    raw_m1_sweep_observation,
)
from market_monitor.wider_research_window import run_wider_research_window


def test_tiny_m1_micro_cross_is_raw_observation_not_qualified_h1_sweep():
    m1 = pd.DataFrame(
        [
            {"timestamp": "2026-05-26T14:01:00Z", "open": 99.9, "high": 100.01, "low": 99.8, "close": 99.9},
        ]
    )
    h1 = pd.DataFrame(
        [
            {"timestamp": "2026-05-26T14:59:00Z", "open": 99.5, "high": 99.9, "low": 98.8, "close": 99.1, "volume": 100, "completed": True},
        ]
    )
    refs = pd.DataFrame([_reference("resistance", level=100.0, confirmed_at="2026-05-26T10:59:00Z")])

    assert raw_m1_sweep_observation(m1_rows=m1, reference_level=100.0, direction="BEARISH") is True

    events = detect_qualified_h1_sweep_reclaims(h1_bars=h1, reference_levels=refs)

    assert events.empty


def test_adjacent_weak_swing_does_not_qualify():
    h1 = _bearish_h1_sequence(
        reference_level=100.0,
        confirmed_at="2026-05-26T12:59:00Z",
        sweep_ts="2026-05-26T14:59:00Z",
        reaction_low=99.8,
        sweep_high=100.2,
        sweep_close=99.7,
    )
    refs = pd.DataFrame([_reference("young", level=100.0, confirmed_at="2026-05-26T12:59:00Z", swing_center_timestamp="2026-05-26T12:59:00Z")])

    events = detect_qualified_h1_sweep_reclaims(h1_bars=h1, reference_levels=refs)

    row = events.iloc[0]
    assert row["raw_sweep"] == "true"
    assert row["qualified_h1_sweep"] == "false"
    assert "level_too_young" in row["qualified_h1_sweep_reject_reason"]


def test_proper_bearish_h1_sweep_qualifies():
    h1 = _bearish_h1_sequence(
        reference_level=100.0,
        confirmed_at="2026-05-26T00:59:00Z",
        sweep_ts="2026-05-26T16:59:00Z",
        reaction_low=95.0,
        sweep_high=101.2,
        sweep_close=99.2,
    )
    refs = pd.DataFrame([_reference("resistance", level=100.0, confirmed_at="2026-05-26T00:59:00Z")])

    events = detect_qualified_h1_sweep_reclaims(h1_bars=h1, reference_levels=refs)

    row = events.iloc[0]
    assert row["qualified_h1_sweep"] == "true"
    assert row["sweep_wick_present"] == "true"
    assert row["penetration_quality"] == "ATR_CONFIRMED"
    assert row["volume_expansion_flag"] == "true"


def test_bearish_failed_reclaim_qualifies_and_entry_timestamp_is_reclaim_close():
    h1 = _bearish_h1_sequence(
        reference_level=100.0,
        confirmed_at="2026-05-26T00:59:00Z",
        sweep_ts="2026-05-26T16:59:00Z",
        reaction_low=95.0,
        sweep_high=101.2,
        sweep_close=99.8,
        reclaim_ts="2026-05-26T17:59:00Z",
        reclaim_close=98.9,
    )
    refs = pd.DataFrame([_reference("resistance", level=100.0, confirmed_at="2026-05-26T00:59:00Z")])

    events = detect_qualified_h1_sweep_reclaims(h1_bars=h1, reference_levels=refs)

    row = events.iloc[0]
    assert row["qualified_h1_sweep"] == "true"
    assert row["qualified_h1_failed_reclaim"] == "true"
    assert row["reclaim_h1_close_ts"] == "2026-05-26T17:59:00Z"
    assert row["entry_candidate_ts"] == "2026-05-26T17:59:00Z"
    assert row["entry_candidate_ts"] != row["sweep_h1_close_ts"]


def test_720m_broad_context_requires_qualified_local_trigger_for_entry(tmp_path: Path):
    paths = _write_wider_fixture(
        tmp_path,
        [
            _setup("broad_context", "2026-06-01T00:03:00Z", qualified=False),
            _setup("qualified", "2026-06-01T00:04:00Z", qualified=True),
        ],
    )

    result = run_wider_research_window(
        setup_timeline_path=paths["setups"],
        feed_dir=paths["feed_dir"],
        selected_zones_path=paths["zones"],
        output_dir=tmp_path / "out",
        start="2026-06-01",
        end="2026-06-01",
    )

    rows = pd.read_csv(result.classification_path).set_index("setup_id")

    assert rows.loc["broad_context", "setup_role_classification"] == "RAW_SWEEP_OBSERVATION"
    assert str(rows.loc["broad_context", "policy_replay_allowed"]).lower() == "false"
    assert rows.loc["broad_context", "classification_reason"] == "raw_sweep_not_qualified"
    assert rows.loc["qualified", "setup_role_classification"] == "MAJOR_SHORT_TRIGGER_AFTER_H1_SWEEP"
    assert str(rows.loc["qualified", "policy_replay_allowed"]).lower() == "true"


def _reference(reference_id: str, *, level: float, confirmed_at: str, swing_center_timestamp: str = "2026-05-25T20:59:00Z") -> dict[str, object]:
    return {
        "reference_id": reference_id,
        "reference_level": level,
        "reference_type": "H1_SWING_HIGH",
        "direction": "BEARISH",
        "confirmed_at": confirmed_at,
        "swing_center_timestamp": swing_center_timestamp,
    }


def _bearish_h1_sequence(
    *,
    reference_level: float,
    confirmed_at: str,
    sweep_ts: str,
    reaction_low: float,
    sweep_high: float,
    sweep_close: float,
    reclaim_ts: str | None = None,
    reclaim_close: float | None = None,
) -> pd.DataFrame:
    confirmed = pd.Timestamp(confirmed_at)
    sweep = pd.Timestamp(sweep_ts)
    rows = []
    ts = confirmed
    while ts < sweep:
        rows.append(
            {
                "timestamp": ts.isoformat().replace("+00:00", "Z"),
                "open": reference_level - 1.0,
                "high": reference_level - 0.2,
                "low": reaction_low,
                "close": reaction_low + 0.4,
                "volume": 100.0,
                "completed": True,
            }
        )
        ts += pd.Timedelta(hours=1)
    rows.append(
        {
            "timestamp": sweep.isoformat().replace("+00:00", "Z"),
            "open": reference_level - 0.2,
            "high": sweep_high,
            "low": reference_level - 0.9,
            "close": sweep_close,
            "volume": 180.0,
            "completed": True,
        }
    )
    if reclaim_ts:
        rows.append(
            {
                "timestamp": reclaim_ts,
                "open": reference_level + 0.1,
                "high": reference_level + 0.3,
                "low": reference_level - 2.0,
                "close": reclaim_close,
                "volume": 140.0,
                "completed": True,
            }
        )
    return pd.DataFrame(rows)


def _write_wider_fixture(tmp_path: Path, setups: list[dict[str, object]]) -> dict[str, Path]:
    feed_dir = tmp_path / "feed"
    feed_dir.mkdir()
    pd.DataFrame(
        [
            {"timestamp": "2026-06-01T00:00:00Z", "open": 100, "high": 101, "low": 99, "close": 100},
            {"timestamp": "2026-06-01T00:01:00Z", "open": 100, "high": 102, "low": 99, "close": 100},
            {"timestamp": "2026-06-01T00:02:00Z", "open": 100, "high": 102, "low": 98, "close": 99},
            {"timestamp": "2026-06-01T00:03:00Z", "open": 99, "high": 104, "low": 98, "close": 100},
            {"timestamp": "2026-06-01T00:04:00Z", "open": 100, "high": 104, "low": 98, "close": 99},
            {"timestamp": "2026-06-01T00:05:00Z", "open": 99, "high": 100, "low": 92, "close": 93},
        ]
    ).to_csv(feed_dir / "2026-06-01.csv", index=False)
    setup_path = tmp_path / "setup_research_timeline.csv"
    pd.DataFrame(setups).to_csv(setup_path, index=False)
    zones = pd.DataFrame(
        [
            {"zone_id": "demand", "side": "SELL_SIDE", "price_lower": 90, "price_upper": 92},
            {"zone_id": "supply", "side": "BUY_SIDE", "price_lower": 105, "price_upper": 107},
        ]
    )
    zones.to_csv(tmp_path / "selected_zones.csv", index=False)
    return {"feed_dir": feed_dir, "setups": setup_path, "zones": tmp_path / "selected_zones.csv"}


def _setup(setup_id: str, formed_at: str, *, qualified: bool) -> dict[str, object]:
    return {
        "setup_id": setup_id,
        "setup_formed_at": formed_at,
        "source_window_start": "2026-06-01T00:00:00Z",
        "source_window_end": formed_at,
        "source_time_precision": "RAW_REGIME_WINDOW_720M",
        "setup_type": "SUPPLY_SWEEP_RECLAIM_DOWN_SETUP",
        "direction_context": "DOWN",
        "trigger_status": "ARMED",
        "market_state": "FAILED_BREAKOUT_SELLER_RECLAIM",
        "dominant_side": "SELLER",
        "setup_reference_level": 101.0,
        "stop_reference": 106.0,
        "target_reference_zone": "demand:SELL_SIDE:90-92",
        "sweep_status": "raw_sweep_observed",
        "raw_sweep": "true",
        "qualified_h1_sweep": str(qualified).lower(),
        "qualified_h1_failed_reclaim": str(qualified).lower(),
        "evidence_summary": "fixture",
    }
