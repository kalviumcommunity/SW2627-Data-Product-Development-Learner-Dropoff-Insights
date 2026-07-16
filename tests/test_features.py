from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.features.build_features import build_features


class TestLearnerFeatures(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture_path = (
            Path(__file__).resolve().parent / "fixtures" / "sample_learner_course_aggregates.csv"
        )
        # Ensure fixture file exists
        if not self.fixture_path.exists():
            raise FileNotFoundError(
                f"Missing test fixture: {self.fixture_path}. Run fixture creation step first."
            )

    def test_output_schema_and_mvp_columns(self) -> None:
        """Confirm the output file contains the 12 MVP dashboard columns in correct order."""
        features_df = build_features(self.fixture_path, inactivity_threshold_days=21)

        expected_mvp_columns = [
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
            "suggested_action",
        ]

        # Check that all expected columns are present at the beginning of the DataFrame
        for idx, col in enumerate(expected_mvp_columns):
            self.assertEqual(
                features_df.columns[idx],
                col,
                f"Column at index {idx} should be '{col}', got '{features_df.columns[idx]}'",
            )

        # Check total columns (12 MVP + others from the input, e.g. enrollment_date, completion_status, etc.)
        self.assertGreaterEqual(len(features_df.columns), 12)

    def test_learner_state_completed(self) -> None:
        """Verify behavior for completed learners (by status, date, or progress)."""
        features_df = build_features(self.fixture_path, inactivity_threshold_days=21)

        completed_learners = ["L_COMPLETED_STATUS", "L_COMPLETED_DATE", "L_COMPLETED_PROGRESS"]
        for learner_id in completed_learners:
            row = features_df[features_df["learner_id"] == learner_id].iloc[0]
            self.assertEqual(
                row["learner_status"],
                "completed",
                f"Learner {learner_id} should be labeled 'completed'",
            )
            self.assertEqual(
                row["risk_score"], 0, f"Learner {learner_id} should have a risk score of 0"
            )
            self.assertEqual(row["risk_bucket"], "low")
            self.assertEqual(row["suggested_action"], "No action needed")

    def test_learner_state_unstarted(self) -> None:
        """Verify behavior for unstarted learners (enrollment but no activity)."""
        features_df = build_features(self.fixture_path, inactivity_threshold_days=21)

        row = features_df[features_df["learner_id"] == "L_UNSTARTED"].iloc[0]
        self.assertEqual(row["learner_status"], "unstarted")
        self.assertEqual(row["risk_score"], 60)
        self.assertEqual(row["risk_bucket"], "medium")
        self.assertEqual(
            row["primary_risk_reason"], "No meaningful activity after enrollment"
        )
        self.assertEqual(row["suggested_action"], "Send onboarding reminder")

    def test_learner_state_silent_dropoff(self) -> None:
        """Verify behavior for silent drop-off learners (inactive >= inactivity_threshold_days)."""
        features_df = build_features(self.fixture_path, inactivity_threshold_days=21)

        row = features_df[features_df["learner_id"] == "L_SILENT_DROPOFF"].iloc[0]
        self.assertEqual(row["learner_status"], "silent_dropoff")
        self.assertEqual(row["risk_score"], 70)  # inactivity gap (50) + stalled progress (20)
        self.assertEqual(row["risk_bucket"], "high")
        self.assertEqual(row["primary_risk_reason"], "Inactive beyond threshold")
        self.assertEqual(row["suggested_action"], "Send check-in reminder")

    def test_learner_state_at_risk_quiz(self) -> None:
        """Verify behavior for at-risk learners due to low latest quiz score."""
        features_df = build_features(self.fixture_path, inactivity_threshold_days=21)

        row = features_df[features_df["learner_id"] == "L_AT_RISK_QUIZ"].iloc[0]
        self.assertEqual(row["learner_status"], "at_risk")
        self.assertEqual(row["risk_score"], 25)
        self.assertEqual(row["risk_bucket"], "low")
        self.assertEqual(row["primary_risk_reason"], "Latest quiz score is low")
        self.assertEqual(row["suggested_action"], "Offer quiz support")

    def test_learner_state_at_risk_gap(self) -> None:
        """Verify behavior for at-risk learners due to growing inactivity gap (days >= 10)."""
        features_df = build_features(self.fixture_path, inactivity_threshold_days=21)

        row = features_df[features_df["learner_id"] == "L_AT_RISK_GAP"].iloc[0]
        self.assertEqual(row["learner_status"], "at_risk")
        self.assertEqual(row["risk_score"], 25)
        self.assertEqual(row["risk_bucket"], "low")
        self.assertEqual(row["primary_risk_reason"], "Activity gap is growing")
        self.assertEqual(row["suggested_action"], "Send check-in reminder")

    def test_learner_state_at_risk_stalled(self) -> None:
        """Verify behavior for at-risk learners due to stalled progress & activity gap."""
        features_df = build_features(self.fixture_path, inactivity_threshold_days=21)

        row = features_df[features_df["learner_id"] == "L_AT_RISK_STALLED"].iloc[0]
        self.assertEqual(row["learner_status"], "at_risk")
        self.assertEqual(row["risk_score"], 45)  # gap (25) + stalled (20)
        self.assertEqual(row["risk_bucket"], "medium")
        self.assertEqual(row["primary_risk_reason"], "Activity gap is growing")
        self.assertEqual(row["suggested_action"], "Send check-in reminder")

    def test_learner_state_active(self) -> None:
        """Verify behavior for normal active learners."""
        features_df = build_features(self.fixture_path, inactivity_threshold_days=21)

        row = features_df[features_df["learner_id"] == "L_ACTIVE"].iloc[0]
        self.assertEqual(row["learner_status"], "active")
        self.assertEqual(row["risk_score"], 0)
        self.assertEqual(row["risk_bucket"], "low")
        self.assertEqual(row["primary_risk_reason"], "Healthy activity")
        self.assertEqual(row["suggested_action"], "No action needed")

    def test_missing_and_fallback_columns(self) -> None:
        """Verify safe fallback initialization for missing optional columns."""
        # Create a tiny DataFrame missing everything except identifiers
        missing_df = pd.DataFrame([{"learner_id": "L_MISSING", "course_id": "C_MISSING"}])

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir) / "missing_data.csv"
            missing_df.to_csv(temp_path, index=False)

            features_df = build_features(temp_path, inactivity_threshold_days=21)

            # Check that expected columns are populated with defaults and we didn't crash
            row = features_df.iloc[0]
            self.assertEqual(row["total_sessions"], 0)
            self.assertEqual(row["active_days"], 0)
            self.assertEqual(row["progress_percent"], 0.0)
            self.assertEqual(row["learner_status"], "unstarted")
            self.assertEqual(row["risk_score"], 60)
            self.assertEqual(row["risk_bucket"], "medium")


if __name__ == "__main__":
    unittest.main()
