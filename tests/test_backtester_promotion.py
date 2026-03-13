from pathlib import Path

import pandas as pd
import pytest

from backtester.promotion import (
    PromotionContractError,
    build_promotion_artifacts,
    write_promotion_csvs,
)


def _validation_df(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["scope", "validation_status"])


def _robustness_df(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["scope", "robustness_status"])


def test_determinism_same_inputs_identical_outputs():
    validation = _validation_df(
        [
            {"scope": "ALL_TRADES", "validation_status": "PASS"},
            {"scope": "RESOLVED_ONLY", "validation_status": "REVIEW"},
            {"scope": "R1", "validation_status": "FAIL"},
        ]
    )
    robustness = _robustness_df(
        [
            {"scope": "ALL_TRADES", "robustness_status": "ROBUST"},
            {"scope": "RESOLVED_ONLY", "robustness_status": "UNSTABLE"},
            {"scope": "R1", "robustness_status": "ROBUST"},
        ]
    )

    first = build_promotion_artifacts(validation_summary_df=validation, robustness_summary_df=robustness)
    second = build_promotion_artifacts(validation_summary_df=validation, robustness_summary_df=robustness)

    pd.testing.assert_frame_equal(first.decisions, second.decisions)
    pd.testing.assert_frame_equal(first.details, second.details)


def test_decision_matrix_is_explicit_and_deterministic():
    validation = _validation_df(
        [
            {"scope": "ALL_TRADES", "validation_status": "PASS"},
            {"scope": "RESOLVED_ONLY", "validation_status": "FAIL"},
            {"scope": "R1", "validation_status": "PASS"},
            {"scope": "R2", "validation_status": "REVIEW"},
            {"scope": "R3", "validation_status": "PASS"},
        ]
    )
    robustness = _robustness_df(
        [
            {"scope": "ALL_TRADES", "robustness_status": "ROBUST"},
            {"scope": "RESOLVED_ONLY", "robustness_status": "ROBUST"},
            {"scope": "R1", "robustness_status": "FRAGILE"},
            {"scope": "R2", "robustness_status": "ROBUST"},
            {"scope": "R3", "robustness_status": "UNSTABLE"},
        ]
    )

    artifacts = build_promotion_artifacts(validation_summary_df=validation, robustness_summary_df=robustness)
    decisions = artifacts.decisions.set_index("scope")

    assert decisions.loc["ALL_TRADES", "promotion_decision"] == "PROMOTE"  # PASS + ROBUST
    assert decisions.loc["RESOLVED_ONLY", "promotion_decision"] == "REJECT"  # FAIL + ROBUST
    assert decisions.loc["R1", "promotion_decision"] == "REJECT"  # PASS + FRAGILE
    assert decisions.loc["R2", "promotion_decision"] == "REVIEW"  # REVIEW + ROBUST
    assert decisions.loc["R3", "promotion_decision"] == "REVIEW"  # PASS + UNSTABLE


def test_missing_scope_honesty_validation_present_robustness_missing_is_review_not_promote():
    validation = _validation_df(
        [
            {"scope": "ALL_TRADES", "validation_status": "PASS"},
            {"scope": "RESOLVED_ONLY", "validation_status": "PASS"},
        ]
    )
    robustness = _robustness_df([
        {"scope": "ALL_TRADES", "robustness_status": "ROBUST"},
    ])

    artifacts = build_promotion_artifacts(validation_summary_df=validation, robustness_summary_df=robustness)
    decisions = artifacts.decisions.set_index("scope")

    assert decisions.loc["RESOLVED_ONLY", "promotion_decision"] == "REVIEW"
    assert decisions.loc["RESOLVED_ONLY", "robustness_status"] == "NOT_AVAILABLE"

    details = artifacts.details.set_index("scope")
    assert details.loc["RESOLVED_ONLY", "matrix_rule"] == "missing robustness scope => REVIEW"


