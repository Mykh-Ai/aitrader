from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from market_monitor.run_significant_zone_selector import main
from market_monitor.significant_zone_selector import (
    SELECTED_ZONE_COLUMNS,
    run_significant_zone_selector,
)


FORBIDDEN_RUNTIME_TERMS = [
    "signal",
    "entry",
    "exit",
    "pnl",
    "order",
    "executor",
    "backtester",
    "live_ready",
    "edge_validated",
]


def test_selector_creates_required_outputs_and_caps_visible_zones(tmp_path: Path):
    input_root = _write_selector_input(tmp_path / "daily", _baseline_rows())
    output_dir = tmp_path / "selector"

    result = run_significant_zone_selector(
        input_root=input_root,
        output_dir=output_dir,
        start="2026-03-22",
        end="2026-03-22",
        max_visible_zones=7,
    )

    assert result.selected_zones_path.exists()
    assert result.summary_path.exists()
    assert result.manifest_path.exists()
    selected = pd.read_csv(result.selected_zones_path)
    assert selected.columns.tolist() == SELECTED_ZONE_COLUMNS
    assert len(_visible_rows(selected)) <= 7
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["missing_data_flags"]["liquidations"] == "not_available"
    assert manifest["missing_data_flags"]["vwap"] == "not_available"
    assert manifest["visible_zone_count"] <= 7


def test_selector_keeps_buy_and_sell_side_visible_when_available(tmp_path: Path):
    input_root = _write_selector_input(tmp_path / "daily", _baseline_rows())

    result = run_significant_zone_selector(
        input_root=input_root,
        output_dir=tmp_path / "selector",
        start="2026-03-22",
        end="2026-03-22",
        max_visible_zones=7,
    )

    selected = pd.read_csv(result.selected_zones_path)
    visible = _visible_rows(selected)
    assert "BUY_SIDE" in set(visible["side"])
    assert "SELL_SIDE" in set(visible["side"])


def test_htf_sources_outrank_equivalent_m15_and_session_zones(tmp_path: Path):
    input_root = _write_selector_input(
        tmp_path / "daily",
        [
            _zone("zone_h4", "SELL_SIDE", "H4", has_h4_source=True, confidence_tier="HIGH"),
            _zone("zone_h1", "SELL_SIDE", "H1", has_h1_source=True, confidence_tier="HIGH"),
            _zone("zone_m15", "SELL_SIDE", "M15", confidence_tier="HIGH"),
            _zone("zone_session", "SELL_SIDE", "SESSION", has_session_source=True, confidence_tier="HIGH"),
        ],
    )

    result = run_significant_zone_selector(
        input_root=input_root,
        output_dir=tmp_path / "selector",
        start="2026-03-22",
        end="2026-03-22",
    )

    selected = pd.read_csv(result.selected_zones_path).set_index("zone_id")
    assert selected.loc["zone_h4", "significance_score"] > selected.loc["zone_h1", "significance_score"]
    assert selected.loc["zone_h1", "significance_score"] > selected.loc["zone_m15", "significance_score"]
    assert selected.loc["zone_m15", "significance_score"] > selected.loc["zone_session", "significance_score"]
    assert selected.loc["zone_session", "bucket"] != "MAJOR"


def test_expired_consumed_chopped_and_session_noise_hidden_by_default(tmp_path: Path):
    input_root = _write_selector_input(
        tmp_path / "daily",
        [
            _zone("zone_active_h4", "BUY_SIDE", "H4", has_h4_source=True, confidence_tier="HIGH"),
            _zone("zone_expired", "SELL_SIDE", "H4", status="EXPIRED", has_h4_source=True, confidence_tier="HIGH"),
            _zone("zone_consumed", "SELL_SIDE", "H4", status="CONSUMED", has_h4_source=True, confidence_tier="HIGH"),
            _zone("zone_chopped", "SELL_SIDE", "H4", status="CHOPPED_THROUGH", has_h4_source=True, confidence_tier="HIGH"),
            _zone("zone_session_noise", "SELL_SIDE", "SESSION", has_session_source=True, confidence_tier="LOW"),
        ],
    )

    result = run_significant_zone_selector(
        input_root=input_root,
        output_dir=tmp_path / "selector",
        start="2026-03-22",
        end="2026-03-22",
    )

    selected = pd.read_csv(result.selected_zones_path).set_index("zone_id")
    for zone_id in ["zone_expired", "zone_consumed", "zone_chopped", "zone_session_noise"]:
        assert str(selected.loc[zone_id, "visible_on_snapshot"]).lower() == "false"
        assert selected.loc[zone_id, "reason_hidden"]
    assert selected.loc["zone_session_noise", "bucket"] in {"LOCAL_CONTEXT", "NOISE_HIDE_BY_DEFAULT"}


