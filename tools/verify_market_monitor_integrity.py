"""Independent source/prefix verification of canonical Monitor entry points.

Writes only local_runs/. No detector, scoring model, outcomes or data repair.
Run with --cutoff for an independently truncated historical reconstruction.
"""
from __future__ import annotations

import argparse
from datetime import date, timedelta
import hashlib
import json
from pathlib import Path
import sys
import time
import ast
import subprocess
import os
import pickle
import cProfile
from io import StringIO

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pandas as pd
from market_monitor.feed_adapter import load_feed
from market_monitor.feed_source import resolve_daily_feed_source
from market_monitor.chronological import ChronologicalMonitor
from market_monitor.zone_registry import _update_lifecycle, CARRY_FORWARD_STATUSES
from market_monitor.causality import evidence_times
from market_monitor.events import build_market_move_groups
from market_monitor.label_taxonomy import build_sweep_label_frames
from market_monitor.structure import build_structure_levels
from market_monitor.structure import _observation_feed
from market_monitor.liquidity_zones import build_liquidity_map
from market_monitor.zone_registry import build_zone_registry

OUT = ROOT / "local_runs/market_monitor_main_integrity_2026_10_18"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preserve():
    path = OUT / "preservation.json"
    if not path.exists():
        files = []
        for folder in ["feed", "feed_recovered"]:
            files.extend((ROOT / folder).glob("2026-*.csv"))
        for folder in ["research/canonical", "research/own_signal_run", "research/strategy_search"]:
            files.extend(p for p in (ROOT / folder).rglob("*") if p.is_file() and "__pycache__" not in p.parts)
        files.append(ROOT / "binance_aggregator_shi.py")
        path.write_text(json.dumps({p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(set(files))}, indent=2))
    before = json.loads(path.read_text())
    external = OUT / "historical_external_preservation.json"
    if not external.exists():
        files = []
        for prefix in ["SHI_RESET_40Q_", "SHI_RESET_40R_", "SHI_RESET_40S_", "SHI_RESET_40T_", "SHI_RESET_40U_", "SHI_RESET_40V_"]:
            for directory in (ROOT / "market_monitor_runs").glob(prefix + "*"):
                files.extend(p for p in directory.rglob("*") if p.is_file())
        external.write_text(json.dumps({str(p.relative_to(ROOT)): digest(p) for p in sorted(set(files))}, indent=2))
    before.update(json.loads(external.read_text()))
    historical = ROOT / "market_monitor_runs/SHI_RESET_40A_own_signal_causality_preflight_v0/summary.json"
    if historical.exists():
        before.update(json.loads(historical.read_text())["source_hashes"])
    changed = [name for name, sha in before.items() if not (ROOT / name).exists() or digest(ROOT / name) != sha]
    assert not changed, changed
    return len(before)


def policy_parity():
    names = ["_add_source_scores", "_add_lifecycle_scores", "_add_confidence_scores", "_add_distance_scores",
             "_add_interaction_scores", "_add_precision_scores", "_add_event_scores", "_add_observation_scores",
             "_add_context_penalties", "_bucket_for_zone", "_base_hidden_reason", "_assign_visibility",
             "_rebalance_visible_sides", "_promote_to_side_minimum", "_is_visibility_eligible", "_visibility_sorted_indices"]
    evidence = {}
    for filename, functions in [
        ("market_monitor/significant_zone_selector.py", names),
        ("market_monitor/setup_builder.py", ["_seller_dominance_retest_down", "_supply_sweep_reclaim_down",
            "_demand_sweep_reclaim_up", "_accepted_breakout_up"]),
        ("market_monitor/label_taxonomy.py", ["_label_row", "_structural_invalid_reason", "_field_invalid_reason",
            "_no_label_reason", "_rejected_reason", "_accepted_reason", "_base_row", "_summary_frame"]),
    ]:
        original = subprocess.check_output(["git", "show", "0af6d740206aa6628cc688a813288bc79d0de34d:" + filename], cwd=ROOT, text=True)
        old = {node.name: ast.dump(node, include_attributes=False) for node in ast.parse(original).body if isinstance(node, ast.FunctionDef)}
        new = {node.name: ast.dump(node, include_attributes=False) for node in ast.parse((ROOT / filename).read_text()).body if isinstance(node, ast.FunctionDef)}
        for name in functions:
            assert old[name] == new[name], (filename, name)
            evidence[filename + ":" + name] = "EXACT_AST_PARITY"
    (OUT / "policy_parity.json").write_text(json.dumps(evidence, indent=2))


