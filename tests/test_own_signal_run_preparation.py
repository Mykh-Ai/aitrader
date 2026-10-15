from __future__ import annotations

import copy
from pathlib import Path

import pandas as pd
import pytest

from research.own_signal_run.causal import CausalSignalEngine
from research.own_signal_run.contracts import load_contract, validate_signal
from research.own_signal_run.feed import closed_bars, digest, read_sources
from research.own_signal_run.replay import apply_costs, replay_signals, summarize

CONTRACT = Path(__file__).resolve().parents[1] / "research/own_signal_run/contract_v1.json"


def config() -> dict:
    c = load_contract(CONTRACT)
    c["warmup_hours"] = 24
    c["periods"] = [{"name": "SYNTHETIC_CONTROL", "start": "2026-03-01T00:00:00Z", "end": "2026-04-01T00:00:00Z"}]
    return c


def feed_control(invert: bool = False, hours: int = 40) -> pd.DataFrame:
    rows = []
    for i in range(hours):
        o, h, low, close, qty = 100.0, 100.2, 99.8, 100.0, 1.0
        if i == 8:
            low = 97.0
        if i == 20:
            h = 101.0
        if i == 35:
            o, h, low, close, qty = 100.2, 101.8, 100.1, 100.8, 2.0
        if i == 36:
            o, h, low, close, qty = 100.8, 100.9, 100.6, 100.7, 2.0
        if i == 37:
            o, h, low, close, qty = 100.2, 101.1, 99.9, 100.0, 2.0
        if invert:
            o, h, low, close = 200 - o, 200 - low, 200 - h, 200 - close
        for m in range(60):
            ts = pd.Timestamp("2026-03-01T00:01:00Z") + pd.Timedelta(minutes=i * 60 + m)
            rows.append({"Timestamp": ts, "OpenPrice": o, "HiPrice": h, "LowPrice": low, "ClosePrice": close,
                         "TotalQty": qty, "Trades": 10, "BuyQty": qty * (0.8 if invert else 0.2),
                         "SellQty": qty * (0.2 if invert else 0.8), "OpenInterest": 1000.0, "FundingRate": 0.0,
                         "LiqBuyQty": 0.0, "LiqSellQty": 0.0, "DataQuality": "RAW"})
    return pd.DataFrame(rows)


def signal(direction: str = "SHORT") -> dict:
    return {"candidate_id": "control", "family": "SELLER_DOMINANCE_RETEST_DOWN" if direction == "SHORT" else "DEMAND_SWEEP_RECLAIM_UP",
            "direction": direction, "accepted": True, "available_at": "2026-03-02T00:00:00Z",
            "decision_at": "2026-03-02T00:00:00Z", "entry_open_at": "2026-03-02T00:01:00Z",
            "state_end": "2026-03-02T00:00:00Z", "flow_end": "2026-03-02T00:00:00Z",
            "source_level_available_at": "2026-03-01T00:00:00Z", "target_level_available_at": "2026-03-01T00:00:00Z",
            "decision_price": 100.0, "stop_price": 101.0 if direction == "SHORT" else 99.0,
            "target_price": 98.0 if direction == "SHORT" else 102.0,
            "sweep_at": "" if direction == "SHORT" else "2026-03-01T23:00:00Z", "sweep_low": 99.0, "sweep_high": 101.0}


def replay_feed() -> pd.DataFrame:
    f = feed_control().iloc[:5].copy()
    f["Timestamp"] = pd.date_range("2026-03-02T00:01:00Z", periods=5, freq="min")
    return f


def test_close_labeled_hour_excludes_next_hour_and_incomplete_confirmation():
    f = feed_control().iloc[:61]
    bars = closed_bars(f, 60)
    assert bars.timestamp.tolist() == [pd.Timestamp("2026-03-01T01:00:00Z"), pd.Timestamp("2026-03-01T02:00:00Z")]
    assert bars.completed.tolist() == [True, False]
    engine = CausalSignalEngine(f, config())
    engine.advance_until(f.Timestamp.max())
    assert len(engine.timeline) == 1


