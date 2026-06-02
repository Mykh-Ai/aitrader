from pathlib import Path

from market_monitor.run_visual_overlay import main

from tests.test_market_monitor_visual_overlay import _write_visual_fixture


def test_visual_overlay_cli_creates_missed_case_chart_and_explanation(tmp_path: Path):
    run_dir, feed_file = _write_visual_fixture(tmp_path, with_liquidations=False)
    output = tmp_path / "missed_visual"

    status = main(
        [
            "--run-dir",
            str(run_dir),
            "--feed-file",
            str(feed_file),
            "--missed-timestamp",
            "2026-03-18T00:02:00Z",
            "--window-hours-before",
            "1",
            "--window-hours-after",
            "1",
            "--output",
            str(output),
        ]
    )

    assert status == 0
    assert (output / "missed_case_20260318_0002.html").exists()
    explanation = output / "missed_case_explanation.md"
    assert explanation.exists()
    text = explanation.read_text(encoding="utf-8")
    assert "timestamp inspected: 2026-03-18T00:02:00Z" in text
    assert "ACTIVE_FORWARD_ZONES_NEAR_PRICE" in text
    assert "CROSSED_HISTORICAL_ZONES_NEAR_PRICE" in text
    assert "CONSUMED_OR_CHOPPED_ZONES_NEAR_PRICE" in text
    assert "BROAD_DISTRIBUTION_REACTION_ZONES_NEAR_PRICE" in text
    assert "nearest above:" in text
    assert "nearest below:" in text
    assert "why no LIQUIDITY_SWEEP_UNRESOLVED was emitted" in text
    assert "repeated_interaction_not_modeled" in text
    assert "Current model does not emit repeated-interaction sweep events from this state" in text
    assert "inactive zone" not in text
    assert "zone_000001" in text
