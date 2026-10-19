from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd
import pytest

from market_monitor.batch_runner import BatchResearchError, run_batch_research
from market_monitor.feed_adapter import deduplicate_feed, load_feed
from market_monitor.feed_quality import build_window_quality, causal_slice
from market_monitor.feed_source import (
    RequiredRecoveredFeedMissing,
    resolve_daily_feed_source,
)
from market_monitor.outputs import write_outputs
from market_monitor.zone_registry import build_zone_registry, write_registry


def test_feed_resolver_selects_base_recovered_and_fails_without_required_recovery(tmp_path: Path):
    feed_dir = tmp_path / "feed"
    recovered_dir = tmp_path / "feed_recovered"
    normal = _write_minutes(feed_dir / "2026-06-01.csv", "2026-06-01T00:00:00Z", 2)
    contaminated = _write_minutes(feed_dir / "2026-04-24.csv", "2026-04-24T00:00:00Z", 2)
    recovered = _write_minutes(recovered_dir / "2026-04-24.csv", "2026-04-24T00:00:00Z", 2)
    before = {path: _sha256(path) for path in [normal, contaminated, recovered]}

    normal_source = resolve_daily_feed_source(feed_dir, pd.Timestamp("2026-06-01").date())
    recovered_source = resolve_daily_feed_source(feed_dir, pd.Timestamp("2026-04-24").date())

    assert normal_source.path == normal
    assert normal_source.source_class == "RAW"
    assert recovered_source.path == recovered
    assert recovered_source.source_class == "RECOVERED_DEGRADED"
    assert recovered_source.selection_reason == "KNOWN_OUTAGE_RECOVERED_PRECEDENCE"
    assert {path: _sha256(path) for path in before} == before

    recovered.unlink()
    with pytest.raises(RequiredRecoveredFeedMissing):
        resolve_daily_feed_source(feed_dir, pd.Timestamp("2026-04-24").date())


def test_row_quality_is_not_broadcast_and_duplicates_survive_until_diagnostics(tmp_path: Path):
    path = tmp_path / "feed.csv"
    frame = _minute_frame("2026-06-01T00:00:00Z", 5)
    frame["IsSynthetic"] = [0, 0, 1, 0, 0]
    frame = pd.concat([frame, frame.iloc[[3]]], ignore_index=True)
    _to_historical(frame).to_csv(path, index=False)

    loaded = load_feed(path, deduplicate=False)
    quality = build_window_quality(loaded, "2026-06-01T00:04:00Z", windows=[5])

    assert loaded["DataQuality"].tolist().count("SYNTHETIC") == 1
    assert loaded["DataQuality"].tolist().count("RAW") == 5
    assert len(loaded) == 6
    assert quality.loc[0, "duplicate_rows"] == 1
    assert quality.loc[0, "completion_status"] == "PARTIAL"
    assert len(deduplicate_feed(loaded)) == 5


def test_missing_minute_and_exact_cross_midnight_windows_are_reported():
    complete = _minute_frame("2026-06-30T20:31:00Z", 241)
    complete = complete.iloc[:-1].copy()
    quality = build_window_quality(complete, "2026-07-01T00:30:00Z", windows=[60, 240])

    assert quality["rows_used"].tolist() == [60, 240]
    assert quality["completion_status"].tolist() == ["COMPLETE_RAW", "COMPLETE_RAW"]

    missing = complete.loc[complete["Timestamp"] != pd.Timestamp("2026-07-01T00:00:00Z")]
    missing_quality = build_window_quality(missing, "2026-07-01T00:30:00Z", windows=[60])
    assert missing_quality.loc[0, "rows_used"] == 59
    assert "2026-07-01T00:00:00Z" in missing_quality.loc[0, "missing_timestamps"]
    assert missing_quality.loc[0, "completion_status"] == "PARTIAL"


def test_midnight_oi_and_zscore_use_previous_day_and_future_rows_are_excluded(tmp_path: Path):
    context = _minute_frame("2026-06-30T23:40:00Z", 31)
    progression = context.loc[
        (context["Timestamp"] >= pd.Timestamp("2026-07-01T00:00:00Z"))
        & (context["Timestamp"] <= pd.Timestamp("2026-07-01T00:09:00Z"))
    ].copy()
    out = tmp_path / "out"

    frames = write_outputs(
        progression,
        out,
        run_timestamp="2026-07-01T00:09:00Z",
        input_files=["previous.csv", "current.csv"],
        calculation_feed=context,
    )
    volume = frames["volume_delta_state.csv"]

    assert volume.iloc[0]["timestamp"] == "2026-07-01T00:00:00Z"
    assert volume.iloc[0]["oi_change"] == 1.0
    prior_20 = context.loc[context["Timestamp"] <= pd.Timestamp("2026-07-01T00:00:00Z"), "TotalQty"].tail(20)
    expected = (prior_20.iloc[-1] - prior_20.mean()) / prior_20.std(ddof=0)
    assert volume.iloc[0]["volume_zscore"] == pytest.approx(expected)
    assert pd.to_datetime(volume["timestamp"], utc=True).max() == pd.Timestamp("2026-07-01T00:09:00Z")


