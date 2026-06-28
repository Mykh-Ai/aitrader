from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

from market_monitor.hidden_flow_research import _context_read, _episode_read, run_hidden_flow_research
from market_monitor.run_hidden_flow_research import main


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


def test_hidden_flow_research_creates_required_outputs(tmp_path: Path):
    paths = _run_fixture(tmp_path, pattern="positive_upper")
    out = paths["out"]

    for filename in [
        "market_regime_windows.csv",
        "hidden_flow_candidates.csv",
        "hidden_flow_future_labels.csv",
        "hidden_flow_research_summary.md",
        "hidden_flow_manifest.json",
    ]:
        assert (out / filename).exists()
        assert (out / filename).stat().st_size > 0


def test_positive_delta_low_progress_detected_as_pressure_anomaly(tmp_path: Path):
    paths = _run_fixture(tmp_path, pattern="positive_lower")
    windows = pd.read_csv(paths["out"] / "market_regime_windows.csv")
    candidates = pd.read_csv(paths["out"] / "hidden_flow_candidates.csv")

    assert windows["cumulative_delta"].max() > 0
    assert windows["pressure_without_progress_score"].max() >= 45
    assert set(windows["candidate_label"]) & {
        "HIDDEN_ACCUMULATION_UP_CANDIDATE",
        "DOWNTREND_EXHAUSTION_CANDIDATE",
        "COMPRESSION_BEFORE_EXPANSION_CANDIDATE",
    }
    assert not set(candidates["candidate_label"]) & {
        "HIDDEN_ACCUMULATION_UP_CANDIDATE",
        "DOWNTREND_EXHAUSTION_CANDIDATE",
        "BUYER_ABSORPTION_CANDIDATE",
    }


def test_positive_delta_near_upper_zone_is_not_blindly_bullish(tmp_path: Path):
    paths = _run_fixture(tmp_path, pattern="positive_upper")
    candidates = pd.read_csv(paths["out"] / "hidden_flow_candidates.csv")

    assert not candidates.empty
    assert candidates.iloc[0]["candidate_label"] in {
        "SELLER_ABSORPTION_CANDIDATE",
        "HIDDEN_DISTRIBUTION_DOWN_CANDIDATE",
    }
    assert "HIDDEN_ACCUMULATION_UP_CANDIDATE" not in set(candidates.head(5)["candidate_label"])


def test_negative_delta_near_lower_zone_can_be_buyer_absorption(tmp_path: Path):
    paths = _run_fixture(tmp_path, pattern="negative_lower")
    windows = pd.read_csv(paths["out"] / "market_regime_windows.csv")
    candidates = pd.read_csv(paths["out"] / "hidden_flow_candidates.csv")

    assert "BUYER_ABSORPTION_CANDIDATE" in set(windows["candidate_label"])
    assert "BUYER_ABSORPTION_CANDIDATE" not in set(candidates["candidate_label"])


def test_high_compression_without_directional_evidence_stays_neutral(tmp_path: Path):
    paths = _run_fixture(tmp_path, pattern="neutral_compression")
    candidates = pd.read_csv(paths["out"] / "hidden_flow_candidates.csv")

    assert not candidates.empty
    assert candidates.iloc[0]["candidate_label"] == "COMPRESSION_BEFORE_EXPANSION_CANDIDATE"
    assert candidates.iloc[0]["neutral_compression_score"] >= candidates.iloc[0]["accumulation_direction_score"]
    assert candidates.iloc[0]["neutral_compression_score"] >= candidates.iloc[0]["distribution_direction_score"]


def test_future_labels_are_generated_but_not_used_for_candidate_detection(tmp_path: Path):
    up_paths = _run_fixture(tmp_path / "up", pattern="neutral_compression", future_direction="up")
    down_paths = _run_fixture(tmp_path / "down", pattern="neutral_compression", future_direction="down")
    up_candidates = pd.read_csv(up_paths["out"] / "hidden_flow_candidates.csv")
    down_candidates = pd.read_csv(down_paths["out"] / "hidden_flow_candidates.csv")
    up_future = pd.read_csv(up_paths["out"] / "hidden_flow_future_labels.csv")
    down_future = pd.read_csv(down_paths["out"] / "hidden_flow_future_labels.csv")
    up_candidate = _candidate_for_window(up_candidates, "2026-03-22T02:00:00+00:00", "2026-03-22T02:59:00+00:00")
    down_candidate = _candidate_for_window(
        down_candidates, "2026-03-22T02:00:00+00:00", "2026-03-22T02:59:00+00:00"
    )

    assert up_candidate["candidate_label"] == down_candidate["candidate_label"]
    assert up_candidate["directional_classification_reason"] == down_candidate["directional_classification_reason"]
    up_labels = set(up_future.loc[up_future["candidate_id"] == up_candidate["candidate_id"], "impulse_direction_label"])
    down_labels = set(
        down_future.loc[down_future["candidate_id"] == down_candidate["candidate_id"], "impulse_direction_label"]
    )
    assert up_labels != down_labels


