from pathlib import Path

import pandas as pd

from market_monitor.run_visual_overlay import main


def test_visual_overlay_cli_creates_full_day_chart(tmp_path: Path):
    run_dir, feed_file = _write_visual_fixture(tmp_path, with_liquidations=False)
    output = tmp_path / "visual"

    status = main(
        [
            "--run-dir",
            str(run_dir),
            "--feed-file",
            str(feed_file),
            "--output",
            str(output),
            "--format",
            "html",
        ]
    )

    assert status == 0
    chart = output / "liquidity_overlay_2026-03-18.html"
    assert chart.exists()
    assert (output / "visual_audit_manifest.csv").exists()
    text = chart.read_text(encoding="utf-8")
    assert "zone_000001" in text
    assert "100.0" in text
    assert "102.0" in text
    assert "move_20260318_000100_BUY_SIDE_000001" in text
    assert "SWEEP_ACCEPTED" in text
    assert "Volume TotalQty" in text
    assert "Delta BuyQty - SellQty" in text
    assert "Open Interest" in text
    assert "Liquidation fields unavailable for this feed/day." in text
    assert "consumption_status" in text
    assert "DOUBLE_TOP" in text
    assert "structural_zone_mode" in text
    assert "outer=100.0-102.0" in text
    assert "core=100.5-101.5" in text


def test_visual_overlay_cli_creates_market_move_chart(tmp_path: Path):
    run_dir, feed_file = _write_visual_fixture(tmp_path, with_liquidations=True)
    output = tmp_path / "move_visual"

    status = main(
        [
            "--run-dir",
            str(run_dir),
            "--feed-file",
            str(feed_file),
            "--market-move-id",
            "move_20260318_000100_BUY_SIDE_000001",
            "--window-hours-before",
            "1",
            "--window-hours-after",
            "1",
            "--output",
            str(output),
        ]
    )

    assert status == 0
    chart = output / "market_move_move_20260318_000100_BUY_SIDE_000001.html"
    assert chart.exists()
    text = chart.read_text(encoding="utf-8")
    assert "what_was_swept" in text
    assert "BUY_SIDE sweep of zone_000001" in text
    assert "consumption_status=SWEPT_ONCE" in text
    assert "HTF structural liquidity level" in text
    assert "active_forward_role=RETEST_ZONE" in text
    assert "why_label" in text
    assert "Liquidations LiqBuyQty + LiqSellQty" in text


def test_weak_local_session_only_case_shows_badge(tmp_path: Path):
    run_dir, feed_file = _write_visual_fixture(tmp_path, with_liquidations=False)
    registry = pd.read_csv(run_dir / "liquidity_zone_registry.csv")
    registry.loc[0, "source_timeframes"] = "SESSION"
    registry.loc[0, "source_timeframe_primary"] = "SESSION"
    registry.loc[0, "htf_level_type"] = ""
    registry.loc[0, "htf_origin_timestamp"] = ""
    registry.loc[0, "htf_origin_price"] = pd.NA
    registry.loc[0, "htf_confirmation_timestamp"] = ""
    registry.loc[0, "htf_lifecycle_status"] = "LOCAL_ONLY"
    registry.loc[0, "htf_sweep_count"] = 0
    registry.loc[0, "htf_close_through_count"] = 0
    registry.loc[0, "htf_acceptance_count"] = 0
    registry.loc[0, "sweep_importance_class"] = "LOCAL_SESSION_SWEEP"
    registry.loc[0, "confidence_tier"] = "LOW"
    registry.to_csv(run_dir / "liquidity_zone_registry.csv", index=False)
    output = tmp_path / "weak_local_visual"

    status = main(
        [
            "--run-dir",
            str(run_dir),
            "--feed-file",
            str(feed_file),
            "--market-move-id",
            "move_20260318_000100_BUY_SIDE_000001",
            "--output",
            str(output),
        ]
    )

    assert status == 0
    text = (output / "market_move_move_20260318_000100_BUY_SIDE_000001.html").read_text(encoding="utf-8")
    assert "LOW_CONFIDENCE_LOCAL_SWEEP" in text
    assert "SESSION-only source" in text


