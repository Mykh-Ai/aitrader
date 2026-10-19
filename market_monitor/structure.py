from __future__ import annotations

import pandas as pd
import hashlib
from market_monitor.causality import utc


M15_SWING_LEFT_RIGHT = 2
H1_SWING_LEFT_RIGHT = 2
H4_SWING_LEFT_RIGHT = 1
EQUAL_LEVEL_TOLERANCE_BPS = 5
SESSION_DEFINITIONS = [
    ("ASIA", 0, 8),
    ("EUROPE", 8, 16),
    ("US", 16, 24),
]

STRUCTURE_LEVEL_COLUMNS = [
    "level_id",
    "created_at",
    "LevelAvailableAtUTC",
    "ConfirmingBarCloseUTC",
    "level_timestamp",
    "timeframe",
    "level_type",
    "source_timeframe_primary",
    "side",
    "price",
    "htf_level_type",
    "htf_origin_timestamp",
    "htf_origin_price",
    "htf_confirmation_timestamp",
    "source_start",
    "source_end",
    "touch_count",
    "strength_score",
    "status",
    "data_quality",
    "source_level_ids",
]


def build_structure_levels(feed: pd.DataFrame, *, as_of=None) -> pd.DataFrame:
    if feed.empty:
        return pd.DataFrame(columns=STRUCTURE_LEVEL_COLUMNS)

    frame = feed.sort_values("Timestamp", kind="mergesort").copy()
    if as_of is not None:
        frame = frame.loc[frame.Timestamp.le(utc(as_of))]
    frame = _observation_feed(frame)
    frame["day"] = (frame["Timestamp"] - pd.Timedelta(nanoseconds=1)).dt.floor("D")
    rows: list[dict[str, object]] = []
    rows.extend(_daily_reference_levels(frame))
    rows.extend(_finalized_session_levels(frame, as_of=as_of))
    rows.extend(_confirmed_swing_levels(frame, "M15", M15_SWING_LEFT_RIGHT, as_of=as_of))
    rows.extend(_confirmed_swing_levels(frame, "H1", H1_SWING_LEFT_RIGHT, as_of=as_of))
    rows.extend(_confirmed_swing_levels(frame, "H4", H4_SWING_LEFT_RIGHT, as_of=as_of))

    levels = _assign_level_ids(pd.DataFrame(rows, columns=STRUCTURE_LEVEL_COLUMNS))
    equal_levels = _equal_level_rows(levels)
    if not equal_levels.empty:
        equal_levels = _assign_level_ids(
            equal_levels, start_index=len(levels) + 1
        )
        levels = pd.concat([levels, equal_levels], ignore_index=True)
        levels = _sort_levels(levels)
    pattern_levels = _pattern_structure_level_rows(levels)
    if not pattern_levels.empty:
        pattern_levels = _assign_level_ids(pattern_levels, start_index=len(levels) + 1)
        levels = pd.concat([levels, pattern_levels], ignore_index=True)
        levels = _sort_levels(levels)
    return levels


