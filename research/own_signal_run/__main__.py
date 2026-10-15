from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from .causal import CausalSignalEngine
from .contracts import contract_hash, load_contract, validate_signal
from .feed import closed_bars, digest, read_sources, usable_observations
from .replay import replay_signals, summarize

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "market_monitor_runs/SHI_RESET_40B_own_signal_run_preparation_v1"
DEPENDENCIES = ["market_monitor/feed_adapter.py", "market_monitor/market_structure_state.py", "market_monitor/qualified_h1_sweep_reclaim.py"]


def code_hashes(root: Path) -> dict:
    paths = sorted((root / "research/own_signal_run").glob("*.py")) + [root / p for p in DEPENDENCIES]
    return {p.relative_to(root).as_posix(): digest(p) for p in paths}


def save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, sort_keys=True, indent=2, default=str, allow_nan=False) + "\n", encoding="utf-8")


def prepare(root: Path, out: Path, contract: dict) -> dict:
    if (out / "signals").exists() or (out / "financial_proxy_replay").exists():
        raise ValueError("Study outputs already exist; use a new versioned output directory")
    out.mkdir(parents=True, exist_ok=True)
    feed, inventory = read_sources(root, contract["source_start"], contract["source_cutoff"])
    inventory.to_csv(out / "feed_inventory.csv", index=False)
    gaps = []
    expected_start, expected_end = pd.Timestamp(contract["source_start"]), pd.Timestamp(contract["source_cutoff"])
    for previous, current in zip(feed.Timestamp.iloc[:-1], feed.Timestamp.iloc[1:]):
        count = int((current - previous).total_seconds() / 60) - 1
        if count > 0:
            gaps.append({"first_missing_close": previous + pd.Timedelta(minutes=1), "last_missing_close": current - pd.Timedelta(minutes=1), "missing_minutes": count})
    for begin, end in [(expected_start, feed.Timestamp.iloc[0] - pd.Timedelta(minutes=1)), (feed.Timestamp.iloc[-1] + pd.Timedelta(minutes=1), expected_end)]:
        if begin <= end:
            gaps.append({"first_missing_close": begin, "last_missing_close": end, "missing_minutes": int((end - begin).total_seconds() / 60) + 1})
    pd.DataFrame(gaps, columns=["first_missing_close", "last_missing_close", "missing_minutes"]).to_csv(out / "feed_gaps.csv", index=False)
    feed.loc[feed.DataQuality.ne("RAW"), ["Timestamp", "SourceFile", "DataQuality", "IsRecovered", "IsSynthetic", "InvalidRow"]].to_csv(out / "degraded_minutes.csv", index=False)
    working = usable_observations(feed)
    h1 = closed_bars(working, 60)
    manifest = {"task_id": "SHI_RESET_40B_OWN_SIGNAL_RUN_PREPARATION", "status": "INPUTS_FROZEN_SMOKE_REQUIRED",
                "contract_sha256": contract_hash(contract), "code_hashes": code_hashes(root),
                "source_hashes": dict(zip(inventory.loc[inventory.status.eq("READ"), "path"], inventory.loc[inventory.status.eq("READ"), "sha256"])),
                "selected_rows": len(feed), "first_selected_close": feed.Timestamp.iloc[0], "last_selected_close": feed.Timestamp.iloc[-1],
                "missing_minutes": sum(x["missing_minutes"] for x in gaps), "degraded_minutes": int(feed.DataQuality.ne("RAW").sum()),
                "recovered_minutes": int(feed.IsRecovered.sum()), "invalid_minutes": int(feed.InvalidRow.sum()),
                "closed_raw_h1_bars": int(h1.raw.sum()), "last_complete_h1_close": h1.loc[h1.completed, "timestamp"].max(),
                "computationally_skipped_primary_rows": len(feed) - len(working), "usable_h1_bars": int((h1.usable & h1.completed).sum()),
                "live_day_file_included": False, "profitability_run_performed": False, "source_data_modified": False,
                "financial_market_scope": contract["execution_market"], "pristine_holdout_claim": False,
                "limitations": ["Costs are frozen assumptions, not verified account tariffs", "No executable BTC/USDC Spot Margin fill data", "Historical periods have already been examined in prior research", "Single minute omissions continue the experiment and are explicitly counted; extended gaps/recovered context remain separate"]}
    save_json(out / "frozen_contract.json", contract)
    save_json(out / "preparation_manifest.json", manifest)
    save_json(out / "readiness.json", {"status": "PREPARED_INPUTS_SMOKE_REQUIRED", "profitability_run_performed": False})
    return manifest


