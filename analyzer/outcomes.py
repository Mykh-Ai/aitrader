"""Research-only setup outcome evaluation over a fixed forward horizon."""

from __future__ import annotations

import math

import pandas as pd

OUTCOME_COLUMNS = [
    "SetupId",
    "SetupBarTs",
    "Direction",
    "ReferenceLevel",
    "OutcomeHorizonBars",
    "OutcomeBarsObserved",
    "OutcomeStatus",
    "MFE_Pct",
    "MAE_Pct",
    "CloseReturn_Pct",
    "BestHigh",
    "BestLow",
    "FinalClose",
    "OutcomeEndTs",
    "H2_Post3Label_v1",
    "H2_Post6Label_v1",
    "H2_Post12Label_v1",
]

OUTCOME_HORIZON_BARS = 12

MULTI_HORIZON_OUTCOME_COLUMNS = [
    "VariantId",
    "SetupId",
    "SetupType",
    "Direction",
    "SetupBarTs",
    "ReferenceLevel",
    "OutcomeHorizonBars",
    "OutcomeBarsObserved",
    "OutcomeStatus",
    "OutcomeEndTs",
    "MFE_Pct",
    "MAE_Pct",
    "CloseReturn_Pct",
    "TimeToMFE_Bars",
    "TimeToMFE_Ts",
    "TimeToMAE_Bars",
    "TimeToMAE_Ts",
    "MaxGapMinutesObserved",
    "HasLargeGap",
]

LARGE_OUTCOME_GAP_MINUTES = 1.0

_H2_SETUP_TYPES = {"IMPULSE_FADE_RECLAIM_LONG_V1", "IMPULSE_FADE_RECLAIM_SHORT_V1"}
_H2_MIN_CONTINUATION_MOVE_PCT = 0.05


def _validated_reference_level(reference_level: object) -> float:
    numeric_reference_level = pd.to_numeric(reference_level, errors="coerce")
    if pd.isna(numeric_reference_level):
        raise ValueError(f"Invalid ReferenceLevel: {reference_level!r} (must be numeric, finite, and non-zero)")

    reference_level_float = float(numeric_reference_level)
    if not math.isfinite(reference_level_float) or reference_level_float == 0.0:
        raise ValueError(
            f"Invalid ReferenceLevel: {reference_level!r} "
            "(must be numeric, finite, and non-zero)"
        )
    return reference_level_float


def _empty_outcomes() -> pd.DataFrame:
    return pd.DataFrame(columns=OUTCOME_COLUMNS)


def _empty_multi_horizon_outcomes() -> pd.DataFrame:
    return pd.DataFrame(columns=MULTI_HORIZON_OUTCOME_COLUMNS)


def _validate_required_columns(df: pd.DataFrame, setups_df: pd.DataFrame) -> None:
    required_df = {"Timestamp", "High", "Low", "Close"}
    missing_df = required_df - set(df.columns)
    if missing_df:
        raise KeyError(
            "Missing required columns for setup outcome evaluation: "
            f"{sorted(missing_df)}"
        )

    required_setups = {"SetupId", "SetupBarTs", "Direction", "ReferenceLevel"}
    missing_setups = required_setups - set(setups_df.columns)
    if missing_setups:
        raise KeyError(
            "Missing required columns for setup outcome evaluation: "
            f"{sorted(missing_setups)}"
        )




def _h2_post3_label(direction: str, setup_close: float, early_forward: pd.DataFrame) -> str:
    if early_forward.empty:
        return "NO_EARLY_CONTINUATION"

    if direction == "LONG":
        early_best = float(early_forward["High"].max())
        early_mfe_pct = ((early_best - setup_close) / setup_close) * 100
        continued = early_best > setup_close and early_mfe_pct >= _H2_MIN_CONTINUATION_MOVE_PCT
    else:
        early_best = float(early_forward["Low"].min())
        early_mfe_pct = ((setup_close - early_best) / setup_close) * 100
        continued = early_best < setup_close and early_mfe_pct >= _H2_MIN_CONTINUATION_MOVE_PCT

    return "EARLY_CONTINUATION" if continued else "NO_EARLY_CONTINUATION"


def _h2_post6_label(direction: str, reference_level: float, forward6: pd.DataFrame) -> str:
    if forward6.empty:
        return pd.NA

    if direction == "LONG":
        failed = bool((forward6["Close"] < reference_level).any())
    else:
        failed = bool((forward6["Close"] > reference_level).any())

    return "RECLAIM_FAILED" if failed else "RECLAIM_HELD"


