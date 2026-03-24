"""Діагностичний прогін analyzer з multi-day windows.

Мета: перевірити чи FE=0 streak є наслідком single-day windows.
Запускати на VPS: python3 research/scripts/diagnostic_multiday_windows.py

Не змінює production логіку. Не змінює параметри.
Output: тільки summary table + per-window key metrics.
"""

from __future__ import annotations

import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

# Визначаємо repo root
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(REPO_ROOT))

FEED_DIR = REPO_ROOT / "feed"
OUTPUT_BASE = REPO_ROOT / "research" / "findings" / "diagnostic_multiday"

WINDOWS_3DAY = [
    (date(2026, 3, 18), date(2026, 3, 20)),
    (date(2026, 3, 19), date(2026, 3, 21)),
    (date(2026, 3, 20), date(2026, 3, 22)),
    (date(2026, 3, 21), date(2026, 3, 23)),
]

WINDOWS_5DAY = [
    (date(2026, 3, 18), date(2026, 3, 22)),
    (date(2026, 3, 19), date(2026, 3, 23)),
]


def _date_range(start: date, end: date) -> list[date]:
    """Inclusive date range."""
    days = []
    current = start
    while current <= end:
        days.append(current)
        current += timedelta(days=1)
    return days


def _concat_feeds(dates: list[date], feed_dir: Path) -> Path | None:
    """Конкатенує feed files у тимчасовий CSV. Повертає шлях або None."""
    import pandas as pd

    frames = []
    for d in dates:
        feed_file = feed_dir / f"{d.isoformat()}.csv"
        if not feed_file.exists():
            print(f"  MISSING: {feed_file}")
            return None
        frames.append(pd.read_csv(feed_file, encoding="utf-8"))

    combined = pd.concat(frames, ignore_index=True)
    combined["Timestamp"] = pd.to_datetime(combined["Timestamp"], utc=True)
    combined = combined.sort_values("Timestamp").reset_index(drop=True)

    # Видалити дублікати по Timestamp (boundary overlap)
    combined = combined.drop_duplicates(subset=["Timestamp"], keep="first")

    tmp = tempfile.NamedTemporaryFile(
        suffix=".csv", prefix="multiday_feed_", delete=False, mode="w"
    )
    combined.to_csv(tmp.name, index=False)
    tmp.close()
    return Path(tmp.name)


