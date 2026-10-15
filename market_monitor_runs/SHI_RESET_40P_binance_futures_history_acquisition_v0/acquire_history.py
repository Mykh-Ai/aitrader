"""User-authorized historical data acquisition only. No strategy or replay imports."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

import pandas as pd

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
PRIOR = ROOT / "market_monitor_runs/SHI_RESET_40O_binance_futures_archive_oos_validation_v0"
DATA_START = pd.Timestamp("2025-02-01T00:00:00Z")
SCORE_START = pd.Timestamp("2025-03-01T00:00:00Z")
DATA_END = pd.Timestamp("2026-03-09T23:59:00Z")
TASK = "SHI_RESET_40P_BINANCE_FUTURES_HISTORY_ACQUISITION_V0"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True, default=str,
                                      allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def archive_plan():
    # The previous exchange minute supplies the first right-close-labelled row.
    rows = [{"date": "2025-01-31", "cadence": "daily", "role": "LEFT_BOUNDARY_MINUTE"}]
    rows += [{"date": ts.strftime("%Y-%m"), "cadence": "monthly",
              "role": "WARMUP" if ts < SCORE_START else "HISTORICAL_EVALUATION_SOURCE"}
             for ts in pd.date_range(DATA_START, "2026-02-01T00:00:00Z", freq="MS")]
    rows += [{"date": f"2026-03-{day:02d}", "cadence": "daily", "role": "HISTORICAL_EVALUATION_SOURCE"}
             for day in range(1, 10)]
    return rows


def partition(frame):
    """Partition UTC right-close labels; never infer strategy outcomes."""
    stamps = pd.to_datetime(frame.Timestamp, utc=True)
    kept = frame.loc[stamps.between(DATA_START, DATA_END)].copy()
    kept["HistoryRole"] = pd.to_datetime(kept.Timestamp, utc=True).map(
        lambda ts: "WARMUP_ONLY" if ts < SCORE_START else "HISTORICAL_EVALUATION_SOURCE")
    return kept


def check_grid(frame):
    stamps = pd.DatetimeIndex(pd.to_datetime(frame.Timestamp, utc=True))
    expected = pd.date_range(DATA_START, DATA_END, freq="min")
    assert stamps.is_monotonic_increasing, "NON_CHRONOLOGICAL_SOURCE"
    assert not stamps.duplicated().any(), "DUPLICATE_MINUTES"
    missing = expected.difference(stamps)
    extra = stamps.difference(expected)
    assert len(missing) == 0, f"MISSING_MINUTES: {len(missing)}"
    assert len(extra) == 0, f"OUT_OF_BOUNDARY_MINUTES: {len(extra)}"
    assert len(stamps) == len(expected)
    return len(expected)


def prepare():
    assert not (OUT / "run_manifest.json").exists(), "MANIFEST_ALREADY_FROZEN"
    prior_manifest = json.loads((PRIOR / "run_manifest.json").read_text())
    old_hashes = json.loads((PRIOR / "artifact_hashes.json").read_text())
    protected = dict(prior_manifest["immutable_source_and_strategy_hashes"])
    protected.update({(PRIOR / name).relative_to(ROOT).as_posix(): digest
                      for name, digest in old_hashes.items()})
    protected[(PRIOR / "artifact_hashes.json").relative_to(ROOT).as_posix()] = sha(PRIOR / "artifact_hashes.json")
    for name, digest in protected.items():
        assert sha(ROOT / name) == digest, f"PRIOR_IDENTITY_MISMATCH: {name}"
    adapter = PRIOR / "archive_source.py"
    manifest = {
        "task": TASK, "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "DATA_ACQUISITION_AND_INTEGRITY_ONLY",
        "starting_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip(),
        "authorization": "User subsequently requested Binance historical data from March 2025. This authorizes acquisition after 40O stopped, not an OOS replay or a parity waiver.",
        "interval_inherited_from_40O": True,
        "data_start_right_close_utc": str(DATA_START), "data_end_right_close_utc": str(DATA_END),
        "warmup_start_inclusive_utc": str(DATA_START), "warmup_end_exclusive_utc": str(SCORE_START),
        "prospective_scored_start_inclusive_utc": str(SCORE_START),
        "prospective_scored_end_inclusive_utc": str(DATA_END),
        "archive_plan": archive_plan(), "normalization": "UNCHANGED_40O_ARCHIVE_ADAPTER",
        "adapter_path": adapter.relative_to(ROOT).as_posix(), "adapter_sha256": sha(adapter),
        "acquisition_code_sha256": sha(__file__),
        "prior_source_gate": "BINANCE_KLINE_SURROGATE_PARITY_FAILED",
        "source_parity_accepted": False, "OOS_replay_authorized": False,
        "strategy_modules_imported": False, "OOS_strategy_outcomes_read": False,
        "strategy_changes": False, "production_changes": False,
        "OI_funding_liquidations_required": False,
        "data_retention": "Local research cache. All ZIP/CHECKSUM files and normalized daily CSVs retained unchanged; source URLs, byte sizes, exact hashes and reproduction commands are committed, not bulk cache bytes.",
        "immutable_prior_file_hashes": protected,
    }
    save("run_manifest.json", manifest)
    print(json.dumps({"task": TASK, "archives_planned": len(archive_plan()),
                      "expected_normalized_minutes": len(pd.date_range(DATA_START, DATA_END, freq="min")),
                      "OOS_replay_authorized": False}), flush=True)


def load_manifest():
    manifest = json.loads((OUT / "run_manifest.json").read_text())
    assert manifest["task"] == TASK and manifest["archive_plan"] == archive_plan()
    assert manifest["acquisition_code_sha256"] == sha(__file__), "ACQUISITION_CODE_CHANGED"
    assert not manifest["OOS_replay_authorized"] and not manifest["source_parity_accepted"]
    assert sha(ROOT / manifest["adapter_path"]) == manifest["adapter_sha256"], "ADAPTER_CHANGED"
    return manifest


def adapter():
    manifest = load_manifest()
    spec = importlib.util.spec_from_file_location("archive_data_only_40P", ROOT / manifest["adapter_path"])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.OUT = OUT  # All new writes go to 40P; the 40O module/file is unchanged.
    return module


def acquire():
    source = adapter()
    records = {}
    def checkpoint():
        ordered = [records[item["date"]] for item in archive_plan() if item["date"] in records]
        save("source_manifest.json", {"task": TASK, "official_base": source.BASE,
             "official_schema": "https://github.com/binance/binance-public-data/blob/master/README.md#futures",
             "market": "USD_M_PERPETUAL_FUTURES", "symbol": "BTCUSDT", "interval": "1m",
             "source_type": "klines", "OOS_source_acquired_by_new_user_authorization": True,
             "OOS_strategy_outcomes_read": False, "archives": ordered})
        pd.DataFrame(ordered).to_csv(OUT / "archive_inventory.csv", index=False)
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(source.acquire, item["date"], item["cadence"]): item for item in archive_plan()}
        for future in as_completed(futures):
            item = futures[future]
            record = future.result()
            record["role"] = item["role"]
            records[item["date"]] = record
            checkpoint()
            print(f"{len(records)}/{len(futures)} {item['date']} {record['status']}", flush=True)
    assert all(row["status"] == "CHECKSUM_VERIFIED" for row in records.values()), "INCOMPLETE_ACQUISITION"


def verify_archives():
    manifest = load_manifest()
    source = json.loads((OUT / "source_manifest.json").read_text())
    assert [(r["date"], r["cadence"]) for r in source["archives"]] == [(r["date"], r["cadence"]) for r in archive_plan()]
    for row in source["archives"]:
        assert row["status"] == "CHECKSUM_VERIFIED"
        path = OUT / row["archive_path"]
        official, name = path.with_name(path.name + ".CHECKSUM").read_text().strip().split()[:2]
        assert name.lstrip("*") == path.name
        assert sha(path) == official == row["local_sha256"] == row["binance_checksum_sha256"]
        assert path.stat().st_size == row["bytes"]
    for name, digest in manifest["immutable_prior_file_hashes"].items():
        assert sha(ROOT / name) == digest, f"PRIOR_FILE_CHANGED: {name}"
    return source


def normalize():
    source = verify_archives()
    api = adapter()
    frames = []
    for row in source["archives"]:
        frame = api.read_kline_zip(OUT / row["archive_path"])
        assert len(frame) == row["row_count"]
        frame["SourceArchive"] = row["filename"]
        frames.append(frame)
    full = pd.concat(frames, ignore_index=True)
    kept = partition(full).sort_values("Timestamp").reset_index(drop=True)
    check_grid(kept)
    assert (kept.BuyQty <= kept.TotalQty + 1e-6).all()
    assert (kept.SellQty >= 0).all()
    assert ((kept.TotalQty - kept.BuyQty - kept.SellQty).abs() <= 1.0001e-6).all()
    feed = OUT / "normalized_futures_feed"
    feed.mkdir(exist_ok=True)
    inventory = []
    for day, frame in kept.groupby(kept.Timestamp.dt.strftime("%Y-%m-%d"), sort=True):
        path = feed / f"{day}.csv"
        frame.to_csv(path, index=False, lineterminator="\n")
        inventory.append({"date": day, "file": path.relative_to(OUT).as_posix(), "bytes": path.stat().st_size,
                          "sha256": sha(path), "rows": len(frame), "first_timestamp": frame.Timestamp.iloc[0],
                          "last_timestamp": frame.Timestamp.iloc[-1], "traded_minutes": int(frame.Traded.sum()),
                          "nontraded_minutes": int((~frame.Traded).sum()), "history_role": frame.HistoryRole.iloc[0]})
    pd.DataFrame(inventory).to_csv(OUT / "normalized_inventory.csv", index=False)
    summary = {"status": "DATA_ACQUIRED_AND_NORMALIZED_NOT_STRATEGY_VALIDATED", "archives": len(source["archives"]),
        "original_zip_bytes": sum(r["bytes"] for r in source["archives"]),
        "source_rows": len(full), "normalized_rows": len(kept), "source_rows_outside_declared_boundary": len(full) - len(kept),
        "normalized_daily_files": len(inventory), "normalized_bytes": sum(r["bytes"] for r in inventory),
        "warmup_rows": int(kept.HistoryRole.eq("WARMUP_ONLY").sum()),
        "evaluation_source_rows": int(kept.HistoryRole.eq("HISTORICAL_EVALUATION_SOURCE").sum()),
        "first_timestamp": kept.Timestamp.iloc[0], "last_timestamp": kept.Timestamp.iloc[-1],
        "missing_minutes": 0, "duplicate_minutes": 0, "nontraded_minutes": int((~kept.Traded).sum()),
        "timestamp_contract": "Exchange candle open + 60s = SHI-style right-close label; original clocks retained",
        "price_decimals": 2, "quantity_decimals": 6, "BuyQty": "taker_buy_base_asset_volume",
        "SellQty": "unrounded total base volume minus unrounded taker-buy base volume, then rounded to 6 decimals",
        "Trades_semantics": "Binance component trades; not equal to SHI received aggTrade event count",
        "unavailable_fields": ["OpenInterest", "FundingRate", "LiqBuyQty", "LiqSellQty"],
        "unavailable_fields_policy": "Inherited schema zeros are placeholders flagged unavailable; not observations or strategy filters",
        "source_parity_accepted": False, "OOS_strategy_outcomes_read": False, "OOS_replay_executed": False}
    save("normalization_summary.json", summary)
    print(json.dumps(summary, default=str), flush=True)


def verify():
    source = verify_archives()
    inventory = pd.read_csv(OUT / "normalized_inventory.csv")
    summary = json.loads((OUT / "normalization_summary.json").read_text())
    stamps = []
    for row in inventory.itertuples():
        path = OUT / row.file
        assert sha(path) == row.sha256 and path.stat().st_size == row.bytes
        frame = pd.read_csv(path)
        assert len(frame) == row.rows == 1440
        labels = pd.to_datetime(frame.Timestamp, utc=True)
        opens = pd.to_datetime(frame.ExchangeOpenAt, utc=True)
        assert labels.eq(opens + pd.Timedelta(minutes=1)).all()
        assert labels.iloc[0].strftime("%Y-%m-%d") == row.date
        assert labels.iloc[-1].strftime("%Y-%m-%d") == row.date
        stamps.extend(labels)
    expected = check_grid(pd.DataFrame({"Timestamp": stamps}))
    assert expected == summary["normalized_rows"] == int(inventory.rows.sum())
    assert len(inventory) == summary["normalized_daily_files"]
    assert not summary["OOS_strategy_outcomes_read"] and not summary["OOS_replay_executed"]
    assert not (PRIOR / "parity_acceptance.json").exists()
    assert not (PRIOR / "first_oos_attempt.json").exists()
    save("verification.json", {"status": "PASS", "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "archives_checksum_verified": len(source["archives"]), "normalized_files_sha_verified": len(inventory),
        "normalized_minutes_verified": expected, "all_daily_files_have_1440_rows": True,
        "right_close_mapping_verified": True, "prior_files_unchanged": True,
        "source_parity_still_unaccepted": True, "OOS_replay_executed": False})
    print(f"PASS: {len(source['archives'])} official checksums; {len(inventory)} daily files; {expected} unique UTC minutes", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["prepare", "acquire", "normalize", "verify"])
    globals()[parser.parse_args().phase]()