def aggregate_timeframe(feed: pd.DataFrame, timeframe: str, *, as_of=None) -> pd.DataFrame:
    rules = {"M15": "15min", "H1": "h", "H4": "4h"}
    if timeframe not in rules:
        raise ValueError(f"Unsupported timeframe: {timeframe}")
    columns = [
        "Timestamp",
        "OpenPrice",
        "HiPrice",
        "LowPrice",
        "ClosePrice",
        "TotalQty",
        "Trades",
        "BuyQty",
        "SellQty",
        "OpenInterest",
        "FundingRate",
        "DataQuality",
        "source_start",
        "source_end",
        "completion_status",
        "missing_minute_count",
    ]
    if feed.empty:
        return pd.DataFrame(columns=columns)

    rule = rules[timeframe]
    frame = _observation_feed(feed)
    if as_of is not None:
        frame = frame.loc[frame.Timestamp.le(utc(as_of))]
    if frame.empty:
        return pd.DataFrame(columns=columns)
    # Feed timestamps label minute CLOSES. A minute closing on an H1/H4
    # boundary belongs to the bar that just closed, not the next bar.
    # Label each aggregate with its actual closing UTC timestamp.
    duration = pd.Timedelta({"h": "1h"}.get(rule, rule))
    frame["bar_timestamp"] = (
        (frame["Timestamp"] - pd.Timedelta(nanoseconds=1)).dt.floor(rule)
        + duration
    )
    bars = (
        frame.groupby("bar_timestamp", sort=True)
        .agg(
            Timestamp=("bar_timestamp", "first"),
            OpenPrice=("OpenPrice", "first"),
            HiPrice=("HiPrice", "max"),
            LowPrice=("LowPrice", "min"),
            ClosePrice=("ClosePrice", "last"),
            TotalQty=("TotalQty", "sum"),
            Trades=("Trades", "sum"),
            BuyQty=("BuyQty", "sum"),
            SellQty=("SellQty", "sum"),
            OpenInterest=("OpenInterest", "last"),
            FundingRate=("FundingRate", "last"),
            DataQuality=("DataQuality", _quality_values),
            source_start=("Timestamp", "min"),
            source_end=("Timestamp", "max"),
        )
        .reset_index(drop=True)
    )
    # Never expose the last partial higher-timeframe candle as a completed
    # structural observation. Missing individual minutes do not, by
    # themselves, invalidate an already elapsed bar.
    bars = bars.loc[bars["Timestamp"] <= (utc(as_of) if as_of is not None else frame["Timestamp"].max())]
    # Elapsed does not mean observed: retain explicit quality for sparse bars.
    grouped = frame.groupby("bar_timestamp")["Timestamp"]
    counts = grouped.size()
    gaps = frame["Timestamp"].diff().where(frame["bar_timestamp"].eq(frame["bar_timestamp"].shift()))
    interior = gaps.groupby(frame["bar_timestamp"]).max().reindex(bars.Timestamp).fillna(pd.Timedelta(0)).reset_index(drop=True)
    leading = bars.source_start - (bars.Timestamp - duration)
    trailing = bars.Timestamp - bars.source_end
    partial = (interior > pd.Timedelta(minutes=2)) | (leading > pd.Timedelta(minutes=2)) | (trailing > pd.Timedelta(minutes=1))
    bars["completion_status"] = partial.map({True: "PARTIAL", False: "CLOSED_OBSERVED"})
    bars["missing_minute_count"] = int(duration / pd.Timedelta(minutes=1)) - bars.Timestamp.map(counts)
    return bars[columns].reset_index(drop=True)


def _observation_feed(feed: pd.DataFrame) -> pd.DataFrame:
    frame = feed.sort_values("Timestamp", kind="mergesort").copy()
    if frame["Timestamp"].duplicated().any():
        raise ValueError("duplicate minute observations must be resolved with source provenance")
    if "DataQuality" not in frame:
        frame["DataQuality"] = frame.get("SourceClass", "RAW")
    if "IsSynthetic" in frame:
        frame.loc[pd.to_numeric(frame.IsSynthetic, errors="raise").ne(0), "DataQuality"] = "SYNTHETIC"
    frame = frame.loc[~frame["DataQuality"].isin(["SYNTHETIC", "INVALID"])].copy()
    return frame.reset_index(drop=True)


def _observed_window(frame, start, end):
    timestamps = frame.loc[frame.Timestamp.gt(start) & frame.Timestamp.le(end), "Timestamp"]
    if timestamps.empty:
        return False
    points = pd.DatetimeIndex([start, *timestamps, end])
    return bool((points[1:] - points[:-1]).max() <= pd.Timedelta(minutes=2))