def test_directional_sub_scores_and_reason_are_output(tmp_path: Path):
    paths = _run_fixture(tmp_path, pattern="positive_upper")
    candidates = pd.read_csv(paths["out"] / "hidden_flow_candidates.csv")
    required = {
        "prior_trend_direction",
        "range_position",
        "zone_position_context",
        "close_location_in_window",
        "accumulation_direction_score",
        "distribution_direction_score",
        "buyer_absorption_score",
        "seller_absorption_score",
        "neutral_compression_score",
        "directional_classification_reason",
    }

    assert required <= set(candidates.columns)
    reason = str(candidates.iloc[0]["directional_classification_reason"])
    assert len(reason) >= 20
    assert "prior_trend=" in reason
    assert "zone_context=" in reason


def test_episode_context_columns_and_manifest_are_output(tmp_path: Path):
    paths = _run_fixture(tmp_path, pattern="positive_upper")
    candidates = pd.read_csv(paths["out"] / "hidden_flow_candidates.csv")
    manifest = json.loads((paths["out"] / "hidden_flow_manifest.json").read_text(encoding="utf-8"))
    summary = (paths["out"] / "hidden_flow_research_summary.md").read_text(encoding="utf-8")
    required = {
        "context_1d_read",
        "context_1d_price_change_pct",
        "context_1d_range_pct",
        "context_1d_close_position",
        "context_1d_delta_pct",
        "context_1d_open_interest_change",
        "context_1d_minutes_available",
        "context_3d_read",
        "context_7d_read",
        "episode_review_state",
        "episode_read",
        "episode_context_reason",
    }

    assert required <= set(candidates.columns)
    assert set(candidates["episode_read"]) <= {
        "HIDDEN_DISTRIBUTION_STAGE_CONTEXT_ONLY",
        "PULLBACK_ABSORBED_IN_DOWNTREND_COMPRESSION",
        "PULLBACK_ABSORBED_IN_UPTREND_COMPRESSION",
        "RANGE_UPPER_DISTRIBUTION_REJECTION",
        "SELLER_ABSORPTION_STAGE_CONTEXT_ONLY",
        "UNRESOLVED_ABSORPTION_CONTEXT",
        "UNRESOLVED_COMPRESSION_CONTEXT",
        "UNRESOLVED_CONTEXT",
    }
    assert manifest["episode_context_windows_minutes"] == {"1d": 1440, "3d": 4320, "7d": 10080}
    assert manifest["episode_context_uses_future_data"] is False
    assert manifest["episode_linked_compression_confidence_tiers"] == ["HIGH", "MEDIUM"]
    assert manifest["episode_link_lookback_hours"] == 72
    assert "Episode reads" in summary
    visible = candidates[candidates["visible_for_review"].astype(str).str.lower() == "true"]
    assert set(visible["episode_review_state"]) <= {"PROMOTE"}
    assert "HIDDEN_DISTRIBUTION_STAGE_CONTEXT_ONLY" not in set(visible["episode_read"])

def test_context_read_uses_range_close_position_and_pressure_not_only_price_change():
    assert _context_read(price_change_pct=-0.35, range_pct=2.2, close_position=0.08, delta_pct=-18.0) == "DOWN"
    assert _context_read(price_change_pct=0.05, range_pct=1.0, close_position=0.5, delta_pct=1.0) == "RANGE"
    assert _context_read(price_change_pct=0.35, range_pct=2.2, close_position=0.92, delta_pct=18.0) == "UP"

def test_episode_read_classifies_only_linked_distribution_to_compression_chain():
    base = {
        "candidate_label": "COMPRESSION_BEFORE_EXPANSION_CANDIDATE",
        "zone_position_context": "near_upper_zone",
        "nearest_zone_side": "BUY_SIDE",
        "context_1d_read": "DOWN",
        "context_3d_read": "RANGE",
        "episode_chain_type": "DISTRIBUTION_TO_COMPRESSION",
    }

    up_read, _ = _episode_read(pd.Series({**base, "context_7d_read": "UP"}))
    range_read, _ = _episode_read(pd.Series({**base, "context_1d_read": "RANGE", "context_7d_read": "RANGE"}))
    down_read, _ = _episode_read(pd.Series({**base, "context_1d_read": "RANGE", "context_7d_read": "DOWN"}))
    standalone_distribution, _ = _episode_read(
        pd.Series(
            {
                **base,
                "candidate_label": "HIDDEN_DISTRIBUTION_DOWN_CANDIDATE",
                "context_7d_read": "UP",
                "episode_chain_type": "NONE",
            }
        )
    )
    unlinked_compression, _ = _episode_read(pd.Series({**base, "context_7d_read": "UP", "episode_chain_type": "NONE"}))

    assert up_read == "PULLBACK_ABSORBED_IN_UPTREND_COMPRESSION"
    assert range_read == "RANGE_UPPER_DISTRIBUTION_REJECTION"
    assert down_read == "PULLBACK_ABSORBED_IN_DOWNTREND_COMPRESSION"
    assert standalone_distribution == "HIDDEN_DISTRIBUTION_STAGE_CONTEXT_ONLY"
    assert unlinked_compression == "UNRESOLVED_COMPRESSION_CONTEXT"


