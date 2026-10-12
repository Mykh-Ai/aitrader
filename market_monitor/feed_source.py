from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import pandas as pd


OUTAGE_START = pd.Timestamp("2026-04-23T17:05:00Z")
OUTAGE_END = pd.Timestamp("2026-05-06T22:51:00Z")


class FeedSourceError(RuntimeError):
    """Raised when the governed daily feed source cannot be selected safely."""


class RequiredRecoveredFeedMissing(FeedSourceError):
    """Raised instead of silently falling back to contaminated base feed."""


@dataclass(frozen=True)
class DailyFeedSource:
    day: date
    path: Path
    source_class: str
    selection_reason: str


def recovered_required(day: date) -> bool:
    day_start = pd.Timestamp(day.isoformat(), tz="UTC")
    day_end = day_start + pd.Timedelta(days=1) - pd.Timedelta(nanoseconds=1)
    return day_start <= OUTAGE_END and day_end >= OUTAGE_START


def resolve_daily_feed_source(
    feed_dir: str | Path,
    day: date,
    *,
    recovered_dir: str | Path | None = None,
) -> DailyFeedSource:
    base_root = Path(feed_dir)
    recovered_root = Path(recovered_dir) if recovered_dir is not None else base_root.parent / "feed_recovered"
    filename = f"{day.isoformat()}.csv"
    base_path = base_root / filename
    recovered_path = recovered_root / filename

    if recovered_required(day):
        if not recovered_path.exists():
            raise RequiredRecoveredFeedMissing(
                f"required recovered feed missing for {day.isoformat()}: {recovered_path}"
            )
        return DailyFeedSource(
            day=day,
            path=recovered_path,
            source_class="RECOVERED_DEGRADED",
            selection_reason="KNOWN_OUTAGE_RECOVERED_PRECEDENCE",
        )

    if not base_path.exists():
        raise FeedSourceError(f"base feed missing for {day.isoformat()}: {base_path}")
    return DailyFeedSource(
        day=day,
        path=base_path,
        source_class="RAW",
        selection_reason="NORMAL_PERIOD_BASE_FEED",
    )


def discover_daily_dates(
    feed_dir: str | Path,
    *,
    recovered_dir: str | Path | None = None,
) -> list[date]:
    roots = [Path(feed_dir)]
    recovered_root = Path(recovered_dir) if recovered_dir is not None else Path(feed_dir).parent / "feed_recovered"
    if recovered_root != roots[0]:
        roots.append(recovered_root)

    days: set[date] = set()
    for root in roots:
        if not root.exists():
            continue
        for path in root.iterdir():
            if path.suffix.lower() != ".csv":
                continue
            try:
                days.add(date.fromisoformat(path.stem))
            except ValueError:
                continue
    return sorted(days)


def previous_day(day: date) -> date:
    return day - timedelta(days=1)
