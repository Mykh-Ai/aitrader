from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd


class FeedContractError(ValueError):
    """Raised when feed input cannot be normalized into the monitor contract."""


HISTORICAL_TO_PROTECTED = {
    "AggTrades": "Trades",
    "Volume": "TotalQty",
    "Close": "ClosePrice",
    "High": "HiPrice",
    "Low": "LowPrice",
    "Open": "OpenPrice",
}

OUTPUT_COLUMNS = [
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
    "LiqBuyQty",
    "LiqSellQty",
    "LiquidationDataAvailable",
    "DataQuality",
    "SourceClass",
    "SourceFile",
]

PRICE_COLUMNS = ["OpenPrice", "HiPrice", "LowPrice", "ClosePrice"]
NUMERIC_COLUMNS = [
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
    "LiqBuyQty",
    "LiqSellQty",
]


def load_feed(
    paths: str | Path | Iterable[str | Path],
    *,
    deduplicate: bool = False,
) -> pd.DataFrame:
    files = _resolve_input_paths(paths)
    frames = [_read_one_csv(path) for path in files]
    if not frames:
        raise FeedContractError("No CSV input files found")

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.sort_values(
        ["Timestamp", "SourceFile", "_source_order"], kind="mergesort"
    )
    if deduplicate:
        combined = combined.drop_duplicates(subset=["Timestamp"], keep="last")
    combined = combined.sort_values(["Timestamp"], kind="mergesort")
    combined = combined[OUTPUT_COLUMNS].reset_index(drop=True)
    return combined


def _resolve_input_paths(paths: str | Path | Iterable[str | Path]) -> list[Path]:
    if isinstance(paths, (str, Path)):
        path = Path(paths)
        if path.is_dir():
            files = sorted(p for p in path.iterdir() if p.suffix.lower() == ".csv")
        else:
            files = [path]
    else:
        files = sorted(Path(path) for path in paths)

    if not files:
        raise FeedContractError("No CSV input files found")

    missing = [str(path) for path in files if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Input file not found: {missing[0]}")

    non_csv = [str(path) for path in files if path.suffix.lower() != ".csv"]
    if non_csv:
        raise FeedContractError(f"Input file is not CSV: {non_csv[0]}")

    return files


def _read_one_csv(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path)
    frame = raw.rename(columns=HISTORICAL_TO_PROTECTED).copy()
    liquidation_data_available = {"LiqBuyQty", "LiqSellQty"}.issubset(frame.columns)

    if "Timestamp" not in frame.columns:
        raise FeedContractError("Missing required column: Timestamp")

    if "OpenPrice" not in frame.columns and "ClosePrice" in frame.columns:
        frame["OpenPrice"] = frame["ClosePrice"]

    missing_prices = [column for column in PRICE_COLUMNS if column not in frame.columns]
    if missing_prices:
        raise FeedContractError(
            "Missing required price columns: " + ", ".join(missing_prices)
        )

    for column in [
        "TotalQty",
        "Trades",
        "BuyQty",
        "SellQty",
        "OpenInterest",
        "FundingRate",
        "LiqBuyQty",
        "LiqSellQty",
    ]:
        if column not in frame.columns:
            frame[column] = 0

    frame["Timestamp"] = pd.to_datetime(frame["Timestamp"], utc=True, errors="coerce")
    if frame["Timestamp"].isna().any():
        raise FeedContractError("Invalid Timestamp values")

    for column in NUMERIC_COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
        if frame[column].isna().any():
            raise FeedContractError(f"Invalid numeric values in column: {column}")

    frame["LiquidationDataAvailable"] = liquidation_data_available
    source_class = _source_class_for(path)
    frame["SourceClass"] = source_class
    frame["DataQuality"] = _data_quality_for(source_class, frame)
    frame["SourceFile"] = path.name
    frame["_source_order"] = range(len(frame))
    return frame


def deduplicate_feed(feed: pd.DataFrame) -> pd.DataFrame:
    """Deterministically deduplicate only after callers record diagnostics."""
    if feed.empty:
        return feed.copy()
    return (
        feed.sort_values(["Timestamp", "SourceFile"], kind="mergesort")
        .drop_duplicates(subset=["Timestamp"], keep="last")
        .sort_values("Timestamp", kind="mergesort")
        .reset_index(drop=True)
    )


def _source_class_for(path: Path) -> str:
    path_parts = {part.lower() for part in path.parts}
    if "feed_recovered" in path_parts:
        return "RECOVERED_DEGRADED"
    return "RAW"


def _data_quality_for(source_class: str, frame: pd.DataFrame) -> pd.Series:
    quality = pd.Series(source_class, index=frame.index, dtype="object")
    if "IsSynthetic" in frame.columns:
        synthetic = pd.to_numeric(frame["IsSynthetic"], errors="coerce").fillna(0)
        quality.loc[synthetic != 0] = "SYNTHETIC"
    return quality