def _write_visual_fixture(tmp_path: Path, *, with_liquidations: bool) -> tuple[Path, Path]:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    feed_file = tmp_path / "feed.csv"
    header = (
        "Timestamp,Open,High,Low,Close,Volume,AggTrades,BuyQty,SellQty,VWAP,"
        "OpenInterest,FundingRate"
    )
    rows = [
        "2026-03-18T00:00:00Z,99,100.5,98.5,99.5,10,5,6,4,99.5,1000,0.0001",
        "2026-03-18T00:01:00Z,99.5,103.5,99,103,50,10,35,15,102,1012,0.0001",
        "2026-03-18T00:02:00Z,103,103.2,101.5,101.8,20,8,9,11,102,1010,0.0001",
    ]
    if with_liquidations:
        header += ",LiqBuyQty,LiqSellQty"
        rows = [row + ",0.1,0.2" for row in rows]
    feed_file.write_text("\n".join([header, *rows]), encoding="utf-8")

    (run_dir / "market_summary.md").write_text("# summary\n", encoding="utf-8")
    pd.DataFrame(
        [
            {
                "level_id": "level_000001",
                "timestamp": "2026-03-18T00:00:00Z",
                "source_timeframe": "H1",
                "level_type": "H1_SWING_HIGH",
                "price": 101.0,
                "confidence_tier": "HIGH",
                "status": "ACTIVE",
            }
        ]
    ).to_csv(run_dir / "structure_levels.csv", index=False)
    pd.DataFrame([_zone_row()]).to_csv(run_dir / "liquidity_map.csv", index=False)
    pd.DataFrame([_zone_row()]).to_csv(run_dir / "liquidity_zone_registry.csv", index=False)
    pd.DataFrame([_pattern_row()]).to_csv(run_dir / "pattern_structures.csv", index=False)
    pd.DataFrame([_event_row()]).to_csv(run_dir / "event_log.csv", index=False)
    pd.DataFrame([_move_row()]).to_csv(run_dir / "market_move_groups.csv", index=False)
    pd.DataFrame([_observation_row()]).to_csv(run_dir / "post_sweep_observation.csv", index=False)
    pd.DataFrame([_label_row()]).to_csv(run_dir / "sweep_label_taxonomy.csv", index=False)
    pd.DataFrame(
        [
            {
                "timestamp": "2026-03-18T00:01:00Z",
                "total_qty": 50,
                "buy_qty": 35,
                "sell_qty": 15,
                "delta": 20,
                "delta_pct": 0.4,
                "volume_zscore": 2.2,
                "delta_zscore": 2.0,
                "oi": 1012,
                "oi_change": 12,
                "funding_rate": 0.0001,
                "data_quality": "RAW",
            }
        ]
    ).to_csv(run_dir / "volume_delta_state.csv", index=False)
    return run_dir, feed_file


