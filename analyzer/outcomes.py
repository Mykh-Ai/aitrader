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
]

OUTCOME_HORIZON_BARS = 12


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
            }
        )
        outcome_rows.append(row)

    outcomes = pd.DataFrame(outcome_rows)
    return outcomes.loc[:, OUTCOME_COLUMNS]
