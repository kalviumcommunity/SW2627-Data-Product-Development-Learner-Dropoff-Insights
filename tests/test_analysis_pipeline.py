from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.analysis.run_analysis_pipeline import run_analysis_pipeline


class TestAnalysisPipeline(unittest.TestCase):
    def test_pipeline_writes_observed_features_and_rankings(self) -> None:
        aggregates = pd.DataFrame(
            [
                {
                    "learner_id": "C1",
                    "course_id": "COURSE",
                    "completion_status": "completed",
                    "progress_percent": 1.0,
                    "total_sessions": 12,
                    "active_days": 8,
                    "average_session_duration": 20,
                    "latest_activity_date": "2026-07-20",
                    "quiz_attempt_count": 4,
                    "average_quiz_score": 90,
                    "latest_quiz_score": 92,
                },
                {
                    "learner_id": "C2",
                    "course_id": "COURSE",
                    "completion_status": "completed",
                    "progress_percent": 1.0,
                    "total_sessions": 10,
                    "active_days": 7,
                    "average_session_duration": 18,
                    "latest_activity_date": "2026-07-18",
                    "quiz_attempt_count": 3,
                    "average_quiz_score": 85,
                    "latest_quiz_score": 88,
                },
                {
                    "learner_id": "D1",
                    "course_id": "COURSE",
                    "completion_status": "active",
                    "progress_percent": 0.25,
                    "total_sessions": 3,
                    "active_days": 2,
                    "average_session_duration": 8,
                    "latest_activity_date": "2026-06-01",
                    "quiz_attempt_count": 1,
                    "average_quiz_score": 42,
                    "latest_quiz_score": 40,
                },
                {
                    "learner_id": "D2",
                    "course_id": "COURSE",
                    "completion_status": "active",
                    "progress_percent": 0.30,
                    "total_sessions": 4,
                    "active_days": 2,
                    "average_session_duration": 9,
                    "latest_activity_date": "2026-06-03",
                    "quiz_attempt_count": 1,
                    "average_quiz_score": 48,
                    "latest_quiz_score": 45,
                },
            ]
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            aggregate_input = tmp_path / "aggregates.csv"
            feature_output = tmp_path / "features.csv"
            driver_output = tmp_path / "drivers.csv"
            aggregates.to_csv(aggregate_input, index=False)

            result = run_analysis_pipeline(
                aggregate_input=aggregate_input,
                feature_output=feature_output,
                driver_output=driver_output,
                require_observed=True,
            )

            features = pd.read_csv(feature_output)
            drivers = pd.read_csv(driver_output)
            self.assertEqual(result.return_code, 0)
            self.assertEqual(result.analysis_source, "observed_data")
            self.assertEqual(
                set(features["learner_status"]),
                {"completed", "silent_dropoff"},
            )
            self.assertTrue((drivers["completed_group_count"] == 2).all())
            self.assertTrue((drivers["dropoff_group_count"] == 2).all())

    def test_strict_mode_rejects_fallback_rankings(self) -> None:
        aggregates = pd.DataFrame(
            [
                {
                    "learner_id": "C1",
                    "course_id": "COURSE",
                    "completion_status": "completed",
                    "progress_percent": 1.0,
                    "total_sessions": 5,
                    "active_days": 3,
                }
            ]
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            aggregate_input = tmp_path / "aggregates.csv"
            aggregates.to_csv(aggregate_input, index=False)

            result = run_analysis_pipeline(
                aggregate_input=aggregate_input,
                feature_output=tmp_path / "features.csv",
                driver_output=tmp_path / "drivers.csv",
                require_observed=True,
            )

            self.assertEqual(result.return_code, 1)
            self.assertEqual(result.analysis_source, "fallback_example")