@pytest.mark.parametrize("invert,family", [(False, "SUPPLY_SWEEP_RECLAIM_DOWN"), (True, "DEMAND_SWEEP_RECLAIM_UP")])
def test_causal_controls_produce_sequence_candidates_with_available_evidence(invert, family):
    engine = CausalSignalEngine(feed_control(invert), config())
    engine.advance_until("2026-03-02T16:00:00Z")
    decisions, timeline = engine.frames()
    rows = decisions[(decisions.family == family) & decisions.accepted]
    assert not rows.empty
    for row in rows.to_dict("records"):
        validate_signal(row, config())
        assert pd.Timestamp(row["decision_at"]) > pd.Timestamp(row["sweep_at"])
    assert pd.to_datetime(timeline.prefix_last_close, utc=True).le(pd.to_datetime(timeline.decision_at, utc=True)).all()
    assert not timeline.filter(like="_reset").to_numpy().any()


def test_retest_control_and_prefix_extension_and_chunk_invariance():
    c, f = config(), feed_control()
    original = CausalSignalEngine(f, c)
    original.advance_until(f.Timestamp.max())
    decisions, timeline = original.frames()
    assert ((decisions.family == "SELLER_DOMINANCE_RETEST_DOWN") & decisions.accepted).any()
    extra = feed_control(hours=44).iloc[len(f):].copy()
    extra[["OpenPrice", "HiPrice", "LowPrice", "ClosePrice"]] *= 10
    changed = CausalSignalEngine(pd.concat([f, extra], ignore_index=True), c)
    changed.advance_until(f.Timestamp.max())
    pd.testing.assert_frame_equal(decisions, changed.frames()[0])
    pd.testing.assert_frame_equal(timeline, changed.frames()[1])
    split = CausalSignalEngine(f, c)
    split.advance_until("2026-03-02T00:00:00Z")
    split.advance_until(f.Timestamp.max())
    pd.testing.assert_frame_equal(decisions, split.frames()[0])
    pd.testing.assert_frame_equal(timeline, split.frames()[1])


def test_degraded_flow_cannot_admit_even_when_price_pattern_matches():
    f = feed_control()
    f.loc[f.Timestamp.eq(pd.Timestamp("2026-03-02T10:30:00Z")), "DataQuality"] = "RECOVERED_DEGRADED"
    engine = CausalSignalEngine(f, config())
    engine.advance_until(f.Timestamp.max())
    decisions, _ = engine.frames()
    if not decisions.empty:
        assert not decisions.accepted.any()


def test_qualified_opposing_penetration_blocks_short_retest():
    f = feed_control()
    f.loc[f.Timestamp.between(pd.Timestamp("2026-03-02T13:01:00Z"), pd.Timestamp("2026-03-02T14:00:00Z")), "LowPrice"] = 96.0
    engine = CausalSignalEngine(f, config())
    engine.advance_until(f.Timestamp.max())
    decisions, _ = engine.frames()
    rows = decisions[(decisions.family == "SELLER_DOMINANCE_RETEST_DOWN") & decisions.decision_at.eq("2026-03-02T14:00:00+00:00")]
    assert not rows.empty and not rows.accepted.any()
    assert rows.rejection_reasons.str.contains("COUNTER_SWEEP_CONFLICT").all()


@pytest.mark.parametrize("field", ["state_end", "flow_end", "source_level_available_at", "target_level_available_at"])
def test_adapter_rejects_later_evidence(field):
    row = signal()
    row[field] = "2026-03-02T23:59:00Z"
    with pytest.raises(ValueError, match="Unavailable evidence"):
        validate_signal(row, config())


def test_rejects_stop_inside_sweep_and_same_bar_reclaim():
    row = signal("LONG")
    row["stop_price"] = 99.5
    with pytest.raises(ValueError, match="inside sweep"):
        validate_signal(row, config())
    row = signal("LONG")
    row["sweep_at"] = row["decision_at"]
    with pytest.raises(ValueError, match="next 1-3"):
        validate_signal(row, config())


