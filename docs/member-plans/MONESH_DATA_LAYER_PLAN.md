# Monesh - Data Engineer Plan

## Role

Monesh owns the SQL and data layer for Learner Drop-off Insights.

Primary responsibility:

- Turn raw CSV files into reliable SQLite tables and reusable SQL aggregates for analysis and dashboard use.

## Why This Role Matters

The dashboard and analysis are only useful if the learner activity data is trustworthy. This lane makes the raw data usable by handling schema design, ingestion, cleaning, type normalization, duplicate handling, and data quality validation.

## Owned Deliverables

### 1. SQLite Schema

Design tables for:

- learners
- courses
- enrollments
- sessions
- quizzes
- learner_course_aggregates
- data_quality_results

Expected output:

- SQL schema file.
- Data dictionary explaining key columns.
- Primary key and foreign key decisions.

### 2. Raw Data Ingestion

Build a repeatable ingestion script that:

- Reads raw CSV files from `data/raw/`.
- Validates required columns.
- Normalizes column names.
- Converts dates and numeric fields.
- Loads cleaned records into SQLite.

Expected output:

- Ingestion script under `src/ingestion/`.
- SQLite database created under `data/processed/`.
- Clear terminal logs for rows loaded, skipped, or failed.

### 3. Data Cleaning Rules

Handle:

- Missing learner IDs.
- Missing course IDs.
- Duplicate learner-course records.
- Invalid timestamps.
- Negative or impossible session duration.
- Quiz scores outside valid ranges.

Expected output:

- Cleaning rule documentation.
- Validation results table or CSV.

### 4. SQL Aggregates

Write SQL queries that calculate:

- total_sessions
- active_days
- average_session_duration
- latest_activity_date
- days_since_last_activity
- longest_inactivity_gap
- quiz_attempt_count
- average_quiz_score
- latest_quiz_score

Expected output:

- SQL files under `src/database/queries/`.
- Aggregate table usable by Shaswath's feature engineering.

## Handoff Contracts

### To Shaswath

Provide a learner-course aggregate table with one row per learner-course pair.

Required fields:

- learner_id
- course_id
- enrollment_date
- completion_status
- progress_percent
- latest_activity_date
- total_sessions
- active_days
- average_session_duration
- quiz_attempt_count
- average_quiz_score
- latest_quiz_score

### To Jaswanth

Provide stable tables or views for dashboard use:

- overview KPI source
- learner risk source
- data quality source

## First PR Scope

Branch name suggestion:

```text
monesh/data-layer-plan
```

PR title:

```text
Add data layer plan for learner drop-off pipeline
```

This PR includes:

- Monesh's data engineering responsibilities.
- Planned SQLite schema.
- Data quality checks.
- SQL aggregate handoff contract.

## Future Implementation PRs

1. Add SQLite schema.
2. Add raw CSV ingestion script.
3. Add data quality checks.
4. Add SQL aggregate queries.
5. Add tests for schema and validation.

## Acceptance Criteria

- Raw data can be loaded without manual notebook work.
- SQLite tables have documented grain and keys.
- Invalid records are detected and reported.
- Shaswath can build features from the aggregate output.
- Jaswanth can use validation outputs for CI checks and documentation.

## Viva Preparation

Monesh should be ready to explain:

- Why each SQLite table exists.
- How duplicate and missing records are handled.
- Which fields are required for completion/drop-off analysis.
- How SQL aggregates support feature engineering.
- How data quality checks prevent misleading dashboard metrics.

## Current Open Questions

1. What raw CSV files are provided?
2. Which column stores course completion?
3. Are session timestamps event-level or daily summaries?
4. Are quiz scores stored as percentage or raw marks?
5. Is course duration available for inactivity threshold logic?