def _h2_post12_label(mfe_pct: float, mae_pct: float, close_return_pct: float) -> str:
    if close_return_pct >= _H2_MIN_CONTINUATION_MOVE_PCT and mae_pct > -_H2_MIN_CONTINUATION_MOVE_PCT:
        return "FULL_FADE"
    if mfe_pct >= _H2_MIN_CONTINUATION_MOVE_PCT:
        return "PARTIAL_FADE"
    return "NO_FADE"


def _build_h2_labels(setup: object, setup_close: float, reference_level: float, forward: pd.DataFrame, mfe_pct: float, mae_pct: float, close_return_pct: float) -> tuple[object, object, object]:
    setup_type = getattr(setup, "SetupType", None)
    if setup_type not in _H2_SETUP_TYPES:
        return (pd.NA, pd.NA, pd.NA)

    if setup.Direction not in {"LONG", "SHORT"}:
        raise ValueError(f"Unsupported setup direction for H2 observational labels: {setup.Direction}")

    early_forward = forward.iloc[:3]
    forward6 = forward.iloc[:6]

    return (
        _h2_post3_label(setup.Direction, setup_close=setup_close, early_forward=early_forward),
        _h2_post6_label(setup.Direction, reference_level=reference_level, forward6=forward6),
        _h2_post12_label(mfe_pct=mfe_pct, mae_pct=mae_pct, close_return_pct=close_return_pct),
    )

def _outcome_status(observed_bars: int, horizon_bars: int) -> str:
    if observed_bars == 0:
        return "NO_FORWARD_BARS"
    if observed_bars == horizon_bars:
        return "FULL_HORIZON"
    return "PARTIAL_HORIZON"


def _gap_metadata(setup_bar_ts: pd.Timestamp, forward: pd.DataFrame) -> tuple[float | pd.NA, bool]:
    if forward.empty:
        return (pd.NA, False)

    timestamps = pd.concat(
        [
            pd.Series([setup_bar_ts]),
            pd.to_datetime(forward["Timestamp"], utc=True).reset_index(drop=True),
        ],
        ignore_index=True,
    )
    gaps = timestamps.diff().dt.total_seconds().div(60.0).dropna()
    if gaps.empty:
        return (pd.NA, False)

    max_gap = float(gaps.max())
    return (max_gap, bool(max_gap > LARGE_OUTCOME_GAP_MINUTES))


