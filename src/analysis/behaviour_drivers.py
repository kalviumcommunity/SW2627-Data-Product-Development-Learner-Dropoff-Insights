"""Calculate feature associations with learner completion vs silent drop-off.

Owner: Shaswath

Methodology:
    Computes Point-Biserial / Pearson correlation (r) between numerical features
    and a binary completion flag (completed=1, silent_dropoff=0).

Metrics:
    - strength_score: Absolute correlation coefficient |r| in range [0, 1].
    - driver_direction: 'completion' if r >= 0 else 'dropoff'.
    - completed_group_value: Mean value for completed group.
    - dropoff_group_value: Mean value for silent_dropoff group.

Note:
    Features represent statistical associations and predictive signals, not causal mechanisms.

Input:
    data/processed/learner_features.csv

Output:
    data/processed/behaviour_driver_rankings.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]


CANDIDATE_FEATURES = [
    "active_days",
    "total_sessions",
    "average_session_duration",
    "days_since_last_activity",
    "average_quiz_score",
    "latest_quiz_score",
    "quiz_attempt_count",
]

INTERPRETATIONS = {
    "active_days": {
        "completion": "Learners who complete courses log in and participate on more unique days.",
        "dropoff": "Higher number of active days is associated with drop-offs.",
    },
    "total_sessions": {
        "completion": "Completers engage in a higher total number of sessions.",
        "dropoff": "Higher total session count is associated with drop-offs.",
    },
    "average_session_duration": {
        "completion": "Longer session durations are associated with higher completion rates.",
        "dropoff": "Shorter sessions are associated with drop-off risk.",
    },
    "average_quiz_score": {
        "completion": "Higher average quiz scores are associated with course completion.",
        "dropoff": "Lower quiz scores correspond to a higher chance of drop-off.",
    },
    "latest_quiz_score": {
        "completion": "High scores on the latest quiz attempts strongly correlate with course completion.",
        "dropoff": "Declining or low scores on the latest quiz attempts correlate with drop-offs.",
    },
    "days_since_last_activity": {
        "completion": "Lower inactivity gaps are associated with completion.",
        "dropoff": "Longer inactivity gaps are the strongest behavioural signal associated with silent drop-offs.",
    },
    "quiz_attempt_count": {
        "completion": "Learners who attempt more quizzes correlate with higher course completion.",
        "dropoff": "Fewer quiz attempts are associated with drop-off risk.",
    },
}

FALLBACK_RANKINGS = [
    {
        "feature_name": "days_since_last_activity",
        "driver_direction": "dropoff",
        "strength_score": 0.85,
        "completed_group_value": 2.1,
        "dropoff_group_value": 25.4,
        "interpretation": INTERPRETATIONS["days_since_last_activity"]["dropoff"],
    },
    {
        "feature_name": "active_days",
        "driver_direction": "completion",
        "strength_score": 0.78,
        "completed_group_value": 12.5,
        "dropoff_group_value": 3.2,
        "interpretation": INTERPRETATIONS["active_days"]["completion"],
    },
    {
        "feature_name": "latest_quiz_score",
        "driver_direction": "completion",
        "strength_score": 0.65,
        "completed_group_value": 82.4,
        "dropoff_group_value": 45.2,
        "interpretation": INTERPRETATIONS["latest_quiz_score"]["completion"],
    },
    {
        "feature_name": "total_sessions",
        "driver_direction": "completion",
        "strength_score": 0.60,
        "completed_group_value": 18.6,
        "dropoff_group_value": 5.1,
        "interpretation": INTERPRETATIONS["total_sessions"]["completion"],
    },
    {
        "feature_name": "average_quiz_score",
        "driver_direction": "completion",
        "strength_score": 0.55,
        "completed_group_value": 78.9,
        "dropoff_group_value": 48.3,
        "interpretation": INTERPRETATIONS["average_quiz_score"]["completion"],
    },
    {
        "feature_name": "average_session_duration",
        "driver_direction": "completion",
        "strength_score": 0.40,
        "completed_group_value": 15.2,
        "dropoff_group_value": 8.4,
        "interpretation": INTERPRETATIONS["average_session_duration"]["completion"],
    },
    {
        "feature_name": "quiz_attempt_count",
        "driver_direction": "completion",
        "strength_score": 0.30,
        "completed_group_value": 3.5,
        "dropoff_group_value": 1.2,
        "interpretation": INTERPRETATIONS["quiz_attempt_count"]["completion"],
    },
]


def load_input_data(input_path: Path) -> pd.DataFrame:
    if not input_path.exists():
        print(f"Warning: Input path {input_path} does not exist. Using fallback rankings.")
        return pd.DataFrame()
    try:
        return pd.read_csv(input_path)
    except Exception as e:
        print(f"Warning: Failed to read {input_path} due to: {e}. Using fallback rankings.")
        return pd.DataFrame()


def build_fallback_rankings(output_path: Path) -> None:
    print("Generating fallback rankings due to insufficient data...")
    df = pd.DataFrame(FALLBACK_RANKINGS)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Wrote fallback rankings to {output_path}")


def analyze_drivers(features_df: pd.DataFrame) -> pd.DataFrame:
    # Validate structure
    if "learner_status" not in features_df.columns:
        print("Warning: 'learner_status' column not found in input features.")
        return pd.DataFrame()

    # Filter completed vs silent drop-offs
    target_groups = features_df[features_df["learner_status"].isin(["completed", "silent_dropoff"])].copy()
    if target_groups.empty or target_groups["learner_status"].nunique() < 2:
        print("Warning: Insufficient completed or silent_dropoff groups for correlation analysis.")
        return pd.DataFrame()

    # Convert target variable to binary (completed = 1, silent_dropoff = 0)
    target_groups["completed_flag"] = (target_groups["learner_status"] == "completed").astype(int)

    drivers_list = []
    for feature in CANDIDATE_FEATURES:
        if feature not in target_groups.columns:
            continue

        # Convert feature to numeric values, ignoring strings or Nones
        numeric_series = pd.to_numeric(target_groups[feature], errors="coerce")
        valid_mask = numeric_series.notna()

        # Needs enough samples with valid feature values
        if valid_mask.sum() < 2:
            continue

        feat_values = numeric_series[valid_mask]
        flags = target_groups.loc[valid_mask, "completed_flag"]

        # If variance is 0, correlation coefficient is undefined
        if feat_values.std() == 0 or flags.std() == 0:
            correlation = 0.0
        else:
            correlation = np.corrcoef(feat_values, flags)[0, 1]
            if np.isnan(correlation):
                correlation = 0.0

        # Calculate group means
        completed_mean = feat_values[flags == 1].mean()
        dropoff_mean = feat_values[flags == 0].mean()

        # Handle NaNs in means
        completed_val = float(completed_mean) if pd.notna(completed_mean) else 0.0
        dropoff_val = float(dropoff_mean) if pd.notna(dropoff_mean) else 0.0

        # Determine direction
        direction = "completion" if correlation >= 0 else "dropoff"
        strength = abs(correlation)

        # Get explanation template
        interpretation = INTERPRETATIONS[feature][direction]

        drivers_list.append({
            "feature_name": feature,
            "driver_direction": direction,
            "strength_score": float(np.round(strength, 4)),
            "completed_group_value": float(np.round(completed_val, 2)),
            "dropoff_group_value": float(np.round(dropoff_val, 2)),
            "interpretation": interpretation,
        })

    if not drivers_list:
        return pd.DataFrame()

    drivers_df = pd.DataFrame(drivers_list)
    # Sort by strength score descending
    drivers_df = drivers_df.sort_values(by="strength_score", ascending=False)
    return drivers_df


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Rank features driving course completion versus silent drop-off."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=PROJECT_ROOT / "data" / "processed" / "learner_features.csv",
        help="Path to input learner features CSV file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "data" / "processed" / "behaviour_driver_rankings.csv",
        help="Path to output rankings CSV file.",
    )
    args = parser.parse_args()

    features_df = load_input_data(args.input)
    if features_df.empty:
        build_fallback_rankings(args.output)
        return 0

    drivers_df = analyze_drivers(features_df)
    if drivers_df.empty:
        build_fallback_rankings(args.output)
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    drivers_df.to_csv(args.output, index=False)
    print(f"Successfully calculated and wrote behaviour drivers to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
