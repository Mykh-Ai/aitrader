"""New research diagnostic contracts; no historical strategy result in tests."""
import ast
import importlib.util
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "market_monitor_runs/SHI_RESET_40Q_frozen_archive_replay_v0"


def module(name):
    spec = importlib.util.spec_from_file_location("test40Q_" + name, RUN / f"{name}.py")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


adapter = module("frozen_adapter")
reporting = module("reporting")


def frozen_signal_function():
    path = adapter.OLD / "frozen_snapshot/research/strategy_search/features.py"
    tree = ast.parse(path.read_text())
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "signals")
    namespace = {"pd": pd, "np": np}
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(path), "exec"), namespace)
    return namespace["signals"]


@pytest.mark.parametrize("family,lookback,flow,trend", [("TREND_RETEST", 96, .04, "EMA"), ("ACCEPTED_BREAK", 48, 0., "PRESSURE")])
def test_date_only_adapter_preserves_frozen_conditions_under_clock_translation(family, lookback, flow, trend):
    frozen = frozen_signal_function()
    new, _, evidence = adapter.calendar_adapter(frozen)
    frame = pd.DataFrame({"timestamp": pd.date_range("2026-07-01", periods=240, freq="h", tz="UTC"),
        "close": 101., "open": 100., "high": 102., "low": 99., "ema24": 100., "ema72": 99., "ema168": 98.,
        "context_usable": True, "usable": True, "volume_ratio": 1.5, "delta": .05, "change24": -.01, "delta24": -.01,
        "upper96": 110., "lower96": 90., "upper48": 110., "lower48": 102.})
    if family == "ACCEPTED_BREAK":
        frame["delta"] = -.05
        frame.loc[:99, "close"] = 103.
        frame.loc[:99, "high"] = 104.
    original = frozen(frame, family, lookback, flow, 1.3, trend)
    translated = frame.copy()
    translated.timestamp -= pd.Timedelta(days=365)
    np.testing.assert_array_equal(original, new(translated, family, lookback, flow, 1.3, trend))
    assert np.count_nonzero(original) > 0
    assert evidence["all_noncalendar_formula_AST_unchanged"] and evidence["removed_count"] == 3


def test_first_diagnostic_attempt_is_not_a_parity_acceptance_and_cannot_repeat(tmp_path, monkeypatch):
    monkeypatch.setattr(adapter, "OUT", tmp_path)
    (tmp_path / "run_manifest.json").write_text("{}")
    manifest = {"user_authorized_archive_diagnostic_after_parity_warning": True, "strategy_count": 1,
                "optimization_allowed": False, "variant_search_allowed": False, "source_parity_accepted": False}
    with pytest.raises(AssertionError):
        adapter.authorize_first_replay({**manifest, "optimization_allowed": True})
    adapter.authorize_first_replay(manifest)
    with pytest.raises(FileExistsError):
        adapter.authorize_first_replay(manifest)
    assert not (tmp_path / "parity_acceptance.json").exists()


@pytest.mark.parametrize("completed,net,pf,without,censored,expected", [
    (11, 1000, 2., 200, 0, "ARCHIVE_REPLAY_INSUFFICIENT_SAMPLE"),
    (12, -100, .8, -300, 0, "ARCHIVE_REPLAY_REJECTS_CURRENT_CANDIDATE_ON_THIS_SOURCE"),
    (12, 100, 1.24, 10, 0, "ARCHIVE_REPLAY_REJECTS_CURRENT_CANDIDATE_ON_THIS_SOURCE"),
    (12, 100, 2., -10, 0, "ARCHIVE_REPLAY_REJECTS_CURRENT_CANDIDATE_ON_THIS_SOURCE"),
    (12, 100, 2., 10, 1, "ARCHIVE_REPLAY_INCOMPLETE_DATA"),
    (12, 100, 2., 10, 0, "ARCHIVE_REPLAY_FINANCIAL_CRITERIA_MET_SOURCE_UNVALIDATED"),
])
def test_predeclared_verdict_never_claims_source_parity(completed, net, pf, without, censored, expected):
    assert adapter.verdict(completed, net, pf, without, censored) == expected


def test_earlier_cutoff_never_credits_a_later_target_or_future_censor():
    cutoff = pd.Timestamp("2026-03-09T23:59Z")
    frame = pd.DataFrame({"entry_at": [cutoff - pd.Timedelta(days=1)] * 2,
        "exit_at": [cutoff + pd.Timedelta(hours=1), pd.NaT], "expiry_at": [cutoff + pd.Timedelta(days=6)] * 2,
        "censor_detected_at": [pd.NaT, cutoff + pd.Timedelta(hours=2)],
        "censored": [False, True], "status_at_cutoff": ["CLOSED", "CENSORED_DATA"], "exit_reason": ["TARGET", "CENSORED_DATA"],
        "exit_price": [200., np.nan], "gross_usd": [100., np.nan], "commission_usd": [5., np.nan],
        "slippage_usd": [1., np.nan], "net_usd": [94., np.nan], "net_R": [2., np.nan]})
    result = reporting.at_cutoff(frame, cutoff)
    assert result.status_at_cutoff.eq("OPEN_AT_CUTOFF").all()
    assert result.net_usd.isna().all() and result.exit_at.isna().all()


def test_precise_entry_tuple_ignores_appended_future_extrema():
    class DummyBase:
        pass
    class Kernel:
        ReplayData = DummyBase
    cls = adapter.precise_data_class(Kernel)
    data = cls()
    data.minute = pd.Timedelta(minutes=1).value
    decision = pd.Timestamp("2026-07-01T12:00Z").value
    data.available = np.array([decision])
    data.minute_ts = np.array([decision + 2 * data.minute, decision + 3 * data.minute])
    data.raw = np.array([True, True])
    data.mo, data.mh, data.ml = np.array([100., 100.]), np.array([101., 102.]), np.array([99., 98.])
    data.entries = {}
    before = data.entry(0)
    data.mh[1], data.ml[1] = 1e9, .01
    data.entries = {}
    assert data.entry(0) == before
    assert before[1] == decision + data.minute and before[2] == 100.
