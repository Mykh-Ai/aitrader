from __future__ import annotations

import argparse
from pathlib import Path

from market_monitor.wider_research_window import WiderResearchWindowError, run_wider_research_window


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run SHI_RESET_38J wider research-window setup classification.")
    parser.add_argument("--setup-timeline", required=True, help="Path to setup_research_timeline.csv.")
    parser.add_argument("--feed-dir", required=True, help="Directory containing feed YYYY-MM-DD.csv files.")
    parser.add_argument("--selected-zones", required=True, help="Path to selected_zones.csv.")
    parser.add_argument("--start", required=True, help="Start date, YYYY-MM-DD.")
    parser.add_argument("--end", required=True, help="End date, YYYY-MM-DD.")
    parser.add_argument("--out-dir", required=True, help="Output directory for 38J wider-window artifacts.")
    args = parser.parse_args(argv)

    try:
        result = run_wider_research_window(
            setup_timeline_path=Path(args.setup_timeline),
            feed_dir=Path(args.feed_dir),
            selected_zones_path=Path(args.selected_zones),
            start=args.start,
            end=args.end,
            output_dir=Path(args.out_dir),
        )
    except WiderResearchWindowError as exc:
        print(f"wider research-window classification failed: {exc}")
        return 2

    print(
        "wider research-window classification complete: "
        f"setups={result.setup_count} "
        f"policy_rows={result.policy_replay_count} "
        f"classification={result.classification_path} "
        f"summary={result.summary_path} "
        f"manifest={result.manifest_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
