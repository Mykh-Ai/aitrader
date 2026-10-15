"""User-authorized frozen archive replay and predeclared source comparisons."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import subprocess
import sys

import numpy as np
import pandas as pd

from frozen_adapter import (OUT, ROOT, OLD, SOURCE, START, END, OLD_END, WARMUP, sha, save,
                            load_kernel, calendar_adapter, install_calendar, precise_data_class,
                            classify, verdict, authorize_first_replay)
from reporting import metrics, monthly, at_cutoff, verify_paths, markdown

MATCH_START = pd.Timestamp("2026-03-11T13:45:00Z")
MATCH_ENTRY_START = pd.Timestamp("2026-03-18T14:00:00Z")


def archive_records():
    records = []
    for folder, file in [(OUT, "source_context_manifest.json"), (SOURCE, "source_manifest.json"),
                         (OUT, "extension_source_manifest.json"), (OLD, "source_manifest.json")]:
        for item in json.loads((folder / file).read_text())["archives"]:
            if folder == SOURCE and item["date"] == "2025-01-31":
                continue  # Replaced by the complete, earlier January monthly source.
            record = dict(item)
            record["absolute_path"] = str(folder / record["archive_path"])
            records.append(record)
    assert len(records) == len({r["filename"] for r in records}) == 65
    return sorted(records, key=lambda row: row["first_exchange_open"])


def freeze():
    kernel = load_kernel()
    selected = kernel.identity()
    fn, text, evidence = calendar_adapter(kernel.hybrid_signals.__globals__["signals"])
    (OUT / "calendar_signal_adapter.py").write_text(text, encoding="utf-8", newline="\n")
    save("calendar_adapter_evidence.json", evidence)
    sources = archive_records()
    for row in sources:
        path = Path(row["absolute_path"])
        expected, name = path.with_name(path.name + ".CHECKSUM").read_text().split()[:2]
        assert expected == row["local_sha256"] == sha(path) and name.lstrip("*") == path.name
    identity_files = [OLD / "research_kernel.py", OLD / "parity_gate.json", OLD / "frozen_identity_verification.json",
                      SOURCE / "run_manifest.json", SOURCE / "source_manifest.json", SOURCE / "normalized_inventory.csv",
                      ROOT / "research/active_own_signal_selection.json", ROOT / "research/latest_own_signal_replay.json",
                      ROOT / "market_monitor_runs/SHI_RESET_40L_chronological_replay_through_2026_10_14_v0/closed_trade_ledger_usdc.csv"]
    for name in ["source_context_plan.json", "source_context_manifest.json", "extension_source_plan.json", "extension_source_manifest.json"]:
        identity_files.append(OUT / name)
    manifest = {
        "task": "SHI_RESET_40Q_FROZEN_ARCHIVE_REPLAY_V0", "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "starting_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip(),
        "user_authorized_archive_diagnostic_after_parity_warning": True,
        "user_requests": ["Ну шо, запускай.", "Булоб добре прогон на данних бінанс зробити до 14.10.2026 заоазом порівняємо всі місяці які пройшли SHA feed."],
        "source_parity_accepted": False, "40O_verdict_preserved": "BINANCE_KLINE_SURROGATE_PARITY_FAILED",
        "scope": "New source-specific research diagnostic; not a passed40O OOS validation or source equivalence claim",
        "strategy_version": selected["version"], "selected_variant": selected["selected_variant"],
        "rules_sha256": selected["rules_sha256"], "filter_manifest_sha256": selected["filter_manifest_sha256"],
        "strategy_count": 1, "optimization_allowed": False, "variant_search_allowed": False,
        "financial_result_attempts": 1, "predeclared_books": [
            "CONTINUOUS_BINANCE: all archive history; Jan2025warmup; entries March2025 through Oct14 2026; date-neutral admission",
            "MATCHED_BINANCE: same SHI history start and40L calendar; Binance signals; Binance execution proxy",
            "MATCHED_SHI: same SHI history start and40L calendar; SHI signals; identical Binance execution proxy"],
        "books_are_source_comparisons_not_strategy_variants": True,
        "no_selection_between_books": True, "continuous_book_is_primary": True,
        "warmup_start": str(WARMUP), "entry_start": str(START), "end": str(END),
        "older_interval_end": str(OLD_END), "older_interval_exits_after_end_not_scored": True,
        "warmup_extension_reason": "Frozen H4 inventory max age30days plus delayed confirmation exceeds February's28days; January added before outcomes",
        "matched_history_start": str(MATCH_START), "matched_calendar": "unchanged40L exclusions; October admitted",
        "execution_market": "FUTURES_PRICE_PROXY", "signal_symbol": "BTCUSDT_USD_M_PERPETUAL",
        "notional": 3000, "completed_trade_fee": 5, "adverse_slippage_bps_per_fill": 2,
        "entry_latency_minutes": 1, "cooldown_minutes": 3, "one_position_per_book": True,
        "stop_first_intraminute": True, "hold_hours": 168, "LONG_target_R": 10, "SHORT_target_R": 6,
        "data_gap_policy": "Frozen CENSOR; skip isolated missing/nontraded minute with actualUTC; extended gaps retained as unresolved evidence",
        "tail_policy": "No forced close/future tail; open and censored rows retained separately with no realized profit credit",
        "precise_entry_adapter": "Same entry tuple p/time/open; entry-minute-only auxiliary OHLC replaces unused future first-hour aggregates; 40L final-H1 admission retained",
        "causality_prefixes": ["2025-06-30T12:30:00Z", "2026-07-15T12:30:00Z"],
        "financial_criteria": {"completed_minimum": 12, "net_gt": 0, "profit_factor_ge": 1.25,
                               "net_excluding_best_two_gt": 0, "no_data_censored_trades": True},
        "financial_pass_cannot_accept_source_parity_or_production": True,
        "calendar_adapter_evidence": evidence,
        "baseline_spec": selected["baseline_contract"]["futures_signal_baseline"],
        "input_manifest_hashes": {p.relative_to(ROOT).as_posix(): sha(p) for p in identity_files},
        "frozen_snapshot_code_hashes": kernel.executed_hashes(),
        "task_code_hashes": {p.name: sha(p) for p in sorted(OUT.glob("*.py"))},
        "archive_sources": [{k: v for k, v in row.items() if k != "absolute_path"} | {"path": Path(row["absolute_path"]).relative_to(ROOT).as_posix()} for row in sources],
        "runtime": {"python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__},
        "production_changes": False, "private_API_orders_borrow_deploy": False,
        "market_state_reset": False, "H4_state_reset": False, "book_reset_within_each_declared_cohort": False,
    }
    assert not (OUT / "run_manifest.json").exists(), "USE_A_VERSIONED_SUCCESSOR"
    save("run_manifest.json", manifest)
    print("Frozen before returns: one40H strategy; three declared source-comparison books;65official archives", flush=True)


def verify_manifest():
    manifest = json.loads((OUT / "run_manifest.json").read_text())
    for name, digest in manifest["task_code_hashes"].items():
        assert sha(OUT / name) == digest, f"TASK_CODE_CHANGED: {name}"
    for name, digest in manifest["input_manifest_hashes"].items():
        assert sha(ROOT / name) == digest, f"PRIOR_IDENTITY_CHANGED: {name}"
    for name, digest in manifest["frozen_snapshot_code_hashes"].items():
        assert sha(OLD / "frozen_snapshot" / name) == digest, name
    assert manifest["end"] == str(END) and manifest["entry_start"] == str(START)
    assert not (OLD / "parity_acceptance.json").exists() and not (OLD / "first_oos_attempt.json").exists()
    return manifest


def known_control(kernel):
    feed, spot, bars, _, data, space, original, spec, _ = kernel.load()
    f = kernel.entry_metrics(feed, bars, original, np.flatnonzero(original), spec)
    final, _ = kernel.filtered_directions(space, f, kernel.RULES)
    adapted_data = precise_data_class(kernel)(data.feed, data.bars)
    control = kernel.replay_hybrid(adapted_data, final, spec["long"], spec["short"])
    saved = pd.read_csv(kernel.H / "selected_trade_ledger_usdc.csv")
    for col in ["decision_at", "entry_at", "exit_at", "expiry_at"]:
        saved[col] = pd.to_datetime(saved[col], utc=True)
    pd.testing.assert_frame_equal(control, saved[control.columns], check_exact=False, rtol=1e-10, atol=1e-10)
    assert len(control) == 13 and abs(control.net_usd.sum() - 1090.8118508490645) < 1e-8
    for i in np.flatnonzero(final):
        before, after = data.entry(i), adapted_data.entry(i)
        assert before is None and after is None or before[:3] == after[:3]
    save("known_control_verification.json", {"original40H13trades_reproduced": True,
        "original_control_net_usdc": float(control.net_usd.sum()), "precise_entry_time_price_unchanged": True,
        "unused_future_hour_aggregates_not_read_by_adapter": True})


def load_archives(manifest):
    spec = importlib.util.spec_from_file_location("40Q_read_archive", OLD / "archive_source.py")
    api = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api)
    parts = []
    for number, row in enumerate(manifest["archive_sources"], 1):
        path = ROOT / row["path"]
        assert sha(path) == row["local_sha256"] == row["binance_checksum_sha256"]
        frame = api.read_kline_zip(path)
        frame["SourceFile"] = row["path"]
        parts.append(frame)
        if number % 15 == 0:
            print(f"Normalized official sources {number}/65", flush=True)
    feed = pd.concat(parts, ignore_index=True).sort_values("Timestamp").reset_index(drop=True)
    feed = feed.loc[feed.Timestamp.between(WARMUP, END)].reset_index(drop=True)
    assert not feed.Timestamp.duplicated().any()
    expected = pd.date_range(WARMUP, END, freq="min")
    assert pd.DatetimeIndex(feed.Timestamp).equals(expected), "ARCHIVE_GRID_NOT_COMPLETE"
    folder = OUT / "normalized_futures_feed"
    folder.mkdir(exist_ok=True)
    inventory = []
    for day, group in feed.groupby(feed.Timestamp.dt.strftime("%Y-%m-%d")):
        path = folder / f"{day}.csv"
        group.to_csv(path, index=False, lineterminator="\n")
        inventory.append({"date": day, "file": path.relative_to(OUT).as_posix(), "rows": len(group),
                          "sha256": sha(path), "nontraded_minutes": int((~group.Traded).sum())})
    pd.DataFrame(inventory).to_csv(OUT / "normalized_inventory.csv", index=False)
    save("normalization_summary.json", {"rows": len(feed), "first": feed.Timestamp.iloc[0], "last": feed.Timestamp.iloc[-1],
        "archives": len(manifest["archive_sources"]), "daily_files": len(inventory), "missing_or_duplicate_minutes": 0,
        "nontraded_minutes": int((~feed.Traded).sum()), "source_parity_accepted": False})
    return feed


def admission(bars, matched):
    if not matched:
        return bars.available_at.between(START, END).to_numpy()
    allowed = bars.timestamp.ge(MATCH_ENTRY_START)
    for start, end in [("2026-04-23T17:05:00Z", "2026-05-10T00:00:00Z"),
                       ("2026-06-22T00:00:00Z", "2026-06-29T00:00:00Z"),
                       ("2026-08-25T00:00:00Z", "2026-09-01T00:00:00Z")]:
        allowed &= ~bars.timestamp.between(pd.Timestamp(start), pd.Timestamp(end), inclusive="left")
    return (allowed & bars.available_at.le(END)).to_numpy()


def pipeline(kernel, feed, spec, matched=False):
    bars = kernel.features(feed)
    raw = kernel.hybrid_signals(bars, spec["long"], spec["short"])
    raw[~admission(bars, matched)] = 0
    data = kernel.ReplayData(feed, bars)
    inventory = kernel.h4_inventory(feed, bars)
    cands, rejected = kernel.candidate_map(data, raw, spec, {"short_space_1r": True}, inventory)
    space = np.zeros_like(raw)
    for i, row in cands.items():
        space[i] = row["side"]
    f = kernel.rolling_inputs(feed, bars.loc[raw != 0], raw)
    final, allowed = kernel.filtered_directions(space, f, kernel.RULES)
    rejection = {row["signal_index"]: row["reason"] for row in rejected}
    f["H4_space_allowed"] = space[f.signal_index.to_numpy(dtype=int)] != 0
    f["delta_rules_allowed"] = allowed
    f["allowed_pre_book"] = final[f.signal_index.to_numpy(dtype=int)] != 0
    reasons, estimates, references = [], [], []
    for row in f.itertuples():
        i, side = row.signal_index, row.direction
        reason = []
        if not space[i]:
            reason.append(rejection.get(i, "H4_SPACE_REJECTED"))
        if not row.window24_usable:
            reason.append("DELTA24_UNUSABLE")
        elif not abs(row.delta24_pct) < 4:
            reason.append("DELTA24_OUTSIDE_STRICT_BAND4")
        if side > 0 and not (row.window4_usable and row.delta4_pct > 0):
            reason.append("LONG_DELTA4_NOT_POSITIVE_OR_UNUSABLE")
        reasons.append("|".join(reason) if reason else "ALLOWED_PRE_BOOK")
        rules = kernel.ExitRules(**spec["long" if side > 0 else "short"]["exit"])
        estimates.append(kernel.initial_stop(data, i, side, bars.close.iloc[i], rules))
        references.append(cands.get(i, {}).get("reference_available_at", pd.NaT))
    f["blocker_reasons"], f["decision_close_stop_estimate"], f["H4_reference_available_at"] = reasons, estimates, references
    for hours in [4, 24]:
        assert (f[f"window{hours}_last_observation_at"] <= f.decision_at).all()
    bars = bars.copy()
    bars["raw_direction"], bars["final_direction"] = raw, final
    bars["H4_inventory_hash"] = [hashlib.sha256(json.dumps(inventory[i], sort_keys=True, default=str).encode()).hexdigest() for i in range(len(bars))]
    return bars, raw, final, f


def prefix_checks(kernel, feed, spec, full):
    results = []
    bars, raw, final, f = full
    for stamp in [pd.Timestamp("2025-06-30T12:30:00Z"), pd.Timestamp("2026-07-15T12:30:00Z")]:
        prefix = feed.loc[feed.Timestamp.le(stamp)].reset_index(drop=True)
        pb, pr, pf, pm = pipeline(kernel, prefix, spec)
        pd.testing.assert_frame_equal(pb, bars.iloc[:len(pb)].reset_index(drop=True))
        np.testing.assert_array_equal(pr, raw[:len(pb)])
        np.testing.assert_array_equal(pf, final[:len(pb)])
        pd.testing.assert_frame_equal(pm, f.loc[f.signal_index.lt(len(pb))].reset_index(drop=True))
        results.append({"source_prefix_end": stamp, "closed_H1": len(pb), "raw_candidates": len(pm),
                        "features_H4_candidates_gates_stops_identical": True})
    return results


def replay_book(kernel, signals, execution_feed, spec):
    bars, raw, final, candidates = signals
    data = precise_data_class(kernel)(execution_feed, bars)
    trades = kernel.replay_hybrid(data, final, spec["long"], spec["short"])
    if trades.empty:
        columns = ["signal_index", "direction", "decision_at", "entry_at", "entry_price", "stop_price", "target_price",
                   "initial_risk_usd", "target_R", "exit_at", "exit_price", "exit_reason", "gross_usd", "commission_usd",
                   "slippage_usd", "net_usd", "net_R", "censored", "expiry_at", "family"]
        trades = pd.DataFrame(columns=columns)
        for name in ["decision_at", "entry_at", "exit_at", "expiry_at"]:
            trades[name] = pd.to_datetime(trades[name], utc=True)
        for name in ["entry_price", "stop_price", "target_price", "net_usd", "net_R", "initial_risk_usd", "target_R"]:
            trades[name] = trades[name].astype(float)
        trades["censored"] = trades.censored.astype(bool)
    trades = classify(trades)
    trades["direction_label"] = np.where(trades.direction.gt(0), "LONG", "SHORT")
    trades["execution_market"] = "FUTURES_PRICE_PROXY"
    trades["notional_usd_equivalent"] = 3000
    assert trades.entry_at.between(START, END).all()
    checks = verify_paths(trades, data, final)
    failure_times = {row["signal_index"]: row["censor_detected_at"] for row in checks}
    trades["censor_detected_at"] = pd.to_datetime(trades.signal_index.map(failure_times), utc=True)
    return trades, checks


def execute():
    manifest = verify_manifest()
    assert not (OUT / "first_replay_attempt.json").exists(), "FIRST_RESULT_ALREADY_ATTEMPTED_NO_SEARCH"
    kernel = load_kernel()
    known_control(kernel)
    install_calendar(kernel)
    spec = manifest["baseline_spec"]
    feed = load_archives(manifest)
    print("Archive UTC grid complete; building uninterrupted frozen signals", flush=True)
    full = pipeline(kernel, feed, spec)
    full[0].to_csv(OUT / "continuous_feature_state.csv", index=False)
    full[3].to_csv(OUT / "oos_candidates.csv", index=False)
    print("Full signals built; checking future-append invariance before financial results", flush=True)
    prefixes = prefix_checks(kernel, feed, spec, full)
    archive_match = feed.loc[feed.Timestamp.ge(MATCH_START)].reset_index(drop=True)
    print("Prefix checks passed; reconstructing matched SHI/Binance source cohorts", flush=True)
    shi, source_inventory = kernel.read_sources(ROOT, str(MATCH_START), str(END))
    source_inventory.to_csv(OUT / "SHI_source_inventory.csv", index=False)
    matched_archive = pipeline(kernel, archive_match, spec, matched=True)
    matched_shi = pipeline(kernel, shi, spec, matched=True)
    # Compare the common 40L calendar directly to its immutable original helper.
    path = ROOT / "market_monitor_runs/SHI_RESET_40L_chronological_replay_through_2026_10_14_v0/policy.py"
    module_spec = importlib.util.spec_from_file_location("frozen40L_calendar_control", path)
    control_policy = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(control_policy)
    for state in [matched_archive, matched_shi]:
        expected = control_policy.hybrid_signals(state[0], spec["long"], spec["short"])
        np.testing.assert_array_equal(expected, state[1])
    save("causality_checks.json", {"status": "PASS", "real_prefix_results": prefixes,
         "all_feature_windows_end_at_decision": True, "H4_confirmations_available_by_decision": True,
         "matched_raw_signals_equal_immutable40L_calendar_helper": True,
         "precise_entry_helper_does_not_read_future_hour_path": True,
         "source_timestamp": "exchangeopen+60s right-close", "future_leakage_detected": False,
         "source_parity_accepted": False, "financial_returns_read_before_checks": False})
    # Freeze actual SHI source bytes and executed identities before the first return.
    sources = source_inventory.loc[source_inventory.status.eq("READ")]
    save("execution_manifest.json", {"run_manifest_sha256": sha(OUT / "run_manifest.json"),
         "SHI_source_hashes": dict(zip(sources.path, sources.sha256)),
         "frozen_executed_code_hashes": kernel.executed_hashes(),
         "task_code_hashes": manifest["task_code_hashes"], "strategy_count": 1,
         "predeclared_books": manifest["predeclared_books"], "no_optimization": True})
    authorize_first_replay(manifest)
    print("Causality/control/identity checks passed; executing the three predeclared source books once", flush=True)
    all_books, path_checks = {}, {}
    for name, state, prices in [("continuous_binance", full, feed),
                                 ("matched_binance", matched_archive, archive_match),
                                 ("matched_SHI", matched_shi, archive_match)]:
        trades, checked = replay_book(kernel, state, prices, spec)
        trades.to_csv(OUT / f"{name}_trades.csv", index=False)
        state[3].to_csv(OUT / f"{name}_candidates.csv", index=False)
        monthly(trades, START if name == "continuous_binance" else MATCH_ENTRY_START, END).to_csv(OUT / f"{name}_monthly.csv", index=False)
        all_books[name], path_checks[name] = trades, checked
    trades = all_books["continuous_binance"]
    trades.to_csv(OUT / "oos_trades.csv", index=False)
    table = monthly(trades, START, END)
    table.to_csv(OUT / "oos_monthly_summary.csv", index=False)
    primary = metrics(trades)
    primary["raw_candidates"] = len(full[3])
    primary["policy_gate_passing_candidates"] = int(np.count_nonzero(full[2]))
    days = (END - START + pd.Timedelta(minutes=1)).total_seconds() / 86400
    primary["signal_frequency"] = {"calendar_days": days, "raw_per30days": len(full[3]) / days * 30,
         "gate_passing_per30days": np.count_nonzero(full[2]) / days * 30, "entries_per30days": len(trades) / days * 30}
    earlier = at_cutoff(trades, OLD_END)
    earlier.to_csv(OUT / "older_interval_trades_to_2026_03_09.csv", index=False)
    earlier_metrics = metrics(earlier)
    earlier_metrics["raw_candidates"] = int(full[3].decision_at.le(OLD_END).sum())
    earlier_metrics["policy_gate_passing_candidates"] = int(np.count_nonzero(full[2][full[0].available_at.le(OLD_END)]))
    status = verdict(primary["completed_trades"], primary["net_usd"], primary["profit_factor"],
                     primary["net_excluding_best_2_usd"], primary["data_censored"])
    older_status = verdict(earlier_metrics["completed_trades"], earlier_metrics["net_usd"], earlier_metrics["profit_factor"],
                           earlier_metrics["net_excluding_best_2_usd"], earlier_metrics["data_censored"])
    result = {"status": status, "execution_market": "FUTURES_PRICE_PROXY", "source_parity_accepted": False,
              "continuous_archive": primary, "older_interval_end": str(OLD_END), "older_interval": earlier_metrics,
              "older_interval_verdict": older_status, "source_comparison": {name: metrics(value) for name, value in all_books.items() if name != "continuous_binance"},
              "40O_verdict_unchanged": "BINANCE_KLINE_SURROGATE_PARITY_FAILED", "production_promoted": False}
    save("oos_metrics.json", result)
    comparisons = []
    published = pd.read_csv(ROOT / "market_monitor_runs/SHI_RESET_40L_chronological_replay_through_2026_10_14_v0/closed_trade_ledger_usdc.csv")
    published["entry_at"] = pd.to_datetime(published.entry_at, utc=True)
    published["month"] = published.entry_at.dt.strftime("%Y-%m")
    for stamp in pd.date_range("2026-03-01", "2026-10-01", freq="MS"):
        month = stamp.strftime("%Y-%m")
        row = {"month": month}
        for name, book in all_books.items():
            group = book.loc[book.entry_at.dt.strftime("%Y-%m").eq(month)]
            m = metrics(group)
            row[f"{name}_entries"], row[f"{name}_net_proxy_usd"] = len(group), m["net_usd"]
        old = published.loc[published.month.eq(month)]
        row["published40L_spot_entries"], row["published40L_spot_net_usdc"] = len(old), float(old.net_usd.sum())
        comparisons.append(row)
    comparison = pd.DataFrame(comparisons)
    comparison.to_csv(OUT / "monthly_source_comparison.csv", index=False)
    parity = matched_shi[0][["timestamp", "raw_direction", "final_direction"]].merge(
        matched_archive[0][["timestamp", "raw_direction", "final_direction"]], on="timestamp", how="outer", suffixes=("_SHI", "_binance"), indicator=True)
    parity["decision_equal"] = parity.raw_direction_SHI.eq(parity.raw_direction_binance) & parity.final_direction_SHI.eq(parity.final_direction_binance)
    parity.to_csv(OUT / "matched_candidate_parity.csv", index=False)
    closed = trades.loc[trades.status_at_cutoff.eq("CLOSED")]
    distribution = pd.cut(closed.net_R, [-np.inf, -2, -1, -.5, 0, 1, 2, 4, 6, 10, np.inf]).value_counts(sort=False)
    pd.DataFrame({"net_R_interval": distribution.index.astype(str), "trades": distribution.to_numpy()}).to_csv(OUT / "R_outcome_distribution.csv", index=False)
    save("independent_path_checks.json", {"status": "PASS", "books": path_checks})
    verify_manifest()
    assert all(sha(ROOT / r.path) == r.sha256 for r in sources.itertuples())
    save("code_hashes.json", {"executed_frozen_snapshot": kernel.executed_hashes(), "40Q_tooling": manifest["task_code_hashes"]})
    lines = ["# 40Q frozen Binance archive replay", "", f"Verdict: **{status}**. Source parity remains failed; this is a source-specific diagnostic, not accepted40O validation.", "",
        f"Primary: {START} through {END}; Jan2025 technical warmup. One frozen40H strategy, $3000/trade, $5 completed-trade fee, 2bps/fill, FUTURES_PRICE_PROXY.", "",
        f"Completed {primary['completed_trades']}, wins/losses {primary['wins']}/{primary['losses']}; net **${primary['net_usd']:.2f}**. Gross ${primary['gross_usd']:.2f}, fees ${primary['commission_usd']:.2f}, modeled slippage ${primary['modeled_slippage_usd']:.2f}.",
        f"PF {primary['profit_factor']}; closed-trade DD ${primary['max_closed_trade_drawdown_usd']:.2f}; net without best2 ${primary['net_excluding_best_2_usd']:.2f}. Open {primary['open_at_cutoff']}; data-censored {primary['data_censored']}.", "",
        f"Older interval through March9 2026: {earlier_metrics['completed_trades']} completed, net ${earlier_metrics['net_usd']:.2f}, {older_status}. No later exits credited.", "",
        "## All months — entry-month attribution", "", markdown(table), "",
        "## Matched source comparison", "", "Matched Binance and SHI books share the same 40L calendar/history start and identical Binance futures execution prices. Only the signal source differs. Published40L is separate historical spot-price evidence, not a common-price source comparison.", "", markdown(comparison), "",
        "No rule tuning or book selection. Original40H/40L research spot results remain separate. Full normalized data and source paths/hashes are retained locally. No live/API/Executor/production changes. Source equivalence remains unresolved; this task does not approve server shadow or live trading.", ""]
    (OUT / "result.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(json.dumps({"verdict": status, "continuous_archive": primary, "older_interval": earlier_metrics,
                      "matched_source_comparison": result["source_comparison"]}, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["freeze", "execute"])
    globals()[parser.parse_args().phase]()
