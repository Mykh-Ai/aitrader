"""Sprint 04 holdout feed audit.

This script is a gate before any true holdout replay. It inspects local feed
files after the Sprint 03 freeze point and writes candidate-specific audit
artifacts. It does not run Analyzer, Backtester, Executor, or live trading.
"""

from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_CANDIDATE_ID = "CAND_SHORT_CTX_SPIKE_GE2_ENTRY_DELAY_1"
DEFAULT_CANDIDATE_DIR = Path("research/candidates") / DEFAULT_CANDIDATE_ID
REQUIRED_MIN_ROWS = 1000
MAX_SYNTHETIC_PCT = 5.0


@dataclass(frozen=True)
class FreezeContext:
    commit: str
    timestamp: pd.Timestamp


def read_freeze_context(protocol_path: Path) -> FreezeContext:
    text = protocol_path.read_text(encoding="utf-8")
    commit_match = re.search(r"Freeze point:\s*Sprint 03 commit `([^`]+)`", text)
    ts_match = re.search(r"Contract freeze timestamp:\s*`([^`]+)`", text)
    if not ts_match:
        raise SystemExit(f"Cannot find contract freeze timestamp in {protocol_path}")
    commit = commit_match.group(1) if commit_match else "UNKNOWN"
    timestamp = pd.Timestamp(ts_match.group(1))
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")
    return FreezeContext(commit=commit, timestamp=timestamp)


def find_feed_files(feed_root: Path, freeze_ts: pd.Timestamp) -> list[Path]:
    if not feed_root.exists():
        return []
    files: list[Path] = []
    freeze_day = freeze_ts.date()
    for path in sorted(feed_root.glob("*.csv")):
        try:
            day = date.fromisoformat(path.stem)
        except ValueError:
            continue
        if day >= freeze_day:
            files.append(path)
    return files


