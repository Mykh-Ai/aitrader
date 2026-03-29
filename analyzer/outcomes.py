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

def build_setup_outcomes(df: pd.DataFrame, setups_df: pd.DataFrame) -> pd.DataFrame:
    """Build deterministic per-setup outcome rows over a fixed forward horizon."""
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
        forward = features.iloc[setup_idx + 1 : setup_idx + 1 + OUTCOME_HORIZON_BARS]
        observed_bars = int(len(forward))

        row = {
            "SetupId": setup.SetupId,
            "SetupBarTs": setup.SetupBarTs,
            "Direction": setup.Direction,
            "ReferenceLevel": setup.ReferenceLevel,
            "OutcomeHorizonBars": OUTCOME_HORIZON_BARS,
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

        if observed_bars == OUTCOME_HORIZON_BARS:
            status = "FULL_HORIZON"
        else:
            status = "PARTIAL_HORIZON"

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
