from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.analysis.behaviour_drivers import analyze_drivers, main


class TestBehaviourDrivers(unittest.TestCase):
    def test_schema_of_output_and_correlation(self) -> None:
        """Verify the output schema and calculated correlation direction with sufficient data."""
        # Create a mock features DataFrame with 2 completed and 2 silent_dropoff rows
        mock_features = pd.DataFrame([
            {
                "learner_id": "L1",
                "course_id": "C1",
                "learner_status": "completed",
                "active_days": 10,
                "days_since_last_activity": 2,
                "latest_quiz_score": 85.0,
            },
            {
                "learner_id": "L2",
                "course_id": "C1",
                "learner_status": "completed",
                "active_days": 12,
                "days_since_last_activity": 1,
                "latest_quiz_score": 90.0,
            },
            {
                "learner_id": "L3",
                "course_id": "C1",
                "learner_status": "silent_dropoff",
                "active_days": 2,
                "days_since_last_activity": 25,
                "latest_quiz_score": 45.0,
            },
            {
                "learner_id": "L4",
                "course_id": "C1",
                "learner_status": "silent_dropoff",
                "active_days": 3,
                "days_since_last_activity": 30,
                "latest_quiz_score": 50.0,
            },
        ])

        drivers_df = analyze_drivers(mock_features)

        # Confirm we got results
        self.assertFalse(drivers_df.empty)

        # Check required columns
        expected_columns = [
            "feature_name",
            "driver_direction",
            "strength_score",
            "completed_group_value",
            "dropoff_group_value",
            "completed_group_count",
            "dropoff_group_count",
            "analysis_source",
            "interpretation",
        ]
        for col in expected_columns:
            self.assertIn(col, drivers_df.columns)

        # Check sorting by strength_score descending
        strength_scores = drivers_df["strength_score"].tolist()
        self.assertEqual(strength_scores, sorted(strength_scores, reverse=True))

        # Check direction of active_days (should be completion since completed has higher value)
        active_days_row = drivers_df[drivers_df["feature_name"] == "active_days"].iloc[0]
        self.assertEqual(active_days_row["driver_direction"], "completion")
        self.assertGreater(active_days_row["strength_score"], 0.8)  # Should correlate strongly
        self.assertEqual(active_days_row["completed_group_value"], 11.0)
        self.assertEqual(active_days_row["dropoff_group_value"], 2.5)
        self.assertEqual(active_days_row["completed_group_count"], 2)
        self.assertEqual(active_days_row["dropoff_group_count"], 2)
        self.assertEqual(active_days_row["analysis_source"], "observed_data")

        # Check direction of days_since_last_activity (should be dropoff since silent_dropoff has higher value)
        inactivity_row = drivers_df[
            drivers_df["feature_name"] == "days_since_last_activity"
        ].iloc[0]
        self.assertEqual(inactivity_row["driver_direction"], "dropoff")
        self.assertGreater(inactivity_row["strength_score"], 0.8)
        self.assertEqual(inactivity_row["completed_group_value"], 1.5)
        self.assertEqual(inactivity_row["dropoff_group_value"], 27.5)

    def test_fallback_generation_insufficient_data(self) -> None:
        """Verify fallback rankings generation when there is only one status class."""
        mock_features = pd.DataFrame([
            {
                "learner_id": "L1",
                "course_id": "C1",
                "learner_status": "completed",
                "active_days": 10,
                "days_since_last_activity": 2,
                "latest_quiz_score": 85.0,
            }
        ])

        # Returns empty dataframe since correlation cannot be done
        drivers_df = analyze_drivers(mock_features)
        self.assertTrue(drivers_df.empty)

        # Running the main execution path with insufficient data generates fallback rankings
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_input = Path(tmpdir) / "learner_features.csv"
            temp_output = Path(tmpdir) / "behaviour_driver_rankings.csv"

            mock_features.to_csv(temp_input, index=False)

            # Invoke main via sys.argv mock
            import sys
            orig_argv = sys.argv
            try:
                sys.argv = [
                    "behaviour_drivers.py",
                    "--input",
                    str(temp_input),
                    "--output",
                    str(temp_output),
                ]
                main()
            finally:
                sys.argv = orig_argv

            # Verify that fallback CSV exists and is populated
            self.assertTrue(temp_output.exists())
            fallback_df = pd.read_csv(temp_output)
            self.assertEqual(len(fallback_df), 7)
            self.assertEqual(fallback_df.iloc[0]["feature_name"], "days_since_last_activity")
            self.assertEqual(fallback_df.iloc[0]["driver_direction"], "dropoff")
            self.assertEqual(fallback_df.iloc[0]["analysis_source"], "fallback_example")
            self.assertEqual(fallback_df.iloc[0]["completed_group_count"], 0)

    def test_feature_requires_two_valid_rows_per_outcome_group(self) -> None:
        features = pd.DataFrame(
            [
                {"learner_status": "completed", "active_days": 10},
                {"learner_status": "completed", "active_days": None},
                {"learner_status": "silent_dropoff", "active_days": 2},
                {"learner_status": "silent_dropoff", "active_days": 3},
            ]
        )

        self.assertTrue(analyze_drivers(features).empty)


if __name__ == "__main__":
    unittest.main()
