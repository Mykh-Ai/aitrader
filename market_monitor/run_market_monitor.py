from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from market_monitor.config import DEFAULT_OUTPUT_ROOT, DEFAULT_RUN_ID
from market_monitor.feed_adapter import FeedContractError, deduplicate_feed, load_feed
from market_monitor.feed_quality import build_window_quality, causal_slice
from market_monitor.feed_source import (
    FeedSourceError,
    discover_daily_dates,
    resolve_daily_feed_source,
)
from market_monitor.outputs import write_outputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the market state monitor skeleton.")
    parser.add_argument("--input", required=True, help="CSV file or directory of CSV files.")
    parser.add_argument(
        "--output",
        default=None,
        help="Output directory. Defaults to market_monitor_runs/run.",
    )
    parser.add_argument(
        "--run-timestamp",
        default=None,
        help="Deterministic timestamp override for tests and reproducible runs.",
    )
    parser.add_argument(
        "--registry-in",
        default=None,
        help="Optional input liquidity zone registry CSV to carry forward.",
    )
    parser.add_argument(
        "--registry-out",
        default=None,
        help="Optional output liquidity zone registry CSV. Defaults to output/liquidity_zone_registry.csv.",
    )
    parser.add_argument(
        "--cutoff",
        default=None,
        help="Optional inclusive UTC calculation cutoff. Rows after it are excluded.",
    )
    parser.add_argument(
        "--progression-start",
        default=None,
        help="Optional inclusive UTC boundary separating warm-up context from new progression rows.",
    )
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    output_dir = Path(args.output) if args.output else DEFAULT_OUTPUT_ROOT / DEFAULT_RUN_ID
    run_timestamp = args.run_timestamp or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    try:
        raw_feed, input_files = _load_canonical_input(input_path)
        cutoff = pd.Timestamp(args.cutoff) if args.cutoff else raw_feed["Timestamp"].max()
        raw_feed = causal_slice(raw_feed, cutoff)
        if raw_feed.empty:
            raise FeedContractError("No feed rows available at or before cutoff")
        window_quality = build_window_quality(raw_feed, cutoff)
        calculation_feed = deduplicate_feed(raw_feed)
        if args.progression_start:
            progression_start = pd.Timestamp(args.progression_start)
            progression_start = (
                progression_start.tz_localize("UTC")
                if progression_start.tzinfo is None
                else progression_start.tz_convert("UTC")
            )
            feed = calculation_feed.loc[calculation_feed["Timestamp"] >= progression_start].copy()
        else:
            if args.registry_in and calculation_feed["Timestamp"].dt.floor("D").nunique() > 1:
                raise FeedContractError(
                    "--progression-start is required when registry-in is combined with multi-day context"
                )
            feed = calculation_feed
        if feed.empty:
            raise FeedContractError("No progression rows available for requested interval")
        frames = write_outputs(
            feed,
            output_dir,
            run_timestamp=run_timestamp,
            input_files=input_files,
            registry_in_path=Path(args.registry_in) if args.registry_in else None,
            registry_out_path=Path(args.registry_out) if args.registry_out else None,
            calculation_feed=calculation_feed,
            window_quality=window_quality,
        )
    except (FeedContractError, FeedSourceError, FileNotFoundError, ValueError) as exc:
        print(f"market monitor failed: {exc}", file=sys.stderr)
        return 2

    print(
        "market monitor complete: "
        f"rows={len(feed)} output={output_dir} "
        f"structure_levels={len(frames['structure_levels.csv'])} "
        f"liquidity_zones={len(frames['liquidity_map.csv'])} "
        f"registry_zones={len(frames['liquidity_zone_registry.csv'])}"
    )
    return 0


def _load_canonical_input(input_path: Path) -> tuple[pd.DataFrame, list[str]]:
    if input_path.is_dir():
        days = discover_daily_dates(input_path)
        if not days:
            raise FeedContractError("No daily feed CSV files found")
        selected = [resolve_daily_feed_source(input_path, day) for day in days]
        paths = [item.path for item in selected]
    else:
        try:
            day = datetime.strptime(input_path.stem, "%Y-%m-%d").date()
        except ValueError:
            paths = [input_path]
        else:
            paths = [resolve_daily_feed_source(input_path.parent, day).path]
    return load_feed(paths, deduplicate=False), [str(path) for path in paths]


if __name__ == "__main__":
    raise SystemExit(main())