def _favorable_adverse_series(direction: str, reference_level: float, forward: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    if direction == "LONG":
        favorable = ((forward["High"] - reference_level) / reference_level) * 100
        adverse = ((forward["Low"] - reference_level) / reference_level) * 100
        return favorable, adverse
    if direction == "SHORT":
        favorable = ((reference_level - forward["Low"]) / reference_level) * 100
        adverse = ((reference_level - forward["High"]) / reference_level) * 100
        return favorable, adverse
    raise ValueError(f"Unsupported setup direction for outcome evaluation: {direction}")


def _first_extreme_position(series: pd.Series, value: float, *, use_max: bool) -> int:
    mask = series == value
    if not mask.any():
        return 0
    return int(mask[mask].index[0])


def build_setup_outcomes(
    df: pd.DataFrame,
    setups_df: pd.DataFrame,
    *,
    outcome_horizon_bars: int = OUTCOME_HORIZON_BARS,
) -> pd.DataFrame:
    """Build deterministic per-setup outcome rows over a fixed forward horizon."""
    if outcome_horizon_bars < 1:
        raise ValueError("outcome_horizon_bars must be >= 1")

    _validate_required_columns(df, setups_df)

    if setups_df.empty:
        return _empty_outcomes()

    features = df.loc[:, ["Timestamp", "High", "Low", "Close"]].copy()
    features["Timestamp"] = pd.to_datetime(features["Timestamp"], utc=True)

    setup_ts = pd.to_datetime(setups_df["SetupBarTs"], utc=True)
    ts_counts = setup_ts.map(features["Timestamp"].value_counts()).fillna(0).astype(int)

    if (ts_counts == 0).any():
        bad = setup_ts.loc[ts_counts == 0]
        raise ValueError(
            "Expected exactly one feature row per setup SetupBarTs; "
            f"invalid matches: {[f'{ts.isoformat()} (matches=0)' for ts in bad]}"
        )

    if (ts_counts > 1).any():
        bad = setup_ts.loc[ts_counts > 1]
        counts = ts_counts.loc[ts_counts > 1]
        raise ValueError(
            "Expected exactly one feature row per setup SetupBarTs; "
            "invalid matches: "
            f"{[f'{ts.isoformat()} (matches={count})' for ts, count in zip(bad, counts, strict=False)]}"
        )

    ts_to_index = pd.Series(features.index.to_numpy(), index=features["Timestamp"])

    outcome_rows = []
    for setup in setups_df.itertuples(index=False):
        setup_bar_ts = pd.Timestamp(setup.SetupBarTs)
        if setup_bar_ts.tzinfo is None:
            setup_bar_ts = setup_bar_ts.tz_localize("UTC")
        else:
            setup_bar_ts = setup_bar_ts.tz_convert("UTC")

        setup_idx = int(ts_to_index[setup_bar_ts])
        forward = features.iloc[setup_idx + 1 : setup_idx + 1 + outcome_horizon_bars]
        observed_bars = int(len(forward))

        row = {
            "SetupId": setup.SetupId,
            "SetupBarTs": setup.SetupBarTs,
            "Direction": setup.Direction,
            "ReferenceLevel": setup.ReferenceLevel,
            "OutcomeHorizonBars": outcome_horizon_bars,
            "OutcomeBarsObserved": observed_bars,
        }

        if observed_bars == 0:
            row.update(
                {
                    "OutcomeStatus": "NO_FORWARD_BARS",
                    "MFE_Pct": pd.NA,
                    "MAE_Pct": pd.NA,
                    "CloseReturn_Pct": pd.NA,
                    "BestHigh": pd.NA,
                    "BestLow": pd.NA,
                    "FinalClose": pd.NA,
                    "OutcomeEndTs": pd.NaT,
                    "H2_Post3Label_v1": pd.NA,
                    "H2_Post6Label_v1": pd.NA,
                    "H2_Post12Label_v1": pd.NA,
                }
            )
            outcome_rows.append(row)
            continue

        status = _outcome_status(observed_bars, outcome_horizon_bars)

        best_high = forward["High"].max()
        best_low = forward["Low"].min()
        final_close = forward["Close"].iloc[-1]
        outcome_end_ts = forward["Timestamp"].iloc[-1]
        reference_level = _validated_reference_level(setup.ReferenceLevel)
        setup_close = float(features.iloc[setup_idx]["Close"])

        if setup.Direction == "LONG":
            mfe_pct = ((best_high - reference_level) / reference_level) * 100
            mae_pct = ((best_low - reference_level) / reference_level) * 100
            close_return_pct = ((final_close - reference_level) / reference_level) * 100
        elif setup.Direction == "SHORT":
            mfe_pct = ((reference_level - best_low) / reference_level) * 100
            mae_pct = ((reference_level - best_high) / reference_level) * 100
            close_return_pct = ((reference_level - final_close) / reference_level) * 100
        else:
            raise ValueError(f"Unsupported setup direction for outcome evaluation: {setup.Direction}")

        h2_post3_label, h2_post6_label, h2_post12_label = _build_h2_labels(
            setup=setup,
            setup_close=setup_close,
            reference_level=reference_level,
            forward=forward,
            mfe_pct=mfe_pct,
            mae_pct=mae_pct,
            close_return_pct=close_return_pct,
        )

        row.update(
            {
                "OutcomeStatus": status,
                "MFE_Pct": mfe_pct,
                "MAE_Pct": mae_pct,
                "CloseReturn_Pct": close_return_pct,
                "BestHigh": best_high,
                "BestLow": best_low,
                "FinalClose": final_close,
                "OutcomeEndTs": outcome_end_ts,
                "H2_Post3Label_v1": h2_post3_label,
                "H2_Post6Label_v1": h2_post6_label,
                "H2_Post12Label_v1": h2_post12_label,
            }
        )
        outcome_rows.append(row)

    outcomes = pd.DataFrame(outcome_rows)
    return outcomes.loc[:, OUTCOME_COLUMNS]


def build_setup_outcomes_by_horizon(
    df: pd.DataFrame,
    setups_df: pd.DataFrame,
    *,
    variant_id: str,
    outcome_horizons: tuple[int, ...],
) -> pd.DataFrame:
    """Build research-only multi-horizon outcome rows for sidecar variants."""
    if not variant_id or not str(variant_id).strip():
        raise ValueError("variant_id must be a non-empty string")
    if not outcome_horizons:
        raise ValueError("outcome_horizons must contain at least one horizon")
    invalid_horizons = [h for h in outcome_horizons if int(h) < 1]
    if invalid_horizons:
        raise ValueError(f"outcome_horizons must be >= 1; invalid={invalid_horizons}")

    _validate_required_columns(df, setups_df)

    if setups_df.empty:
        return _empty_multi_horizon_outcomes()

    features = df.loc[:, ["Timestamp", "High", "Low", "Close"]].copy()
    features["Timestamp"] = pd.to_datetime(features["Timestamp"], utc=True)

    setup_ts = pd.to_datetime(setups_df["SetupBarTs"], utc=True)
    ts_counts = setup_ts.map(features["Timestamp"].value_counts()).fillna(0).astype(int)

    if (ts_counts == 0).any():
        bad = setup_ts.loc[ts_counts == 0]
        raise ValueError(
            "Expected exactly one feature row per setup SetupBarTs; "
            f"invalid matches: {[f'{ts.isoformat()} (matches=0)' for ts in bad]}"
        )

    if (ts_counts > 1).any():
        bad = setup_ts.loc[ts_counts > 1]
        counts = ts_counts.loc[ts_counts > 1]
        raise ValueError(
            "Expected exactly one feature row per setup SetupBarTs; "
            "invalid matches: "
            f"{[f'{ts.isoformat()} (matches={count})' for ts, count in zip(bad, counts, strict=False)]}"
        )

    ts_to_index = pd.Series(features.index.to_numpy(), index=features["Timestamp"])

    outcome_rows: list[dict] = []
    for setup in setups_df.itertuples(index=False):
        setup_bar_ts = pd.Timestamp(setup.SetupBarTs)
        if setup_bar_ts.tzinfo is None:
            setup_bar_ts = setup_bar_ts.tz_localize("UTC")
        else:
            setup_bar_ts = setup_bar_ts.tz_convert("UTC")

        setup_idx = int(ts_to_index[setup_bar_ts])
        reference_level = _validated_reference_level(setup.ReferenceLevel)

        for horizon in outcome_horizons:
            horizon_bars = int(horizon)
            forward = features.iloc[setup_idx + 1 : setup_idx + 1 + horizon_bars].reset_index(drop=True)
            observed_bars = int(len(forward))
            max_gap, has_large_gap = _gap_metadata(setup_bar_ts, forward)

            row = {
                "VariantId": str(variant_id),
                "SetupId": setup.SetupId,
                "SetupType": getattr(setup, "SetupType", pd.NA),
                "Direction": setup.Direction,
                "SetupBarTs": setup.SetupBarTs,
                "ReferenceLevel": setup.ReferenceLevel,
                "OutcomeHorizonBars": horizon_bars,
                "OutcomeBarsObserved": observed_bars,
                "OutcomeStatus": _outcome_status(observed_bars, horizon_bars),
                "MaxGapMinutesObserved": max_gap,
                "HasLargeGap": has_large_gap,
            }

            if observed_bars == 0:
                row.update(
                    {
                        "OutcomeEndTs": pd.NaT,
                        "MFE_Pct": pd.NA,
                        "MAE_Pct": pd.NA,
                        "CloseReturn_Pct": pd.NA,
                        "TimeToMFE_Bars": pd.NA,
                        "TimeToMFE_Ts": pd.NaT,
                        "TimeToMAE_Bars": pd.NA,
                        "TimeToMAE_Ts": pd.NaT,
                    }
                )
                outcome_rows.append(row)
                continue

            favorable, adverse = _favorable_adverse_series(setup.Direction, reference_level, forward)
            mfe_pct = float(favorable.max())
            mae_pct = float(adverse.min())
            mfe_pos = _first_extreme_position(favorable, mfe_pct, use_max=True)
            mae_pos = _first_extreme_position(adverse, mae_pct, use_max=False)
            final_close = float(forward["Close"].iloc[-1])

            if setup.Direction == "LONG":
                close_return_pct = ((final_close - reference_level) / reference_level) * 100
            elif setup.Direction == "SHORT":
                close_return_pct = ((reference_level - final_close) / reference_level) * 100
            else:
                raise ValueError(f"Unsupported setup direction for outcome evaluation: {setup.Direction}")

            row.update(
                {
                    "OutcomeEndTs": forward["Timestamp"].iloc[-1],
                    "MFE_Pct": mfe_pct,
                    "MAE_Pct": mae_pct,
                    "CloseReturn_Pct": close_return_pct,
                    "TimeToMFE_Bars": int(mfe_pos + 1),
                    "TimeToMFE_Ts": forward["Timestamp"].iloc[mfe_pos],
                    "TimeToMAE_Bars": int(mae_pos + 1),
                    "TimeToMAE_Ts": forward["Timestamp"].iloc[mae_pos],
                }
            )
            outcome_rows.append(row)

    outcomes = pd.DataFrame(outcome_rows)
    return outcomes.loc[:, MULTI_HORIZON_OUTCOME_COLUMNS]