def _daily_reference_levels(frame: pd.DataFrame) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    days = list(frame.groupby("day", sort=True))
    for index, (_, group) in enumerate(days):
        day_start = group["Timestamp"].min()
        open_row = group.sort_values("Timestamp", kind="mergesort").iloc[0]
        if day_start == group["day"].iloc[0] + pd.Timedelta(minutes=1):
            rows.append(
                _level_row(
                    created_at=open_row["Timestamp"],
                    level_timestamp=open_row["Timestamp"],
                    timeframe="D1",
                    level_type="DAY_OPEN",
                    side="NEUTRAL",
                    price=open_row["OpenPrice"],
                    source_start=day_start,
                    source_end=open_row["Timestamp"],
                    touch_count=1,
                    strength_score=45,
                    data_quality=str(open_row["DataQuality"]),
                )
            )
        if index == 0:
            continue

        _, previous = days[index - 1]
        previous_day = pd.Timestamp(previous["day"].iloc[0])
        if group["day"].iloc[0] != previous_day + pd.Timedelta(days=1):
            continue
        if not _observed_window(previous, previous_day, previous_day + pd.Timedelta(days=1)):
            continue
        previous_start = previous["Timestamp"].min()
        previous_end = previous["Timestamp"].max()
        high_row = previous.sort_values(
            ["HiPrice", "Timestamp"], ascending=[False, True], kind="mergesort"
        ).iloc[0]
        low_row = previous.sort_values(
            ["LowPrice", "Timestamp"], ascending=[True, True], kind="mergesort"
        ).iloc[0]
        rows.append(
            _level_row(
                created_at=day_start,
                level_timestamp=high_row["Timestamp"],
                timeframe="D1",
                level_type="PDH",
                side="BUY_SIDE",
                price=high_row["HiPrice"],
                source_start=previous_start,
                source_end=previous_end,
                touch_count=_touch_count(previous, high_row["HiPrice"], "HiPrice"),
                strength_score=85,
                data_quality=_quality(previous),
            )
        )
        rows.append(
            _level_row(
                created_at=day_start,
                level_timestamp=low_row["Timestamp"],
                timeframe="D1",
                level_type="PDL",
                side="SELL_SIDE",
                price=low_row["LowPrice"],
                source_start=previous_start,
                source_end=previous_end,
                touch_count=_touch_count(previous, low_row["LowPrice"], "LowPrice"),
                strength_score=85,
                data_quality=_quality(previous),
            )
        )
    return rows


def _finalized_session_levels(frame: pd.DataFrame, *, as_of=None) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    max_ts = utc(as_of) if as_of is not None else frame["Timestamp"].max()
    for day, day_group in frame.groupby("day", sort=True):
        for session_name, start_hour, end_hour in SESSION_DEFINITIONS:
            session_start = day + pd.Timedelta(hours=start_hour)
            session_end = day + pd.Timedelta(hours=end_hour)
            mask = (day_group["Timestamp"] > session_start) & (
                day_group["Timestamp"] <= session_end
            )
            session = day_group.loc[mask].sort_values("Timestamp", kind="mergesort")
            if session.empty or max_ts < session_end or not _observed_window(session, session_start, session_end):
                continue
            high_row = session.sort_values(
                ["HiPrice", "Timestamp"], ascending=[False, True], kind="mergesort"
            ).iloc[0]
            low_row = session.sort_values(
                ["LowPrice", "Timestamp"], ascending=[True, True], kind="mergesort"
            ).iloc[0]
            rows.append(
                _level_row(
                    created_at=session_end,
                    level_timestamp=high_row["Timestamp"],
                    timeframe="SESSION",
                    level_type=f"{session_name}_HIGH",
                    side="BUY_SIDE",
                    price=high_row["HiPrice"],
                    source_start=session_start,
                    source_end=session_end,
                    touch_count=_touch_count(session, high_row["HiPrice"], "HiPrice"),
                    strength_score=55,
                    data_quality=_quality(session),
                )
            )
            rows.append(
                _level_row(
                    created_at=session_end,
                    level_timestamp=low_row["Timestamp"],
                    timeframe="SESSION",
                    level_type=f"{session_name}_LOW",
                    side="SELL_SIDE",
                    price=low_row["LowPrice"],
                    source_start=session_start,
                    source_end=session_end,
                    touch_count=_touch_count(session, low_row["LowPrice"], "LowPrice"),
                    strength_score=55,
                    data_quality=_quality(session),
                )
            )
    return rows