def verified_inputs(root: Path, out: Path) -> tuple[pd.DataFrame, dict]:
    contract = load_contract(out / "frozen_contract.json")
    manifest = json.loads((out / "preparation_manifest.json").read_text(encoding="utf-8"))
    if contract_hash(contract) != manifest["contract_sha256"] or code_hashes(root) != manifest["code_hashes"]:
        raise ValueError("Frozen contract or code changed; create a new preparation version")
    feed, inventory = read_sources(root, contract["source_start"], contract["source_cutoff"])
    actual = dict(zip(inventory.loc[inventory.status.eq("READ"), "path"], inventory.loc[inventory.status.eq("READ"), "sha256"]))
    if actual != manifest["source_hashes"]:
        raise ValueError("Frozen feed identity changed")
    return feed, contract


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline own-feed preparation, causal signals and fixed-exit proxy replay")
    parser.add_argument("mode", choices=["prepare", "smoke", "signals", "replay"])
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--contract", type=Path, default=Path(__file__).with_name("contract_v1.json"))
    parser.add_argument("--until", default="2026-03-25T14:00:00Z", help="Smoke cutoff; no financial replay")
    args = parser.parse_args()
    if args.mode == "prepare":
        manifest = prepare(args.root, args.output, load_contract(args.contract))
        print(json.dumps({k: manifest[k] for k in ["status", "selected_rows", "missing_minutes", "degraded_minutes", "last_complete_h1_close"]}, default=str))
        return
    feed, contract = verified_inputs(args.root, args.output)
    if args.mode in {"smoke", "signals"}:
        if args.mode == "smoke":
            feed = feed.loc[feed.Timestamp <= pd.Timestamp(args.until)].copy()
        engine = CausalSignalEngine(feed, contract)
        engine.advance_until(feed.Timestamp.max())
        decisions, timeline = engine.frames()
        if not decisions.empty:
            for decision in decisions.loc[decisions.accepted].to_dict("records"):
                validate_signal(decision, contract)
        folder = args.output / ("causal_smoke" if args.mode == "smoke" else "signals")
        folder.mkdir(parents=True, exist_ok=True)
        decisions.to_csv(folder / "candidate_decisions.csv", index=False)
        timeline.to_csv(folder / "state_continuity.csv", index=False)
        save_json(folder / "generation_manifest.json", {"contract_sha256": contract_hash(contract),
                  "candidate_decisions_sha256": digest(folder / "candidate_decisions.csv"),
                  "state_continuity_sha256": digest(folder / "state_continuity.csv"),
                  "code_hashes": code_hashes(args.root), "cutoff": feed.Timestamp.max(),
                  "source": "Aitrader_feed_only", "financial_replay": False})
        if args.mode == "smoke":
            extended = CausalSignalEngine(pd.concat([feed, verified_inputs(args.root, args.output)[0].loc[lambda f: (f.Timestamp > feed.Timestamp.max()) & (f.Timestamp <= feed.Timestamp.max() + pd.Timedelta(hours=2))]], ignore_index=True), contract)
            extended.advance_until(feed.Timestamp.max())
            other_decisions, other_timeline = extended.frames()
            pd.testing.assert_frame_equal(decisions, other_decisions)
            pd.testing.assert_frame_equal(timeline, other_timeline)
            split = CausalSignalEngine(feed, contract)
            middle = feed.Timestamp.iloc[len(feed) // 2]
            split.advance_until(middle)
            split.advance_until(feed.Timestamp.max())
            pd.testing.assert_frame_equal(decisions, split.frames()[0])
            pd.testing.assert_frame_equal(timeline, split.frames()[1])
            save_json(args.output / "readiness.json", {"status": "PREPARED_FOR_EXPLICIT_OFFLINE_PROXY_RUN", "real_feed_smoke_cutoff": args.until,
                      "h1_steps": len(timeline), "candidate_decisions": len(decisions), "accepted_candidates": int(decisions.accepted.sum()) if not decisions.empty else 0,
                      "future_append_invariance": True, "chunk_continuity": True, "profitability_run_performed": False,
                      "gate": "RESEARCH_PREPARATION_ONLY_NO_BACKTESTER_PROMOTION_OR_LIVE_AUTHORITY"})
        print(json.dumps({"mode": args.mode, "h1_steps": len(timeline), "candidate_decisions": len(decisions), "financial_replay": False}))
    else:
        path = args.output / "signals/candidate_decisions.csv"
        if not path.exists():
            raise ValueError("Generate the frozen causal signal stream first")
        generation = json.loads((path.parent / "generation_manifest.json").read_text(encoding="utf-8"))
        if generation["contract_sha256"] != contract_hash(contract) or generation["code_hashes"] != code_hashes(args.root) or generation["candidate_decisions_sha256"] != digest(path):
            raise ValueError("Causal generation lineage changed")
        try:
            decisions = pd.read_csv(path).fillna({"sweep_at": ""})
        except pd.errors.EmptyDataError:
            decisions = pd.DataFrame()
        ledger, admission = replay_signals(feed, decisions, contract)
        folder = args.output / "financial_proxy_replay"
        folder.mkdir(parents=True, exist_ok=True)
        ledger.to_csv(folder / "trade_ledger.csv", index=False)
        admission.to_csv(folder / "entry_admission.csv", index=False)
        summarize(ledger, contract).to_csv(folder / "family_period_results.csv", index=False)
        save_json(folder / "manifest.json", {"contract_sha256": contract_hash(contract), "candidate_decisions_sha256": digest(path),
                  "execution_market": contract["execution_market"], "costs_verified": False, "live_authority": False,
                  "ledger_rows": len(ledger), "backtester_promotion_gate_enabled": False})
        print(json.dumps({"mode": args.mode, "ledger_rows": len(ledger), "live_authority": False}))


if __name__ == "__main__":
    main()
