import pandas as pd
import pytest

from market_monitor import structure, zone_registry, significant_zone_selector as selector
from market_monitor import setup_builder


def minutes(start="2026-05-07T00:01:00Z", count=600):
    return pd.DataFrame({"Timestamp": pd.date_range(start, periods=count, freq="min"),
                         "OpenPrice": 100., "HiPrice": 101., "LowPrice": 99., "ClosePrice": 100.,
                         "TotalQty": 10., "Trades": 1, "BuyQty": 5., "SellQty": 5.,
                         "OpenInterest": 1000., "FundingRate": .0001, "DataQuality": "RAW"})


def zone():
    return {"zone_id": "input", "created_at": "2026-05-07T00:01:00Z", "side": "BUY_SIDE",
            "zone_type": "H1_SWING_HIGH_ZONE", "price_lower": 100., "price_upper": 102., "price_mid": 101.,
            "source_level_ids": "level_1", "source_timeframes": "H1", "status": "ACTIVE",
            "confidence_score": 65, "confidence_tier": "MEDIUM", "touch_count": 0,
            "data_quality": "RAW"}


def test_duplicate_minutes_are_not_counted_as_observations():
    frame = minutes(count=60)
    with pytest.raises(ValueError, match="duplicate"):
        structure.aggregate_timeframe(pd.concat([frame, frame.iloc[:1]]), "H1")


def test_session_boundary_uses_close_labels():
    frame = minutes(count=480)
    frame.loc[frame.Timestamp.eq(pd.Timestamp("2026-05-07T08:00Z")), "HiPrice"] = 200.
    levels = structure.build_structure_levels(frame)
    assert levels.loc[levels.level_type.eq("ASIA_HIGH"), "price"].tolist() == [200.]


def test_session_not_final_at_last_open_label():
    levels = structure.build_structure_levels(minutes(count=479))
    assert not levels.level_type.eq("ASIA_HIGH").any()


def test_daily_boundary_includes_midnight_close_in_previous_day():
    frame = minutes(count=1441)
    frame.loc[frame.Timestamp.eq(pd.Timestamp("2026-05-08T00:00Z")), "HiPrice"] = 200.
    levels = structure.build_structure_levels(frame)
    assert levels.loc[levels.level_type.eq("PDH"), "price"].tolist() == [200.]


def test_extended_gap_cannot_confirm_a_swing():
    frame = minutes(count=420)
    frame.loc[frame.Timestamp.dt.hour.eq(2), "HiPrice"] = 120.
    frame = frame.loc[~frame.Timestamp.dt.hour.eq(3)]
    levels = structure.build_structure_levels(frame)
    assert not levels.level_type.eq("H1_SWING_HIGH").any()


def test_registry_repeated_prefix_is_idempotent():
    frame = minutes(count=60)
    one, _ = zone_registry.build_zone_registry(liquidity_map=pd.DataFrame([zone()]), feed=frame)
    two, _ = zone_registry.build_zone_registry(liquidity_map=pd.DataFrame([zone()]), feed=frame, registry_in=one)
    pd.testing.assert_frame_equal(one, two)


def test_registry_replay_does_not_inflate_touch_history():
    frame = minutes(count=60)
    one, _ = zone_registry.build_zone_registry(liquidity_map=pd.DataFrame([zone()]), feed=frame)
    two, _ = zone_registry.build_zone_registry(liquidity_map=pd.DataFrame(), feed=frame, registry_in=one)
    assert one.touch_count.tolist() == two.touch_count.tolist()


def test_selector_has_real_asof_contract():
    import inspect
    assert "as_of" in inspect.signature(selector.run_significant_zone_selector).parameters


def test_target_strictly_outside_price_and_finite():
    zones = pd.DataFrame([{"zone_id": "z", "side": "BUY_SIDE", "price_lower": 100., "price_upper": 101.}])
    assert setup_builder._target_reference_zone(zones, "BUY_SIDE", 100.) == ""
    assert setup_builder._target_reference_zone(zones, "BUY_SIDE", float("nan")) == ""


def test_hidden_flow_normalization_cannot_read_later_windows():
    from market_monitor.hidden_flow_research import _add_relative_metrics
    before = pd.DataFrame({"window_minutes": [60, 60], "total_qty": [10., 20.], "trades": [2., 4.], "range_pct": [1., 2.]})
    longer = pd.concat([before, pd.DataFrame({"window_minutes": [60], "total_qty": [100000.], "trades": [9999.], "range_pct": [99.]})], ignore_index=True)
    pd.testing.assert_frame_equal(_add_relative_metrics(before), _add_relative_metrics(longer).iloc[:2])