def sources(cutoff):
    day = date(2026, 3, 11)
    parts, files = [], []
    while day <= cutoff.date():
        selected = resolve_daily_feed_source(ROOT / "feed", day)
        frame = load_feed(selected.path, deduplicate=False)
        frame = frame.loc[frame.Timestamp.le(cutoff)]
        assert not frame.Timestamp.duplicated().any()
        assert frame.Timestamp.dt.year.eq(2026).all()
        parts.append(frame)
        files.append({"path": str(selected.path.relative_to(ROOT)), "sha256": digest(selected.path),
                      "source_class": selected.source_class, "rows": len(frame)})
        day += timedelta(days=1)
    return pd.concat(parts, ignore_index=True), files


def decision_digest(decision):
    tables = {**decision["frames"], "selected": decision["selected_zones"], "state": decision["state"],
              "flow": decision["hidden_flow_windows"], "setups": pd.DataFrame(decision["setups"])}
    hashes = {name: hashlib.sha256(frame.to_json(orient="split", date_format="iso", double_precision=15).encode()).hexdigest()
              for name, frame in sorted(tables.items())}
    hashes["snapshot"] = hashlib.sha256(json.dumps(decision["snapshot"], sort_keys=True, default=str).encode()).hexdigest()
    return hashes


def known_blocker_cases():
    cases = [
        ("2026-03-11T17:00Z", "H1", "2026-03-11T15:33Z", 69618.6, "2026-03-11T18:00Z"),
        ("2026-04-24T13:00Z", "H1", "2026-04-24T11:09Z", 77402., "2026-04-24T14:00Z"),
        ("2026-04-24T13:00Z", "H4", "2026-04-24T11:09Z", 77402., "2026-04-24T16:00Z"),
        ("2026-05-07T13:00Z", "H4", "2026-05-07T10:29Z", 80521.8, "2026-05-07T16:00Z"),
        ("2026-09-02T13:00Z", "H4", "2026-09-02T10:52Z", 76151.9, "2026-09-02T16:00Z"),
    ]
    evidence, cached = [], {}
    for cutoff, timeframe, origin, price, earliest in cases:
        if cutoff not in cached:
            feed, files = sources(pd.Timestamp(cutoff))
            cached[cutoff] = build_structure_levels(feed, as_of=cutoff), files
        levels, files = cached[cutoff]
        matching = levels.loc[levels.timeframe.eq(timeframe)
            & pd.to_datetime(levels.level_timestamp, utc=True).eq(pd.Timestamp(origin))
            & pd.to_numeric(levels.price).eq(price)]
        assert matching.empty, (cutoff, timeframe, origin, "premature historical pivot remains available")
        evidence.append({"cutoff": cutoff, "timeframe": timeframe, "origin": origin, "price": price,
            "earliest_confirmation_close": earliest, "premature_levels": len(matching), "source_files": files})
    (OUT / "known_blocker_regressions.json").write_text(json.dumps(evidence, indent=2))
    print(f"PASS {len(evidence)} original premature H1/H4 cases using independently reread real prefixes", flush=True)


