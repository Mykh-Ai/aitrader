from __future__ import annotations

import pandas as pd


STRUCTURE_LEVEL_COLUMNS = [
    "level_id",
    "created_at",
    "level_timestamp",
    "timeframe",
    "level_type",
    "side",
    "price",
    "source_start",
    "source_end",
    "touch_count",
    "strength_score",
    "status",
    "data_quality",
]


def build_structure_levels(feed: pd.DataFrame) -> pd.DataFrame:
    if feed.empty:
        return pd.DataFrame(columns=STRUCTURE_LEVEL_COLUMNS)

    frame = feed.sort_values("Timestamp", kind="mergesort").copy()
    frame["day"] = frame["Timestamp"].dt.floor("D")
    rows: list[dict[str, object]] = []

    rows.extend(_daily_reference_levels(frame))
    rows.extend(_session_extreme_levels(frame))
    rows.extend(_h1_swing_levels(frame))

    levels = pd.DataFrame(rows, columns=STRUCTURE_LEVEL_COLUMNS)
    if levels.empty:
        return levels

    levels = levels.sort_values(
        ["created_at", "level_timestamp", "level_type", "price"], kind="mergesort"
    ).reset_index(drop=True)
    levels["level_id"] = [f"level_{idx + 1:06d}" for idx in range(len(levels))]
    return levels


def _daily_reference_levels(frame: pd.DataFrame) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    days = list(frame.groupby("day", sort=True))
    for index, (day, group) in enumerate(days):
        day_start = group["Timestamp"].min()
        open_row = group.sort_values("Timestamp", kind="mergesort").iloc[0]
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
                data_quality=_quality(group),
            )
        )

        if index == 0:
            continue

        _, previous = days[index - 1]
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
                strength_score=80,
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
                strength_score=80,
                data_quality=_quality(previous),
            )
        )
    return rows


def _session_extreme_levels(frame: pd.DataFrame) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for _, group in frame.groupby("day", sort=True):
        session_start = group["Timestamp"].min()
        current_high = None
        current_low = None
        for _, row in group.sort_values("Timestamp", kind="mergesort").iterrows():
            if current_high is None or row["HiPrice"] >= current_high:
                current_high = row["HiPrice"]
                rows.append(
                    _level_row(
                        created_at=row["Timestamp"],
                        level_timestamp=row["Timestamp"],
                        timeframe="SESSION",
                        level_type="SESSION_HIGH",
                        side="BUY_SIDE",
                        price=row["HiPrice"],
                        source_start=session_start,
                        source_end=row["Timestamp"],
                        touch_count=1,
                        strength_score=55,
                        data_quality=row["DataQuality"],
                    )
                )
            if current_low is None or row["LowPrice"] <= current_low:
                current_low = row["LowPrice"]
                rows.append(
                    _level_row(
                        created_at=row["Timestamp"],
                        level_timestamp=row["Timestamp"],
                        timeframe="SESSION",
                        level_type="SESSION_LOW",
                        side="SELL_SIDE",
                        price=row["LowPrice"],
                        source_start=session_start,
                        source_end=row["Timestamp"],
                        touch_count=1,
                        strength_score=55,
                        data_quality=row["DataQuality"],
                    )
                )
    return rows


def _h1_swing_levels(frame: pd.DataFrame) -> list[dict[str, object]]:
    hourly = (
        frame.assign(hour=frame["Timestamp"].dt.floor("h"))
        .groupby("hour", sort=True)
        .agg(
            source_start=("Timestamp", "min"),
            source_end=("Timestamp", "max"),
            high=("HiPrice", "max"),
            low=("LowPrice", "min"),
            data_quality=("DataQuality", _quality_values),
        )
        .reset_index()
    )
    rows: list[dict[str, object]] = []
    if len(hourly) < 3:
        return rows

    for index in range(1, len(hourly) - 1):
        previous = hourly.iloc[index - 1]
        current = hourly.iloc[index]
        nxt = hourly.iloc[index + 1]
        created_at = nxt["source_end"]
        if current["high"] > previous["high"] and current["high"] > nxt["high"]:
            level_ts = _timestamp_for_price(frame, current["source_start"], current["source_end"], "HiPrice", current["high"])
            rows.append(
                _level_row(
                    created_at=created_at,
                    level_timestamp=level_ts,
                    timeframe="H1",
                    level_type="H1_SWING_HIGH",
                    side="BUY_SIDE",
                    price=current["high"],
                    source_start=current["source_start"],
                    source_end=current["source_end"],
                    touch_count=1,
                    strength_score=65,
                    data_quality=current["data_quality"],
                )
            )
        if current["low"] < previous["low"] and current["low"] < nxt["low"]:
            level_ts = _timestamp_for_price(frame, current["source_start"], current["source_end"], "LowPrice", current["low"])
            rows.append(
                _level_row(
                    created_at=created_at,
                    level_timestamp=level_ts,
                    timeframe="H1",
                    level_type="H1_SWING_LOW",
                    side="SELL_SIDE",
                    price=current["low"],
                    source_start=current["source_start"],
                    source_end=current["source_end"],
                    touch_count=1,
                    strength_score=65,
                    data_quality=current["data_quality"],
                )
            )
    return rows


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
) -> dict[str, object]:
    return {
        "level_id": "",
        "created_at": _format_ts(created_at),
        "level_timestamp": _format_ts(level_timestamp),
        "timeframe": timeframe,
        "level_type": level_type,
        "side": side,
        "price": float(price),
        "source_start": _format_ts(source_start),
        "source_end": _format_ts(source_end),
        "touch_count": int(touch_count),
        "strength_score": int(strength_score),
        "status": "ACTIVE",
        "data_quality": data_quality,
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
    unique = set(values)
    if unique == {"RAW"}:
        return "RAW"
    if "RECOVERED_DEGRADED" in unique:
        return "RECOVERED_DEGRADED"
    return sorted(unique)[0]


def _format_ts(value) -> str:
    return pd.Timestamp(value).tz_convert("UTC").isoformat().replace("+00:00", "Z")

