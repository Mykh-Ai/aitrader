from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

from market_monitor.run_trader_snapshot import main
from market_monitor.trader_snapshot_builder import (
    RENDERED_ZONE_COLUMNS,
    TraderSnapshotBuilderError,
    build_trader_snapshot,
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


def test_builder_requires_selected_zones_csv(tmp_path: Path):
    feed_dir = _write_feed(tmp_path / "feed")
    input_root = _write_input_root(tmp_path / "daily")

    try:
        build_trader_snapshot(
            start="2026-03-22",
            end="2026-03-22",
            selected_zones_path=tmp_path / "missing.csv",
            input_root=input_root,
            feed_dir=feed_dir,
            output_dir=tmp_path / "out",
        )
    except TraderSnapshotBuilderError as exc:
        assert "selected_zones.csv not found" in str(exc)
    else:
        raise AssertionError("expected missing selected_zones.csv failure")


def test_builder_renders_only_visible_selected_zones_and_ignores_registry(tmp_path: Path):
    paths = _build_fixture_snapshot(tmp_path)

    rendered = pd.read_csv(paths["out"] / "rendered_zones.csv")
    assert rendered.columns.tolist() == RENDERED_ZONE_COLUMNS
    assert len(rendered) == 3
    assert set(rendered["zone_id"]) == {"zone_alpha", "zone_beta", "zone_gamma"}
    assert rendered["visible_on_snapshot"].astype(str).str.lower().eq("true").all()

    svg = (paths["out"] / "trader_snapshot.svg").read_text(encoding="utf-8")
    html = (paths["out"] / "trader_snapshot.html").read_text(encoding="utf-8")
    assert "hidden_zone" not in svg
    assert "hidden_zone" not in html
    assert "registry_only_zone" not in svg
    assert "registry_only_zone" not in html


def test_builder_outputs_required_artifacts_and_png(tmp_path: Path):
    paths = _build_fixture_snapshot(tmp_path)
    out = paths["out"]

    for filename in [
        "trader_snapshot.html",
        "trader_snapshot.svg",
        "trader_snapshot.png",
        "trader_snapshot_manifest.json",
        "rendered_zones.csv",
        "snapshot_state.json",
    ]:
        assert (out / filename).exists()
        assert (out / filename).stat().st_size > 0


def test_builder_caps_drawn_zones_at_seven(tmp_path: Path):
    feed_dir = _write_feed(tmp_path / "feed")
    input_root = _write_input_root(tmp_path / "daily")
    selected = [_zone_row(f"visible_{idx}", "BUY_SIDE" if idx % 2 else "SELL_SIDE", idx, True) for idx in range(8)]
    selected_path = _write_selected_zones(tmp_path / "selected_zones.csv", selected)

    try:
        build_trader_snapshot(
            start="2026-03-22",
            end="2026-03-22",
            selected_zones_path=selected_path,
            input_root=input_root,
            feed_dir=feed_dir,
            output_dir=tmp_path / "out",
        )
    except TraderSnapshotBuilderError as exc:
        assert "selected visible zones exceeds 7" in str(exc)
    else:
        raise AssertionError("expected visible zone cap failure")


def test_snapshot_state_contains_required_market_context(tmp_path: Path):
    paths = _build_fixture_snapshot(tmp_path)
    state = json.loads((paths["out"] / "snapshot_state.json").read_text(encoding="utf-8"))

    assert state["current_price"] == 101.0
    assert state["visible_zone_count"] == 3
    assert state["buy_side_visible_count"] == 2
    assert state["sell_side_visible_count"] == 1
    assert state["nearest_buy_side_zone"]["zone_id"] == "zone_alpha"
    assert state["nearest_sell_side_zone"]["zone_id"] == "zone_beta"
    assert state["nearest_above_price_zone"]["zone_id"] == "zone_alpha"
    assert state["nearest_below_price_zone"]["zone_id"] == "zone_beta"
    assert state["zone_in_front_of_price"]["above_price"]["zone_id"] == "zone_alpha"
    assert state["missing_data_flags"] == {
        "compression": "not_available",
        "liquidations": "not_available",
        "vwap": "not_available",
    }
    assert state["forbidden_trade_fields_absent"] is True


def test_cli_accepts_stable_arguments(tmp_path: Path):
    feed_dir = _write_feed(tmp_path / "feed")
    input_root = _write_input_root(tmp_path / "daily")
    selected_path = _write_selected_zones(
        tmp_path / "selected_zones.csv",
        [
            _zone_row("zone_alpha", "BUY_SIDE", 1, True, price_lower=102, price_upper=104, representative=103),
            _zone_row("zone_beta", "SELL_SIDE", 2, True, price_lower=96, price_upper=98, representative=97),
        ],
    )
    out = tmp_path / "out"

    status = main(
        [
            "--start",
            "2026-03-22",
            "--end",
            "2026-03-22",
            "--selected-zones",
            str(selected_path),
            "--input-root",
            str(input_root),
            "--feed-dir",
            str(feed_dir),
            "--out-dir",
            str(out),
        ]
    )

    assert status == 0
    assert (out / "trader_snapshot.html").exists()
    assert (out / "trader_snapshot.svg").exists()
    assert (out / "trader_snapshot.png").exists()


def test_outputs_avoid_forbidden_runtime_concepts(tmp_path: Path):
    paths = _build_fixture_snapshot(tmp_path)
    out = paths["out"]
    text = "\n".join(
        [
            (out / "trader_snapshot.html").read_text(encoding="utf-8"),
            (out / "trader_snapshot.svg").read_text(encoding="utf-8"),
            (out / "snapshot_state.json").read_text(encoding="utf-8"),
            (out / "trader_snapshot_manifest.json").read_text(encoding="utf-8"),
            (out / "rendered_zones.csv").read_text(encoding="utf-8"),
        ]
    ).lower()
    for term in FORBIDDEN_RUNTIME_TERMS:
        assert not re.search(rf"(?<![a-z0-9_]){re.escape(term)}(?![a-z0-9_])", text)
    assert "BUY_SIDE" in (out / "trader_snapshot.html").read_text(encoding="utf-8")
    assert "SELL_SIDE" in (out / "trader_snapshot.html").read_text(encoding="utf-8")
    assert not re.search(r"(?<!_)BUY(?!_SIDE)", text, re.IGNORECASE)
    assert not re.search(r"(?<!_)SELL(?!_SIDE)", text, re.IGNORECASE)


def _build_fixture_snapshot(tmp_path: Path) -> dict[str, Path]:
    feed_dir = _write_feed(tmp_path / "feed")
    input_root = _write_input_root(tmp_path / "daily")
    selected_path = _write_selected_zones(
        tmp_path / "selected_zones.csv",
        [
            _zone_row("zone_alpha", "BUY_SIDE", 1, True, price_lower=102, price_upper=104, representative=103),
            _zone_row("zone_beta", "SELL_SIDE", 2, True, price_lower=96, price_upper=98, representative=97),
            _zone_row("zone_gamma", "BUY_SIDE", 3, True, price_lower=106, price_upper=108, representative=107),
            _zone_row("hidden_zone", "SELL_SIDE", 4, False, price_lower=94, price_upper=95, representative=94.5),
        ],
    )
    out = tmp_path / "out"
    build_trader_snapshot(
        start="2026-03-22",
        end="2026-03-22",
        selected_zones_path=selected_path,
        input_root=input_root,
        feed_dir=feed_dir,
        output_dir=out,
    )
    return {"feed": feed_dir, "input_root": input_root, "selected": selected_path, "out": out}


def _write_feed(feed_dir: Path) -> Path:
    feed_dir.mkdir(parents=True)
    pd.DataFrame(
        [
            {"Timestamp": "2026-03-22 00:00:00", "Open": 100, "High": 101, "Low": 99, "Close": 100},
            {"Timestamp": "2026-03-22 00:01:00", "Open": 100, "High": 102, "Low": 99, "Close": 101},
        ]
    ).to_csv(feed_dir / "2026-03-22.csv", index=False)
    return feed_dir


def _write_input_root(input_root: Path) -> Path:
    day_dir = input_root / "2026-03-22"
    day_dir.mkdir(parents=True)
    pd.DataFrame(
        [{"zone_id": "registry_only_zone", "side": "SELL_SIDE", "price_mid": 99.0}]
    ).to_csv(day_dir / "liquidity_zone_registry.csv", index=False)
    return input_root


def _write_selected_zones(path: Path, rows: list[dict[str, object]]) -> Path:
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def _zone_row(
    zone_id: str,
    side: str,
    rank: int,
    visible: bool,
    *,
    price_lower: float = 100,
    price_upper: float = 102,
    representative: float = 101,
) -> dict[str, object]:
    return {
        "rank": rank,
        "zone_id": zone_id,
        "side": side,
        "bucket": "MAJOR",
        "source_timeframe": "CLUSTER|H1|H4|SESSION",
        "source_family": "H4_MAJOR_STRUCTURE",
        "price_lower": price_lower,
        "price_upper": price_upper,
        "representative_price": representative,
        "current_price": 101.0,
        "distance_to_current_price_pct": representative - 101.0,
        "significance_score": 150 - rank,
        "reason_selected": "H4 structural source; H1 structural source; event evidence count=1",
        "visible_on_snapshot": "true" if visible else "false",
        "evidence_fields_missing": "compression=not_available|liquidations=not_available|vwap=not_available",
        "flow_evidence_summary": "events=1; liquidations=not_available; vwap=not_available",
    }
