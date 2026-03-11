"""Schema contracts for Analyzer Phase 0.

This module defines raw input requirements and explicit feature contracts.
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

NUMERIC_RAW_COLUMNS = [
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
]

OPTIONAL_RAW_COLUMNS: list[str] = []

# Implemented in Phase 1A and expected in current pipeline output.
FEATURE_COLUMNS_IMPLEMENTED = [
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
]

# Planned placeholders for future phases; not materialized yet.
FEATURE_COLUMNS_PLANNED = [
    "session",
    "minutes_from_eu_open",
    "minutes_from_us_open",
]

# Backward-compatible union contract.
FEATURE_COLUMNS_PHASE0 = FEATURE_COLUMNS_IMPLEMENTED + FEATURE_COLUMNS_PLANNED

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


def non_numeric_required_columns(columns: list[str]) -> list[str]:
    """Return configured numeric columns that are not present in a dataset."""
    existing = set(columns)
    return [col for col in NUMERIC_RAW_COLUMNS if col not in existing]