def test_uncompleted_string_false_is_not_truthy_and_cannot_reclaim():
    from market_monitor.qualified_h1_sweep_reclaim import _prepare_h1_bars, _attach_failed_reclaim
    frame = pd.DataFrame({"timestamp": pd.to_datetime(["2026-05-07T01:00Z", "2026-05-07T02:00Z"]),
                          "open": [110., 105.], "high": [120., 110.], "low": [105., 90.],
                          "close": [110., 95.], "volume": [10., 10.], "completed": ["true", "false"]})
    bars = _prepare_h1_bars(frame)
    assert bars.completed.tolist() == [True, False]
    row = {"qualified_h1_sweep": "true", "sweep_reference_level": 100., "sweep_direction": "BEARISH"}
    _attach_failed_reclaim(row, bars, bars.iloc[0], 3)
    assert row["reclaim_reject_reason"] == "incomplete_or_missing_confirmation_bar"
    assert row.get("qualified_h1_failed_reclaim") != "true"


def test_selector_filters_future_event_and_observation_without_changing_weights():
    loaded = {name: pd.DataFrame() for name in selector.INPUT_TABLES}
    row = {**zone(), "_source_day": "2026-05-07", "snapshot_available_at_utc": "2026-05-07T01:00Z",
           "source_timeframes": "H4", "has_h4_source": True, "confidence_tier": "HIGH", "precision_status": "PRECISE",
           "distance_from_close_pct": .1}
    loaded["liquidity_map.csv"] = pd.DataFrame([row])
    expected = selector._score_zone(pd.Series(row), pd.DataFrame(), pd.DataFrame())
    loaded["event_log.csv"] = pd.DataFrame([{"zone_id": "input", "_source_day": "2026-05-07",
        "event_timestamp": "2026-05-07T02:00Z", "volume_zscore": 99.}])
    loaded["post_sweep_observation.csv"] = pd.DataFrame([{"zone_id": "input", "_source_day": "2026-05-07",
        "snapshot_available_at_utc": "2026-05-07T01:00Z", "observation_end_timestamp": "2026-05-07T02:00Z", "post_oi_change": 999.}])
    selected = selector.select_zones_at(loaded, "2026-05-07T01:00Z")
    assert len(selected) == 1
    for key in ["significance_score", "score_components_json", "penalty_components_json", "bucket"]:
        assert selected.iloc[0][key] == expected[key]
    assert pd.Timestamp(selected.iloc[0].selection_cutoff_utc) == pd.Timestamp("2026-05-07T01:00Z")


def test_later_daily_snapshots_are_not_backdated_to_setup_time():
    from market_monitor.causality import latest_zone_snapshot
    zones = pd.DataFrame([{**zone(), "source_day": "2026-05-25"}])
    assert latest_zone_snapshot(zones, "2026-03-12T16:59Z").empty


def test_hidden_latest_snapshot_prevents_resurrecting_old_visible_row():
    from market_monitor.causality import latest_zone_snapshot
    zones = pd.DataFrame([{**zone(), "selection_cutoff_utc": "2026-05-07T01:00Z", "visible_on_snapshot": "true"},
                          {**zone(), "selection_cutoff_utc": "2026-05-07T02:00Z", "visible_on_snapshot": "false"}])
    latest = latest_zone_snapshot(zones, "2026-05-07T02:00Z")
    assert setup_builder._visible_zones(latest).empty


def test_legacy_registry_file_requires_reconstruction(tmp_path):
    path = tmp_path / "legacy.csv"
    pd.DataFrame([{**zone(), "first_seen_at": "2026-05-07T00:01Z"}]).to_csv(path, index=False)
    with pytest.raises(ValueError, match="uncertified"):
        zone_registry.load_registry(path)


def test_provisional_h4_metrics_do_not_survive_closure():
    frame = minutes(start="2026-05-07T00:01Z", count=240)
    frame.loc[frame.Timestamp.eq(pd.Timestamp("2026-05-07T01:00Z")), "ClosePrice"] = 110.
    row = {"source_timeframes": "H4", "source_timeframe_primary": "H4", "first_seen_at": "2026-05-07T00:00Z",
           "htf_confirmation_timestamp": "2026-05-07T00:00Z", "side": "BUY_SIDE", "htf_close_through_count": 100}
    early = zone_registry._htf_lifecycle_metrics(row, frame.iloc[:60], 102., 105.)
    late = zone_registry._htf_lifecycle_metrics({**row, **early}, frame, 102., 105.)
    assert early["htf_close_through_count"] == late["htf_close_through_count"] == 0


