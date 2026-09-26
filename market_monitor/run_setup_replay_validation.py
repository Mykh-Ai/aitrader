from __future__ import annotations

import argparse
import sys
from pathlib import Path

from market_monitor.setup_replay_validation import (
    ReplayInterval,
    SetupReplayValidationError,
    run_setup_replay_validation,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Replay-validate existing 37K setup timeline rows using forward feed path only for outcomes."
    )
    parser.add_argument(
        "--interval",
        action="append",
        required=True,
        help="Interval spec: interval_id|start_iso|end_iso|setup_research_timeline.csv|setup_builder_manifest.json",
    )
    parser.add_argument("--feed-dir", required=True, help="Directory containing feed YYYY-MM-DD.csv files.")
    parser.add_argument("--out-dir", required=True, help="Output directory for setup replay validation artifacts.")
    args = parser.parse_args(argv)

    try:
        intervals = [_parse_interval_spec(spec) for spec in args.interval]
        result = run_setup_replay_validation(
            intervals=intervals,
            feed_dir=Path(args.feed_dir),
            output_dir=Path(args.out_dir),
        )
    except (SetupReplayValidationError, ValueError) as exc:
        print(f"setup replay validation failed: {exc}", file=sys.stderr)
        return 2

    print(
        "setup replay validation complete: "
        f"rows={result.result_count} "
        f"setup_replay_results={result.results_path} "
        f"summary={result.summary_path} "
        f"manifest={result.manifest_path}"
    )
    return 0


def _parse_interval_spec(spec: str) -> ReplayInterval:
    parts = spec.split("|")
    if len(parts) not in {4, 5}:
        raise ValueError("interval spec must have 4 or 5 pipe-separated fields")
    manifest = Path(parts[4]) if len(parts) == 5 and parts[4] else None
    return ReplayInterval(
        interval_id=parts[0],
        start=parts[1],
        end=parts[2],
        setup_timeline_path=Path(parts[3]),
        setup_manifest_path=manifest,
    )


if __name__ == "__main__":
    raise SystemExit(main())
