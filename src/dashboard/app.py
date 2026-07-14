"""Streamlit dashboard scaffold for Learner Drop-off Insights.

Owner: Shaswath
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st


DATA_DIR = Path("data/processed")
FEATURES_PATH = DATA_DIR / "learner_features.csv"
DRIVERS_PATH = DATA_DIR / "behaviour_driver_rankings.csv"
QUALITY_PATH = DATA_DIR / "data_quality_results.csv"


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def metric_value(frame: pd.DataFrame, label: str, default: str = "Pending") -> str:
    if frame.empty:
        return default
    if label == "completion_rate" and "learner_status" in frame:
        completed = (frame["learner_status"] == "completed").sum()
        return f"{completed / len(frame):.1%}"
    if label == "dropoff_rate" and "learner_status" in frame:
        dropped = (frame["learner_status"] == "silent_dropoff").sum()
        return f"{dropped / len(frame):.1%}"
    if label == "high_risk" and "risk_bucket" in frame:
        return str((frame["risk_bucket"] == "high").sum())
    if label == "median_inactivity" and "days_since_last_activity" in frame:
        return f"{frame['days_since_last_activity'].median():.0f} days"
    return default


def overview(features: pd.DataFrame) -> None:
    st.header("Overview")
    st.caption("Current learner health across completion, drop-off, and risk.")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Completion rate", metric_value(features, "completion_rate"))
    col2.metric("Silent drop-off rate", metric_value(features, "dropoff_rate"))
    col3.metric("High-risk learners", metric_value(features, "high_risk"))
    col4.metric("Median inactivity gap", metric_value(features, "median_inactivity"))

    if features.empty:
        st.info("Waiting for learner feature output from the analysis pipeline.")
        return

    if "risk_bucket" in features:
        st.subheader("Risk bucket distribution")
        st.bar_chart(features["risk_bucket"].value_counts())


def behaviour_drivers(drivers: pd.DataFrame) -> None:
    st.header("Behaviour Drivers")
    st.caption("Behaviours most associated with completion or silent drop-off.")

    if drivers.empty:
        st.info("Waiting for behaviour driver rankings from the analysis lane.")
        return

    st.dataframe(drivers, use_container_width=True)

    if {"feature_name", "strength_score"}.issubset(drivers.columns):
        chart_data = drivers.set_index("feature_name")["strength_score"]
        st.bar_chart(chart_data)


def learner_risk_list(features: pd.DataFrame) -> None:
    st.header("Learner Risk List")
    st.caption("Prioritized learner list for mentor intervention.")

    if features.empty:
        st.info("Waiting for learner risk scores from the analysis pipeline.")
        return

    display_columns = [
        "learner_id",
        "course_id",
        "risk_bucket",
        "risk_score",
        "days_since_last_activity",
        "latest_quiz_score",
        "primary_risk_reason",
        "suggested_action",
    ]
    available_columns = [col for col in display_columns if col in features.columns]
    sorted_features = features.sort_values(
        by="risk_score",
        ascending=False,
    ) if "risk_score" in features else features

    st.dataframe(sorted_features[available_columns], use_container_width=True)


def data_quality(quality: pd.DataFrame) -> None:
    st.header("Data Quality")
    st.caption("Pipeline validation status and known data issues.")

    if quality.empty:
        st.info("Waiting for data quality results from the data layer.")
        return

    st.dataframe(quality, use_container_width=True)


def main() -> None:
    st.set_page_config(
        page_title="Learner Drop-off Insights",
        layout="wide",
    )
    st.title("Learner Drop-off Insights")
    st.write("Mentor-facing dashboard for course completion and silent drop-off risk.")

    features = load_csv(FEATURES_PATH)
    drivers = load_csv(DRIVERS_PATH)
    quality = load_csv(QUALITY_PATH)

    tabs = st.tabs(["Overview", "Behaviour Drivers", "Learner Risk List", "Data Quality"])
    with tabs[0]:
        overview(features)
    with tabs[1]:
        behaviour_drivers(drivers)
    with tabs[2]:
        learner_risk_list(features)
    with tabs[3]:
        data_quality(quality)


if __name__ == "__main__":
    main()