def test_incremental_structure_matches_shared_full_prefix_detector():
    frame = minutes(count=1200)
    frame.loc[frame.Timestamp.dt.hour.eq(5), "HiPrice"] = 120.
    state = structure.StructureState()
    for cutoff in pd.date_range(frame.Timestamp.min().ceil("h"), frame.Timestamp.max(), freq="h"):
        state.update(frame.loc[frame.Timestamp.le(cutoff)])
    pd.testing.assert_frame_equal(state.levels, structure._sort_levels(structure.build_structure_levels(frame)), check_dtype=False)


def test_complete_canonical_decision_is_invariant_to_future_feed():
    from market_monitor.chronological import ChronologicalMonitor
    frame = minutes(count=180)
    one, two = ChronologicalMonitor(), ChronologicalMonitor()
    for cutoff in pd.date_range("2026-05-07T01:00Z", "2026-05-07T02:00Z", freq="h"):
        a, b = one.update(frame.loc[frame.Timestamp.le(cutoff)], cutoff), two.update(frame, cutoff)
        for key in ["selected_zones", "state", "hidden_flow_windows"]:
            pd.testing.assert_frame_equal(a[key], b[key])
        for name in a["frames"]:
            pd.testing.assert_frame_equal(a["frames"][name], b["frames"][name])
        assert a["snapshot"] == b["snapshot"]


def test_merge_does_not_reclassify_old_candles_against_new_geometry():
    import json
    frame = minutes(count=60)
    for column in ["OpenPrice", "ClosePrice"]:
        frame[column] = 69900.
    frame["HiPrice"], frame["LowPrice"] = 69901., 69899.
    frame.loc[frame.Timestamp.dt.minute.eq(30), "HiPrice"] = 70020.
    original = {**zone(), "created_at": "2026-05-07T00:00Z", "price_lower": 70000., "price_upper": 70010., "price_mid": 70005.}
    old, _ = zone_registry.build_zone_registry(liquidity_map=pd.DataFrame([original]), feed=frame)
    added = {**original, "created_at": "2026-05-07T01:00Z", "source_level_ids": "level_2", "price_lower": 70005., "price_upper": 70030., "price_mid": 70017.5}
    merged, _ = zone_registry.build_zone_registry(liquidity_map=pd.DataFrame([added]), feed=frame, registry_in=old)
    active = merged.loc[merged.status.ne("MERGED")].iloc[0]
    assert pd.Timestamp(active.geometry_available_at_utc) == pd.Timestamp("2026-05-07T01:00Z")
    assert active.touch_count == active.cross_count == 0
    history = json.loads(active.prior_geometry_history_json)
    assert history[0]["cross_count"] == 1


def test_event_identity_survives_an_earlier_unrelated_event():
    from market_monitor.events import build_event_log
    from market_monitor.outputs import build_volume_delta_state
    frame = minutes(count=60)
    registry, _ = zone_registry.build_zone_registry(liquidity_map=pd.DataFrame([zone()]), feed=frame)
    first = build_event_log(registry=registry, feed=frame, volume_delta_state=build_volume_delta_state(frame))
    earlier = registry.iloc[0].to_dict()
    earlier.update(zone_id="zone_other", first_seen_at="2026-05-07T00:00Z", geometry_available_at_utc="2026-05-07T00:00Z")
    second = build_event_log(registry=pd.concat([registry, pd.DataFrame([earlier])]), feed=frame,
                             volume_delta_state=build_volume_delta_state(frame))
    pd.testing.assert_series_equal(first.event_id.reset_index(drop=True),
                                    second.loc[second.zone_id.ne("zone_other"), "event_id"].reset_index(drop=True))


def test_post_sweep_window_never_borrows_later_minutes_to_fill_a_gap():
    from market_monitor.post_sweep_observation import _observation_row, _context_frame
    import json
    frame = minutes(count=31).drop(index=5)
    event = pd.Series({"event_id": "e", "event_close": 100., "event_timestamp": "2026-05-07T00:00Z", "zone_id": "z", "side": "BUY_SIDE",
                       "data_quality": "RAW", "evidence_json": json.dumps({"price_lower": 100., "price_upper": 102., "price_mid": 101., "zone_type": "H1_SWING_HIGH_ZONE"})})
    row = _observation_row(event, frame, _context_frame(pd.DataFrame()))
    assert row["observation_bars_available"] == 29 and not row["observation_complete"]
    assert pd.Timestamp(row["observation_end_timestamp"]) == pd.Timestamp("2026-05-07T00:30Z")