def _zone_row() -> dict[str, object]:
    return {
        "zone_id": "zone_000001",
        "first_seen_at": "2026-03-18T00:00:00Z",
        "last_seen_at": "2026-03-18T00:02:00Z",
        "last_updated_at": "2026-03-18T00:02:00Z",
        "side": "BUY_SIDE",
        "zone_type": "H1_SWING_HIGH_ZONE",
        "price_lower": 100.0,
        "price_upper": 102.0,
        "price_mid": 101.0,
        "source_level_ids": "level_000001",
        "source_timeframes": "H1",
        "source_timeframe_primary": "H1",
        "htf_level_type": "H1_SWING_HIGH",
        "htf_origin_timestamp": "2026-03-18T00:00:00Z",
        "htf_origin_price": 101.0,
        "htf_confirmation_timestamp": "2026-03-18T00:00:00Z",
        "status": "CROSSED_UNCLASSIFIED",
        "consumption_status": "SWEPT_ONCE",
        "active_forward": "false",
        "cross_through_count": 0,
        "close_above_count": 1,
        "close_below_count": 0,
        "alternating_close_count": 0,
        "bars_inside_zone_lifetime": 0,
        "last_clean_reaction_at": "",
        "consumed_at": "",
        "consumption_reason": "",
        "zone_outer_lower": 100.0,
        "zone_outer_upper": 102.0,
        "zone_core_lower": 100.5,
        "zone_core_upper": 101.5,
        "zone_origin_start": "2026-03-18T00:00:00Z",
        "zone_origin_end": "2026-03-18T00:00:00Z",
        "first_sweep_at": "2026-03-18T00:01:00Z",
        "resweep_count": 0,
        "failed_acceptance_count": 0,
        "rejection_without_sweep_count": 0,
        "drift_away_confirmed_at": "",
        "accepted_above_at": "",
        "accepted_below_at": "",
        "structural_zone_mode": "PATTERN_DERIVED_ZONE",
        "zone_behavior_state": "RETEST_OF_SWEPT_ZONE",
        "active_forward_role": "RETEST_ZONE",
        "htf_lifecycle_status": "HTF_SWEPT",
        "m1_interaction_count": 1,
        "htf_sweep_count": 1,
        "htf_close_through_count": 0,
        "htf_acceptance_count": 0,
        "history_context_start": "2026-03-18T00:00:00Z",
        "history_context_incomplete": "false",
        "sweep_importance_class": "HTF_STRUCTURAL_SWEEP",
        "confidence_score": 80,
        "confidence_tier": "HIGH",
        "age_bars": 3,
        "age_days": 0,
        "touch_count": 1,
        "cross_count": 1,
        "active_days": 1,
        "last_touch_at": "2026-03-18T00:01:00Z",
        "last_cross_at": "2026-03-18T00:01:00Z",
        "merged_into_zone_id": "",
        "data_quality": "RAW",
        "invalidation_reason": "",
        "score_components_json": "{}",
        "source_level_count": 1,
        "source_ref_count": 1,
        "cluster_member_count": 1,
        "zone_width": 2.0,
        "zone_width_pct": 1.98,
        "precision_status": "PRECISE",
        "has_h1_source": True,
        "has_h4_source": False,
        "has_session_source": False,
        "has_equal_level_source": False,
        "has_pdh_pdl_source": False,
    }


def _pattern_row() -> dict[str, object]:
    return {
        "pattern_id": "pattern_000001",
        "created_at": "2026-03-18T00:00:00Z",
        "pattern_type": "DOUBLE_TOP",
        "pattern_role": "BUY_SIDE_LIQUIDITY",
        "side": "BUY_SIDE",
        "status": "SWEPT",
        "confidence_tier": "HIGH",
        "price_lower": 100.0,
        "price_upper": 102.0,
        "price_mid": 101.0,
        "neckline_price": "",
        "left_point_timestamp": "2026-03-18T00:00:00Z",
        "left_point_price": 101.0,
        "head_point_timestamp": "",
        "head_point_price": "",
        "right_point_timestamp": "2026-03-18T00:00:00Z",
        "right_point_price": 101.0,
        "source_timeframe": "H1",
        "source_level_ids": "level_000001",
        "pattern_source_points_json": "{}",
        "linked_zone_id": "zone_000001",
        "invalidated_at": "",
        "invalidation_reason": "",
        "data_quality": "RAW",
    }


def _event_row() -> dict[str, object]:
    return {
        "event_id": "event_000001",
        "event_timestamp": "2026-03-18T00:01:00Z",
        "event_type": "LIQUIDITY_SWEEP_UNRESOLVED",
        "zone_id": "zone_000001",
        "side": "BUY_SIDE",
        "price_before": 99.5,
        "event_high": 103.5,
        "event_low": 99.0,
        "event_close": 103.0,
        "excursion_abs": 1.5,
        "excursion_atr": 0,
        "volume_zscore": 2.2,
        "delta_zscore": 2.0,
        "oi_change": 12.0,
        "reaction_status": "UNRESOLVED",
        "market_move_id": "move_20260318_000100_BUY_SIDE_000001",
        "market_move_role": "PRIMARY",
        "market_move_event_count": 1,
        "group_start_timestamp": "2026-03-18T00:01:00Z",
        "group_end_timestamp": "2026-03-18T00:01:00Z",
        "group_span_minutes": 0.0,
        "grouping_window_mode": "ANCHORED_FIXED_WINDOW",
        "evidence_json": "{}",
        "data_quality": "RAW",
    }