def test_previous_day_context_is_not_replayed_as_registry_progression(tmp_path: Path):
    seed_feed = _minute_frame("2026-06-30T23:58:00Z", 1, close_start=90)
    registry, _ = build_zone_registry(
        liquidity_map=pd.DataFrame([_zone()]),
        feed=seed_feed,
    )
    registry_path = tmp_path / "registry.csv"
    write_registry(registry, registry_path)
    before_touch = int(float(registry.loc[registry["zone_id"] == "zone_000001", "touch_count"].iloc[0]))

    old_context = _minute_frame("2026-06-30T23:59:00Z", 1, close_start=105)
    progression = _minute_frame("2026-07-01T00:00:00Z", 2, close_start=90)
    context = pd.concat([seed_feed, old_context, progression], ignore_index=True)
    frames = write_outputs(
        progression,
        tmp_path / "out",
        run_timestamp="2026-07-01T00:01:00Z",
        input_files=["previous.csv", "current.csv"],
        registry_in_path=registry_path,
        calculation_feed=context,
    )
    row = frames["liquidity_zone_registry.csv"].loc[
        frames["liquidity_zone_registry.csv"]["zone_id"] == "zone_000001"
    ].iloc[0]

    assert int(float(row["touch_count"])) == before_touch + 1
    assert row["last_touch_at"] == "2026-06-30T23:59:00Z"
    # The previously unseen last minute is legitimate lifetime context, but
    # must not be emitted again as a new July progression event.
    events = frames["event_log.csv"]
    assert events.empty or pd.to_datetime(events.event_timestamp, utc=True).ge(pd.Timestamp("2026-07-01T00:00Z")).all()


def test_batch_uses_recovered_source_and_one_synthetic_minute_does_not_skip_day(tmp_path: Path):
    feed_dir = tmp_path / "feed"
    recovered_dir = tmp_path / "feed_recovered"
    raw = _write_minutes(feed_dir / "2026-04-24.csv", "2026-04-24T00:00:00Z", 5)
    recovered = _write_minutes(recovered_dir / "2026-04-24.csv", "2026-04-24T00:00:00Z", 5, synthetic_at=2)
    before = {_sha256(raw), _sha256(recovered)}

    result = run_batch_research(
        feed_dir,
        tmp_path / "batch",
        start_date="2026-04-24",
        end_date="2026-04-24",
        run_timestamp="2026-04-24T00:04:00Z",
    )
    manifest = pd.read_csv(result.manifest_path)

    assert manifest.loc[0, "status"] == "PROCESSED"
    assert manifest.loc[0, "source_class"] == "RECOVERED_DEGRADED"
    assert manifest.loc[0, "selection_reason"] == "KNOWN_OUTAGE_RECOVERED_PRECEDENCE"
    assert "SYNTHETIC=1" in manifest.loc[0, "data_quality_summary"]
    assert {_sha256(raw), _sha256(recovered)} == before


def test_batch_missing_required_recovered_source_fails_loudly(tmp_path: Path):
    feed_dir = tmp_path / "feed"
    _write_minutes(feed_dir / "2026-04-24.csv", "2026-04-24T00:00:00Z", 5)

    with pytest.raises(BatchResearchError, match="REQUIRED_RECOVERED_MISSING"):
        run_batch_research(
            feed_dir,
            tmp_path / "batch",
            start_date="2026-04-24",
            end_date="2026-04-24",
            run_timestamp="2026-04-24T00:04:00Z",
        )


def test_missing_minute_keeps_valid_day_progression_and_next_day_registry_carry(tmp_path: Path):
    feed_dir = tmp_path / "feed"
    day1 = _minute_frame("2026-06-01T00:00:00Z", 5).drop(index=2).reset_index(drop=True)
    day1["IsSynthetic"] = 0
    day1_path = feed_dir / "2026-06-01.csv"
    day1_path.parent.mkdir(parents=True)
    _to_historical(day1).to_csv(day1_path, index=False)
    _write_minutes(feed_dir / "2026-06-02.csv", "2026-06-02T00:00:00Z", 5)

    result = run_batch_research(
        feed_dir,
        tmp_path / "batch",
        start_date="2026-06-01",
        end_date="2026-06-02",
        run_timestamp="2026-06-02T00:04:00Z",
    )
    manifest = pd.read_csv(result.manifest_path)
    quality = pd.read_csv(result.daily_output_dirs[0] / "window_quality.csv")
    five_minute = quality.loc[quality["window_minutes"] == 5].iloc[0]

    assert manifest["status"].tolist() == ["PROCESSED", "PROCESSED"]
    assert manifest.loc[1, "registry_in"] == "daily/2026-06-01/liquidity_zone_registry.csv"
    assert five_minute["completion_status"] == "PARTIAL"
    assert "2026-06-01T00:02:00Z" in five_minute["missing_timestamps"]