def test_post_sweep_structure_event_is_dated_at_evidence_availability():
    from market_monitor.market_structure_state import _build_structure_events
    post = pd.DataFrame([{"side": "SELL_SIDE", "source_event_timestamp": "2026-05-07T01:00Z",
        "observation_end_timestamp": "2026-05-07T01:30Z", "zone_price_lower": 99., "zone_price_upper": 101.,
        "zone_price_mid": 100., "net_close_change_pct": 1., "bars_above_zone": 20, "bars_below_zone": 0,
        "max_return_inside_zone": 0., "max_excursion_beyond_zone": 1.}])
    events = _build_structure_events(post, pd.DataFrame())
    assert pd.Timestamp(events.iloc[0].event_timestamp) == pd.Timestamp("2026-05-07T01:30Z")
    assert pd.Timestamp(events.iloc[0].source_event_timestamp) == pd.Timestamp("2026-05-07T01:00Z")


def test_40a_original_invalidated_rows_remain_regression_evidence():
    from pathlib import Path
    from market_monitor.causality import latest_zone_snapshot
    root = Path(__file__).resolve().parents[1] / "market_monitor_runs/SHI_RESET_38V_full_feed_38s_to_setup_builder_crosscheck_v0"
    if not (root / "full_feed_setup_builder_candidates.csv").exists():
        pytest.skip("historical invalidated source artifacts are external to main")
    rows = pd.read_csv(root / "full_feed_setup_builder_candidates.csv")
    zones = pd.read_csv(root / "support/selected_zones/selected_zones.csv")
    visible = zones.loc[zones.visible_on_snapshot.astype(str).str.lower().eq("true")].set_index("zone_id")
    backdated, later = 0, 0
    for record in rows.to_dict("records"):
        formed, state_end = pd.Timestamp(record["setup_formed_at"]), pd.Timestamp(record["end_timestamp"])
        backdated += state_end > formed
        assert pd.Timestamp(setup_builder._formed_at(pd.Series(record), None)) >= state_end
        reference = visible.loc[record["target_reference_zone"].split(":")[0]]
        if pd.Timestamp(reference.source_day, tz="UTC") > formed.normalize():
            later += 1
            assert latest_zone_snapshot(pd.DataFrame([reference]), formed).empty
    assert len(rows) == 51 and backdated == 49 and later == 24


@pytest.mark.parametrize("side", ["BUY_SIDE", "SELL_SIDE"])
def test_lifecycle_cache_is_exactly_equal_to_full_history_recomputation(side):
    frame = minutes(count=720)
    reference = {**zone(), "side": side, "created_at": "2026-05-07T00:00Z",
                 "price_lower": 102. if side == "BUY_SIDE" else 96., "price_upper": 104. if side == "BUY_SIDE" else 98.}
    previous, _ = zone_registry.build_zone_registry(liquidity_map=pd.DataFrame([reference]), feed=frame.iloc[:240])
    for end in [300, 360, 480, 720]:
        cached = zone_registry._update_lifecycle(previous, frame.iloc[:end], use_cache=True)
        full = zone_registry._update_lifecycle(previous, frame.iloc[:end], use_cache=False)
        pd.testing.assert_frame_equal(cached, full)
        previous = cached


def test_htf_confirmation_cannot_join_nonconsecutive_bars_across_source_gap():
    frame = minutes(count=960)
    frame = frame.loc[~frame.Timestamp.between(pd.Timestamp("2026-05-07T08:01Z"), pd.Timestamp("2026-05-07T12:00Z"))]
    frame["ClosePrice"], frame["HiPrice"], frame["LowPrice"] = 110., 111., 109.
    row = {"source_timeframes": "H4", "source_timeframe_primary": "H4", "first_seen_at": "2026-05-07T00:00Z", "side": "BUY_SIDE"}
    metrics = zone_registry._htf_lifecycle_metrics(row, frame, 102., 105.)
    assert metrics["htf_acceptance_count"] == 0
    assert metrics["history_context_incomplete"] == "true"


def test_htf_bar_straddling_new_zone_geometry_cannot_import_earlier_wicks():
    frame = minutes(count=240)
    frame.loc[frame.Timestamp.lt(pd.Timestamp("2026-05-07T03:00Z")), "HiPrice"] = 120.
    row = {"source_timeframes": "H4", "source_timeframe_primary": "H4", "first_seen_at": "2026-05-07T00:00Z",
           "geometry_available_at_utc": "2026-05-07T03:00Z", "side": "BUY_SIDE"}
    assert zone_registry._htf_lifecycle_metrics(row, frame, 102., 105.)["htf_sweep_count"] == 0


