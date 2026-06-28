from __future__ import annotations

import argparse
import sys
from pathlib import Path

from market_monitor.market_structure_state import (
    MarketStructureStateError,
    run_market_structure_state,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run SHI_RESET_37E online market-structure state memory from daily monitor outputs and feed."
    )
    parser.add_argument("--start", required=True, help="Inclusive start date YYYY-MM-DD.")
    parser.add_argument("--end", required=True, help="Inclusive end date YYYY-MM-DD.")
    parser.add_argument(
        "--input-root",
        required=True,
        help="Directory containing accepted daily Market Monitor output directories.",
    )
    parser.add_argument("--feed-dir", required=True, help="Directory containing feed YYYY-MM-DD.csv files.")
    parser.add_argument("--out-dir", required=True, help="Output directory for 37E state artifacts.")
    parser.add_argument(
        "--as-of",
        default="",
        help="Optional ISO timestamp for online-safe intraday state, e.g. 2026-04-07T18:00:00.",
    )
    parser.add_argument(
        "--merge-gap-bps",
        type=float,
        default=50.0,
        help="Maximum price gap in bps for merging nearby levels into one trader-readable band.",
    )
    args = parser.parse_args(argv)

    try:
        result = run_market_structure_state(
            input_root=Path(args.input_root),
            feed_dir=Path(args.feed_dir),
            output_dir=Path(args.out_dir),
            start=args.start,
            end=args.end,
            as_of=args.as_of,
            merge_gap_bps=args.merge_gap_bps,
        )
    except MarketStructureStateError as exc:
        print(f"market structure state failed: {exc}", file=sys.stderr)
        return 2

    print(
        "market structure state complete: "
        f"levels={result.level_count} "
        f"events={result.event_count} "
        f"states={result.state_count} "
        f"market_structure_levels={result.levels_path} "
        f"market_structure_events={result.events_path} "
        f"market_structure_state_timeline={result.state_timeline_path} "
        f"summary={result.summary_path} "
        f"manifest={result.manifest_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