def test_score_and_penalty_json_and_missing_evidence_are_present(tmp_path: Path):
    input_root = _write_selector_input(tmp_path / "daily", _baseline_rows())

    result = run_significant_zone_selector(
        input_root=input_root,
        output_dir=tmp_path / "selector",
        start="2026-03-22",
        end="2026-03-22",
    )

    selected = pd.read_csv(result.selected_zones_path)
    first = selected.iloc[0]
    assert json.loads(first["score_components_json"])
    assert isinstance(json.loads(first["penalty_components_json"]), dict)
    missing = "|".join(selected["evidence_fields_missing"].fillna("").astype(str))
    assert "liquidations=not_available" in missing
    assert "vwap=not_available" in missing
    assert "liquidation_confirmation" not in selected.to_csv(index=False).lower()


def test_cli_accepts_stable_arguments(tmp_path: Path):
    input_root = _write_selector_input(tmp_path / "daily", _baseline_rows())
    output_dir = tmp_path / "selector"

    status = main(
        [
            "--start",
            "2026-03-22",
            "--end",
            "2026-03-22",
            "--input-root",
            str(input_root),
            "--out-dir",
            str(output_dir),
            "--max-visible-zones",
            "7",
        ]
    )

    assert status == 0
    assert (output_dir / "selected_zones.csv").exists()
    assert (output_dir / "significant_zone_selector_summary.md").exists()
    assert (output_dir / "significant_zone_selector_manifest.json").exists()


def test_selector_outputs_avoid_forbidden_runtime_concepts(tmp_path: Path):
    input_root = _write_selector_input(tmp_path / "daily", _baseline_rows())

    result = run_significant_zone_selector(
        input_root=input_root,
        output_dir=tmp_path / "selector",
        start="2026-03-22",
        end="2026-03-22",
    )

    text = "\n".join(
        [
            result.selected_zones_path.read_text(encoding="utf-8"),
            result.summary_path.read_text(encoding="utf-8"),
            result.manifest_path.read_text(encoding="utf-8"),
        ]
    ).lower()
    for term in FORBIDDEN_RUNTIME_TERMS:
        assert term.lower() not in text


def _baseline_rows() -> list[dict[str, object]]:
    rows = [
        _zone("zone_buy_h4", "BUY_SIDE", "CLUSTER|H1|H4|SESSION", has_h1_source=True, has_h4_source=True),
        _zone("zone_sell_h4", "SELL_SIDE", "CLUSTER|H1|H4|SESSION", has_h1_source=True, has_h4_source=True),
    ]
    for idx in range(10):
        rows.append(
            _zone(
                f"zone_extra_{idx:02d}",
                "BUY_SIDE" if idx % 2 == 0 else "SELL_SIDE",
                "H1" if idx % 3 else "M15",
                has_h1_source=idx % 3 != 0,
                confidence_tier="MEDIUM",
                distance=0.4 + idx * 0.1,
            )
        )
    return rows