def _run_window(start: date, end: date, feed_dir: Path, output_base: Path) -> dict:
    """Запускає analyzer pipeline для одного window."""
    from analyzer.pipeline import run as run_pipeline

    label = f"{start.isoformat()}_to_{end.isoformat()}"
    print(f"\n{'='*60}")
    print(f"Window: {label}")
    print(f"{'='*60}")

    dates = _date_range(start, end)
    feed_path = _concat_feeds(dates, feed_dir)
    if feed_path is None:
        return {
            "window": label,
            "status": "MISSING_FEED",
            "setups_rows": "N/A",
            "shortlist_rows": "N/A",
            "formalization_eligible": "N/A",
            "replayable_rulesets_count": "N/A",
        }

    output_dir = output_base / f"diag_{label}"
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        result = run_pipeline(str(feed_path), str(output_dir))

        setups_rows = len(result["setups"])
        shortlist_rows = len(result["shortlist"])
        research_summary = result["research_summary"]

        if research_summary.empty:
            fe_count = 0
            replayable = 0
        else:
            fe_mask = research_summary["FormalizationEligible"] == True  # noqa: E712
            fe_count = int(fe_mask.sum())
            replayable = fe_count

        print(f"  setups:      {setups_rows}")
        print(f"  shortlist:   {shortlist_rows}")
        print(f"  FE rows:     {fe_count}")
        print(f"  replayable:  {replayable}")

        return {
            "window": label,
            "status": "OK",
            "setups_rows": setups_rows,
            "shortlist_rows": shortlist_rows,
            "formalization_eligible": fe_count,
            "replayable_rulesets_count": replayable,
        }

    except Exception as e:
        print(f"  ERROR: {e}")
        return {
            "window": label,
            "status": f"ERROR: {e}",
            "setups_rows": "N/A",
            "shortlist_rows": "N/A",
            "formalization_eligible": "N/A",
            "replayable_rulesets_count": "N/A",
        }
    finally:
        # Cleanup temp feed
        try:
            feed_path.unlink()
        except OSError:
            pass


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Diagnostic multi-day analyzer windows")
    parser.add_argument(
        "--feed-dir",
        type=Path,
        default=FEED_DIR,
        help="Feed directory (default: repo/feed/)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_BASE,
        help="Output base directory",
    )
    args = parser.parse_args()

    feed_dir = args.feed_dir
    output_base = args.output_dir

    print(f"Feed dir: {feed_dir}")
    print(f"Output:   {output_base}")

    # Перевірка наявності feed files
    all_dates = set()
    for start, end in WINDOWS_3DAY + WINDOWS_5DAY:
        for d in _date_range(start, end):
            all_dates.add(d)

    print(f"\nRequired feed dates: {sorted(all_dates)}")
    missing = [d for d in sorted(all_dates) if not (feed_dir / f"{d.isoformat()}.csv").exists()]
    if missing:
        print(f"Missing feeds: {missing}")
        print("Will skip windows with missing data.")
    else:
        print("All feed files present.")

    results = []

    print("\n" + "=" * 60)
    print("3-DAY WINDOWS")
    print("=" * 60)
    for start, end in WINDOWS_3DAY:
        results.append(_run_window(start, end, feed_dir, output_base))

    print("\n" + "=" * 60)
    print("5-DAY WINDOWS")
    print("=" * 60)
    for start, end in WINDOWS_5DAY:
        results.append(_run_window(start, end, feed_dir, output_base))

    # Summary table
    print("\n")
    print("=" * 80)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 80)
    print(f"{'window':<30} {'setups':>8} {'shortlist':>10} {'FE':>4} {'replayable':>11} {'status'}")
    print("-" * 80)
    for r in results:
        print(
            f"{r['window']:<30} {str(r['setups_rows']):>8} "
            f"{str(r['shortlist_rows']):>10} {str(r['formalization_eligible']):>4} "
            f"{str(r['replayable_rulesets_count']):>11} {r['status']}"
        )

    # Single-day reference
    print("\n" + "-" * 80)
    print("SINGLE-DAY REFERENCE (from run_log)")
    print("-" * 80)
    print(f"{'window':<30} {'setups':>8} {'shortlist':>10} {'FE':>4}")
    print("-" * 80)
    single_day_ref = [
        ("2026-03-18 (1d)", 1, 0, 0),
        ("2026-03-19 (1d)", 1, 0, 0),
        ("2026-03-20 (1d)", 1, 0, 0),
        ("2026-03-21 (1d)", 2, 0, 0),
        ("2026-03-22 (1d)", 1, 0, 0),
        ("2026-03-23 (1d)", 3, 0, 0),
    ]
    for label, s, sl, fe in single_day_ref:
        print(f"{label:<30} {s:>8} {sl:>10} {fe:>4}")

    # Verdict
    print("\n" + "=" * 80)
    print("DIAGNOSTIC VERDICT")
    print("=" * 80)

    ok_results = [r for r in results if r["status"] == "OK"]
    if not ok_results:
        print("No windows completed successfully. Cannot determine verdict.")
        return

    any_fe = any(r["formalization_eligible"] > 0 for r in ok_results)
    any_shortlist = any(r["shortlist_rows"] > 0 for r in ok_results)
    max_setups = max(r["setups_rows"] for r in ok_results)
    total_setups_3d = sum(
        r["setups_rows"] for r in ok_results
        if len(r["window"].split("_to_")[0]) == 10
        and (r["window"].count("-") == 4)  # 3-day windows
        and r["setups_rows"] != "N/A"
    )

    if any_fe:
        print("VERDICT: Signal exists but is diluted across days.")
        print(f"  Multi-day windows produce FE>0 rows.")
        print(f"  Max setups in a window: {max_setups}")
    elif any_shortlist:
        print("VERDICT: Signal partially recovers with wider windows.")
        print(f"  Shortlist rows appear but FE=0 persists (Direction/SetupType still blocked).")
        print(f"  Max setups in a window: {max_setups}")
    elif max_setups >= 10:
        print("VERDICT: Setup volume recovers but edge insufficient.")
        print(f"  Max setups: {max_setups}, but no shortlist/FE rows.")
    else:
        print("VERDICT: Signal genuinely absent in this regime.")
        print(f"  Even multi-day windows produce max {max_setups} setups.")
        print(f"  Wider windows do not recover structural event density.")


if __name__ == "__main__":
    main()
