from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from market_monitor.feed_adapter import HISTORICAL_TO_PROTECTED

OUTAGE_START = pd.Timestamp("2026-04-23T17:05:00Z")
OUTAGE_END = pd.Timestamp("2026-05-06T22:51:00Z")
REQUIRED = ["Timestamp", "Open", "High", "Low", "Close", "Volume", "AggTrades", "BuyQty", "SellQty", "OpenInterest", "FundingRate", "LiqBuyQty", "LiqSellQty", "IsSynthetic"]
NUMERIC = REQUIRED[1:]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_sources(root: Path, start: str, cutoff: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Strict read-only source selection. Duplicates/order errors are never hidden."""
    start_ts, end_ts = pd.Timestamp(start), pd.Timestamp(cutoff)
    parts, inventory = [], []
    for day in pd.date_range(start_ts.normalize(), end_ts.normalize(), freq="D"):
        name = day.strftime("%Y-%m-%d.csv")
        base = root / "feed" / name
        recovered = root / "feed_recovered" / name
        candidates = [(base, False)]
        if day <= OUTAGE_END and day + pd.Timedelta(days=1) > OUTAGE_START and recovered.exists():
            candidates.append((recovered, True))
        for path, is_recovered in candidates:
            if not path.exists():
                inventory.append({"path": path.relative_to(root).as_posix(), "status": "MISSING", "rows": 0})
                continue
            before = digest(path)
            frame = pd.read_csv(path)
            missing = sorted(set(REQUIRED) - set(frame.columns))
            if missing:
                raise ValueError(f"{path}: missing fields {missing}")
            frame["Timestamp"] = pd.to_datetime(frame.Timestamp, utc=True, errors="raise")
            if frame.Timestamp.duplicated().any() or not frame.Timestamp.is_monotonic_increasing:
                raise ValueError(f"{path}: duplicate or unordered timestamps")
            if (frame.Timestamp.dt.normalize() != day).any():
                raise ValueError(f"{path}: timestamps outside named UTC day")
            for col in NUMERIC:
                frame[col] = pd.to_numeric(frame[col], errors="raise")
                if not np.isfinite(frame[col]).all():
                    raise ValueError(f"{path}: nonfinite {col}")
            invalid = ((frame[["Open", "High", "Low", "Close"]] <= 0).any(axis=1)
                       | (frame.High < frame[["Open", "Close", "Low"]].max(axis=1))
                       | (frame.Low > frame[["Open", "Close", "High"]].min(axis=1))
                       | (frame[["Volume", "AggTrades", "BuyQty", "SellQty", "OpenInterest", "LiqBuyQty", "LiqSellQty"]] < 0).any(axis=1))
            frame["InvalidRow"] = invalid
            frame["IsRecovered"] = is_recovered
            frame["SourceFile"] = path.relative_to(root).as_posix()
            frame["DataQuality"] = np.where(is_recovered | frame.IsSynthetic.ne(0) | invalid, "RECOVERED_DEGRADED", "RAW")
            inventory.append({"path": path.relative_to(root).as_posix(), "status": "READ", "sha256": before,
                              "rows": len(frame), "first_close": str(frame.Timestamp.min()), "last_close": str(frame.Timestamp.max()),
                              "missing_minutes_in_day": 1440 - len(frame), "synthetic_rows": int(frame.IsSynthetic.ne(0).sum()),
                              "invalid_rows": int(invalid.sum()), "recovered_source": is_recovered})
            if digest(path) != before:
                raise ValueError(f"source changed while reading: {path}")
            in_outage = frame.Timestamp.between(OUTAGE_START, OUTAGE_END)
            chosen = in_outage if is_recovered else ~in_outage
            parts.append(frame.loc[chosen & frame.Timestamp.between(start_ts, end_ts)].copy())
    if not parts:
        raise ValueError("No usable source files")
    frame = pd.concat(parts, ignore_index=True).sort_values("Timestamp", kind="stable")
    if frame.Timestamp.duplicated().any():
        raise ValueError("Selected feed has duplicate timestamps")
    frame = frame.rename(columns=HISTORICAL_TO_PROTECTED).reset_index(drop=True)
    frame["CandleOpenTsUTC"] = frame.Timestamp - pd.Timedelta(minutes=1)
    frame["LiquidationDataAvailable"] = ~frame.IsRecovered & frame.DataQuality.eq("RAW")
    return frame, pd.DataFrame(inventory)


def usable_observations(feed: pd.DataFrame) -> pd.DataFrame:
    """Skip unusable primary observations in memory; keep source history intact."""
    recovered = feed.get("IsRecovered", pd.Series(False, index=feed.index)).astype(bool)
    synthetic = feed.get("IsSynthetic", pd.Series(0, index=feed.index)).ne(0)
    invalid = feed.get("InvalidRow", pd.Series(False, index=feed.index)).astype(bool)
    return feed.loc[~((synthetic | invalid) & ~recovered)].copy().reset_index(drop=True)


def window_is_usable(feed: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> bool:
    """RAW observations plus isolated one-minute omissions; no outage allowance."""
    if feed.empty or not feed.DataQuality.eq("RAW").all():
        return False
    points = pd.DatetimeIndex([start - pd.Timedelta(minutes=1), *feed.Timestamp, end + pd.Timedelta(minutes=1)])
    return bool((points[1:] - points[:-1]).max() <= pd.Timedelta(minutes=2))


def closed_bars(feed: pd.DataFrame, minutes: int) -> pd.DataFrame:
    """Right-closed UTC bars from real observations, retaining omission evidence."""
    groups = feed.groupby(feed.Timestamp.dt.ceil(f"{minutes}min"), sort=True)
    rows = []
    for end, group in groups:
        start = end - pd.Timedelta(minutes=minutes - 1)
        complete = len(group) == minutes and group.Timestamp.iloc[0] == start and group.Timestamp.iloc[-1] == end
        next_index = feed.Timestamp.searchsorted(end, side="left")
        available = feed.Timestamp.iloc[next_index] if next_index < len(feed) else pd.NaT
        usable = window_is_usable(group, start, end)
        rows.append({"timestamp": end, "open": float(group.OpenPrice.iloc[0]), "high": float(group.HiPrice.max()),
                     "low": float(group.LowPrice.min()), "close": float(group.ClosePrice.iloc[-1]),
                     "volume": float(group.TotalQty.sum()), "buy": float(group.BuyQty.sum()), "sell": float(group.SellQty.sum()),
                     "oi_change": float(group.OpenInterest.iloc[-1] - group.OpenInterest.iloc[0]),
                     "liq_buy": float(group.LiqBuyQty.sum()), "liq_sell": float(group.LiqSellQty.sum()),
                     "completed": bool(pd.notna(available)), "complete_observations": bool(complete),
                     "available_at": available, "usable": usable, "omitted_minutes": minutes - len(group),
                     "raw": bool(complete and group.DataQuality.eq("RAW").all()),
                     "source_start": group.Timestamp.iloc[0], "source_end": group.Timestamp.iloc[-1]})
    return pd.DataFrame(rows)