def _confirmed_swing_levels(
    frame: pd.DataFrame, timeframe: str, left_right: int, *, as_of=None
) -> list[dict[str, object]]:
    bars = aggregate_timeframe(frame, timeframe, as_of=as_of)
    rows: list[dict[str, object]] = []
    if len(bars) < left_right * 2 + 1:
        return rows

    for index in range(left_right, len(bars) - left_right):
        current = bars.iloc[index]
        left = bars.iloc[index - left_right : index]
        right = bars.iloc[index + 1 : index + left_right + 1]
        window = bars.iloc[index - left_right:index + left_right + 1]
        duration = pd.Timedelta(minutes={"M15": 15, "H1": 60, "H4": 240}[timeframe])
        if (window["completion_status"].eq("PARTIAL").any()
                or not window["Timestamp"].diff().dropna().eq(duration).all()):
            continue
        created_at = bars.iloc[index + left_right]["Timestamp"]
        if current["HiPrice"] > left["HiPrice"].max() and current["HiPrice"] > right["HiPrice"].max():
            rows.append(
                _level_row(
                    created_at=created_at,
                    level_timestamp=_timestamp_for_price(
                        frame,
                        current["source_start"],
                        current["source_end"],
                        "HiPrice",
                        current["HiPrice"],
                    ),
                    timeframe=timeframe,
                    level_type=f"{timeframe}_SWING_HIGH",
                    side="BUY_SIDE",
                    price=current["HiPrice"],
                    source_start=current["source_start"],
                    source_end=current["source_end"],
                    touch_count=1,
                    strength_score=_swing_strength_score(timeframe),
                    data_quality=_quality_values(window["DataQuality"]),
                )
            )
        if current["LowPrice"] < left["LowPrice"].min() and current["LowPrice"] < right["LowPrice"].min():
            rows.append(
                _level_row(
                    created_at=created_at,
                    level_timestamp=_timestamp_for_price(
                        frame,
                        current["source_start"],
                        current["source_end"],
                        "LowPrice",
                        current["LowPrice"],
                    ),
                    timeframe=timeframe,
                    level_type=f"{timeframe}_SWING_LOW",
                    side="SELL_SIDE",
                    price=current["LowPrice"],
                    source_start=current["source_start"],
                    source_end=current["source_end"],
                    touch_count=1,
                    strength_score=_swing_strength_score(timeframe),
                    data_quality=_quality_values(window["DataQuality"]),
                )
            )
    return rows


def _swing_strength_score(timeframe: str) -> int:
    if timeframe == "H4":
        return 75
    if timeframe == "H1":
        return 65
    if timeframe == "M15":
        return 50
    return 45


def _equal_level_rows(levels: pd.DataFrame) -> pd.DataFrame:
    if levels.empty:
        return pd.DataFrame(columns=STRUCTURE_LEVEL_COLUMNS)
    sources = levels[
        levels["level_type"].isin(
            {
                "PDH",
                "PDL",
                "ASIA_HIGH",
                "ASIA_LOW",
                "EUROPE_HIGH",
                "EUROPE_LOW",
                "US_HIGH",
                "US_LOW",
                "H1_SWING_HIGH",
                "H1_SWING_LOW",
                "H4_SWING_HIGH",
                "H4_SWING_LOW",
            }
        )
    ].copy()
    rows: list[dict[str, object]] = []
    rows.extend(_cluster_equal_side(sources[sources["side"] == "BUY_SIDE"], "EQUAL_HIGHS"))
    rows.extend(_cluster_equal_side(sources[sources["side"] == "SELL_SIDE"], "EQUAL_LOWS"))
    if not rows:
        return pd.DataFrame(columns=STRUCTURE_LEVEL_COLUMNS)
    return pd.DataFrame(rows, columns=STRUCTURE_LEVEL_COLUMNS)


def _cluster_equal_side(levels: pd.DataFrame, level_type: str) -> list[dict[str, object]]:
    if len(levels) < 2:
        return []
    rows: list[dict[str, object]] = []
    ordered = levels.sort_values(["price", "created_at", "level_id"], kind="mergesort")
    cluster: list[pd.Series] = []
    for _, level in ordered.iterrows():
        if not cluster:
            cluster = [level]
            continue
        cluster_mid = sum(float(item["price"]) for item in cluster) / len(cluster)
        tolerance = cluster_mid * EQUAL_LEVEL_TOLERANCE_BPS / 10000
        if abs(float(level["price"]) - cluster_mid) <= tolerance:
            cluster.append(level)
        else:
            rows.extend(_equal_cluster_to_rows(cluster, level_type))
            cluster = [level]
    rows.extend(_equal_cluster_to_rows(cluster, level_type))
    return rows


