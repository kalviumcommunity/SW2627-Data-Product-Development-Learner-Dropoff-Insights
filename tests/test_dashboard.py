from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd

from src.dashboard.app import (
    RISK_BUCKET_ORDER,
    STATUS_ORDER,
    build_interim_feature_comparison,
    metric_value,
    ordered_value_counts,
    risk_table,
    sorted_options,
)
from src.features.build_features import build_features


class TestDashboardHelpers(unittest.TestCase):
    def setUp(self) -> None:
        fixture_path = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "sample_learner_course_aggregates.csv"
        )
        self.features = build_features(fixture_path, inactivity_threshold_days=21)

    def test_overview_metrics_from_feature_output(self) -> None:
        self.assertEqual(metric_value(self.features, "total_learners"), "9")
        self.assertEqual(metric_value(self.features, "completion_rate"), "33.3%")
        self.assertEqual(metric_value(self.features, "dropoff_rate"), "11.1%")
        self.assertEqual(metric_value(self.features, "high_risk"), "1")
        self.assertEqual(metric_value(self.features, "median_inactivity"), "12 days")

    def test_risk_table_defaults_to_highest_priority(self) -> None:
        table = risk_table(self.features)

        self.assertEqual(table.iloc[0]["learner_id"], "L_SILENT_DROPOFF")
        self.assertEqual(table.iloc[0]["risk_bucket"], "high")
        self.assertEqual(table.iloc[0]["risk_score"], 70)
        self.assertIn("suggested_action", table.columns)

    def test_filter_options_keep_dashboard_ordering(self) -> None:
        status_options = sorted_options(
            self.features,
            "learner_status",
            STATUS_ORDER,
        )
        risk_options = sorted_options(
            self.features,
            "risk_bucket",
            RISK_BUCKET_ORDER,
        )

        self.assertEqual(
            status_options,
            ["completed", "active", "at_risk", "silent_dropoff", "unstarted"],
        )
        self.assertEqual(risk_options, ["high", "medium", "low"])

    def test_ordered_value_counts_use_preferred_order(self) -> None:
        counts = ordered_value_counts(self.features, "learner_status", STATUS_ORDER)

        self.assertEqual(list(counts.index), STATUS_ORDER)
        self.assertEqual(counts.loc["completed"], 3)
        self.assertEqual(counts.loc["silent_dropoff"], 1)

    def test_interim_feature_comparison_uses_completed_and_dropoff_rows(self) -> None:
        comparison = build_interim_feature_comparison(self.features)

        self.assertFalse(comparison.empty)
        self.assertIn("completed", comparison.columns)
        self.assertIn("silent_dropoff", comparison.columns)
        self.assertIn("absolute_gap", comparison.columns)

    def test_empty_or_missing_inputs_do_not_crash_helpers(self) -> None:
        empty_frame = pd.DataFrame()
        missing_columns = pd.DataFrame(
            [{"learner_id": "L1", "course_id": "C1", "risk_score": 10}]
        )

        self.assertEqual(metric_value(empty_frame, "completion_rate"), "Pending")
        self.assertEqual(sorted_options(empty_frame, "risk_bucket"), [])
        self.assertEqual(build_interim_feature_comparison(empty_frame).shape[0], 0)
        self.assertEqual(
            list(risk_table(missing_columns).columns),
            ["learner_id", "course_id", "risk_score"],
        )


if __name__ == "__main__":
    unittest.main()
