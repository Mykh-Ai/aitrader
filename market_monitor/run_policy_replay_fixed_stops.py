from __future__ import annotations

import argparse
from pathlib import Path

from market_monitor.policy_replay_fixed_stops import PolicyReplayFixedStopsError, run_policy_replay_fixed_stops


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run SHI_RESET_38I fixed-anchor structural-stop policy replay.")
    parser.add_argument("--focus-alignment", required=True, help="Path to 38G focus_setup_alignment_check.csv.")
    parser.add_argument("--structural-stops", required=True, help="Path to 38H structural_stop_reference_candidates.csv.")
    parser.add_argument("--manual-verdicts", required=True, help="Path to 38C armed_setup_manual_verdicts.csv.")
    parser.add_argument("--feed-dir", required=True, help="Directory containing feed YYYY-MM-DD.csv files.")
    parser.add_argument("--out-dir", required=True, help="Output directory for fixed-stop policy replay artifacts.")
    args = parser.parse_args(argv)

    try:
        result = run_policy_replay_fixed_stops(
            focus_alignment_path=Path(args.focus_alignment),
            structural_stops_path=Path(args.structural_stops),
            manual_verdicts_path=Path(args.manual_verdicts),
            feed_dir=Path(args.feed_dir),
            output_dir=Path(args.out_dir),
        )
    except PolicyReplayFixedStopsError as exc:
        print(f"fixed-stop policy replay failed: {exc}")
        return 2

    print(
        "fixed-stop policy replay complete: "
        f"rows={result.row_count} "
        f"results={result.results_path} "
        f"summary={result.summary_path} "
        f"manifest={result.manifest_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