@pytest.mark.parametrize("direction", ["LONG", "SHORT"])
def test_costs_charge_both_fills_and_break_even_is_net_loss(direction):
    result = apply_costs(100, 100, 1, direction, 1, config()["cost_scenarios"][1])
    assert result["gross_R"] == 0
    assert result["net_R"] == pytest.approx(-0.141)


def test_entry_clock_same_minute_collision_and_single_family_position():
    f = replay_feed()
    f.loc[f.Timestamp.eq(pd.Timestamp("2026-03-02T00:02:00Z")), ["HiPrice", "LowPrice"]] = [102, 97]
    row = signal()
    duplicate_time = copy.deepcopy(row)
    duplicate_time["candidate_id"] = "second"
    ledger, admissions = replay_signals(f, pd.DataFrame([row, duplicate_time]), config())
    assert len(ledger) == 3
    assert ledger.entry_raw_close_label.eq("2026-03-02T00:02:00+00:00").all()
    assert ledger.exit_reason.eq("STOP").all()
    assert ledger.same_minute_collision.all()
    assert ledger.loc[ledger.cost_scenario.eq("ZERO_COST_DIAGNOSTIC"), "net_R"].iloc[0] == -1
    assert admissions.reason.eq("FAMILY_POSITION_ALREADY_OPEN").sum() == 1


def test_gap_stop_uses_worse_open_and_missing_data_is_censored():
    f = replay_feed()
    f.loc[f.Timestamp.eq(pd.Timestamp("2026-03-02T00:03:00Z")), ["OpenPrice", "HiPrice", "LowPrice", "ClosePrice"]] = [102, 102.2, 101.8, 102]
    ledger, _ = replay_signals(f, pd.DataFrame([signal()]), config())
    assert ledger.exit_reason.eq("STOP_GAP_AT_OPEN").all()
    assert ledger.gross_R.eq(-2).all()
    gapped = replay_feed().drop(index=[2, 3]).reset_index(drop=True)
    ledger, _ = replay_signals(gapped, pd.DataFrame([signal()]), config())
    assert ledger.censored.all()
    assert ledger.exit_reason.eq("UNRESOLVED_DATA_GAP_OR_DEGRADED").all()
    assert summarize(ledger).resolved.eq(0).all()


@pytest.mark.parametrize("kind", ["missing", "synthetic"])
@pytest.mark.parametrize("hole_at", ["2026-03-02T10:30:00Z", "2026-03-01T20:30:00Z", "2026-03-01T22:30:00Z"])
def test_single_bad_minute_does_not_block_signal_families_or_reset_history(kind, hole_at):
    clean = feed_control()
    changed = clean.copy()
    affected = changed.Timestamp.eq(pd.Timestamp(hole_at))
    if kind == "missing":
        changed = changed.loc[~affected].reset_index(drop=True)
    else:
        changed["IsSynthetic"] = 0
        changed.loc[affected, "IsSynthetic"] = 1
        changed.loc[affected, "DataQuality"] = "RECOVERED_DEGRADED"
        changed.loc[affected, ["OpenPrice", "HiPrice", "LowPrice", "ClosePrice", "TotalQty"]] = 1000000
    original, revised = CausalSignalEngine(clean, config()), CausalSignalEngine(changed, config())
    for engine in [original, revised]:
        engine.advance_until(clean.Timestamp.max())
    a, b = original.frames()[0], revised.frames()[0]
    columns = ["family", "decision_at", "source_level_id"]
    pd.testing.assert_frame_equal(a.loc[a.accepted, columns].reset_index(drop=True), b.loc[b.accepted, columns].reset_index(drop=True))
    assert not revised.frames()[1].filter(like="_reset").to_numpy().any()
    assert b.loc[b.accepted, "context_omitted_minutes"].eq(1).any()
    assert not b.loc[b.accepted, "rejection_reasons"].str.contains("EXTENDED_GAP").any()