def compare_structure_checkpoints(name):
    results = []
    for path in sorted((OUT / name).glob("*/all_known_structure_levels.csv")):
        cutoff = pd.to_datetime(path.parent.name, format="%Y%m%d_%H%M", utc=True)
        feed, files = sources(cutoff)
        fresh = build_structure_levels(feed, as_of=cutoff)
        actual = pd.read_csv(path, float_precision="round_trip")
        expected = pd.read_csv(StringIO(fresh.to_csv(index=False)), float_precision="round_trip")
        pd.testing.assert_frame_equal(actual, expected, check_dtype=False, check_exact=True)
        registry = pd.read_csv(path.parent / "full_registry.csv", keep_default_na=False, float_precision="round_trip")
        active = registry.loc[registry.status.isin(CARRY_FORWARD_STATUSES)].copy()
        cached = _update_lifecycle(active, feed, use_cache=True, as_of=cutoff)
        rebuilt = _update_lifecycle(active, feed, use_cache=False, as_of=cutoff)
        pd.testing.assert_frame_equal(cached, rebuilt, check_dtype=False, check_exact=True)
        results.append({"cutoff": str(cutoff), "rows": len(actual), "status": "EXACT_FULL_RECONSTRUCTION_PARITY",
                        "checkpoint_sha256": digest(path), "source_files": len(files),
                        "registry_forced_recomputation": "EXACT_PARITY"})
    assert results, "no saved historical structure checkpoints"
    (OUT / f"{name}_independent_structure_checkpoints.json").write_text(json.dumps(results, indent=2))
    print(f"PASS {len(results)} real full-history versus incremental structure checkpoints", flush=True)


def diagnostic_checkpoint_cases():
    """Bounded source/structure/registry checks; never claim an H1 state replay."""
    full_feed, full_files = sources(pd.Timestamp("2026-10-14T23:59Z"))
    results = []
    for text in ["2026-06-15T14:00Z", "2026-09-02T14:00Z", "2026-10-14T23:00Z"]:
        cutoff = pd.Timestamp(text)
        print(f"CHECK diagnostic {cutoff}: full source/structure, bounded registry samples", flush=True)
        prefix, files = sources(cutoff)
        observed = _observation_feed(prefix)
        levels = build_structure_levels(full_feed, as_of=cutoff)
        independently_loaded = build_structure_levels(prefix, as_of=cutoff)
        pd.testing.assert_frame_equal(levels, independently_loaded, check_dtype=False, check_exact=True)
        assert not evidence_times(levels).gt(cutoff).any()
        for timeframe, group in levels.loc[levels.timeframe.isin(["M15", "H1", "H4"])].groupby("timeframe"):
            frequency, minutes, radius = {"M15": ("15min", 15, 2), "H1": ("h", 60, 2), "H4": ("4h", 240, 1)}[timeframe]
            earliest = pd.to_datetime(group.level_timestamp, utc=True).dt.ceil(frequency) + pd.Timedelta(minutes=minutes * radius)
            assert pd.to_datetime(group.LevelAvailableAtUTC, utc=True).ge(earliest).all()
        zones = build_liquidity_map(levels, float(observed.ClosePrice.iloc[-1]))
        # Diagnostic samples do not claim a reconstructed historical registry.
        # Keep/export the whole canonical inventory; bound only this test's input.
        samples = zones.sort_values("created_at", kind="mergesort").groupby("source_timeframe_primary", sort=False).tail(2)
        registry, _ = build_zone_registry(liquidity_map=samples, feed=prefix, history_feed=full_feed, as_of=cutoff)
        expected, _ = build_zone_registry(liquidity_map=samples, feed=prefix, history_feed=prefix, as_of=cutoff)
        pd.testing.assert_frame_equal(registry, expected, check_dtype=False, check_exact=True)
        assert not evidence_times(registry).gt(cutoff).any()
        active = registry.loc[registry.status.isin(CARRY_FORWARD_STATUSES)].copy()
        pd.testing.assert_frame_equal(_update_lifecycle(active, prefix, use_cache=True, as_of=cutoff),
            _update_lifecycle(active, prefix, use_cache=False, as_of=cutoff), check_dtype=False, check_exact=True)
        destination = OUT / "publication_diagnostic_checkpoints" / cutoff.strftime("%Y%m%d_%H%M")
        destination.mkdir(parents=True, exist_ok=True)
        levels.to_csv(destination / "structure_levels.csv", index=False)
        zones.to_csv(destination / "full_canonical_zone_inventory.csv", index=False)
        registry.to_csv(destination / "registry_cold_start_diagnostic.csv", index=False)
        result = {"cutoff": str(cutoff), "status": "EXACT_SOURCE_STRUCTURE_REGISTRY_PREFIX_PARITY",
            "mode": "FULL_SOURCE_CONTEXT_COLD_START_DIAGNOSTIC", "chronological_h1_continuation_verified": False,
            "registry_scope": "TWO_LATEST_ZONES_PER_CANONICAL_PRIMARY_TIMEFRAME",
            "full_zone_inventory_rows": len(zones), "registry_input_zone_rows": len(samples),
            "structure_rows": len(levels), "registry_rows": len(registry), "source_files": files,
            "source_quality_counts": observed.DataQuality.value_counts().to_dict()}
        (destination / "verification.json").write_text(json.dumps(result, indent=2))
        results.append(result)
        print(f"PASS diagnostic {cutoff}: {len(levels)} levels, {len(registry)} registry rows; not an H1 continuation", flush=True)
    (OUT / "publication_diagnostic_checkpoints.json").write_text(json.dumps(results, indent=2))


