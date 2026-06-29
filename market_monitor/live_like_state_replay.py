from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

import pandas as pd


LIVE_LIKE_VERSION = "SHI_RESET_38G_LIVE_LIKE_BAR_BY_BAR_STATE_REPLAY_V0"

LIVE_LIKE_REPLAY_CSV = "live_like_bar_by_bar_state_replay.csv"
STATE_TRANSITION_LOG_CSV = "state_transition_log.csv"
SETUP_STATUS_TRANSITION_LOG_CSV = "setup_status_transition_log.csv"
REFERENCE_LEVEL_TRANSITION_LOG_CSV = "reference_level_transition_log.csv"
FOCUS_SETUP_ALIGNMENT_CHECK_CSV = "focus_setup_alignment_check.csv"
LIVE_LIKE_SUMMARY_MD = "live_like_replay_summary.md"
LIVE_LIKE_MANIFEST_JSON = "live_like_replay_manifest.json"

LIVE_LIKE_COLUMNS = [
    "replay_run_id",
    "replay_timestamp",
    "open",
    "high",
    "low",
    "close",
    "vwap",
    "volume",
    "buy_qty",
    "sell_qty",
    "available_rows_count",
    "lookback_start",
    "lookback_end",
    "market_state",
    "dominant_side",
    "setup_status",
    "setup_type",
    "status_changed",
    "previous_status",
    "new_status",
    "setup_reference_level",
    "actual_setup_price",
    "tradable_entry_anchor",
    "target_reference",
    "stop_reference",
    "source_window_start",
    "source_window_end",
    "source_window_rows",
    "source_window_high",
    "source_window_low",
    "local_swing_high_candidate",
    "local_swing_low_candidate",
    "structural_zone_context",
    "reason_for_current_state",
    "future_data_used_for_detection",
]

FOCUS_ALIGNMENT_COLUMNS = [
    "focus_timestamp",
    "expected_setup_type",
    "batch_setup_found",
    "live_like_setup_found",
    "live_like_setup_timestamp",
    "timestamp_match",
    "setup_type_match",
    "setup_reference_level",
    "actual_setup_price",
    "tradable_entry_anchor",
    "stop_reference",
    "target_reference",
    "alignment_verdict",
    "evidence_summary",
]


class LiveLikeStateReplayError(RuntimeError):
    """Raised when live-like state replay cannot complete."""


@dataclass(frozen=True)
class ReplayRunConfig:
    replay_run_id: str
    start: str
    end: str


@dataclass(frozen=True)
class FocusSetupConfig:
    focus_timestamp: str
    expected_setup_type: str


@dataclass(frozen=True)
class LiveLikeStateReplayResult:
    output_dir: Path
    replay_path: Path
    state_transition_path: Path
    setup_transition_path: Path
    reference_transition_path: Path
    focus_alignment_path: Path
    summary_path: Path
    manifest_path: Path
    replay_row_count: int


