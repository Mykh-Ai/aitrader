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
    "SwingHigh_H1_Price",
    "SwingHigh_H1_ConfirmedAt",
    "SwingLow_H1_Price",
    "SwingLow_H1_ConfirmedAt",
    "SwingHigh_H4_Price",
    "SwingHigh_H4_ConfirmedAt",
    "SwingLow_H4_Price",
    "SwingLow_H4_ConfirmedAt",
    "Sweep_H1_Up",
    "Sweep_H1_Down",
    "Sweep_H1_Direction",
    "Sweep_H1_ReferenceLevel",
    "Sweep_H1_ReferenceTs",
    "Sweep_H4_Up",
    "Sweep_H4_Down",
    "Sweep_H4_Direction",
    "Sweep_H4_ReferenceLevel",
    "Sweep_H4_ReferenceTs",
    "FailedBreak_H1_Up",
    "FailedBreak_H1_Down",
    "FailedBreak_H1_Direction",
    "FailedBreak_H1_ReferenceLevel",
    "FailedBreak_H1_ReferenceSweepTs",
    "FailedBreak_H1_ConfirmedTs",
    "FailedBreak_H4_Up",
    "FailedBreak_H4_Down",
    "FailedBreak_H4_Direction",
    "FailedBreak_H4_ReferenceLevel",
    "FailedBreak_H4_ReferenceSweepTs",
    "FailedBreak_H4_ConfirmedTs",
    "RelVolume_20",
    "DeltaAbsRatio_20",
    "OIChangeAbsRatio_20",
    "LiqTotalRatio_20",
    "CtxRelVolumeSpike_v1",
    "CtxDeltaSpike_v1",
    "CtxOISpike_v1",
    "CtxLiqSpike_v1",
    "CtxWickReclaim_v1",
    "AbsorptionScore_v1",
    "session",
    "minutes_from_eu_open",
    "minutes_from_us_open",
    "ContextModelVersion",
]

# Planned placeholders for future phases; not materialized yet.
FEATURE_COLUMNS_PLANNED: list[str] = []

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
