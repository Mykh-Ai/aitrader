"""Research-only setup candidate extraction from normalized events."""

from __future__ import annotations

import hashlib

import pandas as pd

SETUP_COLUMNS = [
    "SetupId",
    "SetupType",
    "Direction",
    "Status",
    "DetectedAt",
    "SetupBarTs",
    "ReferenceEventTs",
    "ReferenceEventType",
    "ReferenceEventAnchorTs",
    "ReferenceLevel",
    "AbsorptionScore_v1",
    "CtxRelVolumeSpike_v1",
    "CtxDeltaSpike_v1",
    "CtxOISpike_v1",
    "CtxLiqSpike_v1",
    "CtxWickReclaim_v1",
    "RelVolume_20",
    "DeltaAbsRatio_20",
    "OIChangeAbsRatio_20",
    "LiqTotalRatio_20",
]

ENRICHMENT_COLUMNS = [
    "AbsorptionScore_v1",
    "CtxRelVolumeSpike_v1",
    "CtxDeltaSpike_v1",
    "CtxOISpike_v1",
    "CtxLiqSpike_v1",
    "CtxWickReclaim_v1",
    "RelVolume_20",
    "DeltaAbsRatio_20",
    "OIChangeAbsRatio_20",
    "LiqTotalRatio_20",
]


def _empty_setups() -> pd.DataFrame:
    return pd.DataFrame(columns=SETUP_COLUMNS)


def _setup_id(
    event_type: str,
    source_tf: str,
    reference_event_ts: pd.Timestamp,
    anchor_ts: pd.Timestamp,
    level: float,
) -> str:
    payload = (
        f"{event_type}|{source_tf}|{reference_event_ts.isoformat()}|"
        f"{anchor_ts.isoformat() if pd.notna(anchor_ts) else ''}|{level}"
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def extract_setup_candidates(df: pd.DataFrame, events_df: pd.DataFrame) -> pd.DataFrame:
    """Extract baseline setup candidates from FAILED_BREAK_* events only.

    Step 2 enriches each setup with context snapshot columns from ``df``.
    """
    _ = df
    if events_df.empty:
        return _empty_setups()

    required = {
        "Timestamp",
        "EventType",
        "SourceTF",
        "ReferenceSwingTs",
        "PriceLevel",
    }
    missing = required - set(events_df.columns)
    if missing:
        raise KeyError(
            "Missing required columns for setup extraction: "
            f"{sorted(missing)}"
        )

    out = events_df.copy()
    out = out[out["EventType"].isin(["FAILED_BREAK_DOWN", "FAILED_BREAK_UP"])].copy()
    if out.empty:
        return _empty_setups()

    out = out.drop_duplicates(
        subset=["EventType", "SourceTF", "Timestamp", "ReferenceSwingTs", "PriceLevel"],
        keep="first",
    )

    out["Timestamp"] = pd.to_datetime(out["Timestamp"], utc=True)
    out["ReferenceSwingTs"] = pd.to_datetime(out["ReferenceSwingTs"], utc=True)
    out["PriceLevel"] = pd.to_numeric(out["PriceLevel"], errors="coerce")

    setup_type_map = {
        "FAILED_BREAK_DOWN": "FAILED_BREAK_RECLAIM_LONG",
        "FAILED_BREAK_UP": "FAILED_BREAK_RECLAIM_SHORT",
    }
    direction_map = {
        "FAILED_BREAK_DOWN": "LONG",
        "FAILED_BREAK_UP": "SHORT",
    }

    setups = pd.DataFrame(
        {
            "SetupType": out["EventType"].map(setup_type_map),
            "Direction": out["EventType"].map(direction_map),
            "Status": "CANDIDATE",
            "DetectedAt": out["Timestamp"],
            "SetupBarTs": out["Timestamp"],
            "ReferenceEventTs": out["Timestamp"],
            "ReferenceEventType": out["EventType"],
            "ReferenceEventAnchorTs": out["ReferenceSwingTs"],
            "ReferenceLevel": out["PriceLevel"],
        }
    )

    setups["SetupId"] = [
        _setup_id(
            event_type=event_type,
            source_tf=source_tf,
            reference_event_ts=reference_event_ts,
            anchor_ts=anchor_ts,
            level=level,
        )
        for event_type, source_tf, reference_event_ts, anchor_ts, level in zip(
            out["EventType"],
            out["SourceTF"],
            setups["ReferenceEventTs"],
            setups["ReferenceEventAnchorTs"],
            setups["ReferenceLevel"],
            strict=False,
        )
    ]

    required_feature_columns = {"Timestamp", *ENRICHMENT_COLUMNS}
    missing_feature_columns = required_feature_columns - set(df.columns)
    if missing_feature_columns:
        raise KeyError(
            "Missing required feature columns for setup enrichment: "
            f"{sorted(missing_feature_columns)}"
        )

    features = df.loc[:, ["Timestamp", *ENRICHMENT_COLUMNS]].copy()
    features["Timestamp"] = pd.to_datetime(features["Timestamp"], utc=True)

    setup_bar_counts = setups["SetupBarTs"].map(features["Timestamp"].value_counts())
    invalid_counts = setup_bar_counts.fillna(0).astype(int)
    if (invalid_counts != 1).any():
        bad_rows = setups.loc[invalid_counts != 1, "SetupBarTs"]
        details = [
            f"{ts.isoformat()} (matches={count})"
            for ts, count in zip(bad_rows, invalid_counts[invalid_counts != 1], strict=False)
        ]
        raise ValueError(
            "Expected exactly one feature row per setup SetupBarTs; "
            f"invalid matches: {details}"
        )

    setups = setups.merge(
        features,
        left_on="SetupBarTs",
        right_on="Timestamp",
        how="left",
        sort=False,
        validate="many_to_one",
    ).drop(columns=["Timestamp"])

    setups = setups.sort_values(
        by=["DetectedAt", "ReferenceEventType", "Direction", "SetupId"], kind="mergesort"
    ).reset_index(drop=True)
    return setups.loc[:, SETUP_COLUMNS]