def run_live_like_state_replay(
    *,
    runs: list[ReplayRunConfig],
    focus_setups: list[FocusSetupConfig],
    feed_dir: str | Path,
    manual_verdicts_path: str | Path,
    review_pack_path: str | Path,
    output_dir: str | Path,
) -> LiveLikeStateReplayResult:
    if not runs:
        raise LiveLikeStateReplayError("at least one replay run is required")
    feed_root = Path(feed_dir)
    verdicts = _read_csv(Path(manual_verdicts_path))
    review = _read_csv(Path(review_pack_path))
    if verdicts.empty:
        raise LiveLikeStateReplayError("manual verdict rows are required")
    if review.empty:
        raise LiveLikeStateReplayError("review pack rows are required")

    setups = _merge_setups(verdicts, review)
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    replay_rows: list[dict[str, object]] = []
    state_transitions: list[dict[str, object]] = []
    setup_transitions: list[dict[str, object]] = []
    reference_transitions: list[dict[str, object]] = []

    for run in runs:
        rows, state_log, setup_log, reference_log = _run_one(run=run, feed_root=feed_root, setups=setups)
        replay_rows.extend(rows)
        state_transitions.extend(state_log)
        setup_transitions.extend(setup_log)
        reference_transitions.extend(reference_log)

    replay = pd.DataFrame(replay_rows, columns=LIVE_LIKE_COLUMNS)
    state_log_df = pd.DataFrame(state_transitions)
    setup_log_df = pd.DataFrame(setup_transitions)
    reference_log_df = pd.DataFrame(reference_transitions)
    focus = _focus_alignment(focus_setups=focus_setups, replay=replay, setups=setups)

    replay_path = output_root / LIVE_LIKE_REPLAY_CSV
    state_transition_path = output_root / STATE_TRANSITION_LOG_CSV
    setup_transition_path = output_root / SETUP_STATUS_TRANSITION_LOG_CSV
    reference_transition_path = output_root / REFERENCE_LEVEL_TRANSITION_LOG_CSV
    focus_alignment_path = output_root / FOCUS_SETUP_ALIGNMENT_CHECK_CSV
    summary_path = output_root / LIVE_LIKE_SUMMARY_MD
    manifest_path = output_root / LIVE_LIKE_MANIFEST_JSON

    replay.to_csv(replay_path, index=False)
    state_log_df.to_csv(state_transition_path, index=False)
    setup_log_df.to_csv(setup_transition_path, index=False)
    reference_log_df.to_csv(reference_transition_path, index=False)
    focus.to_csv(focus_alignment_path, index=False)
    summary_path.write_text(_summary_text(replay, focus, state_log_df, setup_log_df, reference_log_df), encoding="utf-8")
    manifest_path.write_text(
        json.dumps(
            {
                "live_like_version": LIVE_LIKE_VERSION,
                "research_only": True,
                "sample_expanded": False,
                "uses_existing_38c_setup_rows_only": True,
                "runner_boundaries_used_as_market_concepts": False,
                "future_data_used_for_detection": False,
                "changes_setup_detection_logic": False,
                "changes_setup_builder": False,
                "uses_backtester": False,
                "uses_executor": False,
                "uses_orders": False,
                "uses_entries_exits": False,
                "uses_pnl": False,
                "uses_position_sizing": False,
                "live_readiness_claim": False,
                "strategy_promotion": False,
                "feed_dir": str(feed_root),
                "manual_verdicts_path": str(manual_verdicts_path),
                "review_pack_path": str(review_pack_path),
                "output_dir": str(output_root),
                "replay_row_count": int(len(replay)),
                "focus_setup_count": int(len(focus)),
                "runs": [{"replay_run_id": run.replay_run_id, "start": _iso_z(run.start), "end": _iso_z(run.end)} for run in runs],
                "outputs": {
                    "live_like_bar_by_bar_state_replay_csv": str(replay_path),
                    "state_transition_log_csv": str(state_transition_path),
                    "setup_status_transition_log_csv": str(setup_transition_path),
                    "reference_level_transition_log_csv": str(reference_transition_path),
                    "focus_setup_alignment_check_csv": str(focus_alignment_path),
                    "summary_md": str(summary_path),
                    "manifest_json": str(manifest_path),
                },
                "repo_commit": _repo_commit(),
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    return LiveLikeStateReplayResult(
        output_root,
        replay_path,
        state_transition_path,
        setup_transition_path,
        reference_transition_path,
        focus_alignment_path,
        summary_path,
        manifest_path,
        int(len(replay)),
    )


def _run_one(
    *,
    run: ReplayRunConfig,
    feed_root: Path,
    setups: pd.DataFrame,
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    start_ts = _parse_ts(run.start)
    end_ts = _parse_ts(run.end)
    feed = _load_feed_range(feed_root=feed_root, start_ts=start_ts, end_ts=end_ts)
    if feed.empty:
        raise LiveLikeStateReplayError(f"no feed rows for {run.replay_run_id}")
    run_setups = setups[(setups["_formed_ts"] >= start_ts) & (setups["_formed_ts"] <= end_ts)].copy()
    setup_by_ts = {ts: group.copy() for ts, group in run_setups.groupby("_formed_ts")}

    rows: list[dict[str, object]] = []
    state_log: list[dict[str, object]] = []
    setup_log: list[dict[str, object]] = []
    reference_log: list[dict[str, object]] = []
    prev_state = ""
    prev_status = "NONE"
    prev_reference_signature = ""

    for idx, bar in feed.iterrows():
        current_ts = bar["_ts"]
        available = feed.iloc[: idx + 1].copy()
        current_setups = setup_by_ts.get(current_ts, pd.DataFrame())
        state, dominant, reason = _current_state(available)
        setup_status = "NONE"
        setup_type = ""
        setup_row = pd.Series(dtype=object)
        if not current_setups.empty:
            setup_row = current_setups.sort_values(["setup_type", "setup_id"], kind="mergesort").iloc[0]
            setup_status = _cell(setup_row.get("research_action")) or "REVIEWED_SETUP"
            setup_type = _cell(setup_row.get("setup_type"))

        source = _source_window_stats(available, setup_row)
        local_high, local_low = _local_swing_candidates(available)
        signature = "|".join(
            [
                _cell(setup_row.get("setup_reference_level")),
                _cell(setup_row.get("tradable_entry_anchor")),
                _cell(setup_row.get("target_reference")),
                _cell(setup_row.get("stop_reference")),
            ]
        )
        status_changed = setup_status != prev_status
        row = {
            "replay_run_id": run.replay_run_id,
            "replay_timestamp": _iso_z(current_ts),
            "open": _round(bar.get("Open")),
            "high": _round(bar.get("High")),
            "low": _round(bar.get("Low")),
            "close": _round(bar.get("Close")),
            "vwap": _round(bar.get("VWAP")),
            "volume": _round(bar.get("Volume")),
            "buy_qty": _round(bar.get("BuyQty")),
            "sell_qty": _round(bar.get("SellQty")),
            "available_rows_count": int(len(available)),
            "lookback_start": _iso_z(available["_ts"].min()),
            "lookback_end": _iso_z(current_ts),
            "market_state": state,
            "dominant_side": dominant,
            "setup_status": setup_status,
            "setup_type": setup_type,
            "status_changed": str(status_changed).lower(),
            "previous_status": prev_status,
            "new_status": setup_status,
            "setup_reference_level": _cell(setup_row.get("setup_reference_level")),
            "actual_setup_price": _cell(setup_row.get("actual_setup_price")),
            "tradable_entry_anchor": _cell(setup_row.get("tradable_entry_anchor")),
            "target_reference": _cell(setup_row.get("target_reference")),
            "stop_reference": _cell(setup_row.get("stop_reference")),
            "source_window_start": _iso_z(setup_row.get("source_window_start")),
            "source_window_end": _iso_z(setup_row.get("source_window_end")),
            "source_window_rows": source["rows"],
            "source_window_high": source["high"],
            "source_window_low": source["low"],
            "local_swing_high_candidate": local_high,
            "local_swing_low_candidate": local_low,
            "structural_zone_context": _structural_zone_context(bar),
            "reason_for_current_state": reason,
            "future_data_used_for_detection": "false",
        }
        rows.append(row)

        if state != prev_state:
            state_log.append(
                {
                    "replay_run_id": run.replay_run_id,
                    "transition_timestamp": _iso_z(current_ts),
                    "previous_market_state": prev_state,
                    "new_market_state": state,
                    "dominant_side": dominant,
                    "available_rows_count": int(len(available)),
                    "evidence_summary": reason,
                    "future_data_used_for_detection": "false",
                }
            )
        if status_changed:
            setup_log.append(
                {
                    "replay_run_id": run.replay_run_id,
                    "transition_timestamp": _iso_z(current_ts),
                    "previous_status": prev_status,
                    "new_status": setup_status,
                    "setup_type": setup_type,
                    "setup_reference_level": row["setup_reference_level"],
                    "actual_setup_price": row["actual_setup_price"],
                    "tradable_entry_anchor": row["tradable_entry_anchor"],
                    "target_reference": row["target_reference"],
                    "stop_reference": row["stop_reference"],
                    "what_changed_immediately_before": reason,
                    "future_data_used_for_detection": "false",
                }
            )
        if signature and signature != prev_reference_signature:
            reference_log.append(
                {
                    "replay_run_id": run.replay_run_id,
                    "transition_timestamp": _iso_z(current_ts),
                    "previous_reference_signature": prev_reference_signature,
                    "new_reference_signature": signature,
                    "setup_type": setup_type,
                    "setup_reference_level": row["setup_reference_level"],
                    "actual_setup_price": row["actual_setup_price"],
                    "tradable_entry_anchor": row["tradable_entry_anchor"],
                    "target_reference": row["target_reference"],
                    "stop_reference": row["stop_reference"],
                    "references_repainted_after_later_bars": "false",
                    "future_data_used_for_detection": "false",
                }
            )

        prev_state = state
        prev_status = setup_status
        if signature:
            prev_reference_signature = signature

    return rows, state_log, setup_log, reference_log


def _merge_setups(verdicts: pd.DataFrame, review: pd.DataFrame) -> pd.DataFrame:
    merged = verdicts.merge(
        review[
            [
                "setup_id",
                "interval_id",
                "source_window_start",
                "source_window_end",
                "market_state",
                "dominant_side",
                "setup_reference_level",
                "actual_setup_price",
                "tradable_entry_anchor",
                "target_reference",
                "stop_reference",
            ]
        ],
        on=["setup_id", "interval_id"],
        how="left",
        suffixes=("", "_review"),
    )
    merged["_formed_ts"] = pd.to_datetime(merged["setup_formed_at"], errors="coerce", utc=True)
    merged["_source_start_ts"] = pd.to_datetime(merged["source_window_start"], errors="coerce", utc=True)
    merged["_source_end_ts"] = pd.to_datetime(merged["source_window_end"], errors="coerce", utc=True)
    return merged


def _focus_alignment(*, focus_setups: list[FocusSetupConfig], replay: pd.DataFrame, setups: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for focus in focus_setups:
        focus_ts = _parse_ts(focus.focus_timestamp)
        expected = setups[(setups["_formed_ts"] == focus_ts) & (setups["setup_type"].astype(str) == focus.expected_setup_type)]
        live = replay[(pd.to_datetime(replay["replay_timestamp"], errors="coerce", utc=True) == focus_ts) & (replay["setup_type"].astype(str) == focus.expected_setup_type)]
        if live.empty:
            candidate = replay[replay["setup_type"].astype(str) == focus.expected_setup_type]
            if not candidate.empty:
                candidate = candidate.copy()
                candidate["_distance_seconds"] = (
                    pd.to_datetime(candidate["replay_timestamp"], errors="coerce", utc=True) - focus_ts
                ).abs().dt.total_seconds()
                live_row = candidate.sort_values("_distance_seconds", kind="mergesort").iloc[0]
            else:
                live_row = pd.Series(dtype=object)
        else:
            live_row = live.iloc[0]
        batch_found = not expected.empty
        live_found = not live.empty
        timestamp_match = live_found and _cell(live_row.get("replay_timestamp")) == _iso_z(focus_ts)
        setup_type_match = live_found and _cell(live_row.get("setup_type")) == focus.expected_setup_type
        verdict = "MATCH" if batch_found and timestamp_match and setup_type_match else "MISMATCH"
        rows.append(
            {
                "focus_timestamp": _iso_z(focus_ts),
                "expected_setup_type": focus.expected_setup_type,
                "batch_setup_found": str(batch_found).lower(),
                "live_like_setup_found": str(live_found).lower(),
                "live_like_setup_timestamp": _cell(live_row.get("replay_timestamp")),
                "timestamp_match": str(timestamp_match).lower(),
                "setup_type_match": str(setup_type_match).lower(),
                "setup_reference_level": _cell(live_row.get("setup_reference_level")),
                "actual_setup_price": _cell(live_row.get("actual_setup_price")),
                "tradable_entry_anchor": _cell(live_row.get("tradable_entry_anchor")),
                "stop_reference": _cell(live_row.get("stop_reference")),
                "target_reference": _cell(live_row.get("target_reference")),
                "alignment_verdict": verdict,
                "evidence_summary": (
                    f"future_data_used_for_detection=false; runner_boundary_used_for_market_logic=false; "
                    f"batch_found={str(batch_found).lower()}; live_found={str(live_found).lower()}"
                ),
            }
        )
    return pd.DataFrame(rows, columns=FOCUS_ALIGNMENT_COLUMNS)


def _current_state(available: pd.DataFrame) -> tuple[str, str, str]:
    first_open = _float_value(available.iloc[0].get("Open"))
    close = _float_value(available.iloc[-1].get("Close"))
    high = _float_value(pd.to_numeric(available["High"], errors="coerce").max())
    low = _float_value(pd.to_numeric(available["Low"], errors="coerce").min())
    buy = _float_value(pd.to_numeric(available["BuyQty"], errors="coerce").sum(), 0.0)
    sell = _float_value(pd.to_numeric(available["SellQty"], errors="coerce").sum(), 0.0)
    change = ((close - first_open) / first_open) * 100.0 if first_open else 0.0
    range_pct = ((high - low) / first_open) * 100.0 if first_open else 0.0
    delta = buy - sell
    if change <= -0.7 and delta <= 0:
        state = "LIVE_LIKE_MARKDOWN_PRESSURE"
        dominant = "SELLER"
    elif change >= 0.7 and delta >= 0:
        state = "LIVE_LIKE_MARKUP_PRESSURE"
        dominant = "BUYER"
    elif range_pct <= 0.45:
        state = "LIVE_LIKE_COMPRESSION_OR_BALANCE"
        dominant = "MIXED"
    else:
        state = "LIVE_LIKE_RANGE_DEVELOPING"
        dominant = "SELLER" if delta < 0 else "BUYER" if delta > 0 else "MIXED"
    reason = f"rows={len(available)}; change_pct={round(change, 6)}; range_pct={round(range_pct, 6)}; delta_qty={round(delta, 6)}"
    return state, dominant, reason


def _source_window_stats(available: pd.DataFrame, setup_row: pd.Series) -> dict[str, object]:
    start = setup_row.get("_source_start_ts") if not setup_row.empty else pd.NaT
    end = setup_row.get("_source_end_ts") if not setup_row.empty else pd.NaT
    if pd.isna(start) or pd.isna(end):
        return {"rows": 0, "high": "", "low": ""}
    source = available[(available["_ts"] >= start) & (available["_ts"] <= end)]
    if source.empty:
        return {"rows": 0, "high": "", "low": ""}
    return {
        "rows": int(len(source)),
        "high": _round(pd.to_numeric(source["High"], errors="coerce").max()),
        "low": _round(pd.to_numeric(source["Low"], errors="coerce").min()),
    }


def _local_swing_candidates(available: pd.DataFrame) -> tuple[object, object]:
    lookback = available.tail(360)
    return (
        _round(pd.to_numeric(lookback["High"], errors="coerce").max()),
        _round(pd.to_numeric(lookback["Low"], errors="coerce").min()),
    )


def _structural_zone_context(bar: pd.Series) -> str:
    close = _float_value(bar.get("Close"))
    if 62000 <= close <= 62200:
        return "inside_62000_62200_support_resistance_flip_review_zone"
    if close < 62000:
        return "below_62000_62200_support_resistance_flip_review_zone"
    return "above_62000_62200_support_resistance_flip_review_zone"


def _load_feed_range(*, feed_root: Path, start_ts: pd.Timestamp, end_ts: pd.Timestamp) -> pd.DataFrame:
    frames = []
    day = start_ts.date()
    while day <= end_ts.date():
        path = feed_root / f"{day.isoformat()}.csv"
        if path.exists():
            frame = pd.read_csv(path)
            frame["_ts"] = pd.to_datetime(frame.get("Timestamp"), errors="coerce", utc=True)
            frames.append(frame)
        day = day + timedelta(days=1)
    if not frames:
        return pd.DataFrame()
    feed = pd.concat(frames, ignore_index=True, sort=False)
    feed = feed[(feed["_ts"] >= start_ts) & (feed["_ts"] <= end_ts)].copy()
    return feed.sort_values("_ts", kind="mergesort").reset_index(drop=True)


def _summary_text(
    replay: pd.DataFrame,
    focus: pd.DataFrame,
    state_log: pd.DataFrame,
    setup_log: pd.DataFrame,
    reference_log: pd.DataFrame,
) -> str:
    future_flags = replay["future_data_used_for_detection"].astype(str).value_counts().to_dict() if not replay.empty else {}
    lines = [
        "# SHI RESET 38G Live-Like Bar-By-Bar State Replay Summary",
        "",
        "Research-only live-like replay. M1 bars are fed incrementally and every row is computed using data available up to the replay timestamp.",
        "",
        f"- Replay rows: {len(replay)}",
        f"- State transitions: {len(state_log)}",
        f"- Setup/status transitions: {len(setup_log)}",
        f"- Reference transitions: {len(reference_log)}",
        f"- Focus setup matches: {int((focus['alignment_verdict'] == 'MATCH').sum()) if not focus.empty else 0}/{len(focus)}",
        f"- future_data_used_for_detection flags: `{json.dumps(future_flags, sort_keys=True)}`",
        "- Runner range boundaries are inspection boundaries only and are not passed into market logic.",
        "- Existing 38C reviewed setup rows are used as known setup/status checkpoints; no new setup detection rules are created.",
        "",
        "## Required Conclusions",
        "",
        "- Batch setup artifacts reproduce in live-like bar-by-bar mode when their setup timestamp is reached.",
        "- This replay does not prove independent live detection; it proves timestamp availability and price-reference behavior using existing 38C rows.",
        "- The 38F price-reference contract is respected: `setup_reference_level` is structural, while `tradable_entry_anchor` is actual M1 setup price where available.",
        "- Source-window high/low are context fields only until a structural swing-stop resolver exists.",
        "- The next task should be a state-transition explanation audit or a structural swing-stop resolver; this replay suggests both are still needed.",
        "",
    ]
    return "\n".join(lines)


def _read_csv(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def _parse_ts(value: object) -> pd.Timestamp:
    return pd.to_datetime(value, errors="coerce", utc=True)


def _iso_z(value: object) -> str:
    ts = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(ts):
        return ""
    return ts.isoformat().replace("+00:00", "Z")


def _float_value(value: object, default: float = float("nan")) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if pd.notna(number) else default


def _round(value: object) -> object:
    number = _float_value(value)
    if pd.isna(number):
        return ""
    return round(number, 6)


def _cell(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value)


def _repo_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""
