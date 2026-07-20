from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.ingestion.run_data_pipeline import run_pipeline


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = PROJECT_ROOT / "src" / "database" / "schema.sql"
AGGREGATE_QUERY_PATH = (
    PROJECT_ROOT / "src" / "database" / "queries" / "learner_course_aggregates.sql"
)


def write_csv(raw_dir: Path, filename: str, rows: list[dict[str, object]]) -> None:
    pd.DataFrame(rows).to_csv(raw_dir / filename, index=False)


def write_complete_raw_fixture(raw_dir: Path) -> None:
    write_csv(
        raw_dir,
        "learners.csv",
        [
            {
                "learner_id": "L1",
                "signup_date": "2026-06-01",
                "cohort": "A",
                "region": "South",
            }
        ],
    )
    write_csv(
        raw_dir,
        "courses.csv",
        [
            {
                "course_id": "C1",
                "course_name": "Python Basics",
                "category": "Programming",
                "expected_duration_days": 30,
            }
        ],
    )
    write_csv(
        raw_dir,
        "enrollments.csv",
        [
            {
                "learner_id": "L1",
                "course_id": "C1",
                "enrollment_date": "2026-06-02",
                "progress_percent": 0.75,
                "completion_status": "active",
                "completion_date": "",
            }
        ],
    )
    write_csv(
        raw_dir,
        "sessions.csv",
        [
            {
                "session_id": "S1",
                "learner_id": "L1",
                "course_id": "C1",
                "session_start_time": "2026-06-03",
                "session_duration_minutes": 20,
                "module_id": "M1",
                "content_type": "video",
            }
        ],
    )
    write_csv(
        raw_dir,
        "quizzes.csv",
        [
            {
                "quiz_attempt_id": "QA1",
                "learner_id": "L1",
                "course_id": "C1",
                "quiz_id": "Q1",
                "attempt_time": "2026-06-04",
                "score": 8,
                "max_score": 10,
                "attempt_number": 1,
            }
        ],
    )


class TestDataPipeline(unittest.TestCase):
    def test_complete_raw_data_runs_validation_and_aggregate_export(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            raw_dir = tmp_path / "raw"
            raw_dir.mkdir()
            database_path = tmp_path / "learner_dropoff.sqlite"
            aggregate_output_path = tmp_path / "learner_course_aggregates.csv"
            write_complete_raw_fixture(raw_dir)

            result = run_pipeline(
                raw_dir=raw_dir,
                database_path=database_path,
                schema_path=SCHEMA_PATH,
                aggregate_output_path=aggregate_output_path,
                aggregate_query_path=AGGREGATE_QUERY_PATH,
                strict_raw=True,
            )

            aggregate_frame = pd.read_csv(aggregate_output_path)

            self.assertEqual(result.return_code, 0)
            self.assertEqual(result.missing_files, [])
            self.assertEqual(result.aggregate_row_count, 1)
            self.assertEqual(aggregate_frame.iloc[0]["learner_id"], "L1")
            self.assertEqual(aggregate_frame.iloc[0]["total_sessions"], 1)
            self.assertEqual(aggregate_frame.iloc[0]["latest_quiz_score"], 80.0)

            with sqlite3.connect(database_path) as connection:
                recorded_results = connection.execute(
                    "SELECT COUNT(*) FROM data_quality_results"
                ).fetchone()[0]
            self.assertEqual(recorded_results, len(result.quality_results))

    def test_empty_raw_folder_is_allowed_in_non_strict_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            raw_dir = tmp_path / "raw"
            raw_dir.mkdir()
            database_path = tmp_path / "learner_dropoff.sqlite"
            aggregate_output_path = tmp_path / "learner_course_aggregates.csv"

            result = run_pipeline(
                raw_dir=raw_dir,
                database_path=database_path,
                schema_path=SCHEMA_PATH,
                aggregate_output_path=aggregate_output_path,
                aggregate_query_path=AGGREGATE_QUERY_PATH,
                strict_raw=False,
            )

            aggregate_frame = pd.read_csv(aggregate_output_path)

            self.assertEqual(result.return_code, 0)
            self.assertEqual(len(result.missing_files), 5)
            self.assertEqual(result.aggregate_row_count, 0)
            self.assertEqual(list(aggregate_frame.columns)[0], "learner_id")

    def test_strict_mode_blocks_aggregate_export_when_raw_files_are_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            raw_dir = tmp_path / "raw"
            raw_dir.mkdir()
            database_path = tmp_path / "learner_dropoff.sqlite"
            aggregate_output_path = tmp_path / "learner_course_aggregates.csv"

            result = run_pipeline(
                raw_dir=raw_dir,
                database_path=database_path,
                schema_path=SCHEMA_PATH,
                aggregate_output_path=aggregate_output_path,
                aggregate_query_path=AGGREGATE_QUERY_PATH,
                strict_raw=True,
            )

            self.assertEqual(result.return_code, 1)
            self.assertEqual(result.aggregate_row_count, 0)
            self.assertFalse(aggregate_output_path.exists())

            with sqlite3.connect(database_path) as connection:
                raw_file_result = connection.execute(
                    """
                    SELECT status, failed_row_count
                    FROM data_quality_results
                    WHERE check_name = 'raw_files_complete'
                    """
                ).fetchone()

            self.assertEqual(raw_file_result, ("failed", 5))


if __name__ == "__main__":
    unittest.main()