def test_invalid_controlled_enums_fail_loudly():
    validation = _validation_df([{"scope": "ALL_TRADES", "validation_status": "MAYBE"}])
    robustness = _robustness_df([{"scope": "ALL_TRADES", "robustness_status": "ROBUST"}])

    with pytest.raises(PromotionContractError, match="validation_status contains unsupported values"):
        build_promotion_artifacts(validation_summary_df=validation, robustness_summary_df=robustness)

    validation_ok = _validation_df([{"scope": "ALL_TRADES", "validation_status": "PASS"}])
    robustness_bad = _robustness_df([{"scope": "ALL_TRADES", "robustness_status": "UNKNOWN"}])

    with pytest.raises(PromotionContractError, match="robustness_status contains unsupported values"):
        build_promotion_artifacts(validation_summary_df=validation_ok, robustness_summary_df=robustness_bad)


def test_manual_review_flag_deterministic_for_review_and_non_review_rows():
    validation = _validation_df(
        [
            {"scope": "ALL_TRADES", "validation_status": "PASS"},
            {"scope": "RESOLVED_ONLY", "validation_status": "PASS"},
            {"scope": "R1", "validation_status": "FAIL"},
        ]
    )
    robustness = _robustness_df(
        [
            {"scope": "ALL_TRADES", "robustness_status": "ROBUST"},
            {"scope": "RESOLVED_ONLY", "robustness_status": "UNSTABLE"},
            {"scope": "R1", "robustness_status": "ROBUST"},
        ]
    )

    decisions = build_promotion_artifacts(validation_summary_df=validation, robustness_summary_df=robustness).decisions.set_index("scope")
    assert decisions.loc["ALL_TRADES", "promotion_decision"] == "PROMOTE"
    assert bool(decisions.loc["ALL_TRADES", "requires_manual_review"]) is False
    assert decisions.loc["RESOLVED_ONLY", "promotion_decision"] == "REVIEW"
    assert bool(decisions.loc["RESOLVED_ONLY", "requires_manual_review"]) is True
    assert decisions.loc["R1", "promotion_decision"] == "REJECT"
    assert bool(decisions.loc["R1", "requires_manual_review"]) is False


def test_notes_explicitly_state_no_live_authorization_language():
    validation = _validation_df([{"scope": "ALL_TRADES", "validation_status": "PASS"}])
    robustness = _robustness_df([{"scope": "ALL_TRADES", "robustness_status": "ROBUST"}])

    decisions = build_promotion_artifacts(validation_summary_df=validation, robustness_summary_df=robustness).decisions
    note = decisions.iloc[0]["notes"]
    assert "execution-design progression only" in note
    assert "not approved for live trading" in note


def test_robustness_scope_without_validation_fails_loudly():
    validation = _validation_df([{"scope": "ALL_TRADES", "validation_status": "PASS"}])
    robustness = _robustness_df(
        [
            {"scope": "ALL_TRADES", "robustness_status": "ROBUST"},
            {"scope": "R1", "robustness_status": "ROBUST"},
        ]
    )

    with pytest.raises(PromotionContractError, match="exists in robustness artifact but not in validation"):
        build_promotion_artifacts(validation_summary_df=validation, robustness_summary_df=robustness)


def test_write_promotion_csvs(tmp_path: Path):
    validation = _validation_df([{"scope": "ALL_TRADES", "validation_status": "PASS"}])
    robustness = _robustness_df([{"scope": "ALL_TRADES", "robustness_status": "ROBUST"}])

    artifacts = build_promotion_artifacts(validation_summary_df=validation, robustness_summary_df=robustness)
    paths = write_promotion_csvs(artifacts=artifacts, output_dir=tmp_path)

    assert (tmp_path / "backtest_promotion_decisions.csv").exists()
    assert (tmp_path / "backtest_promotion_details.csv").exists()
    assert set(paths.keys()) == {
        "backtest_promotion_decisions.csv",
        "backtest_promotion_details.csv",
    }