def verify_control_prefixes(name):
    """Independently reread shorter inputs from exact carried predecessor states."""
    records = {row["cutoff"]: row for row in map(json.loads, (OUT / f"{name}_decisions.jsonl").read_text().splitlines())}
    identity = {str(path.relative_to(ROOT)): digest(path) for path in sorted((ROOT / "market_monitor").glob("*.py"))}
    results = []
    for path in sorted((OUT / name).glob("*/prefix_predecessor.pkl")):
        saved = pickle.loads(path.read_bytes())
        assert saved["identity"] == identity
        monitor = saved["monitor"]
        initial = monitor.cutoff
        target = pd.to_datetime(path.parent.name, format="%Y%m%d_%H%M", utc=True)
        feed, files = sources(target)
        equal = 0
        for timestamp in pd.date_range(initial + pd.Timedelta(hours=1), target, freq="h"):
            available = feed.loc[feed.Timestamp.le(timestamp)]
            decision = monitor.update(available, timestamp)
            assert decision_digest(decision) == records[str(timestamp)]["hashes"], str(timestamp)
            equal += 1
        assert equal == 3
        results.append({"cutoff": str(target), "carried_from": str(initial), "h1_decisions_equal": equal,
            "source_files": files, "predecessor_sha256": digest(path), "state_reset": False,
            "status": "EXACT_FULL_DECISION_PREFIX_PARITY"})
        print(f"PASS independent carried prefix {target}: {equal} H1 decisions", flush=True)
        del saved, monitor, decision, feed
    assert results, "no independently replayable control predecessors"
    (OUT / f"{name}_control_prefixes.json").write_text(json.dumps(results, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cutoff", default="2026-10-14T23:59:00Z")
    parser.add_argument("--name", default="full")
    parser.add_argument("--preservation-only", action="store_true")
    parser.add_argument("--blocker-cases-only", action="store_true")
    parser.add_argument("--compare-checkpoints", help="Independently reread/rebuild every saved real structure checkpoint")
    parser.add_argument("--diagnostic-checkpoints-only", action="store_true",
                        help="User-approved partial validation: later source/structure/registry dates, without an H1 replay claim")
    parser.add_argument("--prefix-input", action="store_true", help="Pass only independently sliced source observations to each update")
    parser.add_argument("--compare", help="Previously saved longer-input run name")
    parser.add_argument("--resume-from", help="Own local checkpoint from an identical canonical source revision")
    parser.add_argument("--profile-day", help="Profile one UTC day without changing calculation semantics")
    parser.add_argument("--full-recompute-every-day", action="store_true",
                        help="Expensive stress verification; normal continuation checks control checkpoints only")
    parser.add_argument("--time-budget-seconds", type=float, default=0,
                        help="Stop cleanly with an exact resumable checkpoint within this wall-clock budget")
    parser.add_argument("--save-prefix-controls", action="store_true",
                        help="Save carried predecessors for independent three-H1 control-prefix comparisons")
    parser.add_argument("--verify-control-prefixes", help="Independently verify saved control predecessors after a full run")
    args = parser.parse_args()
    budget_started = time.monotonic()
    OUT.mkdir(parents=True, exist_ok=True)
    count = preserve()
    policy_parity()
    if args.preservation_only:
        print(f"{count} protected/historical files preserved")
        return
    if args.blocker_cases_only:
        known_blocker_cases()
        preserve()
        return
    if args.compare_checkpoints:
        compare_structure_checkpoints(args.compare_checkpoints)
        preserve()
        return
    if args.diagnostic_checkpoints_only:
        diagnostic_checkpoint_cases()
        preserve()
        return
    if args.verify_control_prefixes:
        verify_control_prefixes(args.verify_control_prefixes)
        preserve()
        return
    cutoff = pd.Timestamp(args.cutoff)
    identity = {str(path.relative_to(ROOT)): digest(path) for path in sorted((ROOT / "market_monitor").glob("*.py"))}
    (OUT / f"{args.name}_code_identity.json").write_text(json.dumps(identity, indent=2))
    (OUT / f"{args.name}_process.json").write_text(json.dumps({"pid": os.getpid(), "cutoff": str(cutoff)}))
    assert cutoff.year == 2026 and cutoff <= pd.Timestamp("2026-10-14T23:59:00Z")
    feed, files = sources(cutoff)
    (OUT / f"{args.name}_sources.json").write_text(json.dumps(files, indent=2))
    monitor = ChronologicalMonitor()
    first_number = 0
    prior_records = ""
    if args.resume_from:
        resume_path = Path(args.resume_from).resolve()
        assert resume_path.parent == OUT.resolve(), "checkpoint must belong to this verification directory"
        saved = pickle.loads(resume_path.read_bytes())
        assert saved["identity"] == identity, "cannot resume state from different canonical code"
        assert saved["prefix_input"] == args.prefix_input
        monitor, first_number = saved["monitor"], saved["number"] + 1
        old_records = (OUT / f"{saved['name']}_decisions.jsonl").read_text()
        prior_records = "".join(line + "\n" for line in old_records.splitlines() if pd.Timestamp(json.loads(line)["cutoff"]) <= monitor.cutoff)
    (OUT / f"{args.name}_continuity.json").write_text(json.dumps({
        "resumed_from": args.resume_from, "prior_cutoff": str(monitor.cutoff) if monitor.cutoff is not None else None,
        "initialization": "EXACT_CARRIED_CHECKPOINT" if args.resume_from else "SOURCE_GENESIS",
        "market_state_reset": False, "structure_levels_reset": False, "liquidity_zones_reset": False,
        "qualified_h1_state_reset": False, "setup_context_reset": False,
    }, indent=2))
    profiler = cProfile.Profile() if args.profile_day else None
    profile_enabled = False
    started = time.monotonic()
    stopped_for_budget = False
    last_number = first_number - 1
    def save_state(number, checkpoint_path=None):
        checkpoint_path = checkpoint_path or OUT / f"{args.name}_state.pkl"
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = checkpoint_path.with_suffix(".tmp")
        temporary_path.write_bytes(pickle.dumps({"monitor": monitor, "number": number, "identity": identity,
            "name": args.name, "prefix_input": args.prefix_input}, protocol=pickle.HIGHEST_PROTOCOL))
        temporary_path.replace(checkpoint_path)
    with (OUT / f"{args.name}_decisions.jsonl").open("w", encoding="utf-8") as stream:
        stream.write(prior_records)
        control_times = [pd.Timestamp(text) for text in ["2026-03-14T14:00Z", "2026-04-24T14:00Z",
            "2026-05-07T14:00Z", "2026-06-15T14:00Z", "2026-07-15T14:00Z", "2026-09-02T14:00Z"]]
        control_times.append(cutoff.floor("h"))
        for number, timestamp in enumerate(pd.date_range(feed.Timestamp.min().ceil("h"), cutoff.floor("h"), freq="h")):
            if number < first_number:
                continue
            if args.time_budget_seconds and time.monotonic() - budget_started >= max(0, args.time_budget_seconds - 20):
                stopped_for_budget = True
                break
            if profiler is not None:
                desired = timestamp.date().isoformat() == args.profile_day
                if desired and not profile_enabled:
                    profiler.enable()
                    profile_enabled = True
                elif profile_enabled and not desired:
                    profiler.disable()
                    profiler.dump_stats(str(OUT / f"{args.name}_profile.stats"))
                    profiler = None
            available = feed.loc[feed.Timestamp.le(timestamp)]
            observed_times = available.loc[~available.DataQuality.isin(["SYNTHETIC", "INVALID"]), "Timestamp"]
            if observed_times.empty or observed_times.max() < timestamp - pd.Timedelta(minutes=1):
                stream.write(json.dumps({"cutoff": str(timestamp), "status": "MISSING_CLOSING_OBSERVATION"}) + "\n")
                continue
            control_checkpoint = timestamp in control_times
            decision = monitor.update(available if args.prefix_input else feed, timestamp)
            levels = monitor.structure.levels
            if not levels.empty:
                assert pd.to_datetime(levels.created_at, utc=True).le(timestamp).all()
                primitives = levels.loc[levels.timeframe.isin(["M15", "H1", "H4"])]
                for tf, group in primitives.groupby("timeframe"):
                    freq = {"M15": "15min", "H1": "h", "H4": "4h"}[tf]
                    # Independently derive confirmation from origin's bar close and detector radius.
                    origin_close = pd.to_datetime(group.level_timestamp, utc=True).dt.ceil(freq)
                    duration = pd.Timedelta(minutes={"M15": 15, "H1": 60, "H4": 240}[tf])
                    expected = origin_close + duration * (1 if tf == "H4" else 2)
                    assert pd.to_datetime(group.created_at, utc=True).ge(expected).all()
            selected = decision["selected_zones"]
            for frame in [*decision["frames"].values(), selected, decision["state"]]:
                if not frame.empty:
                    assert not evidence_times(frame).gt(timestamp).any()
            assert selected.visible_on_snapshot.eq("true").sum() <= 7
            for row in decision["setups"]:
                assert pd.Timestamp(row["setup_formed_at"]) >= pd.Timestamp(row["end_timestamp"])
            record = {"cutoff": str(timestamp), "status": "PASS", "hashes": decision_digest(decision),
                      "registry_rows": len(monitor.registry), "selected_rows": len(selected),
                      "visible": int(selected.visible_on_snapshot.eq("true").sum()), "source_rows": int(feed.Timestamp.le(timestamp).sum())}
            stream.write(json.dumps(record, sort_keys=True) + "\n")
            stream.flush()
            last_number = number
            if args.save_prefix_controls and timestamp + pd.Timedelta(hours=3) in control_times:
                target = timestamp + pd.Timedelta(hours=3)
                save_state(number, OUT / args.name / target.strftime("%Y%m%d_%H%M") / "prefix_predecessor.pkl")
            if control_checkpoint:
                checkpoint = OUT / args.name / timestamp.strftime("%Y%m%d_%H%M")
                checkpoint.mkdir(parents=True, exist_ok=True)
                monitor.structure.levels.to_csv(checkpoint / "all_known_structure_levels.csv", index=False)
                monitor.registry.to_csv(checkpoint / "full_registry.csv", index=False)
                selected.to_csv(checkpoint / "selected_zone_inventory.csv", index=False)
                decision["state"].to_csv(checkpoint / "market_structure_state.csv", index=False)
                (checkpoint / "snapshot.json").write_text(json.dumps(decision["snapshot"], sort_keys=True, indent=2, default=str))
            if control_checkpoint or (args.full_recompute_every_day and number % 24 == 0):
                active = monitor.registry.loc[monitor.registry.status.isin(CARRY_FORWARD_STATUSES)].copy()
                cached = _update_lifecycle(active, available, use_cache=True, as_of=timestamp)
                full = _update_lifecycle(active, available, use_cache=False, as_of=timestamp)
                try:
                    pd.testing.assert_frame_equal(cached, full, check_dtype=False, check_exact=True)
                except AssertionError:
                    cached.to_json(OUT / f"{args.name}_cache_failure.json", orient="records", indent=2)
                    full.to_json(OUT / f"{args.name}_full_recomputation_failure.json", orient="records", indent=2)
                    raise
                pd.testing.assert_frame_equal(decision["frames"]["market_move_groups.csv"].drop(columns="snapshot_available_at_utc", errors="ignore"),
                    build_market_move_groups(monitor.events).drop(columns="snapshot_available_at_utc", errors="ignore"), check_dtype=False, check_exact=True)
                labels, summary = build_sweep_label_frames(observations=monitor.completed_observations, market_move_groups=monitor.market_moves)
                for filename, direct in [("sweep_label_taxonomy.csv", labels), ("sweep_label_summary.csv", summary)]:
                    pd.testing.assert_frame_equal(decision["frames"][filename].drop(columns="snapshot_available_at_utc", errors="ignore"),
                        direct.drop(columns="snapshot_available_at_utc", errors="ignore"), check_dtype=False, check_exact=True)
            if number % 24 == 0 or control_checkpoint:
                print(f"{timestamp}: {number + 1} H1, registry={len(monitor.registry)}, elapsed={time.monotonic()-started:.1f}s", flush=True)
                assert identity == {str(path.relative_to(ROOT)): digest(path) for path in sorted((ROOT / "market_monitor").glob("*.py"))}, "canonical code changed during verification"
                save_state(number)
    if monitor.cutoff is not None:
        save_state(last_number)
    preserve()
    assert identity == {str(path.relative_to(ROOT)): digest(path) for path in sorted((ROOT / "market_monitor").glob("*.py"))}, "canonical code changed during verification"
    if args.compare and not stopped_for_budget:
        reference = {row["cutoff"]: row for row in map(json.loads, (OUT / f"{args.compare}_decisions.jsonl").read_text().splitlines())}
        actual = list(map(json.loads, (OUT / f"{args.name}_decisions.jsonl").read_text().splitlines()))
        for row in actual:
            assert reference[row["cutoff"]] == row, (row["cutoff"], "historical prefix mismatch")
        (OUT / f"{args.name}_prefix_comparison.json").write_text(json.dumps({"reference": args.compare, "cutoffs_equal": len(actual), "final_cutoff": str(cutoff)}, indent=2))
    (OUT / f"{args.name}_completion.json").write_text(json.dumps({
        "complete": not stopped_for_budget, "requested_cutoff": str(cutoff), "last_decision_cutoff": str(monitor.cutoff),
        "stopped_for_budget": stopped_for_budget, "elapsed_seconds": time.monotonic() - budget_started,
        "full_recomputation_mode": "DAILY_STRESS" if args.full_recompute_every_day else "CONTROL_CHECKPOINTS",
        "market_state_reset": False, "structure_levels_reset": False, "liquidity_zones_reset": False,
        "qualified_h1_state_reset": False, "setup_context_reset": False}, indent=2))
    print(f"{'PARTIAL_BUDGET' if stopped_for_budget else 'PASS'} {args.name}; cutoff={monitor.cutoff}; {count} protected files preserved", flush=True)


if __name__ == "__main__":
    main()