def test_uninterrupted_batch_and_equivalent_day_steps_end_with_same_registry(tmp_path: Path):
    feed_dir = tmp_path / "feed"
    day1_path = _write_minutes(feed_dir / "2026-06-01.csv", "2026-06-01T00:00:00Z", 60)
    day2_path = _write_minutes(feed_dir / "2026-06-02.csv", "2026-06-02T00:00:00Z", 60)
    batch = run_batch_research(
        feed_dir,
        tmp_path / "batch",
        start_date="2026-06-01",
        end_date="2026-06-02",
        run_timestamp="2026-06-02T00:59:00Z",
    )

    day1_raw = load_feed(day1_path, deduplicate=False)
    day1 = deduplicate_feed(day1_raw)
    step1 = tmp_path / "steps" / "day1"
    write_outputs(
        day1,
        step1,
        run_timestamp="2026-06-02T00:59:00Z",
        input_files=[str(day1_path)],
        calculation_feed=day1,
        window_quality=build_window_quality(day1_raw, day1["Timestamp"].max()),
    )

    both_raw = load_feed([day1_path, day2_path], deduplicate=False)
    both = deduplicate_feed(both_raw)
    day2 = both.loc[both["Timestamp"].dt.date == pd.Timestamp("2026-06-02").date()].copy()
    step2 = tmp_path / "steps" / "day2"
    write_outputs(
        day2,
        step2,
        run_timestamp="2026-06-02T00:59:00Z",
        input_files=[str(day1_path), str(day2_path)],
        registry_in_path=step1 / "liquidity_zone_registry.csv",
        calculation_feed=causal_slice(both, day2["Timestamp"].max()),
        window_quality=build_window_quality(both_raw, day2["Timestamp"].max()),
    )

    batch_registry = pd.read_csv(batch.daily_output_dirs[-1] / "liquidity_zone_registry.csv", dtype=str).fillna("")
    step_registry = pd.read_csv(step2 / "liquidity_zone_registry.csv", dtype=str).fillna("")
    pd.testing.assert_frame_equal(batch_registry, step_registry)


def _minute_frame(start: str, count: int, *, close_start: float = 100.0) -> pd.DataFrame:
    timestamps = pd.date_range(start, periods=count, freq="min", tz="UTC")
    rows = []
    for index, timestamp in enumerate(timestamps):
        close = close_start + index
        rows.append(
            {
                "Timestamp": timestamp,
                "OpenPrice": close,
                "HiPrice": close,
                "LowPrice": close,
                "ClosePrice": close,
                "TotalQty": 10.0 + index,
                "Trades": 1,
                "BuyQty": 6.0 + index,
                "SellQty": 4.0,
                "OpenInterest": 1000.0 + index,
                "FundingRate": 0.0001,
                "DataQuality": "RAW",
                "SourceClass": "RAW",
                "SourceFile": "fixture.csv",
            }
        )
    return pd.DataFrame(rows)


def _to_historical(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.rename(
        columns={
            "OpenPrice": "Open",
            "HiPrice": "High",
            "LowPrice": "Low",
            "ClosePrice": "Close",
            "TotalQty": "Volume",
            "Trades": "AggTrades",
        }
    ).drop(columns=["DataQuality", "SourceClass", "SourceFile"])


def _write_minutes(
    path: Path,
    start: str,
    count: int,
    *,
    synthetic_at: int | None = None,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = _minute_frame(start, count)
    frame["IsSynthetic"] = 0
    if synthetic_at is not None:
        frame.loc[synthetic_at, "IsSynthetic"] = 1
    _to_historical(frame).to_csv(path, index=False)
    return path


def _zone() -> dict[str, object]:
    return {
        "zone_id": "zone_000001",
        "created_at": "2026-06-30T23:58:00Z",
        "last_updated_at": "2026-06-30T23:58:00Z",
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
        "touch_count": 0,
        "sweep_count": 0,
        "distance_from_close_pct": 0,
        "data_quality": "RAW",
        "invalidation_reason": "",
    }


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
