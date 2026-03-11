"""Schema contracts for Analyzer Phase 0.

This module defines raw input requirements and placeholder output contracts.
"""

from __future__ import annotations

REQUIRED_RAW_COLUMNS = [
    "Timestamp",
    "Open",
    "High",
    "Low",
    "Close",
    "Volume",
    "AggTrades",
    "BuyQty",
    "SellQty",
    "VWAP",
    "OpenInterest",
    "FundingRate",
    "LiqBuyQty",
    "LiqSellQty",
    "IsSynthetic",
]

OPTIONAL_RAW_COLUMNS: list[str] = []

# Phase 0 placeholders from locked base metrics section in spec.
FEATURE_COLUMNS_PHASE0 = [
    "Delta",
    "CVD",
    "DeltaPct",
    "BarRange",
    "BodySize",
    "UpperWick",
    "LowerWick",
    "CloseLocation",
    "BodyToRange",
    "UpperWickToRange",
    "LowerWickToRange",
    "OI_Change",
    "LiqTotal",
    "session",  # TODO(phase1): derive from UTC timestamp boundaries.
    "minutes_from_eu_open",  # TODO(phase1)
    "minutes_from_us_open",  # TODO(phase1)
]

EVENT_COLUMNS = [
    "Timestamp",
    "EventType",
    "Side",
    "PriceLevel",
    "SourceTF",
    "ReferenceSwingTs",
    "ReferenceSwingPrice",
    "Confidence",
    "MetaJson",
]


class SchemaValidationError(ValueError):
    """Raised when raw input schema does not satisfy analyzer requirements."""


def missing_required_columns(columns: list[str]) -> list[str]:
    """Return required columns that are missing from an incoming dataset."""
    existing = set(columns)
    return [col for col in REQUIRED_RAW_COLUMNS if col not in existing]