def test_candidate_count_is_capped_and_prioritized(tmp_path: Path):
    paths = _run_fixture(tmp_path, pattern="positive_lower", minutes=900)
    candidates = pd.read_csv(paths["out"] / "hidden_flow_candidates.csv")

    assert len(candidates) <= 100
    assert int((candidates["visible_for_review"].astype(str).str.lower() == "true").sum()) <= 20
    assert candidates["review_priority_rank"].tolist() == list(range(1, len(candidates) + 1))


def test_candidates_exclude_low_confidence_and_unclear_rows(tmp_path: Path):
    paths = _run_fixture(tmp_path, pattern="positive_lower", minutes=900)
    windows = pd.read_csv(paths["out"] / "market_regime_windows.csv")
    candidates = pd.read_csv(paths["out"] / "hidden_flow_candidates.csv")
    manifest = json.loads((paths["out"] / "hidden_flow_manifest.json").read_text(encoding="utf-8"))

    assert "LOW" in set(windows["confidence"])
    assert "UNCLEAR_FLOW_ANOMALY" in set(windows["candidate_label"])
    assert "LOW" not in set(candidates["confidence"])
    assert "UNCLEAR_FLOW_ANOMALY" not in set(candidates["candidate_label"])
    assert manifest["review_candidate_confidence_tiers"] == ["HIGH"]
    assert manifest["allowed_review_candidate_labels"] == [
        "COMPRESSION_BEFORE_EXPANSION_CANDIDATE",
        "HIDDEN_DISTRIBUTION_DOWN_CANDIDATE",
        "SELLER_ABSORPTION_CANDIDATE",
    ]
    assert manifest["excluded_review_candidate_labels"] == ["UNCLEAR_FLOW_ANOMALY"]
    assert manifest["low_confidence_windows_retained_in_regime_csv"] is True


def test_missing_data_flags_are_marked_not_faked(tmp_path: Path):
    paths = _run_fixture(tmp_path, pattern="neutral_compression")
    candidates = pd.read_csv(paths["out"] / "hidden_flow_candidates.csv")
    manifest = json.loads((paths["out"] / "hidden_flow_manifest.json").read_text(encoding="utf-8"))

    assert manifest["missing_data_flags"]["liquidations"] == "not_available"
    assert "liquidations=not_available" in "|".join(candidates["missing_data_flags"].astype(str))
    assert "vwap=not_available" in "|".join(candidates["missing_data_flags"].astype(str))
    assert "compression=not_available" in "|".join(candidates["missing_data_flags"].astype(str))


def test_outputs_avoid_forbidden_runtime_concepts(tmp_path: Path):
    paths = _run_fixture(tmp_path, pattern="positive_lower")
    out = paths["out"]
    text = "\n".join(
        [
            (out / "market_regime_windows.csv").read_text(encoding="utf-8"),
            (out / "hidden_flow_candidates.csv").read_text(encoding="utf-8"),
            (out / "hidden_flow_future_labels.csv").read_text(encoding="utf-8"),
            (out / "hidden_flow_research_summary.md").read_text(encoding="utf-8"),
            (out / "hidden_flow_manifest.json").read_text(encoding="utf-8"),
        ]
    ).lower()
    for term in FORBIDDEN_RUNTIME_TERMS:
        assert not re.search(rf"(?<![a-z0-9_]){re.escape(term)}(?![a-z0-9_])", text)


def test_cli_accepts_stable_arguments(tmp_path: Path):
    feed_dir = _write_feed(tmp_path / "feed", pattern="positive_lower")
    selected = _write_selected_zones(tmp_path / "selected_zones.csv")
    input_root = _write_input_root(tmp_path / "daily")
    out = tmp_path / "out"

    status = main(
        [
            "--start",
            "2026-03-22",
            "--end",
            "2026-03-22",
            "--feed-dir",
            str(feed_dir),
            "--selected-zones",
            str(selected),
            "--input-root",
            str(input_root),
            "--out-dir",
            str(out),
            "--windows",
            "60",
            "--future-windows",
            "60",
        ]
    )

    assert status == 0
    assert (out / "hidden_flow_candidates.csv").exists()