def test_trader_price_path_does_not_include_later_same_day_quotes(tmp_path):
    from datetime import date
    from market_monitor.trader_snapshot_builder import _load_price_path
    root = tmp_path / "feed"
    root.mkdir()
    pd.DataFrame({"Timestamp": ["2026-05-07T01:00Z", "2026-05-07T02:00Z"], "Open": [100., 200.],
                  "High": [101., 201.], "Low": [99., 199.], "Close": [100., 200.]}).to_csv(root / "2026-05-07.csv", index=False)
    path = _load_price_path(root, date(2026, 5, 7), date(2026, 5, 7), cutoff="2026-05-07T01:00Z")
    assert path.Close.tolist() == [100.]


def test_explicit_elapsed_cutoff_handles_isolated_missing_close_without_inventing_price():
    frame = minutes(count=120).drop(index=59)
    cutoff = pd.Timestamp("2026-05-07T01:00Z")
    bars = structure.aggregate_timeframe(frame, "H1", as_of=cutoff)
    assert bars.Timestamp.tolist() == [cutoff]
    assert bars.iloc[0].source_end == cutoff - pd.Timedelta(minutes=1)
    assert bars.iloc[0].missing_minute_count == 1
    assert bars.iloc[0].completion_status == "CLOSED_OBSERVED"
    from market_monitor.chronological import ChronologicalMonitor
    decision = ChronologicalMonitor().update(frame, cutoff)
    assert decision["state"].iloc[0].h1_observation_status == "CLOSED_OBSERVED"
    assert pd.Timestamp(decision["snapshot"]["cutoff_ts"]) == cutoff
    assert decision["hidden_flow_windows"].window_minutes.eq(60).any()


def test_structure_state_initial_full_context_and_explicit_future_cutoff_match_reference():
    frame = minutes(count=4500)
    frame.loc[frame.Timestamp.dt.hour.eq(5), "HiPrice"] = 120.
    cutoff = frame.Timestamp.iloc[-61]
    actual = structure.StructureState().update(frame, as_of=cutoff)
    expected = structure.build_structure_levels(frame.loc[frame.Timestamp.le(cutoff)], as_of=cutoff)
    pd.testing.assert_frame_equal(actual, expected, check_dtype=False)


def test_registry_rejects_future_geometry_even_when_original_formation_is_old():
    reference = {**zone(), "geometry_available_at_utc": "2026-05-07T02:00Z"}
    with pytest.raises(ValueError, match="unavailable"):
        zone_registry.build_zone_registry(liquidity_map=pd.DataFrame([reference]), feed=minutes(count=60))


def test_chronological_state_preserves_setup_builder_band_contract():
    from market_monitor.chronological import ChronologicalMonitor
    decision = ChronologicalMonitor().update(minutes(count=600), "2026-05-07T10:00Z")
    for name in ["active_support_price_lower", "active_support_price_upper", "active_resistance_price_lower",
                 "active_resistance_price_upper", "active_support_band_id", "active_resistance_band_id", "oi_context"]:
        assert name in decision["state"]


def test_direct_lifecycle_recomputation_excludes_synthetic_source_rows():
    frame = minutes(count=120)
    registry, _ = zone_registry.build_zone_registry(liquidity_map=pd.DataFrame([zone()]), feed=frame)
    contaminated = frame.copy()
    contaminated.loc[20, ["HiPrice", "LowPrice", "ClosePrice", "DataQuality"]] = [200., 0., 0., "SYNTHETIC"]
    clean = contaminated.loc[contaminated.DataQuality.ne("SYNTHETIC")]
    actual = zone_registry._update_lifecycle(registry, contaminated, use_cache=False)
    expected = zone_registry._update_lifecycle(registry, clean, use_cache=False)
    pd.testing.assert_frame_equal(actual, expected)


def test_snapshot_uses_observed_prices_and_quantities_only():
    from market_monitor.snapshot_builder_v39a import build_market_monitor_snapshot_v39a
    frame = minutes(count=1440)
    frame.loc[1439, ["ClosePrice", "TotalQty", "DataQuality"]] = [999999., 999999., "SYNTHETIC"]
    snapshot = build_market_monitor_snapshot_v39a(frame, persist_state=False)
    assert snapshot["structure"]["current_price"] == 100.
    assert snapshot["windows"]["60"]["rows_used"] == 59


