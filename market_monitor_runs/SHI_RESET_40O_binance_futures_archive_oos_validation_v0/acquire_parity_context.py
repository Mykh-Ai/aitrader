"""Known2026 context only. Never request an OOS date during adaptation."""
from concurrent.futures import ThreadPoolExecutor
import json

import pandas as pd

from archive_source import OUT, acquire, save


def main():
    initial = json.loads((OUT / "source_manifest.json").read_text())
    assert all(r["status"] == "CHECKSUM_VERIFIED" for r in initial["archives"])
    plan = [(d.strftime("%Y-%m-%d"), "daily") for d in pd.date_range("2026-03-11", "2026-03-31")]
    plan += [(f"2026-{month:02}", "monthly") for month in range(4, 10)]
    assert all(pd.Timestamp(date + ("-01" if len(date) == 7 else "")) >= pd.Timestamp("2026-03-11") for date, _ in plan)
    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(lambda item: acquire(item[0], item[1]), plan))
    save("source_manifest.json", {"phase": "KNOWN_2026_SOURCE_VALIDATION_ONLY", "archives": records,
         "official_schema": initial["official_schema"], "OOS_downloaded": False, "OOS_outcomes_read": False})
    pd.DataFrame(records).to_csv(OUT / "archive_inventory.csv", index=False)
    assert all(r["status"] == "CHECKSUM_VERIFIED" for r in records), "Required official overlap/context archive unavailable; no OOS"
    print(f"All{len(records)} known2026 archive checksums verified; OOS remains unopened", flush=True)


if __name__ == "__main__":
    main()
