"""One predeclared January2025 source extension for 30-day H4 history."""
import importlib.util
import json

from frozen_adapter import OUT, OLD, SOURCE, WARMUP, sha, save


def main():
    plan = {"date": "2025-01", "market": "USD_M_PERPETUAL_FUTURES", "symbol": "BTCUSDT", "interval": "1m",
            "role": "TECHNICAL_WARMUP_ONLY", "warmup_start_right_close": str(WARMUP),
            "reason": "Frozen H4 inventory keeps references for 30 days plus delayed confirmation; February2025 has only28 days. January supplies >30 days before March1 without inspecting strategy outcomes.",
            "scored_start_unchanged": "2025-03-01T00:00:00Z", "OOS_strategy_outcomes_read": False,
            "adapter_sha256": sha(OLD / "archive_source.py")}
    path = OUT / "source_context_plan.json"
    if path.exists():
        assert json.loads(path.read_text()) == plan
    else:
        save(path.name, plan)
    spec = importlib.util.spec_from_file_location("archive40Q_context", OLD / "archive_source.py")
    api = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api)
    api.OUT = OUT
    record = api.acquire("2025-01", "monthly")
    save("source_context_manifest.json", {"archives": [record], "plan_sha256": sha(path),
         "reused_40P_source_manifest_path": str((SOURCE / "source_manifest.json").relative_to(OUT.parents[1])),
         "reused_40P_source_manifest_sha256": sha(SOURCE / "source_manifest.json")})
    assert record["status"] == "CHECKSUM_VERIFIED", record
    frame = api.read_kline_zip(OUT / record["archive_path"])
    frame = frame.loc[frame.Timestamp.ge(WARMUP) & frame.Timestamp.lt("2025-02-01T00:00:00Z")].copy()
    frame["SourceArchive"] = record["filename"]
    frame["HistoryRole"] = "WARMUP_ONLY"
    path = OUT / "january_warmup_minutes.csv"
    frame.to_csv(path, index=False, lineterminator="\n")
    save("source_context_normalization.json", {"file": path.name, "sha256": sha(path), "rows": len(frame),
         "first": frame.Timestamp.min(), "last": frame.Timestamp.max(), "OOS_strategy_outcomes_read": False})
    print(f"January warmup: official checksum verified; {len(frame)} normalized rows", flush=True)


if __name__ == "__main__":
    main()