@pytest.mark.parametrize("corruption", ["duplicate", "infinity"])
def test_snapshot_rejects_ambiguous_or_nonfinite_observations(corruption):
    from market_monitor.snapshot_builder_v39a import build_market_monitor_snapshot_v39a, MonitorSnapshotV39AError
    frame = minutes(count=60)
    if corruption == "duplicate":
        frame = pd.concat([frame, frame.iloc[:1]])
    else:
        frame.loc[0, "ClosePrice"] = float("inf")
    with pytest.raises(MonitorSnapshotV39AError):
        build_market_monitor_snapshot_v39a(frame, persist_state=False)


def test_snapshot_base_clock_cannot_hide_future_nested_zone_evidence():
    from market_monitor.snapshot_builder_v39a import build_market_monitor_snapshot_v39a, MonitorSnapshotV39AError
    with pytest.raises(MonitorSnapshotV39AError, match="future"):
        build_market_monitor_snapshot_v39a(minutes(count=60), persist_state=False,
            base_snapshot={"cutoff_ts": "2026-05-07T01:00Z", "liquidity_zones": [
                {"zone_id": "z", "created_at": "2026-05-08T00:00Z"}]})


@pytest.mark.parametrize("timeframe,duration,radius", [("H1", 60, 2), ("H4", 240, 1)])
def test_swing_quality_includes_its_recovered_confirmation_dependency(timeframe, duration, radius):
    frame = minutes(count=duration * (2 * radius + 1))
    frame.loc[frame.index // duration == radius, "HiPrice"] = 120.
    frame.loc[frame.index // duration == 2 * radius, "DataQuality"] = "RECOVERED_DEGRADED"
    levels = structure.build_structure_levels(frame)
    pivot = levels.loc[levels.level_type.eq(timeframe + "_SWING_HIGH")].iloc[0]
    assert pivot.data_quality == "RECOVERED_DEGRADED"


def test_custom_registry_export_and_daily_copy_preserve_identical_availability(tmp_path):
    from market_monitor.outputs import write_outputs
    custom = tmp_path / "external_registry.csv"
    daily = tmp_path / "daily"
    write_outputs(minutes(count=600), daily, run_timestamp="2026-05-07T10:00Z", input_files=[], registry_out_path=custom)
    assert custom.read_bytes() == (daily / "liquidity_zone_registry.csv").read_bytes()


def test_partial_genesis_does_not_invent_a_daily_open_from_midday_price():
    levels = structure.build_structure_levels(minutes(start="2026-05-07T13:01Z", count=60))
    assert not levels.level_type.eq("DAY_OPEN").any()


def test_previous_day_references_do_not_bridge_an_unobserved_calendar_day():
    frame = pd.concat([minutes(count=1440), minutes(start="2026-05-09T00:01Z", count=60)], ignore_index=True)
    levels = structure.build_structure_levels(frame)
    assert not levels.level_type.isin(["PDH", "PDL"]).any()


def test_direct_outputs_skip_synthetic_prices_quantities_and_events(tmp_path):
    from market_monitor.outputs import write_outputs
    frame = minutes(count=60)
    frame.loc[20, ["HiPrice", "LowPrice", "ClosePrice", "TotalQty", "DataQuality"]] = [999999., 0., 0., 999999., "SYNTHETIC"]
    result = write_outputs(frame, tmp_path, run_timestamp="2026-05-07T01:00Z", input_files=[], persist=False)
    assert len(result["volume_delta_state.csv"]) == 59
    assert result["volume_delta_state.csv"].total_qty.sum() == 590.


def test_window_quality_counts_synthetic_as_missing_observation_but_retains_source_quality():
    import json
    from market_monitor.feed_quality import build_window_quality
    frame = minutes(count=60)
    frame["IsSynthetic"] = 0
    frame.loc[20, "IsSynthetic"] = 1
    quality = build_window_quality(frame, frame.Timestamp.max(), windows=[60]).iloc[0]
    assert quality.rows_used == 59 and quality.completion_status == "PARTIAL"
    assert json.loads(quality.data_quality_counts)["SYNTHETIC"] == 1


def test_market_state_normalizer_excludes_synthetic_and_normalizes_utc_offsets():
    from market_monitor.market_structure_state import _normalize_feed
    frame = minutes(count=60)
    frame["IsSynthetic"] = 0
    frame.loc[20, "IsSynthetic"] = 1
    frame.Timestamp = frame.Timestamp.dt.tz_convert("Etc/GMT-2").astype(str)
    observed = _normalize_feed(frame)
    assert len(observed) == 59
    assert pd.Timestamp(observed.Timestamp.iloc[0]).tz_localize("UTC") == pd.Timestamp("2026-05-07T00:01Z")


def test_trader_price_reader_excludes_synthetic_rows(tmp_path):
    from datetime import date
    from market_monitor.trader_snapshot_builder import _load_price_path
    frame = minutes(count=60).rename(columns={"OpenPrice": "Open", "HiPrice": "High", "LowPrice": "Low", "ClosePrice": "Close"})
    frame["IsSynthetic"] = 0
    frame.loc[20, ["IsSynthetic", "Close"]] = [1, 999999.]
    frame.to_csv(tmp_path / "2026-05-07.csv", index=False)
    assert len(_load_price_path(tmp_path, date(2026, 5, 7), date(2026, 5, 7))) == 59


def test_hidden_flow_file_reader_rejects_infinite_observations(tmp_path):
    from datetime import date
    from market_monitor.hidden_flow_research import _load_feed, HiddenFlowResearchError
    frame = minutes(count=60)
    frame.loc[20, "ClosePrice"] = float("inf")
    frame.to_csv(tmp_path / "2026-05-07.csv", index=False)
    with pytest.raises(HiddenFlowResearchError, match="invalid"):
        _load_feed(tmp_path, date(2026, 5, 7), date(2026, 5, 7), required_start=date(2026, 5, 7))


def test_historical_omission_does_not_make_current_complete_snapshot_permanently_partial():
    from market_monitor.snapshot_builder_v39a import build_market_monitor_snapshot_v39a
    frame = minutes(count=3000)
    frame.loc[0, "DataQuality"] = "SYNTHETIC"
    snapshot = build_market_monitor_snapshot_v39a(frame, persist_state=False)
    assert snapshot["quality"]["readiness"] == "READY"


def test_prior_flow_excludes_current_window_rows_after_skipped_source_observations():
    from market_monitor.chronological import ChronologicalMonitor
    frame = minutes(count=180)
    frame.loc[20, "DataQuality"] = "SYNTHETIC"
    frame.loc[120, ["ClosePrice", "HiPrice", "LowPrice"]] = [200., 201., 199.]
    decision = ChronologicalMonitor().update(frame, "2026-05-07T03:00Z")
    window = decision["hidden_flow_windows"].loc[lambda x: x.window_minutes.eq(60)].iloc[0]
    assert window.prior_trend_direction == "RANGE"


def test_all_synthetic_progression_carries_context_without_creating_observations(tmp_path):
    from market_monitor.outputs import write_outputs
    history = minutes(count=600)
    history.loc[history.index // 60 == 2, "HiPrice"] = 120.
    previous = write_outputs(history, tmp_path, run_timestamp="2026-05-07T10:00Z", input_files=[], persist=False)
    skipped = minutes(start="2026-05-08T00:01Z", count=60)
    skipped["DataQuality"] = "SYNTHETIC"
    current = write_outputs(skipped, tmp_path, run_timestamp="2026-05-08T01:00Z", input_files=[], persist=False,
        calculation_feed=pd.concat([history, skipped]), registry_state=previous["liquidity_zone_registry.csv"])
    assert current["volume_delta_state.csv"].empty and current["market_state_timeline.csv"].empty
    assert current["event_log.csv"].empty
    for field in ["touch_count", "cross_count", "close_above_count", "close_below_count"]:
        pd.testing.assert_series_equal(current["liquidity_zone_registry.csv"][field], previous["liquidity_zone_registry.csv"][field])


def test_all_synthetic_context_cannot_admit_a_future_registry_snapshot():
    prior, _ = zone_registry.build_zone_registry(liquidity_map=pd.DataFrame([zone()]), feed=minutes(count=120))
    skipped = minutes(count=60)
    skipped["DataQuality"] = "SYNTHETIC"
    with pytest.raises(ValueError, match="future"):
        zone_registry.build_zone_registry(liquidity_map=pd.DataFrame(), feed=skipped, registry_in=prior, as_of="2026-05-07T01:00Z")


def test_uncertified_in_memory_registry_cannot_initialize_canonical_progression():
    frame = minutes(count=120)
    prior, _ = zone_registry.build_zone_registry(liquidity_map=pd.DataFrame([zone()]), feed=frame.iloc[:60])
    prior = prior.drop(columns="registry_state_version")
    prior["htf_close_through_count"] = 100
    with pytest.raises(ValueError, match="uncertified"):
        zone_registry.build_zone_registry(liquidity_map=pd.DataFrame(), feed=frame, registry_in=prior)


def test_prior_flow_uses_utc_duration_without_borrowing_an_older_row_to_fill_a_gap():
    from market_monitor.hidden_flow_research import _prior_trend_context
    frame = minutes(count=360)
    frame.loc[119, "ClosePrice"] = 200.
    frame = frame.drop(index=180).reset_index(drop=True).rename(columns={"Timestamp": "timestamp", "ClosePrice": "close_price"})
    start = int(frame.index[frame.timestamp.eq(pd.Timestamp("2026-05-07T04:01Z"))][0])
    assert _prior_trend_context(frame, start, 120)["prior_trend_direction"] == "RANGE"


def test_partial_h1_state_does_not_enter_confirmed_market_state_memory():
    from market_monitor.chronological import ChronologicalMonitor
    monitor = ChronologicalMonitor()
    frame = minutes(count=120).drop(index=range(20))
    first = monitor.update(frame, "2026-05-07T01:00Z")
    assert first["state"].iloc[0].h1_observation_status == "PARTIAL"
    assert not monitor.previous_states
    second = monitor.update(frame, "2026-05-07T02:00Z")
    assert len(monitor.previous_states) == 1
    assert first["state"].iloc[0].state_id != second["state"].iloc[0].state_id


def test_chronological_setup_review_identity_and_context_continue_across_h1(monkeypatch):
    from market_monitor.chronological import ChronologicalMonitor
    def generated(**kwargs):
        end = kwargs["states"].iloc[0].end_timestamp
        return [{"setup_id": "setup_000001", "setup_formed_at": end, "end_timestamp": end}]
    monkeypatch.setattr(setup_builder, "_build_rows", generated)
    monitor = ChronologicalMonitor()
    frame = minutes(count=180)
    first = monitor.update(frame, "2026-05-07T02:00Z")
    second = monitor.update(frame, "2026-05-07T03:00Z")
    assert first["setups"][0]["setup_id"] != second["setups"][0]["setup_id"]
    assert len(monitor.setup_context) == 2


def test_setup_review_receives_eligible_previous_boundary_flow_window(monkeypatch):
    from market_monitor.chronological import ChronologicalMonitor
    original = setup_builder._build_rows
    consumed = []
    def reviewed(**kwargs):
        consumed.append(kwargs["windows"].copy())
        return original(**kwargs)
    monkeypatch.setattr(setup_builder, "_build_rows", reviewed)
    monitor = ChronologicalMonitor()
    frame = minutes(count=180)
    monitor.update(frame, "2026-05-07T02:00Z")
    monitor.update(frame, "2026-05-07T03:00Z")
    assert pd.to_datetime(consumed[-1].end_timestamp, utc=True).eq(pd.Timestamp("2026-05-07T02:00Z")).any()


def test_closed_htf_cache_advances_on_elapsed_clock_with_an_isolated_missing_close():
    frame = minutes(count=239)
    frame["ClosePrice"], frame["HiPrice"], frame["LowPrice"] = 110., 111., 109.
    reference = {**zone(), "created_at": "2026-05-07T00:00Z", "price_lower": 102., "price_upper": 104.,
                 "source_timeframes": "H4", "source_timeframe_primary": "H4"}
    prior, _ = zone_registry.build_zone_registry(liquidity_map=pd.DataFrame([reference]), feed=frame)
    assert prior.iloc[0].htf_close_through_count == 0
    current, _ = zone_registry.build_zone_registry(liquidity_map=pd.DataFrame(), feed=frame, registry_in=prior,
        as_of="2026-05-07T04:00Z")
    assert current.iloc[0].htf_close_through_count == 1
    repeated, _ = zone_registry.build_zone_registry(liquidity_map=pd.DataFrame(), feed=frame, registry_in=current,
        as_of="2026-05-07T04:00Z")
    pd.testing.assert_frame_equal(current, repeated)


@pytest.mark.parametrize("field", ["ConfirmingBarCloseUTC", "source_event_timestamp", "source_end",
    "first_return_inside_at", "first_close_inside_at", "first_close_beyond_at", "invalidated_at", "retired_at"])
def test_asof_contract_checks_each_consumed_evidence_clock_even_when_snapshot_clock_is_old(field):
    from market_monitor.causality import asof_rows
    row = {"snapshot_available_at_utc": "2026-05-07T01:00Z", field: "2026-05-07T02:00Z"}
    assert asof_rows(pd.DataFrame([row]), "2026-05-07T01:00Z", require_clock=True).empty
