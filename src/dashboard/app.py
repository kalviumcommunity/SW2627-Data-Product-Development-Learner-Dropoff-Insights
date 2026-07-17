"""Streamlit dashboard for Learner Drop-off Insights.

Owner: Jaswanth
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st


DATA_DIR = Path("data/processed")
FEATURES_PATH = DATA_DIR / "learner_features.csv"
DRIVERS_PATH = DATA_DIR / "behaviour_driver_rankings.csv"

STATUS_ORDER = ["completed", "active", "at_risk", "silent_dropoff", "unstarted"]
RISK_BUCKET_ORDER = ["high", "medium", "low"]
DRIVER_DIRECTION_ORDER = ["dropoff", "completion"]
DRIVER_REQUIRED_COLUMNS = {
    "feature_name",
    "driver_direction",
    "strength_score",
    "completed_group_value",
    "dropoff_group_value",
    "interpretation",
}


@st.cache_data(show_spinner=False)
def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def metric_value(frame: pd.DataFrame, label: str, default: str = "Pending") -> str:
    if frame.empty:
        return default
    if label == "total_learners":
        if "learner_id" in frame.columns:
            return f"{frame['learner_id'].nunique():,}"
        return f"{len(frame):,}"
    if label == "completion_rate" and "learner_status" in frame.columns:
        completed = (frame["learner_status"] == "completed").sum()
        return f"{completed / len(frame):.1%}"
    if label == "dropoff_rate" and "learner_status" in frame.columns:
        dropped = (frame["learner_status"] == "silent_dropoff").sum()
        return f"{dropped / len(frame):.1%}"
    if label == "high_risk" and "risk_bucket" in frame.columns:
        return str((frame["risk_bucket"] == "high").sum())
    if label == "median_inactivity" and "days_since_last_activity" in frame.columns:
        median_gap = pd.to_numeric(
            frame["days_since_last_activity"],
            errors="coerce",
        ).median()
        if pd.notna(median_gap):
            return f"{median_gap:.0f} days"
    return default


def sorted_options(
    frame: pd.DataFrame,
    column: str,
    preferred_order: list[str] | None = None,
) -> list[str]:
    if column not in frame.columns or frame[column].dropna().empty:
        return []
    values = [str(value) for value in frame[column].dropna().unique()]
    if preferred_order:
        ordered = [value for value in preferred_order if value in values]
        unordered = sorted(value for value in values if value not in ordered)
        return ordered + unordered
    return sorted(values)


def apply_global_filters(features: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Filters")

    if features.empty:
        st.sidebar.info("Filters activate after `learner_features.csv` is generated.")
        return features

    filtered = features.copy()
    filter_config = [
        ("course_id", "Course", None),
        ("cohort", "Cohort", None),
        ("learner_status", "Learner status", STATUS_ORDER),
        ("risk_bucket", "Risk bucket", RISK_BUCKET_ORDER),
        ("primary_risk_reason", "Risk reason", None),
    ]

    for column, label, preferred_order in filter_config:
        options = sorted_options(filtered, column, preferred_order)
        if not options:
            continue
        selected = st.sidebar.multiselect(label, options, default=options)
        if selected:
            filtered = filtered[filtered[column].astype(str).isin(selected)]

    return filtered


def ordered_value_counts(
    frame: pd.DataFrame,
    column: str,
    preferred_order: list[str],
) -> pd.Series:
    counts = frame[column].value_counts()
    ordered_values = [value for value in preferred_order if value in counts.index]
    remaining_values = sorted(value for value in counts.index if value not in ordered_values)
    return counts.reindex(ordered_values + remaining_values)


def feature_label(feature_name: object) -> str:
    return str(feature_name).replace("_", " ").title()


def prepare_driver_rankings(drivers: pd.DataFrame) -> pd.DataFrame:
    if drivers.empty or not DRIVER_REQUIRED_COLUMNS.issubset(drivers.columns):
        return pd.DataFrame()

    prepared = drivers.copy()
    prepared["strength_score"] = pd.to_numeric(
        prepared["strength_score"],
        errors="coerce",
    ).fillna(0)
    prepared["completed_group_value"] = pd.to_numeric(
        prepared["completed_group_value"],
        errors="coerce",
    )
    prepared["dropoff_group_value"] = pd.to_numeric(
        prepared["dropoff_group_value"],
        errors="coerce",
    )
    prepared["feature_label"] = prepared["feature_name"].map(feature_label)
    return prepared.sort_values("strength_score", ascending=False)


def driver_direction_counts(drivers: pd.DataFrame) -> pd.Series:
    if drivers.empty or "driver_direction" not in drivers.columns:
        return pd.Series(dtype=int)
    return ordered_value_counts(drivers, "driver_direction", DRIVER_DIRECTION_ORDER)


def driver_details_table(drivers: pd.DataFrame) -> pd.DataFrame:
    prepared = prepare_driver_rankings(drivers)
    if prepared.empty:
        return pd.DataFrame()

    table = prepared[
        [
            "feature_label",
            "driver_direction",
            "strength_score",
            "completed_group_value",
            "dropoff_group_value",
            "interpretation",
        ]
    ].copy()
    return table.rename(
        columns={
            "feature_label": "Feature",
            "driver_direction": "Direction",
            "strength_score": "Strength",
            "completed_group_value": "Completed avg",
            "dropoff_group_value": "Silent drop-off avg",
            "interpretation": "Interpretation",
        }
    )


def risk_table(features: pd.DataFrame) -> pd.DataFrame:
    display_columns = [
        "learner_id",
        "course_id",
        "cohort",
        "learner_status",
        "risk_bucket",
        "risk_score",
        "latest_activity_date",
        "days_since_last_activity",
        "latest_quiz_score",
        "primary_risk_reason",
        "suggested_action",
    ]
    available_columns = [
        column for column in display_columns if column in features.columns
    ]
    sorted_features = features.copy()
    sort_columns = [
        column
        for column in ["risk_score", "days_since_last_activity"]
        if column in sorted_features.columns
    ]
    if sort_columns:
        sorted_features = sorted_features.sort_values(
            by=sort_columns,
            ascending=[False] * len(sort_columns),
        )
    return sorted_features[available_columns]


def build_interim_feature_comparison(features: pd.DataFrame) -> pd.DataFrame:
    if "learner_status" not in features.columns:
        return pd.DataFrame()

    comparison_groups = features[
        features["learner_status"].isin(["completed", "silent_dropoff"])
    ].copy()
    if comparison_groups["learner_status"].nunique() < 2:
        return pd.DataFrame()

    candidate_features = [
        "total_sessions",
        "active_days",
        "average_session_duration",
        "days_since_last_activity",
        "average_quiz_score",
        "latest_quiz_score",
        "risk_score",
    ]
    numeric_features = [
        column for column in candidate_features if column in comparison_groups.columns
    ]
    if not numeric_features:
        return pd.DataFrame()

    for column in numeric_features:
        comparison_groups[column] = pd.to_numeric(
            comparison_groups[column],
            errors="coerce",
        )

    grouped = comparison_groups.groupby("learner_status")[numeric_features].mean().T
    if {"completed", "silent_dropoff"}.difference(grouped.columns):
        return pd.DataFrame()

    grouped = grouped.rename_axis("feature_name").reset_index()
    grouped["absolute_gap"] = (
        grouped["completed"] - grouped["silent_dropoff"]
    ).abs()
    return grouped.sort_values("absolute_gap", ascending=False)


def overview(features: pd.DataFrame) -> None:
    st.header("Overview")
    st.caption("Current learner health across completion, drop-off, and risk.")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Learners", metric_value(features, "total_learners"))
    col2.metric("Completion rate", metric_value(features, "completion_rate"))
    col3.metric("Silent drop-off rate", metric_value(features, "dropoff_rate"))
    col4.metric("High-risk learners", metric_value(features, "high_risk"))
    col5.metric("Median inactivity gap", metric_value(features, "median_inactivity"))

    if features.empty:
        st.info("Waiting for learner feature output from the analysis pipeline.")
        return

    chart_col1, chart_col2 = st.columns(2)
    if "learner_status" in features.columns:
        with chart_col1:
            st.subheader("Learner status distribution")
            st.bar_chart(ordered_value_counts(features, "learner_status", STATUS_ORDER))

    if "risk_bucket" in features.columns:
        with chart_col2:
            st.subheader("Risk bucket distribution")
            st.bar_chart(ordered_value_counts(features, "risk_bucket", RISK_BUCKET_ORDER))

    if "primary_risk_reason" in features.columns:
        st.subheader("Top risk reasons")
        st.bar_chart(features["primary_risk_reason"].value_counts().head(8))

    queue_preview = risk_table(features).head(8)
    if not queue_preview.empty:
        st.subheader("Intervention queue preview")
        st.dataframe(queue_preview, use_container_width=True, hide_index=True)


def behaviour_drivers(drivers: pd.DataFrame, features: pd.DataFrame) -> None:
    st.header("Behaviour Drivers")
    st.caption("Behaviours most associated with completion or silent drop-off.")

    if not drivers.empty:
        prepared_drivers = prepare_driver_rankings(drivers)
        if prepared_drivers.empty:
            st.warning("Behaviour driver file is present, but expected columns are missing.")
            st.dataframe(drivers, use_container_width=True, hide_index=True)
            return

        top_driver = prepared_drivers.iloc[0]
        col1, col2, col3 = st.columns(3)
        col1.metric("Ranked behaviours", len(prepared_drivers))
        col2.metric("Top driver", top_driver["feature_label"])
        col3.metric("Top strength", f"{top_driver['strength_score']:.2f}")

        st.info(str(top_driver["interpretation"]))

        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            st.subheader("Ranked driver strength")
            chart_data = prepared_drivers.set_index("feature_label")["strength_score"]
            st.bar_chart(chart_data)

        with chart_col2:
            st.subheader("Driver direction mix")
            st.bar_chart(driver_direction_counts(prepared_drivers))

        st.subheader("Completed vs silent drop-off comparison")
        st.dataframe(
            driver_details_table(prepared_drivers),
            use_container_width=True,
            hide_index=True,
        )
        return

    st.info("Waiting for final behaviour driver rankings from the analysis lane.")

    interim_comparison = build_interim_feature_comparison(features)
    if not interim_comparison.empty:
        st.subheader("Interim completed vs drop-off comparison")
        st.caption(
            "This comparison is a dashboard preview only. "
            "It is not the final behaviour ranking."
        )
        st.dataframe(interim_comparison, use_container_width=True, hide_index=True)


def learner_risk_list(features: pd.DataFrame) -> None:
    st.header("Learner Risk List")
    st.caption("Prioritized learner list for mentor intervention.")

    if features.empty:
        st.info("Waiting for learner risk scores from the analysis pipeline.")
        return

    table = risk_table(features)
    if table.empty:
        st.warning(
            "Learner feature output is present, but expected risk-list columns are missing."
        )
        return

    st.dataframe(table, use_container_width=True, hide_index=True)
    st.download_button(
        "Download filtered risk list",
        data=table.to_csv(index=False).encode("utf-8"),
        file_name="filtered_learner_risk_list.csv",
        mime="text/csv",
    )


def data_status(features: pd.DataFrame, drivers: pd.DataFrame) -> None:
    feature_status = (
        f"{len(features):,} learner-course rows" if not features.empty else "features pending"
    )
    driver_status = (
        f"{len(drivers):,} driver rows" if not drivers.empty else "drivers pending"
    )
    st.caption(f"Data status: {feature_status} | {driver_status}")


def main() -> None:
    st.set_page_config(
        page_title="Learner Drop-off Insights",
        layout="wide",
    )
    st.title("Learner Drop-off Insights")
    st.write("Mentor-facing dashboard for course completion and silent drop-off risk.")

    features = load_csv(FEATURES_PATH)
    drivers = load_csv(DRIVERS_PATH)
    filtered_features = apply_global_filters(features)
    data_status(filtered_features, drivers)

    tabs = st.tabs(["Overview", "Behaviour Drivers", "Learner Risk List"])
    with tabs[0]:
        overview(filtered_features)
    with tabs[1]:
        behaviour_drivers(drivers, filtered_features)
    with tabs[2]:
        learner_risk_list(filtered_features)


if __name__ == "__main__":
    main()