def _write_selector_input(root: Path, liquidity_rows: list[dict[str, object]]) -> Path:
    day_dir = root / "2026-03-22"
    day_dir.mkdir(parents=True)
    pd.DataFrame(liquidity_rows).to_csv(day_dir / "liquidity_map.csv", index=False)
    pd.DataFrame(
        [
            {
                "event_id": "event_000001",
                "event_timestamp": "2026-03-22T00:10:00Z",
                "event_type": "LIQUIDITY_SWEEP_UNRESOLVED",
                "zone_id": "zone_buy_h4",
                "side": "BUY_SIDE",
                "excursion_abs": 150,
                "volume_zscore": 2.5,
                "delta_zscore": 2.2,
                "oi_change": 5,
                "reaction_status": "UNCLASSIFIED",
                "evidence_json": "{}",
                "data_quality": "RAW",
            },
            {
                "event_id": "event_000002",
                "event_timestamp": "2026-03-22T00:11:00Z",
                "event_type": "LIQUIDITY_SWEEP_UNRESOLVED",
                "zone_id": "zone_sell_h4",
                "side": "SELL_SIDE",
                "excursion_abs": 120,
                "volume_zscore": 2.1,
                "delta_zscore": 2.4,
                "oi_change": -4,
                "reaction_status": "UNCLASSIFIED",
                "evidence_json": "{}",
                "data_quality": "RAW",
            },
        ]
    ).to_csv(day_dir / "event_log.csv", index=False)
    pd.DataFrame(
        [
            {
                "observation_id": "observation_000001",
                "source_event_id": "event_000001",
                "source_event_timestamp": "2026-03-22T00:10:00Z",
                "zone_id": "zone_buy_h4",
                "side": "BUY_SIDE",
                "zone_type": "CLUSTERED_BUY_SIDE_ZONE",
                "post_max_volume_zscore": 2.2,
                "post_max_abs_delta_zscore": 2.3,
                "post_oi_change": 6,
                "evidence_json": '{"reaction_verdict":"NOT_CLASSIFIED"}',
                "data_quality": "RAW",
            }
        ]
    ).to_csv(day_dir / "post_sweep_observation.csv", index=False)
    pd.DataFrame(
        [
            {
                "timestamp": "2026-03-22T00:00:00Z",
                "total_qty": 100,
                "buy_qty": 60,
                "sell_qty": 40,
                "delta": 20,
                "delta_pct": 0.2,
                "volume_zscore": 0,
                "delta_zscore": 0,
                "oi": 1000,
                "oi_change": 0,
                "funding_rate": 0.0001,
                "data_quality": "RAW",
            }
        ]
    ).to_csv(day_dir / "volume_delta_state.csv", index=False)
    for filename in [
        "structure_levels.csv",
        "liquidity_zone_registry.csv",
        "market_state_timeline.csv",
        "accumulation_zones.csv",
        "pattern_structures.csv",
    ]:
        pd.DataFrame().to_csv(day_dir / filename, index=False)
    return root


def _visible_rows(frame: pd.DataFrame) -> pd.DataFrame:
    return frame[frame["visible_on_snapshot"].astype(str).str.lower() == "true"]


def _zone(
    zone_id: str,
    side: str,
    source_timeframes: str,
    *,
    status: str = "ACTIVE",
    confidence_tier: str = "HIGH",
    has_h1_source: bool = False,
    has_h4_source: bool = False,
    has_session_source: bool = False,
    distance: float = 0.25,
) -> dict[str, object]:
    source_level_count = max(1, len(source_timeframes.split("|")))
    return {
        "zone_id": zone_id,
        "created_at": "2026-03-22T00:00:00Z",
        "last_updated_at": "2026-03-22T00:00:00Z",
        "side": side,
        "zone_type": f"{source_timeframes.split('|')[-1]}_ZONE",
        "price_lower": 99.5,
        "price_upper": 100.5,
        "price_mid": 100.0,
        "source_level_ids": "level_000001",
        "source_timeframes": source_timeframes,
        "source_timeframe_primary": source_timeframes.split("|")[-1],
        "htf_level_type": "",
        "status": status,
        "consumption_status": status,
        "active_forward": status == "ACTIVE",
        "active_forward_role": "PRIMARY" if status == "ACTIVE" else "",
        "m1_interaction_count": 0,
        "touch_count": 3,
        "sweep_count": 0,
        "resweep_count": 0,
        "htf_sweep_count": 0,
        "distance_from_close_pct": distance,
        "confidence_score": 85 if confidence_tier == "HIGH" else 55,
        "confidence_tier": confidence_tier,
        "precision_status": "PRECISE",
        "zone_width_pct": 0.1,
        "cluster_member_count": source_level_count,
        "source_level_count": source_level_count,
        "source_ref_count": source_level_count,
        "has_h1_source": has_h1_source,
        "has_h4_source": has_h4_source,
        "has_session_source": has_session_source,
        "has_equal_level_source": "CLUSTER" in source_timeframes,
        "has_pdh_pdl_source": False,
        "score_components_json": '{"level_types":"H4_SWING_HIGH"}',
        "data_quality": "RAW",
    }
