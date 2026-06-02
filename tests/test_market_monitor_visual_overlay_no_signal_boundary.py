from pathlib import Path

import pandas as pd

from market_monitor.run_visual_overlay import main

from tests.test_market_monitor_visual_overlay import _write_visual_fixture


def test_visual_overlay_outputs_do_not_create_trade_decision_fields(tmp_path: Path):
    run_dir, feed_file = _write_visual_fixture(tmp_path, with_liquidations=False)
    output = tmp_path / "visual"

    assert main(["--run-dir", str(run_dir), "--feed-file", str(feed_file), "--output", str(output)]) == 0

    manifest = pd.read_csv(output / "visual_audit_manifest.csv")
    forbidden = {"signal", "order", "entry", "exit", "pnl", "position_size", "stop_loss", "take_profit"}
    for column in manifest.columns:
        assert column.lower() not in forbidden

    chart_text = (output / "liquidity_overlay_2026-03-18.html").read_text(encoding="utf-8").lower()
    assert "position_size" not in chart_text
    assert "stop_loss" not in chart_text
    assert "take_profit" not in chart_text
    assert "pnl" not in chart_text