def _run_fixture(
    tmp_path: Path,
    *,
    pattern: str,
    future_direction: str = "up",
    minutes: int = 240,
) -> dict[str, Path]:
    feed_dir = _write_feed(tmp_path / "feed", pattern=pattern, future_direction=future_direction, minutes=minutes)
    selected = _write_selected_zones(tmp_path / "selected_zones.csv")
    input_root = _write_input_root(tmp_path / "daily")
    out = tmp_path / "out"
    run_hidden_flow_research(
        start="2026-03-22",
        end="2026-03-22",
        feed_dir=feed_dir,
        selected_zones_path=selected,
        input_root=input_root,
        output_dir=out,
        windows=[60],
        future_windows=[60],
    )
    return {"feed": feed_dir, "selected": selected, "input_root": input_root, "out": out}


def _candidate_for_window(candidates: pd.DataFrame, start: str, end: str) -> pd.Series:
    matches = candidates[
        (candidates["start_timestamp"].astype(str) == start) & (candidates["end_timestamp"].astype(str) == end)
    ]
    assert not matches.empty
    return matches.iloc[0]


def _write_feed(
    feed_dir: Path,
    *,
    pattern: str,
    future_direction: str = "up",
    minutes: int = 240,
) -> Path:
    feed_dir.mkdir(parents=True)
    rows = []
    base = pd.Timestamp("2026-03-22T00:00:00Z")
    compression_start = 120 if minutes >= 180 else 0
    future_start = max(compression_start + 60, minutes - 60)
    for idx in range(minutes):
        if pattern == "positive_upper":
            buy_qty, sell_qty = 80.0, 20.0
            price = 103.4 + idx * 0.03 if idx < compression_start else 107.0 + (idx % 8) * 0.01
        elif pattern == "negative_lower":
            buy_qty, sell_qty = 20.0, 80.0
            price = 100.0 - idx * 0.035 if idx < compression_start else 96.0 - (idx % 8) * 0.01
        elif pattern == "neutral_compression":
            buy_qty, sell_qty = 50.0, 50.0
            price = 100.0 + ((idx % 20) - 10) * 0.15 if idx < compression_start else 100.0 + (idx % 4) * 0.005
        else:
            buy_qty, sell_qty = (35.0, 65.0) if idx < compression_start else (85.0, 15.0)
            price = 100.0 - idx * 0.035 if idx < compression_start else 96.0 + (idx % 8) * 0.01
        if idx >= future_start:
            if future_direction == "up":
                price += (idx - future_start) * 0.08
            elif future_direction == "down":
                price -= (idx - future_start) * 0.08
        rows.append(
            {
                "Timestamp": (base + pd.Timedelta(minutes=idx)).strftime("%Y-%m-%d %H:%M:%S"),
                "Open": price - 0.03,
                "High": price + 0.12,
                "Low": price - 0.12,
                "Close": price,
                "Volume": buy_qty + sell_qty,
                "AggTrades": 100,
                "BuyQty": buy_qty,
                "SellQty": sell_qty,
                "VWAP": price,
                "OpenInterest": 1000 + idx * 2,
                "FundingRate": 0.00001,
                "LiqBuyQty": 0,
                "LiqSellQty": 0,
                "IsSynthetic": 0,
            }
        )
    pd.DataFrame(rows).to_csv(feed_dir / "2026-03-22.csv", index=False)
    return feed_dir


def _write_selected_zones(path: Path) -> Path:
    pd.DataFrame(
        [
            {
                "rank": 1,
                "zone_id": "upper_zone",
                "side": "BUY_SIDE",
                "bucket": "MAJOR",
                "price_lower": 106.5,
                "price_upper": 107.5,
                "representative_price": 107.0,
                "visible_on_snapshot": "true",
                "evidence_fields_missing": "compression=not_available|liquidations=not_available|vwap=not_available",
            },
            {
                "rank": 2,
                "zone_id": "lower_zone",
                "side": "SELL_SIDE",
                "bucket": "MAJOR",
                "price_lower": 95.5,
                "price_upper": 96.5,
                "representative_price": 96.0,
                "visible_on_snapshot": "true",
                "evidence_fields_missing": "compression=not_available|liquidations=not_available|vwap=not_available",
            },
        ]
    ).to_csv(path, index=False)
    return path


def _write_input_root(path: Path) -> Path:
    (path / "2026-03-22").mkdir(parents=True)
    pd.DataFrame([{"timestamp": "2026-03-22T00:00:00Z"}]).to_csv(
        path / "2026-03-22" / "market_state_timeline.csv", index=False
    )
    return path