def test_missing_hour_boundary_waits_for_next_real_close_without_future_leak():
    clean = feed_control()
    end = pd.Timestamp("2026-03-02T13:00:00Z")
    changed = clean.loc[clean.Timestamp.ne(end)].reset_index(drop=True)
    prefix = changed.loc[changed.Timestamp <= end].copy()
    a, b = CausalSignalEngine(prefix, config()), CausalSignalEngine(changed, config())
    a.advance_until(end)
    b.advance_until(end)
    for x, y in zip(a.frames(), b.frames()):
        pd.testing.assert_frame_equal(x, y)
    b.advance_until(end + pd.Timedelta(minutes=1))
    decisions, timeline = b.frames()
    delayed = timeline[timeline.h1_close_at.eq(end.isoformat())]
    assert len(delayed) == 1 and delayed.decision_at.iloc[0] == (end + pd.Timedelta(minutes=1)).isoformat()
    assert delayed.h1_usable.iloc[0] and delayed.h1_omitted_minutes.iloc[0] == 1
    for row in decisions[decisions.accepted].to_dict("records"):
        validate_signal(row, config())


@pytest.mark.parametrize("kind", ["missing", "synthetic"])
def test_single_minute_during_trade_continues_to_next_real_bar(kind):
    f = replay_feed()
    f.loc[f.Timestamp.eq(pd.Timestamp("2026-03-02T00:05:00Z")), "LowPrice"] = 97.9
    if kind == "missing":
        f = f.loc[f.Timestamp.ne(pd.Timestamp("2026-03-02T00:03:00Z"))].reset_index(drop=True)
    else:
        f["IsSynthetic"] = 0
        f.loc[f.Timestamp.eq(pd.Timestamp("2026-03-02T00:03:00Z")), "IsSynthetic"] = 1
        f.loc[f.Timestamp.eq(pd.Timestamp("2026-03-02T00:03:00Z")), "HiPrice"] = 500
    ledger, _ = replay_signals(f, pd.DataFrame([signal()]), config())
    assert not ledger.censored.any()
    assert ledger.exit_reason.eq("TARGET").all()
    assert ledger.trade_omitted_minutes.eq(1).all()
    assert ledger.gross_R.eq(2).all()
    assert summarize(ledger).single_minute_omissions.eq(1).all()


@pytest.mark.parametrize("kind", ["missing", "synthetic"])
def test_single_bad_entry_minute_uses_next_real_open_with_actual_timestamp(kind):
    f = replay_feed()
    f.loc[f.Timestamp.eq(pd.Timestamp("2026-03-02T00:05:00Z")), "LowPrice"] = 97.9
    if kind == "missing":
        f = f.loc[f.Timestamp.ne(pd.Timestamp("2026-03-02T00:02:00Z"))].reset_index(drop=True)
    else:
        f["IsSynthetic"] = 0
        f.loc[f.Timestamp.eq(pd.Timestamp("2026-03-02T00:02:00Z")), "IsSynthetic"] = 1
    ledger, admission = replay_signals(f, pd.DataFrame([signal()]), config())
    assert admission.admitted.all() and not ledger.censored.any()
    assert ledger.entry_open_at.eq("2026-03-02T00:02:00+00:00").all()
    assert ledger.entry_raw_close_label.eq("2026-03-02T00:03:00+00:00").all()
    assert ledger.entry_omitted_minutes.eq(1).all()


def test_two_consecutive_bad_minutes_remain_distinct_from_single_omission():
    f = feed_control()
    f = f.loc[~f.Timestamp.isin(pd.date_range("2026-03-02T10:30:00Z", periods=2, freq="min"))].reset_index(drop=True)
    engine = CausalSignalEngine(f, config())
    engine.advance_until(f.Timestamp.max())
    assert not engine.frames()[0].accepted.any()


