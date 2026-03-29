"""Research-only H2 impulse reclaim setup extraction from feature rows."""

from __future__ import annotations

import hashlib

import pandas as pd

from .setups import ENRICHMENT_COLUMNS, SETUP_COLUMNS

RECLAIM_WINDOW_BARS = 6
_IMPULSE_SOURCE_TF = "M1"

_REQUIRED_COLUMNS = {
    "Timestamp",
    "Close",
    "ImpulseDetected_v1",
    "ImpulseDirection_v1",
    "ImpulseAnchorMid_v1",
    "ImpulseAnchorVWAP_v1",
    *ENRICHMENT_COLUMNS,
}


def _empty_setups() -> pd.DataFrame:
    return pd.DataFrame(columns=SETUP_COLUMNS)


def _setup_id(
    setup_type: str,
    direction: str,
    impulse_ts: pd.Timestamp,
    setup_ts: pd.Timestamp,
    reference_level: float,
) -> str:
    payload = (
        f"H2_IMPULSE|{setup_type}|{direction}|{impulse_ts.isoformat()}|"
        f"{setup_ts.isoformat()}|{reference_level}"
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def _annotate_lifecycle(setups: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    features = df.loc[:, ["Timestamp", "Close"]].copy()
    features["Timestamp"] = pd.to_datetime(features["Timestamp"], utc=True)
    features = features.sort_values(by=["Timestamp"], kind="mergesort").reset_index(drop=True)

    ts_to_index = pd.Series(features.index.to_numpy(), index=features["Timestamp"])

    lifecycle_status: list[str] = []
    invalidated_at: list[pd.Timestamp] = []
    expired_at: list[pd.Timestamp] = []
    lifecycle_bars_forward: list[int] = []

    for setup in setups.itertuples(index=False):
        setup_idx = int(ts_to_index[setup.SetupBarTs])
        forward = features.iloc[setup_idx + 1 : setup_idx + 13]
        bars_forward = int(len(forward))

        if bars_forward == 0:
            lifecycle_status.append("PENDING")
            invalidated_at.append(pd.NaT)
            expired_at.append(pd.NaT)
            lifecycle_bars_forward.append(0)
            continue

        if setup.Direction == "LONG":
            invalidation_mask = forward["Close"] < setup.ReferenceLevel
        else:
            invalidation_mask = forward["Close"] > setup.ReferenceLevel

        if invalidation_mask.any():
            first_invalidated = forward.loc[invalidation_mask, "Timestamp"].iloc[0]
            lifecycle_status.append("INVALIDATED")
            invalidated_at.append(first_invalidated)
            expired_at.append(pd.NaT)
        else:
            lifecycle_status.append("EXPIRED")
            invalidated_at.append(pd.NaT)
            expired_at.append(forward["Timestamp"].iloc[-1])

        lifecycle_bars_forward.append(bars_forward)

    annotated = setups.copy()
    annotated["LifecycleStatus"] = lifecycle_status
    annotated["InvalidatedAt"] = invalidated_at
    annotated["ExpiredAt"] = expired_at
    annotated["LifecycleBarsForward"] = lifecycle_bars_forward
    return annotated


def extract_impulse_setups(df: pd.DataFrame) -> pd.DataFrame:
    """Extract H2 impulse reclaim setups using first reclaim confirmation within 6 bars."""
    missing = _REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise KeyError(
            "Missing required columns for impulse setup extraction: "
            f"{sorted(missing)}"
        )

    if df.empty:
        return _empty_setups()

    features = df.copy()
    features["Timestamp"] = pd.to_datetime(features["Timestamp"], utc=True)
    features = features.sort_values(by=["Timestamp"], kind="mergesort").reset_index(drop=True)

    rows: list[dict] = []
    for i, row in features.iterrows():
        if not bool(row["ImpulseDetected_v1"]):
            continue

        impulse_direction = row["ImpulseDirection_v1"]
        impulse_ts = row["Timestamp"]
        anchor_mid = pd.to_numeric(row["ImpulseAnchorMid_v1"], errors="coerce")
        anchor_vwap = pd.to_numeric(row["ImpulseAnchorVWAP_v1"], errors="coerce")
        if pd.isna(anchor_mid) or pd.isna(anchor_vwap):
            continue

        window = features.iloc[i + 1 : i + 1 + RECLAIM_WINDOW_BARS]
        if window.empty:
            continue

        if impulse_direction == "IMPULSE_DOWN":
            reference_level = float(max(anchor_mid, anchor_vwap))
            qualifying = window["Close"] > reference_level
            setup_type = "IMPULSE_FADE_RECLAIM_LONG_V1"
            direction = "LONG"
        elif impulse_direction == "IMPULSE_UP":
            reference_level = float(min(anchor_mid, anchor_vwap))
            qualifying = window["Close"] < reference_level
            setup_type = "IMPULSE_FADE_RECLAIM_SHORT_V1"
            direction = "SHORT"
        else:
            continue

        if not qualifying.any():
            continue

        setup_bar = window.loc[qualifying].iloc[0]
        setup_ts = pd.Timestamp(setup_bar["Timestamp"])

        rows.append(
            {
                "SetupType": setup_type,
                "Direction": direction,
                "Status": "CANDIDATE",
                "DetectedAt": setup_ts,
                "SetupBarTs": setup_ts,
                "ReferenceEventTs": impulse_ts,
                "ReferenceEventType": impulse_direction,
                "SourceTF": _IMPULSE_SOURCE_TF,
                "ReferenceEventAnchorTs": impulse_ts,
                "ReferenceLevel": reference_level,
                **{col: setup_bar[col] for col in ENRICHMENT_COLUMNS},
                "SetupId": _setup_id(
                    setup_type=setup_type,
                    direction=direction,
                    impulse_ts=impulse_ts,
                    setup_ts=setup_ts,
                    reference_level=reference_level,
                ),
            }
        )

    if not rows:
        return _empty_setups()

    setups = pd.DataFrame(rows)

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

    setups = _annotate_lifecycle(setups, features)
    setups = setups.sort_values(
        by=["DetectedAt", "ReferenceEventType", "Direction", "SetupId"], kind="mergesort"
    ).reset_index(drop=True)
    return setups.loc[:, SETUP_COLUMNS]
