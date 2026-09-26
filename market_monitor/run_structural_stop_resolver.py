from __future__ import annotations

import argparse
from pathlib import Path

from market_monitor.structural_stop_resolver import StructuralStopResolverError, run_structural_stop_resolver


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run SHI_RESET_38H structural swing-stop resolver.")
    parser.add_argument("--live-like-replay", required=True, help="Path to 38G live_like_bar_by_bar_state_replay.csv.")
    parser.add_argument("--focus-alignment", required=True, help="Path to 38G focus_setup_alignment_check.csv.")
    parser.add_argument("--manual-verdicts", required=True, help="Path to 38C armed_setup_manual_verdicts.csv.")
    parser.add_argument("--out-dir", required=True, help="Output directory for structural stop resolver artifacts.")
    args = parser.parse_args(argv)

    try:
        result = run_structural_stop_resolver(
            live_like_replay_path=Path(args.live_like_replay),
            focus_alignment_path=Path(args.focus_alignment),
            manual_verdicts_path=Path(args.manual_verdicts),
            output_dir=Path(args.out_dir),
        )
    except StructuralStopResolverError as exc:
        print(f"structural stop resolver failed: {exc}")
        return 2

    print(
        "structural stop resolver complete: "
        f"rows={result.row_count} "
        f"candidates={result.candidates_path} "
        f"summary={result.summary_path} "
        f"manifest={result.manifest_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
