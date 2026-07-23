"""Run feature engineering and behaviour-driver analysis as one handoff."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.analysis.behaviour_drivers import (
    analyze_drivers,
    build_fallback_rankings,
)
from src.features.build_features import build_features


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_AGGREGATE_INPUT = (
    PROJECT_ROOT / "data" / "processed" / "learner_course_aggregates.csv"
)
DEFAULT_FEATURE_OUTPUT = (
    PROJECT_ROOT / "data" / "processed" / "learner_features.csv"
)
DEFAULT_DRIVER_OUTPUT = (
    PROJECT_ROOT / "data" / "processed" / "behaviour_driver_rankings.csv"
)


@dataclass(frozen=True)
class AnalysisPipelineResult:
    feature_row_count: int
    driver_row_count: int
    analysis_source: str
    return_code: int


def run_analysis_pipeline(
    aggregate_input: Path = DEFAULT_AGGREGATE_INPUT,
    feature_output: Path = DEFAULT_FEATURE_OUTPUT,
    driver_output: Path = DEFAULT_DRIVER_OUTPUT,
    inactivity_threshold_days: int = 21,
    require_observed: bool = False,
) -> AnalysisPipelineResult:
    features = build_features(aggregate_input, inactivity_threshold_days)
    feature_output.parent.mkdir(parents=True, exist_ok=True)
    features.to_csv(feature_output, index=False)

    drivers = analyze_drivers(features)
    if drivers.empty:
        build_fallback_rankings(driver_output)
        drivers = pd.read_csv(driver_output)
    else:
        driver_output.parent.mkdir(parents=True, exist_ok=True)
        drivers.to_csv(driver_output, index=False)

    sources = set(drivers["analysis_source"].dropna().astype(str))
    analysis_source = next(iter(sources)) if len(sources) == 1 else "mixed"
    return_code = int(require_observed and analysis_source != "observed_data")

    return AnalysisPipelineResult(
        feature_row_count=len(features),
        driver_row_count=len(drivers),
        analysis_source=analysis_source,
        return_code=return_code,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate learner features and behaviour-driver rankings."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_AGGREGATE_INPUT)
    parser.add_argument("--feature-output", type=Path, default=DEFAULT_FEATURE_OUTPUT)
    parser.add_argument("--driver-output", type=Path, default=DEFAULT_DRIVER_OUTPUT)
    parser.add_argument("--inactivity-threshold-days", type=int, default=21)
    parser.add_argument(
        "--require-observed",
        action="store_true",
        help="Return a failure code when only fallback example rankings are produced.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_analysis_pipeline(
        aggregate_input=args.input,
        feature_output=args.feature_output,
        driver_output=args.driver_output,
        inactivity_threshold_days=args.inactivity_threshold_days,
        require_observed=args.require_observed,
    )
    print(f"Wrote {result.feature_row_count} learner feature row(s).")
    print(
        f"Wrote {result.driver_row_count} behaviour driver row(s) "
        f"from {result.analysis_source}."
    )
    if result.return_code:
        print("Observed rankings are required, but the available data was insufficient.")
    return result.return_code


if __name__ == "__main__":
    raise SystemExit(main())
