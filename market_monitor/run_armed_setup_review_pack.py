from __future__ import annotations

import argparse
import sys
from pathlib import Path

from market_monitor.armed_setup_review_pack import (
    ArmedSetupReviewPackError,
    ReviewIntervalInput,
    run_armed_setup_review_pack,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a research-only manual review pack for ARMED setup rows from replay validation."
    )
    parser.add_argument("--replay-results", required=True, help="Path to 38A setup_replay_results.csv.")
    parser.add_argument(
        "--interval",
        action="append",
        required=True,
        help="Interval spec: interval_id|start_iso|end_iso|setup_research_timeline.csv|selected_zones.csv",
    )
    parser.add_argument("--feed-dir", required=True, help="Directory containing feed YYYY-MM-DD.csv files.")
    parser.add_argument("--out-dir", required=True, help="Output directory for the manual review pack.")
    args = parser.parse_args(argv)

    try:
        result = run_armed_setup_review_pack(
            replay_results_path=Path(args.replay_results),
            intervals=[_parse_interval_spec(spec) for spec in args.interval],
            feed_dir=Path(args.feed_dir),
            output_dir=Path(args.out_dir),
        )
    except (ArmedSetupReviewPackError, ValueError) as exc:
        print(f"armed setup review pack failed: {exc}", file=sys.stderr)
        return 2

    print(
        "armed setup review pack complete: "
        f"armed_rows={result.armed_count} "
        f"chart_data_files={result.chart_data_count} "
        f"review_csv={result.review_path} "
        f"summary={result.summary_path} "
        f"manifest={result.manifest_path}"
    )
    return 0


def _parse_interval_spec(spec: str) -> ReviewIntervalInput:
    parts = spec.split("|")
    if len(parts) not in {4, 5}:
        raise ValueError("interval spec must have 4 or 5 pipe-separated fields")
    selected_zones = Path(parts[4]) if len(parts) == 5 and parts[4] else None
    return ReviewIntervalInput(
        interval_id=parts[0],
        start=parts[1],
        end=parts[2],
        setup_timeline_path=Path(parts[3]),
        selected_zones_path=selected_zones,
    )


if __name__ == "__main__":
    raise SystemExit(main())
