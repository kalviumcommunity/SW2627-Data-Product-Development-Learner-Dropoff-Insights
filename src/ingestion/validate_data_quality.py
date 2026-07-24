"""Validate the SQLite learner data layer and record quality results.

Owner: Monesh
"""

from __future__ import annotations

import argparse
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "processed" / "learner_dropoff.sqlite"

REQUIRED_COLUMNS: dict[str, tuple[str, ...]] = {
    "learners": ("learner_id",),
    "courses": ("course_id", "course_name"),
    "enrollments": ("learner_id", "course_id", "enrollment_date"),
    "sessions": ("learner_id", "course_id", "session_start_time"),
    "quizzes": ("learner_id", "course_id", "quiz_id", "attempt_time", "score"),
}

KEY_COLUMNS: dict[str, tuple[str, ...]] = {
    "learners": ("learner_id",),
    "courses": ("course_id",),
    "enrollments": ("learner_id", "course_id"),
    "sessions": ("learner_id", "course_id"),
    "quizzes": ("learner_id", "course_id", "quiz_id"),
}

DATE_COLUMNS: dict[str, tuple[str, ...]] = {
    "learners": ("signup_date",),
    "enrollments": ("enrollment_date", "completion_date"),
    "sessions": ("session_start_time",),
    "quizzes": ("attempt_time",),
}

OPTIONAL_DIMENSIONS: dict[str, tuple[str, ...]] = {
    "learners": ("cohort", "region"),
    "courses": ("category",),
    "sessions": ("content_type",),
}

EXPECTED_TABLES = tuple(REQUIRED_COLUMNS)
ALLOWED_SEVERITIES = {"blocking", "warning"}
ALLOWED_STATUSES = {"passed", "failed", "warning"}


@dataclass(frozen=True)
class QualityResult:
    check_name: str
    severity: str
    status: str
    failed_row_count: int
    message: str

    def __post_init__(self) -> None:
        if self.severity not in ALLOWED_SEVERITIES:
            raise ValueError(f"Unsupported severity: {self.severity}")
        if self.status not in ALLOWED_STATUSES:
            raise ValueError(f"Unsupported status: {self.status}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate learner drop-off SQLite data quality checks."
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE_PATH,
        help="SQLite database created by src/ingestion/load_raw_data.py.",
    )
    return parser.parse_args()


def blank_condition(column_name: str) -> str:
    return f"({column_name} IS NULL OR TRIM(CAST({column_name} AS TEXT)) = '')"


def table_names(connection: sqlite3.Connection) -> set[str]:
    rows = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
    ).fetchall()
    return {row[0] for row in rows}


def column_names(connection: sqlite3.Connection, table_name: str) -> set[str]:
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {row[1] for row in rows}


def count_rows(connection: sqlite3.Connection, query: str) -> int:
    return int(connection.execute(query).fetchone()[0])


