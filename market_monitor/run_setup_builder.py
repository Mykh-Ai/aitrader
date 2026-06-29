from __future__ import annotations

import argparse
from pathlib import Path

from market_monitor.setup_builder import run_setup_builder


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build research-only setup candidates from downstream Market Monitor artifacts."
    )
    parser.add_argument("--state-timeline", required=True, help="Path to market_structure_state_timeline.csv.")
    parser.add_argument("--regime-windows", required=True, help="Path to market_regime_windows.csv.")
    parser.add_argument("--selected-zones", required=True, help="Path to selected_zones.csv.")
    parser.add_argument(
        "--hidden-flow-candidates",
        default="",
        help="Optional path to hidden_flow_candidates.csv. Empty files do not block setup research candidates.",
    )
    parser.add_argument("--out-dir", required=True, help="Output directory for setup builder artifacts.")
    args = parser.parse_args(argv)

    result = run_setup_builder(
        state_timeline_path=Path(args.state_timeline),
        regime_windows_path=Path(args.regime_windows),
        selected_zones_path=Path(args.selected_zones),
        hidden_flow_candidates_path=Path(args.hidden_flow_candidates) if args.hidden_flow_candidates else None,
        output_dir=Path(args.out_dir),
    )
    print(
        "setup builder complete: "
        f"candidates={result.candidate_count} "
        f"setup_research_timeline={result.candidates_path} "
        f"manifest={result.manifest_path} "
        f"summary={result.summary_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
