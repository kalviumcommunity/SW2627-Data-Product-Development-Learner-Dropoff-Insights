"""Create the SQLite data layer and load available raw learner CSV files."""

from __future__ import annotations

import argparse
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class RawFileContract:
    filename: str
    table: str
    columns: tuple[str, ...]
    required_columns: tuple[str, ...]


RAW_FILE_CONTRACTS: tuple[RawFileContract, ...] = (
    RawFileContract(
        filename="learners.csv",
        table="learners",
        columns=("learner_id", "signup_date", "cohort", "region"),
        required_columns=("learner_id",),
    ),
    RawFileContract(
        filename="courses.csv",
        table="courses",
        columns=("course_id", "course_name", "category", "expected_duration_days"),
        required_columns=("course_id", "course_name"),
    ),
    RawFileContract(
        filename="enrollments.csv",
        table="enrollments",
        columns=(
            "learner_id",
            "course_id",
            "enrollment_date",
            "progress_percent",
            "completion_status",
            "completion_date",
        ),
        required_columns=("learner_id", "course_id", "enrollment_date"),
    ),
    RawFileContract(
        filename="sessions.csv",
        table="sessions",
        columns=(
            "session_id",
            "learner_id",
            "course_id",
            "session_start_time",
            "session_duration_minutes",
            "module_id",
            "content_type",
        ),
        required_columns=("learner_id", "course_id", "session_start_time"),
    ),
    RawFileContract(
        filename="quizzes.csv",
        table="quizzes",
        columns=(
            "quiz_attempt_id",
            "learner_id",
            "course_id",
            "quiz_id",
            "attempt_time",
            "score",
            "max_score",
            "attempt_number",
        ),
        required_columns=("learner_id", "course_id", "quiz_id", "attempt_time", "score"),
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create the learner drop-off SQLite database from raw CSV files."
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=PROJECT_ROOT / "data" / "raw",
        help="Folder containing raw CSV files.",
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=PROJECT_ROOT / "data" / "processed" / "learner_dropoff.sqlite",
        help="SQLite database path to create.",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=PROJECT_ROOT / "src" / "database" / "schema.sql",
        help="SQLite schema file path.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail when expected raw files are missing.",
    )
    return parser.parse_args()


def create_database(database_path: Path, schema_path: Path) -> None:
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    database_path.parent.mkdir(parents=True, exist_ok=True)
    if database_path.exists():
        database_path.unlink()

    # sqlite3.Connection's context manager commits or rolls back, but does not
    # close the connection. ``closing`` is required so Windows can release the
    # database file immediately after the operation.
    with closing(sqlite3.connect(database_path)) as connection, connection:
        connection.executescript(schema_path.read_text(encoding="utf-8"))


def prepare_frame(csv_path: Path, contract: RawFileContract) -> tuple[pd.DataFrame, list[str]]:
    frame = pd.read_csv(csv_path, dtype=str)
    frame.columns = [column.strip() for column in frame.columns]

    missing_required = [
        column for column in contract.required_columns if column not in frame.columns
    ]
    if missing_required:
        return frame, missing_required

    for column in contract.columns:
        if column not in frame.columns:
            frame[column] = None

    return frame.loc[:, contract.columns], []


def load_available_files(raw_dir: Path, database_path: Path) -> tuple[list[str], list[str]]:
    missing_files: list[str] = []
    loaded_tables: list[str] = []

    with closing(sqlite3.connect(database_path)) as connection, connection:
        for contract in RAW_FILE_CONTRACTS:
            csv_path = raw_dir / contract.filename
            if not csv_path.exists():
                missing_files.append(contract.filename)
                continue

            frame, missing_required = prepare_frame(csv_path, contract)
            if missing_required:
                raise ValueError(
                    f"{contract.filename} is missing required columns: "
                    f"{', '.join(missing_required)}"
                )

            frame.to_sql(contract.table, connection, if_exists="append", index=False)
            loaded_tables.append(f"{contract.table} ({len(frame)} rows)")

    return missing_files, loaded_tables


def main() -> int:
    args = parse_args()

    create_database(args.database, args.schema)
    missing_files, loaded_tables = load_available_files(args.raw_dir, args.database)

    print(f"Database created: {args.database}")

    if loaded_tables:
        print("Loaded tables:")
        for table_summary in loaded_tables:
            print(f"- {table_summary}")
    else:
        print("No raw CSV files were loaded yet.")

    if missing_files:
        print("Missing expected raw files:")
        for filename in missing_files:
            print(f"- {filename}")
        if args.strict:
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
