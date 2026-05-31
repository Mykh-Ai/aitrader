from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from market_monitor.config import DEFAULT_OUTPUT_ROOT, DEFAULT_RUN_ID
from market_monitor.feed_adapter import FeedContractError, load_feed
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
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    output_dir = Path(args.output) if args.output else DEFAULT_OUTPUT_ROOT / DEFAULT_RUN_ID
    run_timestamp = args.run_timestamp or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    try:
        feed = load_feed(input_path)
        input_files = sorted(feed["SourceFile"].unique().tolist())
        frames = write_outputs(
            feed,
            output_dir,
            run_timestamp=run_timestamp,
            input_files=input_files,
        )
    except (FeedContractError, FileNotFoundError) as exc:
        print(f"market monitor failed: {exc}", file=sys.stderr)
        return 2

    print(
        "market monitor complete: "
        f"rows={len(feed)} output={output_dir} "
        f"structure_levels={len(frames['structure_levels.csv'])} "
        f"liquidity_zones={len(frames['liquidity_map.csv'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
