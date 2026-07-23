from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from src.ingestion.validate_data_quality import (
    QualityResult,
    main,
    run_quality_checks,
    write_quality_results,
)


def create_source_tables(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE learners (
            learner_id TEXT,
            signup_date TEXT,
            cohort TEXT,
            region TEXT
        );

        CREATE TABLE courses (
            course_id TEXT,
            course_name TEXT,
            category TEXT,
            expected_duration_days INTEGER
        );

        CREATE TABLE enrollments (
            learner_id TEXT,
            course_id TEXT,
            enrollment_date TEXT,
            progress_percent REAL,
            completion_status TEXT,
            completion_date TEXT
        );

        CREATE TABLE sessions (
            session_id TEXT,
            learner_id TEXT,
            course_id TEXT,
            session_start_time TEXT,
            session_duration_minutes REAL,
            module_id TEXT,
            content_type TEXT
        );

        CREATE TABLE quizzes (
            quiz_attempt_id TEXT,
            learner_id TEXT,
            course_id TEXT,
            quiz_id TEXT,
            attempt_time TEXT,
            score REAL,
            max_score REAL,
            attempt_number INTEGER
        );
        """
    )


def result_by_name(results: list[QualityResult]) -> dict[str, QualityResult]:
    return {result.check_name: result for result in results}


class TestDataQualityValidation(unittest.TestCase):
    def test_valid_data_passes_blocking_checks_and_records_results(self) -> None:
        with sqlite3.connect(":memory:") as connection:
            create_source_tables(connection)
            connection.executescript(
                """
                INSERT INTO learners VALUES ('L1', '2026-06-01', 'A', 'South');
                INSERT INTO courses VALUES ('C1', 'Python Basics', 'Tech', 30);
                INSERT INTO enrollments
                VALUES ('L1', 'C1', '2026-06-02', 0.75, 'active', NULL);
                INSERT INTO sessions
                VALUES ('S1', 'L1', 'C1', '2026-06-03', 20, 'M1', 'video');
                INSERT INTO quizzes VALUES ('Q1', 'L1', 'C1', 'quiz-1', '2026-06-04', 8, 10, 1);
                """
            )

            results = run_quality_checks(connection)
            write_quality_results(connection, results)

            blocking_failures = [
                result
                for result in results
                if result.severity == "blocking" and result.status == "failed"
            ]
            recorded_count = connection.execute(
                "SELECT COUNT(*) FROM data_quality_results"
            ).fetchone()[0]

            self.assertEqual(blocking_failures, [])
            self.assertEqual(recorded_count, len(results))

    def test_invalid_data_flags_missing_keys_dates_scores_and_durations(self) -> None:
        with sqlite3.connect(":memory:") as connection:
            create_source_tables(connection)
            connection.executescript(
                """
                INSERT INTO learners VALUES ('', 'not-a-date', NULL, NULL);
                INSERT INTO courses VALUES ('C1', 'Python Basics', NULL, 30);
                INSERT INTO enrollments
                VALUES ('L1', 'C1', '2026-06-02', 0.25, 'active', NULL);
                INSERT INTO enrollments
                VALUES ('L1', 'C1', '2026-06-03', 0.30, 'active', NULL);
                INSERT INTO sessions VALUES ('S1', 'L1', 'C1', 'bad-date', -5, 'M1', NULL);
                INSERT INTO quizzes VALUES ('Q1', 'L1', 'C1', 'quiz-1', '2026-06-04', 11, 10, 1);
                """
            )

            results = result_by_name(run_quality_checks(connection))

            self.assertEqual(results["missing_keys:learners"].status, "failed")
            self.assertEqual(
                results["duplicate_enrollment_keys"].failed_row_count,
                1,
            )
            self.assertEqual(
                results["invalid_dates:learners.signup_date"].status,
                "failed",
            )
            self.assertEqual(
                results["invalid_dates:sessions.session_start_time"].status,
                "failed",
            )
            self.assertEqual(results["quiz_score_bounds"].status, "failed")
            self.assertEqual(
                results["session_duration_non_negative"].status,
                "failed",
            )
            self.assertEqual(
                results["optional_dimension:learners.cohort"].status,
                "warning",
            )

    def test_required_column_check_fails_for_missing_schema_columns(self) -> None:
        with sqlite3.connect(":memory:") as connection:
            connection.executescript(
                """
                CREATE TABLE learners (
                    learner_id TEXT
                );

                CREATE TABLE courses (
                    course_id TEXT
                );
                """
            )

            results = result_by_name(run_quality_checks(connection))

            self.assertEqual(results["table_exists:enrollments"].status, "failed")
            self.assertEqual(results["required_columns:courses"].status, "failed")
            self.assertEqual(
                results["required_columns:courses"].failed_row_count,
                1,
            )

    def test_standalone_validation_releases_database_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            database_path = Path(tmpdir) / "quality-check.sqlite"
            with closing(sqlite3.connect(database_path)) as connection:
                create_source_tables(connection)
                connection.commit()

            with patch.object(
                sys,
                "argv",
                ["validate_data_quality.py", "--database", str(database_path)],
            ):
                self.assertEqual(main(), 0)

            database_path.unlink()
            self.assertFalse(database_path.exists())


if __name__ == "__main__":
    unittest.main()
