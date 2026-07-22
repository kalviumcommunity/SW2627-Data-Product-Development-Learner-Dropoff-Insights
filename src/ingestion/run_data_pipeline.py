"""Run the Monesh-owned raw-to-aggregate data pipeline."""

from __future__ import annotations

import argparse
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from src.database.build_aggregates import (
    DEFAULT_OUTPUT_PATH as DEFAULT_AGGREGATE_OUTPUT_PATH,
    DEFAULT_QUERY_PATH as DEFAULT_AGGREGATE_QUERY_PATH,
    export_aggregate_csv,
    refresh_aggregate_table,
    validate_database,
)
from src.ingestion.load_raw_data import (
    PROJECT_ROOT,
    create_database,
    load_available_files,
)
from src.ingestion.validate_data_quality import (
    QualityResult,
    print_summary,
    run_quality_checks,
    write_quality_results,
)


DEFAULT_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "processed" / "learner_dropoff.sqlite"
DEFAULT_SCHEMA_PATH = PROJECT_ROOT / "src" / "database" / "schema.sql"


@dataclass(frozen=True)
class PipelineRunResult:
    loaded_tables: list[str]
    missing_files: list[str]
    quality_results: list[QualityResult]
    aggregate_row_count: int

    @property
    def blocking_failure_count(self) -> int:
        return sum(
            1
            for result in self.quality_results
            if result.severity == "blocking" and result.status == "failed"
        )

    @property
    def warning_count(self) -> int:
        return sum(1 for result in self.quality_results if result.status == "warning")

    @property
    def return_code(self) -> int:
        if self.blocking_failure_count:
            return 1
        return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run ingestion, data quality validation, and aggregate export."
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=DEFAULT_RAW_DIR,
        help="Folder containing raw CSV files.",
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE_PATH,
        help="SQLite database path to create.",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=DEFAULT_SCHEMA_PATH,
        help="SQLite schema file path.",
    )
    parser.add_argument(
        "--aggregate-output",
        type=Path,
        default=DEFAULT_AGGREGATE_OUTPUT_PATH,
        help="CSV output path for learner-course aggregates.",
    )
    parser.add_argument(
        "--aggregate-query",
        type=Path,
        default=DEFAULT_AGGREGATE_QUERY_PATH,
        help="SQL query file used to populate learner_course_aggregates.",
    )
    parser.add_argument(
        "--strict-raw",
        action="store_true",
        help="Fail when any expected raw CSV file is missing.",
    )
    return parser.parse_args()


def run_pipeline(
    raw_dir: Path = DEFAULT_RAW_DIR,
    database_path: Path = DEFAULT_DATABASE_PATH,
    schema_path: Path = DEFAULT_SCHEMA_PATH,
    aggregate_output_path: Path = DEFAULT_AGGREGATE_OUTPUT_PATH,
    aggregate_query_path: Path = DEFAULT_AGGREGATE_QUERY_PATH,
    strict_raw: bool = False,
) -> PipelineRunResult:
    create_database(database_path, schema_path)
    missing_files, loaded_tables = load_available_files(raw_dir, database_path)

    with closing(sqlite3.connect(database_path)) as connection, connection:
        quality_results = run_quality_checks(connection)
        if strict_raw and missing_files:
            quality_results.append(
                QualityResult(
                    check_name="raw_files_complete",
                    severity="blocking",
                    status="failed",
                    failed_row_count=len(missing_files),
                    message=f"Missing raw file(s): {', '.join(missing_files)}.",
                )
            )
        write_quality_results(connection, quality_results)

        blocking_failures = [
            result
            for result in quality_results
            if result.severity == "blocking" and result.status == "failed"
        ]

        if blocking_failures:
            aggregate_row_count = 0
        else:
            validate_database(connection, database_path)
            refresh_aggregate_table(connection, aggregate_query_path)
            aggregate_frame = export_aggregate_csv(connection, aggregate_output_path)
            aggregate_row_count = len(aggregate_frame)

    return PipelineRunResult(
        loaded_tables=loaded_tables,
        missing_files=missing_files,
        quality_results=quality_results,
        aggregate_row_count=aggregate_row_count,
    )


def print_pipeline_summary(result: PipelineRunResult, aggregate_output_path: Path) -> None:
    if result.loaded_tables:
        print("Loaded tables:")
        for table_summary in result.loaded_tables:
            print(f"- {table_summary}")
    else:
        print("No raw CSV files were loaded.")

    if result.missing_files:
        print("Missing expected raw files:")
        for filename in result.missing_files:
            print(f"- {filename}")

    print_summary(result.quality_results)
    if result.return_code == 0:
        print(
            f"Wrote {result.aggregate_row_count} learner-course aggregate rows "
            f"to {aggregate_output_path}"
        )
    else:
        print("Skipped aggregate export because blocking quality checks failed.")


def main() -> int:
    args = parse_args()
    result = run_pipeline(
        raw_dir=args.raw_dir,
        database_path=args.database,
        schema_path=args.schema,
        aggregate_output_path=args.aggregate_output,
        aggregate_query_path=args.aggregate_query,
        strict_raw=args.strict_raw,
    )
    print_pipeline_summary(result, args.aggregate_output)
    return result.return_code


if __name__ == "__main__":
    raise SystemExit(main())
