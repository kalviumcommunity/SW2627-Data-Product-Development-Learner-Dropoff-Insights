# Data Quality Checks

Owner: Monesh

## Purpose

The dashboard should not silently trust bad source data. These checks define the first validation layer for the raw-to-SQLite pipeline.

## Blocking Checks

Blocking checks should fail the pipeline because downstream analysis would become unreliable.

### Required Columns

Each raw file must contain its required columns.

Examples:

- `learners.csv` must contain `learner_id`.
- `enrollments.csv` must contain `learner_id`, `course_id`, and `enrollment_date`.
- `sessions.csv` must contain `learner_id`, `course_id`, and `session_start_time`.
- `quizzes.csv` must contain `learner_id`, `course_id`, `quiz_id`, `attempt_time`, and `score`.

### Missing Keys

Rows with missing learner or course keys are invalid for learner-course analysis.

Check:

- `learner_id` is not null where required.
- `course_id` is not null where required.

### Duplicate Enrollment Keys

There should be only one enrollment record per learner-course pair unless the dataset explicitly supports re-enrollment.

Check:

- duplicate count for `(learner_id, course_id)`.

### Invalid Dates

Date fields must parse to valid timestamps.

Check:

- `signup_date`
- `enrollment_date`
- `completion_date`
- `session_start_time`
- `attempt_time`

### Impossible Quiz Scores

Quiz score values must be inside expected bounds.

Check:

- `score >= 0`
- if `max_score` exists, `score <= max_score`

## Warning Checks

Warning checks should be reported but may not block the pipeline.

### Missing Optional Dimensions

Examples:

- cohort
- region
- category
- content_type

These fields improve filtering but are not required for MVP analysis.

### Missing Session Duration

If session duration is missing, time-based engagement features will be limited.

Fallback:

- Use session count and active days instead of average duration.

### Missing Completion Date

If completion date is missing but completion status exists, completion labels can still be created.

Fallback:

- Use completion status and progress percentage.

## Data Quality Output

The validation process should write one row per check to `data_quality_results`.

Expected fields:

- check_name
- severity
- status
- failed_row_count
- message
- checked_at

## First Implementation Target

The first data validation script should support:

1. Required column checks.
2. Missing key checks.
3. Duplicate enrollment key check.
4. Date parse checks.
5. Quiz score range checks.

This is enough to protect the first analysis and dashboard iteration.

## Implementation Command

After raw files are loaded into SQLite, run:

```bash
python src/ingestion/validate_data_quality.py
```

The script writes one row per validation result into `data_quality_results`.
Blocking failures return a non-zero exit code so CI or manual runs can stop before analysis uses bad data.