def _move_row() -> dict[str, object]:
    return {
        "market_move_id": "move_20260318_000100_BUY_SIDE_000001",
        "group_start_timestamp": "2026-03-18T00:01:00Z",
        "group_end_timestamp": "2026-03-18T00:01:00Z",
        "group_span_minutes": 0.0,
        "grouping_window_minutes": 2,
        "grouping_window_mode": "ANCHORED_FIXED_WINDOW",
        "event_timestamp": "2026-03-18T00:01:00Z",
        "side": "BUY_SIDE",
        "primary_event_id": "event_000001",
        "primary_zone_id": "zone_000001",
        "primary_selection_reason": "highest_confidence_score",
        "primary_selection_components_json": "{}",
        "event_count": 1,
        "zone_ids": "zone_000001",
        "event_ids": "event_000001",
        "min_zone_price_lower": 100.0,
        "max_zone_price_upper": 102.0,
        "representative_zone_price_mid": 101.0,
        "max_excursion_abs": 1.5,
        "max_volume_zscore": 2.2,
        "max_abs_delta_zscore": 2.0,
        "total_oi_change": 12.0,
        "precision_statuses": "PRECISE",
        "confidence_tiers": "HIGH",
        "data_quality": "RAW",
        "evidence_json": "{}",
    }


def _observation_row() -> dict[str, object]:
    return {
        "market_move_id": "move_20260318_000100_BUY_SIDE_000001",
        "market_move_role": "PRIMARY",
        "source_event_id": "event_000001",
        "observation_id": "observation_000001",
        "source_event_timestamp": "2026-03-18T00:01:00Z",
        "zone_id": "zone_000001",
        "side": "BUY_SIDE",
        "zone_price_lower": 100.0,
        "zone_price_upper": 102.0,
        "zone_price_mid": 101.0,
        "zone_width": 2.0,
        "zone_width_pct": 1.98,
        "precision_status": "PRECISE",
        "confidence_score": 80,
        "confidence_tier": "HIGH",
        "data_quality": "RAW",
    }


def _label_row() -> dict[str, object]:
    return {
        "taxonomy_version": "SWEEP_LABEL_TAXONOMY_V1",
        "market_move_id": "move_20260318_000100_BUY_SIDE_000001",
        "label": "SWEEP_ACCEPTED",
        "label_reason": "maintained_close_beyond_swept_side",
        "label_evidence_json": "{}",
        "primary_event_id": "event_000001",
        "primary_observation_id": "observation_000001",
        "primary_zone_id": "zone_000001",
        "side": "BUY_SIDE",
        "source_event_timestamp": "2026-03-18T00:01:00Z",
        "group_start_timestamp": "2026-03-18T00:01:00Z",
        "group_end_timestamp": "2026-03-18T00:01:00Z",
        "group_span_minutes": 0.0,
        "market_move_event_count": 1,
        "precision_status": "PRECISE",
        "group_precision_statuses": "PRECISE",
        "confidence_score": 80,
        "confidence_tier": "HIGH",
        "zone_price_lower": 100.0,
        "zone_price_upper": 102.0,
        "zone_price_mid": 101.0,
        "zone_width": 2.0,
        "zone_width_pct": 1.98,
        "observation_complete": True,
        "observation_bars_expected": 30,
        "observation_bars_available": 30,
        "first_return_inside_at": "",
        "first_close_inside_at": "",
        "bars_inside_zone": 0,
        "bars_above_zone": 30,
        "bars_below_zone": 0,
        "max_return_inside_zone": 0.0,
        "max_excursion_beyond_zone": 1.5,
        "close_at_window_end": 104.0,
        "data_quality": "RAW",
    }
