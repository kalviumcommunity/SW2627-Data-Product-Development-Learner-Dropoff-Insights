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
    progress = float(value)
    if progress > 1:
        return progress / 100
    return progress


def meaningful_activity(row: pd.Series) -> bool:
    sessions = float(row.get("total_sessions", 0) or 0)
    quizzes = float(row.get("quiz_attempt_count", 0) or 0)
    progress = normalize_progress(row.get("progress_percent", 0))
    return sessions > 0 or quizzes > 0 or progress > 0


def is_completed(row: pd.Series) -> bool:
    status = str(row.get("completion_status", "") or "").strip().lower()
    completion_date = row.get("completion_date")
    progress = normalize_progress(row.get("progress_percent", 0))
    return (
        status in COMPLETED_STATUSES
        or pd.notna(completion_date)
        or progress >= 0.90
    )


def assign_status(row: pd.Series, inactivity_threshold_days: int) -> str:
    if is_completed(row):
        return "completed"

    if not meaningful_activity(row):
        return "unstarted"

    days_inactive = float(row.get("days_since_last_activity", 0) or 0)
    latest_quiz_score = row.get("latest_quiz_score")
    progress = normalize_progress(row.get("progress_percent", 0))

    if days_inactive >= inactivity_threshold_days:
        return "silent_dropoff"

    low_latest_score = pd.notna(latest_quiz_score) and float(latest_quiz_score) < 50
    halfway_inactive = days_inactive >= max(10, inactivity_threshold_days // 2)
    stalled_progress = progress < 0.50 and days_inactive >= 10

    if low_latest_score or halfway_inactive or stalled_progress:
        return "at_risk"

    return "active"


def risk_reason(row: pd.Series, inactivity_threshold_days: int) -> tuple[int, str, str]:
    if row["learner_status"] == "completed":
        return 0, "completed", "No action needed"

    if row["learner_status"] == "unstarted":
        return 60, "No meaningful activity after enrollment", "Send onboarding reminder"

    days_inactive = float(row.get("days_since_last_activity", 0) or 0)
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

    if pd.notna(latest_quiz_score) and float(latest_quiz_score) < 50:
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

    if not has_column(frame, "days_since_last_activity"):
        if has_column(frame, "latest_activity_date"):
            latest_date = pd.to_datetime(frame["latest_activity_date"], errors="coerce")
            anchor_date = latest_date.max()
            frame["days_since_last_activity"] = (anchor_date - latest_date).dt.days
        else:
            frame["days_since_last_activity"] = 0

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

    frame["risk_bucket"] = pd.cut(
        frame["risk_score"],
        bins=[-1, 39, 69, 100],
        labels=["low", "medium", "high"],
    ).astype(str)

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
