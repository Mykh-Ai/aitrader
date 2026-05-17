"""Sprint 05 discovery surface scan.

This prototype audits clean feed opportunity without creating strategy rules.
It excludes the contaminated primary-feed outage window and can splice in
feed_recovered rows for that window when recovered-lineage artifacts exist.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


CONTAMINATED_START = pd.Timestamp("2026-04-23 17:05:00", tz="UTC")
CONTAMINATED_END = pd.Timestamp("2026-05-06 22:51:00", tz="UTC")
SESSION_BOUNDS = {
    "asia": (0, 7),
    "london": (7, 13),
    "us": (13, 20),
    "late_us": (20, 24),
}

AUDIT_COLUMNS = [
    "date",
    "rows",
    "data_source",
    "lineage_note",
    "synthetic_pct",
    "volume_sum",
    "daily_return_pct",
    "high_low_range_pct",
    "realized_volatility",
    "max_1h_move",
    "max_4h_move",
    "trend_day",
    "chop_day",
    "expansion_day",
    "reversal_day",
    "day_labels",
    "session_volatility_distribution",
    "large_move_windows",
]


@dataclass(frozen=True)
class DayFrame:
    date: str
    frame: pd.DataFrame
    data_source: str
    lineage_note: str


def _safe_numeric(frame: pd.DataFrame, column: str, default: float = 0.0) -> pd.Series:
    if column not in frame.columns:
        return pd.Series([default] * len(frame.index), index=frame.index, dtype=float)
    return pd.to_numeric(frame[column], errors="coerce").fillna(default)


def _read_feed(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    if "Timestamp" not in frame.columns:
        raise ValueError(f"{path} is missing Timestamp")
    frame["Timestamp"] = pd.to_datetime(frame["Timestamp"], utc=True, errors="coerce")
    frame = frame.dropna(subset=["Timestamp"]).copy()
    frame = frame.sort_values("Timestamp")
    for column in ["Open", "High", "Low", "Close", "Volume", "IsSynthetic"]:
        frame[column] = _safe_numeric(frame, column)
    positive_ohlc = frame[["Open", "High", "Low", "Close"]].gt(0).all(axis=1)
    frame = frame.loc[positive_ohlc].reset_index(drop=True)
    return frame


def recovered_lineage_available(recovered_root: Path, manifest_path: Path) -> bool:
    return recovered_root.exists() and manifest_path.exists()


def build_clean_day_frames(
    *,
    feed_root: Path,
    recovered_root: Path,
    recovered_manifest: Path,
    use_recovered_gap: bool,
) -> list[DayFrame]:
    if not feed_root.exists():
        raise SystemExit(f"Feed root not found: {feed_root}")

    recovered_ok = use_recovered_gap and recovered_lineage_available(recovered_root, recovered_manifest)
    frames: list[DayFrame] = []
    for primary_path in sorted(feed_root.glob("*.csv")):
        try:
            pd.Timestamp(primary_path.stem)
        except ValueError:
            continue

        primary = _read_feed(primary_path)
        if primary.empty:
            frames.append(
                DayFrame(
                    date=primary_path.stem,
                    frame=primary,
                    data_source="primary",
                    lineage_note="empty_primary_file",
                )
            )
            continue

        in_gap = primary["Timestamp"].between(CONTAMINATED_START, CONTAMINATED_END, inclusive="both")
        if not in_gap.any():
            frames.append(
                DayFrame(
                    date=primary_path.stem,
                    frame=primary,
                    data_source="primary",
                    lineage_note="primary_clean_outside_contaminated_window",
                )
            )
            continue

        clean_parts = [primary.loc[~in_gap].copy()]
        data_source = "primary_gap_excluded"
        lineage_note = "contaminated_primary_window_excluded"

        recovered_path = recovered_root / primary_path.name
        if recovered_ok and recovered_path.exists():
            recovered = _read_feed(recovered_path)
            recovered_in_gap = recovered["Timestamp"].between(
                CONTAMINATED_START, CONTAMINATED_END, inclusive="both"
            )
            clean_parts.append(recovered.loc[recovered_in_gap].copy())
            data_source = "primary_plus_recovered_gap"
            lineage_note = "primary outside outage; feed_recovered inside outage; funding/liquidation degraded"
        elif use_recovered_gap:
            lineage_note = "contaminated_primary_window_excluded; recovered_file_missing_or_manifest_missing"

        combined = (
            pd.concat(clean_parts, ignore_index=True)
            .drop_duplicates(subset=["Timestamp"], keep="last")
            .sort_values("Timestamp")
            .reset_index(drop=True)
        )
        frames.append(
            DayFrame(
                date=primary_path.stem,
                frame=combined,
                data_source=data_source,
                lineage_note=lineage_note,
            )
        )
    return frames


def realized_volatility_pct(close: pd.Series) -> float:
    close = pd.to_numeric(close, errors="coerce").dropna()
    close = close[close > 0]
    if len(close.index) < 2:
        return 0.0
    log_returns = (close / close.shift(1)).replace([math.inf, -math.inf], pd.NA)
    log_returns = log_returns.apply(lambda value: math.log(value) if pd.notna(value) and value > 0 else 0.0)
    return float(math.sqrt((log_returns.dropna() ** 2).sum()) * 100.0)


def rolling_move_pct(frame: pd.DataFrame, bars: int) -> float:
    close = _safe_numeric(frame, "Close")
    if len(close.index) <= bars:
        return 0.0
    base = close.shift(bars)
    moves = (close / base.where(base > 0) - 1.0).abs() * 100.0
    moves = moves.replace([math.inf, -math.inf], pd.NA)
    return float(moves.max(skipna=True) or 0.0)


def session_volatility(frame: pd.DataFrame) -> dict[str, float]:
    output: dict[str, float] = {}
    if frame.empty:
        return {name: 0.0 for name in SESSION_BOUNDS}
    hours = frame["Timestamp"].dt.hour
    for name, (start_hour, end_hour) in SESSION_BOUNDS.items():
        mask = hours.ge(start_hour) & hours.lt(end_hour)
        output[name] = round(realized_volatility_pct(frame.loc[mask, "Close"]), 6)
    return output


def large_move_windows(frame: pd.DataFrame, *, limit: int = 5) -> list[dict[str, Any]]:
    windows: list[dict[str, Any]] = []
    if frame.empty:
        return windows
    close = _safe_numeric(frame, "Close")
    for bars, label in [(60, "1h"), (240, "4h")]:
        if len(close.index) <= bars:
            continue
        moves = (close / close.shift(bars) - 1.0) * 100.0
        moves = moves.replace([math.inf, -math.inf], pd.NA)
        for idx in moves.abs().nlargest(limit).index:
            if pd.isna(moves.loc[idx]) or idx < bars:
                continue
            windows.append(
                {
                    "horizon": label,
                    "start_ts": frame.loc[idx - bars, "Timestamp"].isoformat(),
                    "end_ts": frame.loc[idx, "Timestamp"].isoformat(),
                    "move_pct": round(float(moves.loc[idx]), 6),
                }
            )
    return sorted(windows, key=lambda row: abs(row["move_pct"]), reverse=True)[:limit]


def compute_base_row(day: DayFrame) -> dict[str, Any]:
    frame = day.frame
    rows = int(len(frame.index))
    if rows == 0:
        return {
            "date": day.date,
            "rows": 0,
            "data_source": day.data_source,
            "lineage_note": day.lineage_note,
            "synthetic_pct": 0.0,
            "volume_sum": 0.0,
            "daily_return_pct": 0.0,
            "high_low_range_pct": 0.0,
            "realized_volatility": 0.0,
            "max_1h_move": 0.0,
            "max_4h_move": 0.0,
            "session_volatility_distribution": json.dumps(session_volatility(frame), sort_keys=True),
            "large_move_windows": json.dumps([], sort_keys=True),
        }

    close = _safe_numeric(frame, "Close")
    high = _safe_numeric(frame, "High")
    low = _safe_numeric(frame, "Low")
    first_close = float(close.iloc[0])
    last_close = float(close.iloc[-1])
    base_price = first_close if first_close > 0 else float(close[close > 0].iloc[0]) if (close > 0).any() else 1.0
    synthetic = _safe_numeric(frame, "IsSynthetic").ne(0)

    return {
        "date": day.date,
        "rows": rows,
        "data_source": day.data_source,
        "lineage_note": day.lineage_note,
        "synthetic_pct": round(float(100.0 * synthetic.mean()), 6),
        "volume_sum": round(float(_safe_numeric(frame, "Volume").sum()), 6),
        "daily_return_pct": round(float((last_close / base_price - 1.0) * 100.0), 6),
        "high_low_range_pct": round(float((high.max() - low.min()) / base_price * 100.0), 6),
        "realized_volatility": round(realized_volatility_pct(close), 6),
        "max_1h_move": round(rolling_move_pct(frame, 60), 6),
        "max_4h_move": round(rolling_move_pct(frame, 240), 6),
        "session_volatility_distribution": json.dumps(session_volatility(frame), sort_keys=True),
        "large_move_windows": json.dumps(large_move_windows(frame), sort_keys=True),
    }


def add_day_labels(rows: list[dict[str, Any]], frames_by_date: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    if not rows:
        return rows

    metrics = pd.DataFrame(rows)
    range_q75 = float(metrics["high_low_range_pct"].quantile(0.75))
    rv_q75 = float(metrics["realized_volatility"].quantile(0.75))
    range_median = float(metrics["high_low_range_pct"].median())
    rv_median = float(metrics["realized_volatility"].median())
    abs_ret_median = float(metrics["daily_return_pct"].abs().median())

    for row in rows:
        range_pct = float(row["high_low_range_pct"])
        rv = float(row["realized_volatility"])
        daily_ret = float(row["daily_return_pct"])
        trend_strength = abs(daily_ret) / range_pct if range_pct > 0 else 0.0
        frame = frames_by_date[row["date"]]
        first_half_ret = 0.0
        second_half_ret = 0.0
        if len(frame.index) >= 4:
            close = _safe_numeric(frame, "Close")
            first = float(close.iloc[0])
            mid = float(close.iloc[len(close.index) // 2])
            last = float(close.iloc[-1])
            if first > 0 and mid > 0:
                first_half_ret = (mid / first - 1.0) * 100.0
                second_half_ret = (last / mid - 1.0) * 100.0

        expansion_day = bool(range_pct >= range_q75 or rv >= rv_q75)
        trend_day = bool(abs(daily_ret) >= abs_ret_median and trend_strength >= 0.45)
        chop_day = bool(range_pct <= range_median and rv <= rv_median and trend_strength < 0.25)
        reversal_day = bool(
            first_half_ret * second_half_ret < 0
            and min(abs(first_half_ret), abs(second_half_ret)) >= max(0.15, abs_ret_median * 0.3)
            and range_pct >= range_median
        )

        labels = []
        if trend_day:
            labels.append("trend_day")
        if chop_day:
            labels.append("chop_day")
        if expansion_day:
            labels.append("expansion_day")
        if reversal_day:
            labels.append("reversal_day")
        if not labels:
            labels.append("mixed_day")

        row["trend_day"] = trend_day
        row["chop_day"] = chop_day
        row["expansion_day"] = expansion_day
        row["reversal_day"] = reversal_day
        row["day_labels"] = "|".join(labels)
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def build_surface_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        return []
    frame = pd.DataFrame(rows)
    summary_rows: list[dict[str, Any]] = []

    for label in ["trend_day", "chop_day", "expansion_day", "reversal_day"]:
        subset = frame[frame[label].astype(bool)]
        summary_rows.append(
            {
                "surface": label,
                "days": int(len(subset.index)),
                "avg_rows": round(float(subset["rows"].mean() if not subset.empty else 0.0), 3),
                "avg_volume_sum": round(float(subset["volume_sum"].mean() if not subset.empty else 0.0), 6),
                "avg_daily_return_pct": round(float(subset["daily_return_pct"].mean() if not subset.empty else 0.0), 6),
                "avg_high_low_range_pct": round(
                    float(subset["high_low_range_pct"].mean() if not subset.empty else 0.0), 6
                ),
                "avg_realized_volatility": round(
                    float(subset["realized_volatility"].mean() if not subset.empty else 0.0), 6
                ),
                "avg_max_1h_move": round(float(subset["max_1h_move"].mean() if not subset.empty else 0.0), 6),
                "avg_max_4h_move": round(float(subset["max_4h_move"].mean() if not subset.empty else 0.0), 6),
                "notes": "descriptive_opportunity_surface_only_no_strategy_rules",
            }
        )

    source_counts = frame["data_source"].value_counts().to_dict()
    summary_rows.append(
        {
            "surface": "data_lineage",
            "days": int(len(frame.index)),
            "avg_rows": round(float(frame["rows"].mean()), 3),
            "avg_volume_sum": round(float(frame["volume_sum"].mean()), 6),
            "avg_daily_return_pct": round(float(frame["daily_return_pct"].mean()), 6),
            "avg_high_low_range_pct": round(float(frame["high_low_range_pct"].mean()), 6),
            "avg_realized_volatility": round(float(frame["realized_volatility"].mean()), 6),
            "avg_max_1h_move": round(float(frame["max_1h_move"].mean()), 6),
            "avg_max_4h_move": round(float(frame["max_4h_move"].mean()), 6),
            "notes": json.dumps(source_counts, sort_keys=True),
        }
    )
    return summary_rows


def run(args: argparse.Namespace) -> None:
    day_frames = build_clean_day_frames(
        feed_root=Path(args.feed_root),
        recovered_root=Path(args.recovered_root),
        recovered_manifest=Path(args.recovered_manifest),
        use_recovered_gap=not args.no_recovered_gap,
    )
    frames_by_date = {day.date: day.frame for day in day_frames}
    rows = [compute_base_row(day) for day in day_frames]
    rows = add_day_labels(rows, frames_by_date)

    audit_path = Path(args.audit_output)
    summary_path = Path(args.summary_output)
    write_csv(audit_path, rows, AUDIT_COLUMNS)
    summary_rows = build_surface_summary(rows)
    write_csv(
        summary_path,
        summary_rows,
        [
            "surface",
            "days",
            "avg_rows",
            "avg_volume_sum",
            "avg_daily_return_pct",
            "avg_high_low_range_pct",
            "avg_realized_volatility",
            "avg_max_1h_move",
            "avg_max_4h_move",
            "notes",
        ],
    )
    print(f"wrote {audit_path}")
    print(f"wrote {summary_path}")
    print(f"days={len(rows)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Sprint 05 feed opportunity audit and discovery summary.")
    parser.add_argument("--feed-root", default="feed")
    parser.add_argument("--recovered-root", default="feed_recovered")
    parser.add_argument("--recovered-manifest", default="research/canonical/FEED_RECOVERED_MANIFEST.csv")
    parser.add_argument("--audit-output", default="research/results/feed_opportunity_audit.csv")
    parser.add_argument("--summary-output", default="research/results/discovery_surface_summary.csv")
    parser.add_argument("--no-recovered-gap", action="store_true")
    run(parser.parse_args())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