def ensure_results_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS data_quality_results (
            check_id INTEGER PRIMARY KEY AUTOINCREMENT,
            check_name TEXT NOT NULL,
            severity TEXT NOT NULL CHECK (severity IN ('blocking', 'warning')),
            status TEXT NOT NULL CHECK (status IN ('passed', 'failed', 'warning')),
            failed_row_count INTEGER NOT NULL DEFAULT 0,
            message TEXT,
            checked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def check_table_presence(existing_tables: set[str]) -> list[QualityResult]:
    results: list[QualityResult] = []
    for table_name in EXPECTED_TABLES:
        exists = table_name in existing_tables
        results.append(
            QualityResult(
                check_name=f"table_exists:{table_name}",
                severity="blocking",
                status="passed" if exists else "failed",
                failed_row_count=0 if exists else 1,
                message=(
                    f"{table_name} table exists."
                    if exists
                    else f"{table_name} table is missing."
                ),
            )
        )
    return results


def check_required_columns(
    connection: sqlite3.Connection,
    existing_tables: set[str],
) -> list[QualityResult]:
    results: list[QualityResult] = []
    for table_name, required_columns in REQUIRED_COLUMNS.items():
        if table_name not in existing_tables:
            continue

        existing_columns = column_names(connection, table_name)
        missing_columns = [
            column for column in required_columns if column not in existing_columns
        ]
        results.append(
            QualityResult(
                check_name=f"required_columns:{table_name}",
                severity="blocking",
                status="failed" if missing_columns else "passed",
                failed_row_count=len(missing_columns),
                message=(
                    f"Missing required columns: {', '.join(missing_columns)}."
                    if missing_columns
                    else "All required columns are present."
                ),
            )
        )
    return results


def check_missing_keys(
    connection: sqlite3.Connection,
    existing_tables: set[str],
) -> list[QualityResult]:
    results: list[QualityResult] = []
    for table_name, key_columns in KEY_COLUMNS.items():
        if table_name not in existing_tables:
            continue

        existing_columns = column_names(connection, table_name)
        usable_key_columns = [
            column for column in key_columns if column in existing_columns
        ]
        if not usable_key_columns:
            continue

        condition = " OR ".join(blank_condition(column) for column in usable_key_columns)
        failed_count = count_rows(
            connection,
            f"SELECT COUNT(*) FROM {table_name} WHERE {condition}",
        )
        results.append(
            QualityResult(
                check_name=f"missing_keys:{table_name}",
                severity="blocking",
                status="failed" if failed_count else "passed",
                failed_row_count=failed_count,
                message=(
                    f"{failed_count} row(s) have missing key values."
                    if failed_count
                    else "No missing key values found."
                ),
            )
        )
    return results


def check_duplicate_enrollments(
    connection: sqlite3.Connection,
    existing_tables: set[str],
) -> QualityResult | None:
    if "enrollments" not in existing_tables:
        return None

    existing_columns = column_names(connection, "enrollments")
    if {"learner_id", "course_id"}.difference(existing_columns):
        return None

    duplicate_count = count_rows(
        connection,
        """
        SELECT COUNT(*)
        FROM (
            SELECT learner_id, course_id
            FROM enrollments
            GROUP BY learner_id, course_id
            HAVING COUNT(*) > 1
        )
        """,
    )
    return QualityResult(
        check_name="duplicate_enrollment_keys",
        severity="blocking",
        status="failed" if duplicate_count else "passed",
        failed_row_count=duplicate_count,
        message=(
            f"{duplicate_count} duplicate learner-course enrollment key(s) found."
            if duplicate_count
            else "No duplicate learner-course enrollment keys found."
        ),
    )


def check_invalid_dates(
    connection: sqlite3.Connection,
    existing_tables: set[str],
) -> list[QualityResult]:
    results: list[QualityResult] = []
    for table_name, date_columns in DATE_COLUMNS.items():
        if table_name not in existing_tables:
            continue

        existing_columns = column_names(connection, table_name)
        for column in date_columns:
            if column not in existing_columns:
                continue

            invalid_count = count_rows(
                connection,
                f"""
                SELECT COUNT(*)
                FROM {table_name}
                WHERE NOT {blank_condition(column)}
                    AND DATE({column}) IS NULL
                """,
            )
            results.append(
                QualityResult(
                    check_name=f"invalid_dates:{table_name}.{column}",
                    severity="blocking",
                    status="failed" if invalid_count else "passed",
                    failed_row_count=invalid_count,
                    message=(
                        f"{invalid_count} invalid date value(s) found in {column}."
                        if invalid_count
                        else f"All populated {column} values parse as dates."
                    ),
                )
            )
    return results


def check_quiz_score_bounds(
    connection: sqlite3.Connection,
    existing_tables: set[str],
) -> QualityResult | None:
    if "quizzes" not in existing_tables:
        return None

    existing_columns = column_names(connection, "quizzes")
    if "score" not in existing_columns:
        return None

    score_too_high_condition = "0"
    if "max_score" in existing_columns:
        score_too_high_condition = """
            (
                max_score IS NOT NULL
                AND TRIM(CAST(max_score AS TEXT)) != ''
                AND CAST(score AS REAL) > CAST(max_score AS REAL)
            )
        """

    invalid_count = count_rows(
        connection,
        f"""
        SELECT COUNT(*)
        FROM quizzes
        WHERE NOT {blank_condition('score')}
            AND (
                CAST(score AS REAL) < 0
                OR {score_too_high_condition}
            )
        """,
    )
    return QualityResult(
        check_name="quiz_score_bounds",
        severity="blocking",
        status="failed" if invalid_count else "passed",
        failed_row_count=invalid_count,
        message=(
            f"{invalid_count} quiz score value(s) are outside valid bounds."
            if invalid_count
            else "Quiz score values are within expected bounds."
        ),
    )


def check_session_duration(
    connection: sqlite3.Connection,
    existing_tables: set[str],
) -> QualityResult | None:
    if "sessions" not in existing_tables:
        return None

    existing_columns = column_names(connection, "sessions")
    if "session_duration_minutes" not in existing_columns:
        return None

    invalid_count = count_rows(
        connection,
        """
        SELECT COUNT(*)
        FROM sessions
        WHERE NOT (
            session_duration_minutes IS NULL
            OR TRIM(CAST(session_duration_minutes AS TEXT)) = ''
        )
            AND CAST(session_duration_minutes AS REAL) < 0
        """,
    )
    return QualityResult(
        check_name="session_duration_non_negative",
        severity="blocking",
        status="failed" if invalid_count else "passed",
        failed_row_count=invalid_count,
        message=(
            f"{invalid_count} session duration value(s) are negative."
            if invalid_count
            else "Session duration values are non-negative when populated."
        ),
    )


def check_optional_dimensions(
    connection: sqlite3.Connection,
    existing_tables: set[str],
) -> list[QualityResult]:
    results: list[QualityResult] = []
    for table_name, optional_columns in OPTIONAL_DIMENSIONS.items():
        if table_name not in existing_tables:
            continue

        existing_columns = column_names(connection, table_name)
        for column in optional_columns:
            if column not in existing_columns:
                continue

            total_count = count_rows(connection, f"SELECT COUNT(*) FROM {table_name}")
            missing_count = count_rows(
                connection,
                f"SELECT COUNT(*) FROM {table_name} WHERE {blank_condition(column)}",
            )
            status = "warning" if total_count and missing_count == total_count else "passed"
            results.append(
                QualityResult(
                    check_name=f"optional_dimension:{table_name}.{column}",
                    severity="warning",
                    status=status,
                    failed_row_count=missing_count if status == "warning" else 0,
                    message=(
                        f"{column} is missing for all {total_count} row(s)."
                        if status == "warning"
                        else f"{column} has at least some populated values or no rows."
                    ),
                )
            )
    return results


def run_quality_checks(connection: sqlite3.Connection) -> list[QualityResult]:
    existing_tables = table_names(connection)
    results: list[QualityResult] = []

    results.extend(check_table_presence(existing_tables))
    results.extend(check_required_columns(connection, existing_tables))
    results.extend(check_missing_keys(connection, existing_tables))

    duplicate_result = check_duplicate_enrollments(connection, existing_tables)
    if duplicate_result:
        results.append(duplicate_result)

    results.extend(check_invalid_dates(connection, existing_tables))

    quiz_score_result = check_quiz_score_bounds(connection, existing_tables)
    if quiz_score_result:
        results.append(quiz_score_result)

    session_duration_result = check_session_duration(connection, existing_tables)
    if session_duration_result:
        results.append(session_duration_result)

    results.extend(check_optional_dimensions(connection, existing_tables))

    return results


def write_quality_results(
    connection: sqlite3.Connection,
    results: list[QualityResult],
) -> None:
    ensure_results_table(connection)
    connection.execute("DELETE FROM data_quality_results")
    connection.executemany(
        """
        INSERT INTO data_quality_results (
            check_name,
            severity,
            status,
            failed_row_count,
            message
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (
                result.check_name,
                result.severity,
                result.status,
                result.failed_row_count,
                result.message,
            )
            for result in results
        ],
    )
    connection.commit()


def print_summary(results: list[QualityResult]) -> None:
    blocking_failures = [
        result
        for result in results
        if result.severity == "blocking" and result.status == "failed"
    ]
    warnings = [result for result in results if result.status == "warning"]

    print(f"Recorded {len(results)} data quality check result(s).")
    print(f"Blocking failures: {len(blocking_failures)}")
    print(f"Warnings: {len(warnings)}")

    for result in blocking_failures:
        print(f"- {result.check_name}: {result.message}")


def main() -> int:
    args = parse_args()

    if not args.database.exists():
        raise FileNotFoundError(
            f"SQLite database not found: {args.database}. "
            "Run src/ingestion/load_raw_data.py first."
        )

    with closing(sqlite3.connect(args.database)) as connection, connection:
        results = run_quality_checks(connection)
        write_quality_results(connection, results)

    print_summary(results)
    has_blocking_failure = any(
        result.severity == "blocking" and result.status == "failed"
        for result in results
    )
    return 1 if has_blocking_failure else 0


if __name__ == "__main__":
    raise SystemExit(main())