def _equal_cluster_to_rows(
    cluster: list[pd.Series], level_type: str
) -> list[dict[str, object]]:
    if len(cluster) < 2:
        return []
    prices = [float(level["price"]) for level in cluster]
    created_at = max(pd.Timestamp(level["created_at"]) for level in cluster)
    source_start = min(pd.Timestamp(level["source_start"]) for level in cluster)
    source_end = max(pd.Timestamp(level["source_end"]) for level in cluster)
    level_timestamp = min(pd.Timestamp(level["level_timestamp"]) for level in cluster)
    source_ids = sorted(str(level["level_id"]) for level in cluster)
    return [
        _level_row(
            created_at=created_at,
            level_timestamp=level_timestamp,
            timeframe="CLUSTER",
            level_type=level_type,
            side="BUY_SIDE" if level_type == "EQUAL_HIGHS" else "SELL_SIDE",
            price=sum(prices) / len(prices),
            source_start=source_start,
            source_end=source_end,
            touch_count=len(cluster),
            strength_score=min(100, 70 + len(cluster) * 5),
            data_quality=_quality_values([level["data_quality"] for level in cluster]),
            source_level_ids="|".join(source_ids),
        )
    ]


def _pattern_structure_level_rows(levels: pd.DataFrame) -> pd.DataFrame:
    if levels.empty:
        return pd.DataFrame(columns=STRUCTURE_LEVEL_COLUMNS)
    rows: list[dict[str, object]] = []
    for _, level in levels[levels["level_type"].isin({"EQUAL_HIGHS", "EQUAL_LOWS"})].iterrows():
        level_type = "DOUBLE_TOP_HIGH" if level["level_type"] == "EQUAL_HIGHS" else "DOUBLE_BOTTOM_LOW"
        source_ids = str(level.get("source_level_ids", "") or level.get("level_id", ""))
        rows.append(
            _level_row(
                created_at=level["created_at"],
                level_timestamp=level["level_timestamp"],
                timeframe="PATTERN",
                level_type=level_type,
                side=level["side"],
                price=level["price"],
                source_start=level["source_start"],
                source_end=level["source_end"],
                touch_count=int(level["touch_count"]),
                strength_score=min(100, int(level["strength_score"]) + 5),
                data_quality=level["data_quality"],
                source_level_ids=source_ids,
            )
        )
    return pd.DataFrame(rows, columns=STRUCTURE_LEVEL_COLUMNS)


def _assign_level_ids(levels: pd.DataFrame, start_index: int = 1) -> pd.DataFrame:
    levels = levels.reindex(columns=STRUCTURE_LEVEL_COLUMNS)
    if levels.empty:
        return levels
    levels = _sort_levels(levels)
    if start_index > 1:
        levels["level_id"] = ["level_" + hashlib.sha256(
            f"{r['level_type']}|{r['created_at']}|{r['price']}|{r['source_level_ids']}".encode()).hexdigest()[:20]
            for r in levels.to_dict("records")]
    else:
        levels["level_id"] = [f"level_{idx:06d}" for idx in range(1, len(levels) + 1)]
    return levels


def _sort_levels(levels: pd.DataFrame) -> pd.DataFrame:
    levels = levels.sort_values(
        ["created_at", "level_timestamp", "level_type", "price"], kind="mergesort"
    ).reset_index(drop=True)
    return levels


def _level_row(
    *,
    created_at,
    level_timestamp,
    timeframe: str,
    level_type: str,
    side: str,
    price,
    source_start,
    source_end,
    touch_count: int,
    strength_score: int,
    data_quality: str,
    status: str = "ACTIVE",
    source_level_ids: str = "",
) -> dict[str, object]:
    is_htf_structural = timeframe in {"H1", "H4"}
    return {
        "level_id": "",
        "created_at": _format_ts(created_at),
        "LevelAvailableAtUTC": _format_ts(created_at),
        "ConfirmingBarCloseUTC": _format_ts(created_at) if timeframe in {"M15", "H1", "H4"} else "",
        "level_timestamp": _format_ts(level_timestamp),
        "timeframe": timeframe,
        "level_type": level_type,
        "source_timeframe_primary": timeframe,
        "side": side,
        "price": float(price),
        "htf_level_type": level_type if is_htf_structural else "",
        "htf_origin_timestamp": _format_ts(level_timestamp) if is_htf_structural else "",
        "htf_origin_price": float(price) if is_htf_structural else "",
        "htf_confirmation_timestamp": _format_ts(created_at) if is_htf_structural else "",
        "source_start": _format_ts(source_start),
        "source_end": _format_ts(source_end),
        "touch_count": int(touch_count),
        "strength_score": int(strength_score),
        "status": status,
        "data_quality": data_quality,
        "source_level_ids": source_level_ids,
    }


