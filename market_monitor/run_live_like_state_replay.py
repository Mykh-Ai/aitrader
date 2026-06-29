from __future__ import annotations

import argparse
from pathlib import Path

from market_monitor.live_like_state_replay import (
    FocusSetupConfig,
    LiveLikeStateReplayError,
    ReplayRunConfig,
    run_live_like_state_replay,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run SHI_RESET_38G live-like M1 bar-by-bar state replay.")
    parser.add_argument(
        "--run",
        action="append",
        required=True,
        help="Replay run spec: replay_run_id|start_iso|end_iso.",
    )
    parser.add_argument(
        "--focus",
        action="append",
        required=True,
        help="Focus setup spec: focus_timestamp_iso|expected_setup_type.",
    )
    parser.add_argument("--feed-dir", required=True, help="Directory containing feed YYYY-MM-DD.csv files.")
    parser.add_argument("--manual-verdicts", required=True, help="Path to 38C armed_setup_manual_verdicts.csv.")
    parser.add_argument("--review-pack", required=True, help="Path to 38B armed_setup_manual_review.csv.")
    parser.add_argument("--out-dir", required=True, help="Output directory for live-like replay artifacts.")
    args = parser.parse_args(argv)

    try:
        result = run_live_like_state_replay(
            runs=[_parse_run_spec(spec) for spec in args.run],
            focus_setups=[_parse_focus_spec(spec) for spec in args.focus],
            feed_dir=Path(args.feed_dir),
            manual_verdicts_path=Path(args.manual_verdicts),
            review_pack_path=Path(args.review_pack),
            output_dir=Path(args.out_dir),
        )
    except (LiveLikeStateReplayError, ValueError) as exc:
        print(f"live-like state replay failed: {exc}")
        return 2

    print(
        "live-like state replay complete: "
        f"rows={result.replay_row_count} "
        f"replay={result.replay_path} "
        f"focus={result.focus_alignment_path} "
        f"summary={result.summary_path} "
        f"manifest={result.manifest_path}"
    )
    return 0


def _parse_run_spec(spec: str) -> ReplayRunConfig:
    parts = spec.split("|")
    if len(parts) != 3:
        raise ValueError("run spec must have 3 pipe-separated fields")
    return ReplayRunConfig(replay_run_id=parts[0], start=parts[1], end=parts[2])


def _parse_focus_spec(spec: str) -> FocusSetupConfig:
    parts = spec.split("|")
    if len(parts) != 2:
        raise ValueError("focus spec must have 2 pipe-separated fields")
    return FocusSetupConfig(focus_timestamp=parts[0], expected_setup_type=parts[1])


if __name__ == "__main__":
    raise SystemExit(main())