def _safe_numeric(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        return pd.Series([0.0] * len(frame.index), index=frame.index, dtype=float)
    return pd.to_numeric(frame[column], errors="coerce").fillna(0.0)


def audit_file(path: Path, freeze: FreezeContext) -> dict[str, Any]:
    day = date.fromisoformat(path.stem)
    df = pd.read_csv(path)
    rows = int(len(df.index))
    timestamps = pd.to_datetime(df.get("Timestamp"), utc=True, errors="coerce")
    valid_ts = timestamps.dropna()
    min_ts = valid_ts.min() if not valid_ts.empty else pd.NaT
    max_ts = valid_ts.max() if not valid_ts.empty else pd.NaT
    post_freeze_rows = int((timestamps > freeze.timestamp).sum()) if not valid_ts.empty else 0

    if "IsSynthetic" in df.columns:
        synthetic = pd.to_numeric(df["IsSynthetic"], errors="coerce").fillna(0).ne(0)
    else:
        synthetic = pd.Series([False] * rows, index=df.index)
    synthetic_pct = float(100.0 * synthetic.mean()) if rows else 0.0

    ohlc_cols = [col for col in ("Open", "High", "Low", "Close") if col in df.columns]
    zero_ohlc_rows = 0
    if ohlc_cols:
        ohlc = df[ohlc_cols].apply(pd.to_numeric, errors="coerce").fillna(0.0)
        zero_ohlc_rows = int((ohlc <= 0).any(axis=1).sum())

    volume_col = "Volume" if "Volume" in df.columns else "TotalQty"
    volume_sum = float(_safe_numeric(df, volume_col).sum())

    coverage_close_to_full = False
    if not valid_ts.empty:
        expected_start = pd.Timestamp(f"{day.isoformat()}T00:00:00Z")
        expected_end = pd.Timestamp(f"{day.isoformat()}T23:59:00Z")
        coverage_close_to_full = bool(
            min_ts <= expected_start + pd.Timedelta(minutes=5)
            and max_ts >= expected_end - pd.Timedelta(minutes=5)
        )

    completed_day_after_freeze = day > freeze.timestamp.date()
    usable = bool(
        rows >= REQUIRED_MIN_ROWS
        and synthetic_pct <= MAX_SYNTHETIC_PCT
        and zero_ohlc_rows == 0
        and volume_sum > 0
        and coverage_close_to_full
        and completed_day_after_freeze
    )

    reasons: list[str] = []
    if rows < REQUIRED_MIN_ROWS:
        reasons.append("rows_below_1000")
    if synthetic_pct > MAX_SYNTHETIC_PCT:
        reasons.append("synthetic_pct_above_5")
    if zero_ohlc_rows != 0:
        reasons.append("zero_ohlc_rows")
    if volume_sum <= 0:
        reasons.append("zero_volume")
    if not coverage_close_to_full:
        reasons.append("coverage_not_full_utc_day")
    if not completed_day_after_freeze:
        reasons.append("not_completed_utc_day_after_freeze")
    if post_freeze_rows <= 0:
        reasons.append("no_rows_after_freeze_timestamp")

    return {
        "date": day.isoformat(),
        "rows": rows,
        "min_timestamp": "" if pd.isna(min_ts) else min_ts.isoformat(),
        "max_timestamp": "" if pd.isna(max_ts) else max_ts.isoformat(),
        "post_freeze_rows": post_freeze_rows,
        "synthetic_pct": round(synthetic_pct, 6),
        "zero_ohlc_rows": zero_ohlc_rows,
        "volume_sum": round(volume_sum, 6),
        "coverage_close_to_full_utc_day": coverage_close_to_full,
        "completed_utc_day_after_freeze": completed_day_after_freeze,
        "usable_for_holdout": usable,
        "reason": "PASS" if usable else ";".join(reasons),
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "date",
        "rows",
        "min_timestamp",
        "max_timestamp",
        "post_freeze_rows",
        "synthetic_pct",
        "zero_ohlc_rows",
        "volume_sum",
        "coverage_close_to_full_utc_day",
        "completed_utc_day_after_freeze",
        "usable_for_holdout",
        "reason",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, *, freeze: FreezeContext, rows: list[dict[str, Any]], feed_root: Path) -> str:
    usable_rows = [row for row in rows if str(row["usable_for_holdout"]).lower() == "true"]
    verdict = "HOLDOUT_FEED_READY" if usable_rows else "WAIT_NO_HOLDOUT_DATA"
    lines = [
        "# Holdout Feed Audit",
        "",
        f"Candidate: `{DEFAULT_CANDIDATE_ID}`",
        f"Freeze commit: `{freeze.commit}`",
        f"Freeze timestamp: `{freeze.timestamp.isoformat()}`",
        f"Feed root: `{feed_root.as_posix()}`",
        f"Verdict: `{verdict}`",
        "",
        "## Rule",
        "",
        "- Analyze only completed UTC days after the Sprint 03 freeze timestamp.",
        "- A usable day requires rows >= 1000, synthetic_pct <= 5, zero_ohlc_rows = 0, volume_sum > 0, and near-full UTC coverage.",
        "- `feed/2026-05-17.csv` single synthetic zero row, if present from the zip state, is invalid holdout evidence.",
        "",
        "## Rows",
        "",
    ]
    if not rows:
        lines.append("No local feed files at or after the freeze day were found.")
    else:
        lines.append("| date | rows | min_timestamp | max_timestamp | synthetic_pct | zero_ohlc_rows | volume_sum | usable_for_holdout | reason |")
        lines.append("|---|---:|---|---|---:|---:|---:|---|---|")
        for row in rows:
            lines.append(
                "| {date} | {rows} | {min_timestamp} | {max_timestamp} | {synthetic_pct} | {zero_ohlc_rows} | {volume_sum} | {usable_for_holdout} | {reason} |".format(
                    **row
                )
            )
    lines.extend(
        [
            "",
            "## First Usable Day",
            "",
            f"`{usable_rows[0]['date']}`" if usable_rows else "`NONE`",
            "",
            "Do not run holdout replay while verdict is `WAIT_NO_HOLDOUT_DATA`.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return verdict


def run(args: argparse.Namespace) -> str:
    protocol_path = Path(args.protocol_path)
    feed_root = Path(args.feed_root)
    candidate_dir = Path(args.candidate_dir)
    freeze = read_freeze_context(protocol_path)
    rows = [audit_file(path, freeze) for path in find_feed_files(feed_root, freeze.timestamp)]
    csv_path = candidate_dir / "holdout_feed_audit.csv"
    md_path = candidate_dir / "holdout_feed_audit.md"
    write_csv(csv_path, rows)
    verdict = write_markdown(md_path, freeze=freeze, rows=rows, feed_root=feed_root)
    print(f"wrote {csv_path}")
    print(f"wrote {md_path}")
    print(f"verdict={verdict}")
    return verdict


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit post-freeze feed files before Sprint 04 holdout replay.")
    parser.add_argument("--protocol-path", default="research/canonical/HOLDOUT_PROTOCOL.md")
    parser.add_argument("--feed-root", default="feed")
    parser.add_argument("--candidate-dir", default=str(DEFAULT_CANDIDATE_DIR))
    run(parser.parse_args())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
