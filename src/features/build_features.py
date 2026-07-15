"""Build learner-course labels and first-pass risk features.

Owner: Shaswath

Input:
    data/processed/learner_course_aggregates.csv

Output:
    data/processed/learner_features.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


COMPLETED_STATUSES = {"completed", "complete", "passed", "certified"}


def has_column(frame: pd.DataFrame, column: str) -> bool:
    return column in frame.columns


def normalize_progress(value: object) -> float:
    if pd.isna(value):
        return 0.0
    try:
        progress = float(value)
    except (ValueError, TypeError):
        return 0.0
    if progress > 1:
        return progress / 100
    return progress


def meaningful_activity(row: pd.Series) -> bool:
    try:
        sessions = float(row.get("total_sessions", 0) or 0)
    except (ValueError, TypeError):
        sessions = 0.0
    try:
        quizzes = float(row.get("quiz_attempt_count", 0) or 0)
    except (ValueError, TypeError):
        quizzes = 0.0
    progress = normalize_progress(row.get("progress_percent", 0))
    return sessions > 0 or quizzes > 0 or progress > 0


def is_completed(row: pd.Series) -> bool:
    status = str(row.get("completion_status", "") or "").strip().lower()
    completion_date = row.get("completion_date")
    progress = normalize_progress(row.get("progress_percent", 0))
    return (
        status in COMPLETED_STATUSES
        or (pd.notna(completion_date) and str(completion_date).strip() != "")
        or progress >= 0.90
    )


def assign_status(row: pd.Series, inactivity_threshold_days: int) -> str:
    if is_completed(row):
        return "completed"

    if not meaningful_activity(row):
        return "unstarted"

    try:
        days_inactive = float(row.get("days_since_last_activity", 0) or 0)
    except (ValueError, TypeError):
        days_inactive = 0.0
    latest_quiz_score = row.get("latest_quiz_score")
    progress = normalize_progress(row.get("progress_percent", 0))

    if days_inactive >= inactivity_threshold_days:
        return "silent_dropoff"

    try:
        low_latest_score = pd.notna(latest_quiz_score) and float(latest_quiz_score) < 50
    except (ValueError, TypeError):
        low_latest_score = False

    halfway_inactive = days_inactive >= max(10, inactivity_threshold_days // 2)
    stalled_progress = progress < 0.50 and days_inactive >= 10

    if low_latest_score or halfway_inactive or stalled_progress:
        return "at_risk"

    return "active"


def risk_reason(row: pd.Series, inactivity_threshold_days: int) -> tuple[int, str, str]:
    if row.get("learner_status") == "completed":
        return 0, "completed", "No action needed"

    if row.get("learner_status") == "unstarted":
        return 60, "No meaningful activity after enrollment", "Send onboarding reminder"

    try:
        days_inactive = float(row.get("days_since_last_activity", 0) or 0)
    except (ValueError, TypeError):
        days_inactive = 0.0
    latest_quiz_score = row.get("latest_quiz_score")
    progress = normalize_progress(row.get("progress_percent", 0))

    score = 0
    reasons: list[str] = []

    if days_inactive >= inactivity_threshold_days:
        score += 50
        reasons.append("Inactive beyond threshold")
    elif days_inactive >= max(10, inactivity_threshold_days // 2):
        score += 25
        reasons.append("Activity gap is growing")

    try:
        has_low_score = pd.notna(latest_quiz_score) and float(latest_quiz_score) < 50
    except (ValueError, TypeError):
        has_low_score = False

    if has_low_score:
        score += 25
        reasons.append("Latest quiz score is low")

    if progress < 0.50 and days_inactive >= 10:
        score += 20
        reasons.append("Progress appears stalled")

    if not reasons:
        reasons.append("Healthy activity")

    primary_reason = reasons[0]
    if primary_reason == "Latest quiz score is low":
        action = "Offer quiz support"
    elif primary_reason in {"Inactive beyond threshold", "Activity gap is growing"}:
        action = "Send check-in reminder"
    elif primary_reason == "Progress appears stalled":
        action = "Recommend next module"
    else:
        action = "No action needed"

    return min(score, 100), primary_reason, action


def build_features(input_path: Path, inactivity_threshold_days: int) -> pd.DataFrame:
    frame = pd.read_csv(input_path)

    # Check for critical identifier columns
    for col in ["learner_id", "course_id"]:
        if col not in frame.columns:
            raise ValueError(f"Input data is missing critical column: {col}")

    # Set up defaults for optional/expected columns if they are missing
    expected_cols = {
        "enrollment_date": None,
        "completion_status": None,
        "completion_date": None,
        "progress_percent": 0.0,
        "total_sessions": 0,
        "active_days": 0,
        "average_session_duration": 0.0,
        "latest_activity_date": None,
        "quiz_attempt_count": 0,
        "average_quiz_score": None,
        "latest_quiz_score": None,
    }
    for col, default_val in expected_cols.items():
        if col not in frame.columns:
            print(f"Warning: Expected column '{col}' is missing from input. Initializing with default: {default_val}")
            frame[col] = default_val

    if not has_column(frame, "days_since_last_activity"):
        if has_column(frame, "latest_activity_date") and frame["latest_activity_date"].notna().any():
            latest_date = pd.to_datetime(frame["latest_activity_date"], errors="coerce")
            anchor_date = latest_date.max()
            if pd.notna(anchor_date):
                frame["days_since_last_activity"] = (anchor_date - latest_date).dt.days
            else:
                frame["days_since_last_activity"] = 0
        else:
            frame["days_since_last_activity"] = 0

    # Fill NaNs in days_since_last_activity if datetime conversion failed
    frame["days_since_last_activity"] = frame["days_since_last_activity"].fillna(0).astype(int)

    frame["learner_status"] = frame.apply(
        assign_status,
        axis=1,
        inactivity_threshold_days=inactivity_threshold_days,
    )

    risk_outputs = frame.apply(
        risk_reason,
        axis=1,
        inactivity_threshold_days=inactivity_threshold_days,
        result_type="expand",
    )
    frame["risk_score"] = risk_outputs[0]
    frame["primary_risk_reason"] = risk_outputs[1]
    frame["suggested_action"] = risk_outputs[2]

    # Convert risk_score to numeric, handle NaN
    frame["risk_score"] = pd.to_numeric(frame["risk_score"], errors="coerce").fillna(0).astype(int)

    frame["risk_bucket"] = pd.cut(
        frame["risk_score"],
        bins=[-1, 39, 69, 100],
        labels=["low", "medium", "high"],
    ).astype(str)

    # Ensure all 12 MVP columns are present and ordering is clean
    mvp_columns = [
        "learner_id",
        "course_id",
        "learner_status",
        "risk_score",
        "risk_bucket",
        "days_since_last_activity",
        "total_sessions",
        "active_days",
        "average_quiz_score",
        "latest_quiz_score",
        "primary_risk_reason",
        "suggested_action"
    ]
    # We want to make sure the columns are ordered with MVP columns first, then any other columns
    other_columns = [col for col in frame.columns if col not in mvp_columns]
    frame = frame[mvp_columns + other_columns]

    return frame


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default="data/processed/learner_course_aggregates.csv",
        help="Path to learner-course aggregate CSV.",
    )
    parser.add_argument(
        "--output",
        default="data/processed/learner_features.csv",
        help="Path where learner features should be written.",
    )
    parser.add_argument(
        "--inactivity-threshold-days",
        type=int,
        default=21,
        help="Days without activity used to label silent drop-off.",
    )
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    features = build_features(Path(args.input), args.inactivity_threshold_days)
    features.to_csv(output_path, index=False)
    print(f"Wrote {len(features)} learner-course feature rows to {output_path}")


if __name__ == "__main__":
    main()
