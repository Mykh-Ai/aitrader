"""Research-only sidecar variants for Analyzer outputs.

These entrypoints intentionally do not feed baseline rankings, selections,
shortlists, research summaries, or Backtester artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .absorption import detect_absorption
from .base_metrics import add_base_metrics
from .events import build_events
from .failed_breaks import detect_failed_breaks
from .io import ensure_output_dir, save_dataframe
from .loader import load_raw_csv
from .outcomes import build_setup_outcomes_by_horizon
from .setups import SETUP_TTL_BARS, extract_setup_candidates
from .sweeps import detect_sweeps
from .swings import annotate_swings


@dataclass(frozen=True)
class FailedBreakReclaimVariantConfig:
    """Configuration for a failed-break/reclaim research-only sidecar."""

    variant_id: str
    confirmation_bars: int
    setup_ttl_bars: int
    outcome_horizons: tuple[int, ...]
    artifact_namespace: str

    def __post_init__(self) -> None:
        if not self.variant_id.strip():
            raise ValueError("variant_id must be non-empty")
        if self.confirmation_bars < 1:
            raise ValueError("confirmation_bars must be >= 1")
        if self.setup_ttl_bars < 1:
            raise ValueError("setup_ttl_bars must be >= 1")
        if not self.outcome_horizons:
            raise ValueError("outcome_horizons must contain at least one horizon")
        invalid_horizons = [h for h in self.outcome_horizons if h < 1]
        if invalid_horizons:
            raise ValueError(f"outcome_horizons must be >= 1; invalid={invalid_horizons}")
        if not self.artifact_namespace.strip():
            raise ValueError("artifact_namespace must be non-empty")


FAILED_BREAK_RECLAIM_MICRO_V1 = FailedBreakReclaimVariantConfig(
    variant_id="FAILED_BREAK_RECLAIM_MICRO_V1",
    confirmation_bars=5,
    setup_ttl_bars=SETUP_TTL_BARS,
    outcome_horizons=(12,),
    artifact_namespace="research_variants/FAILED_BREAK_RECLAIM_MICRO_V1",
)

FAILED_BREAK_RECLAIM_EXTENDED_V1 = FailedBreakReclaimVariantConfig(
    variant_id="FAILED_BREAK_RECLAIM_EXTENDED_V1",
    confirmation_bars=60,
    setup_ttl_bars=SETUP_TTL_BARS,
    outcome_horizons=(60, 240, 1440, 4320, 10080),
    artifact_namespace="research_variants/FAILED_BREAK_RECLAIM_EXTENDED_V1",
)


def _build_failed_break_reclaim_variant(
    input_path: str | Path,
    *,
    config: FailedBreakReclaimVariantConfig,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    features = load_raw_csv(input_path)
    features = add_base_metrics(features)
    features = annotate_swings(features)
    features = detect_sweeps(features)
    features = detect_failed_breaks(features, confirmation_bars=config.confirmation_bars)
    features = detect_absorption(features)

    events = build_events(features)
    setups = extract_setup_candidates(
        features,
        events,
        setup_ttl_bars=config.setup_ttl_bars,
    )
    outcomes = build_setup_outcomes_by_horizon(
        features,
        setups,
        variant_id=config.variant_id,
        outcome_horizons=config.outcome_horizons,
    )
    return setups, outcomes


def run_research_variants(
    input_path: str | Path,
    output_dir: str | Path,
    *,
    variants: tuple[FailedBreakReclaimVariantConfig, ...] = (FAILED_BREAK_RECLAIM_EXTENDED_V1,),
) -> dict[str, dict[str, object]]:
    """Run explicit research-only sidecar variants.

    Default baseline Analyzer outputs are not produced or consumed here. The caller
    chooses this entrypoint explicitly when sidecar research artifacts are wanted.
    """
    if not variants:
        raise ValueError("variants must contain at least one variant config")

    root = ensure_output_dir(output_dir)
    results: dict[str, dict[str, object]] = {}

    for config in variants:
        setups, outcomes = _build_failed_break_reclaim_variant(input_path, config=config)
        variant_dir = ensure_output_dir(root / config.artifact_namespace)
        outcomes_path = save_dataframe(
            outcomes,
            variant_dir / "analyzer_setup_outcomes_by_horizon.csv",
        )
        results[config.variant_id] = {
            "variant_id": config.variant_id,
            "artifact_namespace": config.artifact_namespace,
            "setups": setups,
            "outcomes_by_horizon": outcomes,
            "outcomes_by_horizon_path": outcomes_path,
        }

    return results