def _touch_count(frame: pd.DataFrame, price: float, column: str) -> int:
    if price == 0:
        return int((frame[column] == price).sum())
    tolerance = abs(price) * 0.0001
    return int((frame[column].sub(price).abs() <= tolerance).sum())


def _timestamp_for_price(
    frame: pd.DataFrame, source_start, source_end, column: str, price: float
):
    mask = (
        (frame["Timestamp"] >= source_start)
        & (frame["Timestamp"] <= source_end)
        & (frame[column] == price)
    )
    return frame.loc[mask].sort_values("Timestamp", kind="mergesort").iloc[0]["Timestamp"]


def _quality(frame: pd.DataFrame) -> str:
    return _quality_values(frame["DataQuality"])


def _quality_values(values) -> str:
    unique = {str(value) for value in values}
    if unique == {"RAW"}:
        return "RAW"
    if "PARTIAL" in unique:
        return "PARTIAL"
    if "SYNTHETIC" in unique:
        return "SYNTHETIC"
    if "RECOVERED_DEGRADED" in unique:
        return "RECOVERED_DEGRADED"
    return sorted(unique)[0]


def _format_ts(value) -> str:
    return pd.Timestamp(value).tz_convert("UTC").isoformat().replace("+00:00", "Z")


class StructureState:
    """Incremental invocation of the canonical detectors, with prior levels.

    Only primitive detection needs a bounded confirmation window; derived
    equal/pattern structures always use the complete causally known inventory.
    No detector or weights are duplicated here.
    """
    def __init__(self):
        self.cutoff = None
        self.primitives = pd.DataFrame(columns=STRUCTURE_LEVEL_COLUMNS)
        self.levels = self.primitives.copy()

    def update(self, feed: pd.DataFrame, *, as_of=None) -> pd.DataFrame:
        cutoff = utc(as_of) if as_of is not None else feed.Timestamp.max()
        if self.cutoff is not None and cutoff < self.cutoff:
            raise ValueError("structure state cannot rewind; reconstruct the historical prefix")
        if self.cutoff == cutoff:
            return self.levels.copy()
        start = feed.Timestamp.min() if self.cutoff is None else cutoff - pd.Timedelta(hours=48)
        window = _observation_feed(feed.loc[feed.Timestamp.between(start, cutoff)])
        window["day"] = (window.Timestamp - pd.Timedelta(nanoseconds=1)).dt.floor("D")
        rows = _daily_reference_levels(window) + _finalized_session_levels(window, as_of=cutoff)
        for timeframe, radius in [("M15", 2), ("H1", 2), ("H4", 1)]:
            rows.extend(_confirmed_swing_levels(window, timeframe, radius, as_of=cutoff))
        fresh = pd.DataFrame(rows, columns=STRUCTURE_LEVEL_COLUMNS)
        if self.cutoff is not None and not fresh.empty:
            fresh = fresh.loc[pd.to_datetime(fresh.created_at, utc=True).gt(self.cutoff)]
        def combine(parts):
            nonempty = [part.dropna(axis=1, how="all") for part in parts if not part.empty]
            return (pd.concat(nonempty, ignore_index=True).reindex(columns=STRUCTURE_LEVEL_COLUMNS)
                    if nonempty else pd.DataFrame(columns=STRUCTURE_LEVEL_COLUMNS))
        primitives = combine([self.primitives, fresh])
        self.primitives = _assign_level_ids(primitives)
        equal = _equal_level_rows(self.primitives)
        equal = _assign_level_ids(equal, start_index=len(self.primitives) + 1)
        combined = combine([self.primitives, equal])
        patterns = _assign_level_ids(_pattern_structure_level_rows(combined), start_index=len(combined) + 1)
        self.levels = _sort_levels(combine([combined, patterns]))
        self.cutoff = cutoff
        return self.levels.copy()
