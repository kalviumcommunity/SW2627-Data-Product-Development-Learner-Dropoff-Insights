from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.analysis.behaviour_drivers import analyze_drivers
from src.features.build_features import build_features
from src.ingestion.run_data_pipeline import run_pipeline


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = PROJECT_ROOT / "src" / "database" / "schema.sql"
AGGREGATE_QUERY_PATH = (
    PROJECT_ROOT / "src" / "database" / "queries" / "learner_course_aggregates.sql"
)


def write_csv(raw_dir: Path, filename: str, rows: list[dict[str, object]]) -> None:
    pd.DataFrame(rows).to_csv(raw_dir / filename, index=False)


def write_end_to_end_raw_fixture(raw_dir: Path) -> None:
    learner_ids = ["C1", "C2", "D1", "D2"]
    write_csv(
        raw_dir,
        "learners.csv",
        [
            {
                "learner_id": learner_id,
                "signup_date": "2026-05-20",
                "cohort": "July-2026",
                "region": "South",
            }
            for learner_id in learner_ids
        ],
    )
    write_csv(
        raw_dir,
        "courses.csv",
        [
            {
                "course_id": "COURSE",
                "course_name": "Python Basics",
                "category": "Programming",
                "expected_duration_days": 45,
            }
        ],
    )
    write_csv(
        raw_dir,
        "enrollments.csv",
        [
            {
                "learner_id": learner_id,
                "course_id": "COURSE",
                "enrollment_date": "2026-06-01",
                "progress_percent": 1.0 if learner_id.startswith("C") else 0.25,
                "completion_status": (
                    "completed" if learner_id.startswith("C") else "active"
                ),
                "completion_date": (
                    "2026-07-20" if learner_id.startswith("C") else ""
                ),
            }
            for learner_id in learner_ids
        ],
    )

    session_dates = {
        "C1": "2026-07-20",
        "C2": "2026-07-18",
        "D1": "2026-06-01",
        "D2": "2026-06-03",
    }
    session_durations = {"C1": 25, "C2": 22, "D1": 8, "D2": 10}
    write_csv(
        raw_dir,
        "sessions.csv",
        [
            {
                "session_id": f"S-{learner_id}",
                "learner_id": learner_id,
                "course_id": "COURSE",
                "session_start_time": session_dates[learner_id],
                "session_duration_minutes": session_durations[learner_id],
                "module_id": "M1",
                "content_type": "video",
            }
            for learner_id in learner_ids
        ],
    )

    quiz_scores = {"C1": 9, "C2": 8, "D1": 4, "D2": 5}
    write_csv(
        raw_dir,
        "quizzes.csv",
        [
            {
                "quiz_attempt_id": f"QA-{learner_id}",
                "learner_id": learner_id,
                "course_id": "COURSE",
                "quiz_id": "Q1",
                "attempt_time": session_dates[learner_id],
                "score": quiz_scores[learner_id],
                "max_score": 10,
                "attempt_number": 1,
            }
            for learner_id in learner_ids
        ],
    )


class TestEndToEndProductFlow(unittest.TestCase):
    def test_raw_files_reach_observed_dashboard_driver_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            raw_dir = tmp_path / "raw"
            raw_dir.mkdir()
            database_path = tmp_path / "learner_dropoff.sqlite"
            aggregate_output = tmp_path / "learner_course_aggregates.csv"
            feature_output = tmp_path / "learner_features.csv"
            driver_output = tmp_path / "behaviour_driver_rankings.csv"
            write_end_to_end_raw_fixture(raw_dir)

            pipeline_result = run_pipeline(
                raw_dir=raw_dir,
                database_path=database_path,
                schema_path=SCHEMA_PATH,
                aggregate_output_path=aggregate_output,
                aggregate_query_path=AGGREGATE_QUERY_PATH,
                strict_raw=True,
            )
            features = build_features(aggregate_output, inactivity_threshold_days=21)
            features.to_csv(feature_output, index=False)
            drivers = analyze_drivers(features)
            drivers.to_csv(driver_output, index=False)

            self.assertEqual(pipeline_result.return_code, 0)
            self.assertEqual(pipeline_result.aggregate_row_count, 4)
            self.assertEqual(
                features["learner_status"].value_counts().to_dict(),
                {"completed": 2, "silent_dropoff": 2},
            )
            self.assertFalse(drivers.empty)
            self.assertEqual(set(drivers["analysis_source"]), {"observed_data"})
            self.assertTrue((drivers["completed_group_count"] == 2).all())
            self.assertTrue((drivers["dropoff_group_count"] == 2).all())

            expected_dashboard_columns = {
                "feature_name",
                "driver_direction",
                "strength_score",
                "completed_group_value",
                "dropoff_group_value",
                "completed_group_count",
                "dropoff_group_count",
                "analysis_source",
                "interpretation",
            }
            self.assertTrue(expected_dashboard_columns.issubset(drivers.columns))
            self.assertTrue(feature_output.exists())
            self.assertTrue(driver_output.exists())