def test_expiry_uses_exact_elapsed_time_and_tail_is_not_counted_as_profit():
    initial = replay_feed().iloc[[0]]
    f = pd.concat([initial] * 2881, ignore_index=True)
    f["Timestamp"] = pd.date_range("2026-03-02T00:01:00Z", periods=len(f), freq="min")
    ledger, _ = replay_signals(f, pd.DataFrame([signal()]), config())
    assert ledger.exit_reason.eq("EXPIRY").all()
    assert ledger.exit_at.eq("2026-03-04T00:01:00+00:00").all()
    ledger, _ = replay_signals(replay_feed(), pd.DataFrame([signal()]), config())
    assert ledger.exit_reason.eq("UNRESOLVED_END_OF_FEED").all()
    assert ledger.net_R.isna().all()


def test_missing_expiry_minute_does_not_capture_a_later_target():
    initial = replay_feed().iloc[[0]]
    f = pd.concat([initial] * 2882, ignore_index=True)
    f["Timestamp"] = pd.date_range("2026-03-02T00:01:00Z", periods=len(f), freq="min")
    expiry = pd.Timestamp("2026-03-04T00:01:00Z")
    f = f.loc[f.Timestamp.ne(expiry)].reset_index(drop=True)
    f.loc[f.Timestamp.eq(expiry + pd.Timedelta(minutes=1)), "LowPrice"] = 90
    ledger, _ = replay_signals(f, pd.DataFrame([signal()]), config())
    assert ledger.exit_reason.eq("EXPIRY_AFTER_SINGLE_MINUTE_SKIP").all()
    assert ledger.exit_at.eq(expiry.isoformat()).all()
    assert ledger.gross_R.eq(0).all()


def test_wrong_side_fill_is_rejected_and_zero_signal_files_have_headers():
    f = replay_feed()
    f.loc[f.Timestamp.eq(pd.Timestamp("2026-03-02T00:02:00Z")), "OpenPrice"] = 102
    ledger, admission = replay_signals(f, pd.DataFrame([signal()]), config())
    assert ledger.empty and "net_R" in ledger
    assert admission.reason.eq("ENTRY_GEOMETRY_FAILED").all()
    ledger, admission = replay_signals(f, pd.DataFrame(), config())
    assert "net_R" in ledger and "reason" in admission
    summary = summarize(ledger, config())
    assert len(summary) == 9 and summary.sample_status.eq("NO_TRADES").all()


def test_read_sources_selects_recovery_only_in_outage_and_preserves_files(tmp_path):
    for folder in ["feed", "feed_recovered"]:
        (tmp_path / folder).mkdir()
    columns = {"Open": 100, "High": 101, "Low": 99, "Close": 100, "Volume": 1, "AggTrades": 1,
               "BuyQty": 0.5, "SellQty": 0.5, "OpenInterest": 1000, "FundingRate": 0, "LiqBuyQty": 0, "LiqSellQty": 0, "IsSynthetic": 0}
    rows = [{"Timestamp": str(ts), **columns} for ts in pd.date_range("2026-04-23T17:04:00Z", periods=4, freq="min")]
    a, b = tmp_path / "feed/2026-04-23.csv", tmp_path / "feed_recovered/2026-04-23.csv"
    pd.DataFrame(rows).to_csv(a, index=False)
    recovered = pd.DataFrame(rows)
    recovered["Close"] = 100.5
    recovered.to_csv(b, index=False)
    before = digest(a), digest(b)
    selected, _ = read_sources(tmp_path, "2026-04-23T17:04:00Z", "2026-04-23T17:07:00Z")
    assert selected.ClosePrice.tolist() == [100, 100.5, 100.5, 100.5]
    assert selected.DataQuality.tolist() == ["RAW", "RECOVERED_DEGRADED", "RECOVERED_DEGRADED", "RECOVERED_DEGRADED"]
    assert (digest(a), digest(b)) == before
    pd.concat([pd.DataFrame(rows), pd.DataFrame(rows[:1])], ignore_index=True).to_csv(a, index=False)
    with pytest.raises(ValueError, match="duplicate or unordered"):
        read_sources(tmp_path, "2026-04-23T17:04:00Z", "2026-04-23T17:07:00Z")
