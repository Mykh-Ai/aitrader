from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

from market_monitor.hidden_flow_research import run_hidden_flow_research
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
    candidates = pd.read_csv(paths["out"] / "hidden_flow_candidates.csv")

    assert not candidates.empty
    top = candidates.iloc[0]
    assert top["cumulative_delta"] > 0
    assert top["pressure_without_progress_score"] >= 45
    assert top["candidate_label"] in {
        "HIDDEN_ACCUMULATION_UP_CANDIDATE",
        "DOWNTREND_EXHAUSTION_CANDIDATE",
        "UNCLEAR_FLOW_ANOMALY",
    }


def test_positive_delta_near_upper_zone_is_not_blindly_bullish(tmp_path: Path):
    paths = _run_fixture(tmp_path, pattern="positive_upper")
    candidates = pd.read_csv(paths["out"] / "hidden_flow_candidates.csv")

    assert not candidates.empty
    assert candidates.iloc[0]["candidate_label"] in {
        "SELLER_ABSORPTION_CANDIDATE",
        "HIDDEN_DISTRIBUTION_DOWN_CANDIDATE",
        "UNCLEAR_FLOW_ANOMALY",
    }
    assert "HIDDEN_ACCUMULATION_UP_CANDIDATE" not in set(candidates.head(5)["candidate_label"])


def test_negative_delta_near_lower_zone_can_be_buyer_absorption(tmp_path: Path):
    paths = _run_fixture(tmp_path, pattern="negative_lower")
    candidates = pd.read_csv(paths["out"] / "hidden_flow_candidates.csv")

    assert "BUYER_ABSORPTION_CANDIDATE" in set(candidates["candidate_label"])


def test_future_labels_are_generated_but_not_used_for_candidate_detection(tmp_path: Path):
    up_paths = _run_fixture(tmp_path / "up", pattern="positive_lower", future_direction="up")
    down_paths = _run_fixture(tmp_path / "down", pattern="positive_lower", future_direction="down")
    up_candidates = pd.read_csv(up_paths["out"] / "hidden_flow_candidates.csv")
    down_candidates = pd.read_csv(down_paths["out"] / "hidden_flow_candidates.csv")
    up_future = pd.read_csv(up_paths["out"] / "hidden_flow_future_labels.csv")
    down_future = pd.read_csv(down_paths["out"] / "hidden_flow_future_labels.csv")

    assert up_candidates.iloc[0]["candidate_label"] == down_candidates.iloc[0]["candidate_label"]
    assert set(up_future["impulse_direction_label"]) != set(down_future["impulse_direction_label"])


def test_candidate_count_is_capped_and_prioritized(tmp_path: Path):
    paths = _run_fixture(tmp_path, pattern="positive_lower", minutes=900)
    candidates = pd.read_csv(paths["out"] / "hidden_flow_candidates.csv")

    assert len(candidates) <= 100
    assert int((candidates["visible_for_review"].astype(str).str.lower() == "true").sum()) <= 20
    assert candidates["review_priority_rank"].tolist() == list(range(1, len(candidates) + 1))


def test_missing_data_flags_are_marked_not_faked(tmp_path: Path):
    paths = _run_fixture(tmp_path, pattern="positive_lower")
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
    price = 100.0
    for idx in range(minutes):
        if pattern == "positive_upper":
            buy_qty, sell_qty = 80.0, 20.0
            price = 107.0 + (idx % 8) * 0.01
        elif pattern == "negative_lower":
            buy_qty, sell_qty = 20.0, 80.0
            price = 96.0 - (idx % 8) * 0.01
        else:
            buy_qty, sell_qty = 85.0, 15.0
            price = 96.0 + (idx % 8) * 0.01
        if idx >= minutes - 60:
            if future_direction == "up":
                price += (idx - (minutes - 60)) * 0.08
            elif future_direction == "down":
                price -= (idx - (minutes - 60)) * 0.08
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
