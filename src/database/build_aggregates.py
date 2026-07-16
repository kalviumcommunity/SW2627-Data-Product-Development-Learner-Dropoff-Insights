"""Build learner-course aggregates from the SQLite data layer.

Owner: Monesh

Input:
    data/processed/learner_dropoff.sqlite

Output:
    data/processed/learner_course_aggregates.csv
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "processed" / "learner_dropoff.sqlite"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "learner_course_aggregates.csv"
DEFAULT_QUERY_PATH = (
    PROJECT_ROOT / "src" / "database" / "queries" / "learner_course_aggregates.sql"
)

REQUIRED_TABLES = (
    "learners",
    "courses",
    "enrollments",
    "sessions",
    "quizzes",
    "learner_course_aggregates",
)

EXPORT_QUERY = """
SELECT
    a.learner_id,
    a.course_id,
    l.cohort,
    l.region,
    c.course_name,
    c.category,
    a.enrollment_date,
    a.completion_status,
    a.completion_date,
    a.progress_percent,
    a.total_sessions,
    a.active_days,
    a.average_session_duration,
    a.latest_activity_date,
    a.quiz_attempt_count,
    a.average_quiz_score,
    a.latest_quiz_score
FROM learner_course_aggregates a
LEFT JOIN learners l
    ON a.learner_id = l.learner_id
LEFT JOIN courses c
    ON a.course_id = c.course_id
ORDER BY a.learner_id, a.course_id
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build learner-course aggregate CSV from the SQLite database."
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE_PATH,
        help="SQLite database created by src/ingestion/load_raw_data.py.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="CSV path for Shaswath's feature engineering input.",
    )
    parser.add_argument(
        "--query",
        type=Path,
        default=DEFAULT_QUERY_PATH,
        help="SQL file used to refresh learner_course_aggregates.",
    )
    return parser.parse_args()


def validate_database(connection: sqlite3.Connection, database_path: Path) -> None:
    existing_tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    missing_tables = sorted(set(REQUIRED_TABLES) - existing_tables)
    if missing_tables:
        missing_list = ", ".join(missing_tables)
        raise RuntimeError(
            f"{database_path} is missing required table(s): {missing_list}. "
            "Run src/ingestion/load_raw_data.py before building aggregates."
        )


def refresh_aggregate_table(
    connection: sqlite3.Connection,
    query_path: Path,
) -> None:
    if not query_path.exists():
        raise FileNotFoundError(f"Aggregate SQL file not found: {query_path}")

    aggregate_sql = query_path.read_text(encoding="utf-8")
    connection.executescript(aggregate_sql)
    connection.commit()


def export_aggregate_csv(
    connection: sqlite3.Connection,
    output_path: Path,
) -> pd.DataFrame:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.read_sql_query(EXPORT_QUERY, connection)
    frame.to_csv(output_path, index=False)
    return frame


def table_row_count(connection: sqlite3.Connection, table_name: str) -> int:
    return connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]


def main() -> int:
    args = parse_args()

    if not args.database.exists():
        raise FileNotFoundError(
            f"SQLite database not found: {args.database}. "
            "Run src/ingestion/load_raw_data.py first."
        )

    with sqlite3.connect(args.database) as connection:
        validate_database(connection, args.database)

        enrollment_count = table_row_count(connection, "enrollments")
        if enrollment_count == 0:
            print(
                "Warning: enrollments table is empty; "
                "output CSV will contain headers only."
            )

        refresh_aggregate_table(connection, args.query)
        output_frame = export_aggregate_csv(connection, args.output)

    print(f"Wrote {len(output_frame)} learner-course aggregate rows to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
