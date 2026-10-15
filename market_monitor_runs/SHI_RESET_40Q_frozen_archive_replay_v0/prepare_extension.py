"""User-requested extension through October14; no signals or returns."""
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json

from frozen_adapter import OUT, OLD, END, sha, save


def main():
    dates = ["2026-03-10"] + [f"2026-10-{day:02d}" for day in range(1, 15)]
    plan = {"dates": dates, "cadence": "daily", "source": "official BTCUSDT USD-M1m klines",
            "user_request": "Булоб добре прогон на данних бінанс зробити до 14.10.2026 заоазом порівняємо всі місяці які пройшли SHA feed.",
            "end_right_close_utc": str(END), "known2026_comparison_is_not_older_OOS": True,
            "unchanged_adapter_sha256": sha(OLD / "archive_source.py"), "returns_seen_before_plan": False}
    path = OUT / "extension_source_plan.json"
    if path.exists():
        assert json.loads(path.read_text()) == plan
    else:
        save(path.name, plan)
    spec = importlib.util.spec_from_file_location("archive40Q_extension", OLD / "archive_source.py")
    api = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api)
    api.OUT = OUT
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(lambda date: api.acquire(date, "daily"), dates))
    save("extension_source_manifest.json", {"archives": rows, "plan_sha256": sha(path)})
    for row in rows:
        print(row["date"], row["status"], flush=True)
    assert all(row["status"] == "CHECKSUM_VERIFIED" for row in rows), "EXTENSION_ACQUISITION_FAILED"


if __name__ == "__main__":
    main()
