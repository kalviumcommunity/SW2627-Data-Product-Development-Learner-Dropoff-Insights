# Data Inventory

Owner: Monesh

## Purpose

This document records the expected raw data files, their grain, and how each file will map into the SQLite data layer.

The real dataset still needs to be inspected before the schema is finalized. Until then, this inventory defines the contract the ingestion pipeline will validate.

## Expected Raw Files

### learners.csv

Grain:

- One row per learner.

Expected columns:

- learner_id
- signup_date
- cohort
- region

Required:

- learner_id

### courses.csv

Grain:

- One row per course.

Expected columns:

- course_id
- course_name
- category
- expected_duration_days

Required:

- course_id
- course_name

### enrollments.csv

Grain:

- One row per learner-course enrollment.

Expected columns:

- learner_id
- course_id
- enrollment_date
- progress_percent
- completion_status
- completion_date

Required:

- learner_id
- course_id
- enrollment_date

### sessions.csv

Grain:

- One row per learner session or activity event.

Expected columns:

- session_id
- learner_id
- course_id
- session_start_time
- session_duration_minutes
- module_id
- content_type

Required:

- learner_id
- course_id
- session_start_time

### quizzes.csv

Grain:

- One row per quiz attempt.

Expected columns:

- quiz_attempt_id
- learner_id
- course_id
- quiz_id
- attempt_time
- score
- max_score
- attempt_number

Required:

- learner_id
- course_id
- quiz_id
- attempt_time
- score

## SQLite Mapping

| Raw file | SQLite table | Grain |
| --- | --- | --- |
| learners.csv | learners | learner |
| courses.csv | courses | course |
| enrollments.csv | enrollments | learner-course |
| sessions.csv | sessions | session event |
| quizzes.csv | quizzes | quiz attempt |
| derived | learner_course_aggregates | learner-course |
| derived | data_quality_results | validation check |

## Handoff To Analysis

The first data handoff to Jaswanth will be a learner-course aggregate output with these fields:

- learner_id
- course_id
- enrollment_date
- completion_status
- completion_date
- progress_percent
- total_sessions
- active_days
- average_session_duration
- latest_activity_date
- quiz_attempt_count
- average_quiz_score
- latest_quiz_score

## Open Dataset Questions

1. Is there a stable `learner_id` in every file?
2. Is completion represented as a flag, status text, certificate date, or progress percentage?
3. Are session records actual sessions or page/event logs?
4. Are quiz scores stored as raw marks or percentages?
5. Are cohorts available for dashboard filtering?
6. Is the data date range long enough to define 14, 21, or 30 day inactivity windows?
