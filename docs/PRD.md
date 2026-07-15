# Product Requirements Document

## Product Name

Learner Drop-off Insights

## Problem Statement

The edtech platform tracks course completion records, quiz performance, and student session activity, but it does not identify which learning behaviours predict long-term course completion versus silent drop-offs.

This creates a decision gap for academic success teams. They can see that some learners stop progressing, but they cannot reliably tell which early behaviours matter, which learners need intervention, or what type of intervention should happen first.

## Product Vision

Build a data product that converts raw learner activity into explainable drop-off risk insights. The product should help mentors and course operations teams identify learners at risk, understand the behaviours driving that risk, and prioritize action before learners silently disengage.

## Primary Users

### Academic Success Mentor

Needs to know which learners require attention this week and why.

Key questions:

- Which learners are most likely to drop off?
- What behaviour changed before the risk appeared?
- Which learners need immediate outreach?

### Course Operations Lead

Needs to understand course-level engagement patterns.

Key questions:

- Which courses or cohorts show high silent drop-off?
- Are drop-offs linked to quiz difficulty, session inactivity, or inconsistent participation?
- Where should support workflows be improved?

### Data Team / Analyst

Needs a reliable, repeatable pipeline.

Key questions:

- Is the source data clean enough to trust?
- Are labels and features generated consistently?
- Can the dashboard be refreshed without manual notebook work?

## Goals

1. Define a clear and defensible labeling rule for course completion versus silent drop-off.
2. Build a repeatable pipeline from raw CSV data to SQLite tables and feature outputs.
3. Engineer behavioural features from sessions, quizzes, and course progress.
4. Identify and rank behaviours associated with completion and drop-off.
5. Build a dashboard that makes learner risk and behaviour drivers easy to inspect.
6. Add automated validation so broken or suspicious data is caught early.

## Non-Goals

- Build a production-grade machine learning system.
- Send automated emails, messages, or notifications to learners.
- Replace mentor judgment with a black-box score.
- Predict lifetime student success beyond the assigned course dataset.
- Build real-time analytics. The MVP assumes batch refresh from available CSV files.

## Success Metrics

### Product Success

- Mentor can identify high-risk learners within 30 seconds of opening the dashboard.
- Dashboard shows top behaviour drivers behind drop-off, not only raw charts.
- Each learner risk row includes at least one explainable reason.
- Course and cohort filters update the main KPIs and charts.

### Data Success

- Raw-to-clean pipeline runs from command line without manual notebook steps.
- SQLite database contains documented tables with expected keys and data types.
- Data quality checks detect missing IDs, duplicate records, invalid dates, and impossible score values.
- Feature generation produces one row per learner-course enrollment.

### Team Success

- Each member has visible PR evidence in their contribution lane.
- Each member can explain their owned part during viva.
- PRD, system design, code, and dashboard remain consistent.

## Assumptions

Because the raw dataset has not been inspected yet, this PRD uses the following working assumptions:

- There is a learner or student identifier.
- There is a course identifier.
- There are course completion records or progress indicators.
- There are quiz attempt records with score and timestamp.
- There are session activity records with timestamp or duration.
- The dataset supports grouping behaviour at learner-course level.

If the actual dataset differs, the PRD should be updated before implementation begins.

## Definitions

### Completed Learner

A learner who has completed the course based on the platform's completion flag, certificate status, or 100 percent progress marker.

Fallback rule if no explicit completion flag exists:

- Learner has reached a high progress threshold, such as 90 percent or more, and has recent course activity near the course end.

### Silent Drop-off

A learner who was previously active but stops engaging without a recorded completion.

Working rule:

- Learner has not completed the course.
- Learner has no session, quiz, or course activity for a defined inactivity window.
- Learner had meaningful earlier activity, so the learner is not simply unstarted.

Initial inactivity threshold:

- 14 days without activity for short courses.
- 21 or 30 days without activity for longer courses.

The final threshold must be validated against the dataset date range and course duration.

### Active Learner

A learner who has not completed the course but has recent activity inside the inactivity threshold.

### At-Risk Learner

An active or inactive learner whose behaviour features match patterns commonly seen before silent drop-off.

## Required Data Entities

### Learners

Expected fields:

- learner_id
- signup_date or enrollment_date
- optional cohort, region, or segment

### Courses

Expected fields:

- course_id
- course_name
- category or track
- expected_duration_days

### Enrollments / Completion

Expected fields:

- learner_id
- course_id
- enrollment_date
- progress_percent
- completion_status
- completion_date

### Sessions

Expected fields:

- learner_id
- course_id
- session_id
- session_start_time
- session_duration_minutes
- content_type or module_id if available

### Quizzes

Expected fields:

- learner_id
- course_id
- quiz_id
- attempt_time
- score
- max_score
- attempt_number

## Feature Requirements

The analysis should produce one feature row per learner-course enrollment.

### Session Behaviour Features

- total_sessions
- active_days
- sessions_per_week
- average_session_duration
- days_since_last_activity
- longest_inactivity_gap
- current_inactivity_gap
- session_streak_max
- missed_week_count, if schedule exists

### Quiz Behaviour Features

- quiz_attempt_count
- average_quiz_score
- latest_quiz_score
- quiz_score_trend
- failed_quiz_count
- retry_rate
- days_between_quiz_attempts

### Course Progress Features

- progress_percent
- progress_velocity
- days_to_25_percent_progress
- days_to_50_percent_progress
- progress_stalled_flag

### Combined Behaviour Features

- low_score_then_inactive_flag
- activity_decay_rate
- early_engagement_score
- consistency_score
- risk_reason_primary

## Analysis Requirements

The product must answer:

1. Which behaviours differ most between completed learners and silent drop-offs?
2. Which behaviours appear early enough to be useful for intervention?
3. Which learner segments, courses, or cohorts have the highest drop-off risk?
4. Which learners are currently high risk and why?

Minimum acceptable analysis:

- Descriptive comparison between completed and silent drop-off learners.
- Ranked feature table by difference, correlation, or simple model importance.
- One simple interpretable model or scoring method, such as logistic regression, decision tree, or weighted rule-based score.
- Written findings with caveats.

Preferred analysis:

- Train/test split if data volume supports it.
- Model evaluation using accuracy, precision, recall, and confusion matrix.
- Explainable feature importance.
- Risk bucket definitions: high, medium, low.

## Functional Requirements

### FR1: Data Ingestion

The system must load raw CSV files into a repeatable staging process.

Owner: Monesh

Acceptance criteria:

- Raw files are read from a documented folder.
- Required columns are checked.
- Invalid rows are logged or rejected with clear reason.

### FR2: SQLite Data Layer

The system must store clean data in SQLite tables.

Owner: Monesh

Acceptance criteria:

- Tables use stable primary keys or composite keys.
- Date and numeric fields are normalized.
- Aggregation SQL queries can be rerun.

### FR3: Label Generation

The system must assign completion/drop-off labels at learner-course level.

Owner: Shaswath

Acceptance criteria:

- Labeling logic is documented.
- Each learner-course row receives exactly one status.
- Edge cases are handled: unstarted learner, active learner, completed learner, silent drop-off.

### FR4: Feature Engineering

The system must generate behavioural features in Pandas.

Owner: Shaswath

Acceptance criteria:

- Feature output has one row per learner-course enrollment.
- Missing data handling is documented.
- Features are reproducible from raw or clean data.

### FR5: Predictive Behaviour Ranking

The system must rank behaviours that predict completion or drop-off.

Owner: Shaswath

Acceptance criteria:

- Output contains feature name, direction, strength, and interpretation.
- Findings separate correlation from causation.
- At least three major behaviour drivers are explained.

### FR6: Dashboard Overview

The dashboard must show the overall course completion and drop-off situation.

Owner: Jaswanth

Acceptance criteria:

- KPI cards show completion rate, silent drop-off rate, at-risk learners, and median inactivity gap.
- Filters support course, cohort, status, and risk bucket where available.
- Visuals update from the processed output.

### FR7: Learner Risk Table

The dashboard must provide a list of learners who need attention.

Owner: Jaswanth

Acceptance criteria:

- Table includes learner ID, course, risk bucket, last activity date, primary risk reason, and suggested action.
- Sorting by risk score is available.
- High-risk learners are visually distinct.

### FR8: Data Quality and Automation

The project must validate data and pipeline health.

Owner: Jaswanth with inputs from Monesh

Acceptance criteria:

- GitHub Actions runs validation or tests on push/PR.
- Failures are readable in CI logs.
- README documents how to run checks locally.

## Dashboard Requirements

### Page 1: Overview

Purpose:

- Show the current learner completion and drop-off picture.

Components:

- KPI cards.
- Completion versus drop-off trend.
- Risk bucket distribution.
- Top predictive behaviours.

### Page 2: Behaviour Drivers

Purpose:

- Explain what behaviours predict completion or drop-off.

Components:

- Feature importance chart.
- Completed versus drop-off comparison chart.
- Quiz score trend comparison.
- Inactivity gap distribution.

### Page 3: Learner Risk List

Purpose:

- Help mentors decide who to contact.

Components:

- Learner risk table.
- Filters for course, cohort, risk, and reason.
- Suggested next action.

## MVP Scope

The MVP must include:

- SQLite database with clean learner, session, quiz, and enrollment data.
- Feature generation script.
- Completion/drop-off labels.
- Ranked behaviour insights.
- Streamlit dashboard with at least three useful screens.
- Basic GitHub Actions validation.
- README instructions.

## Stretch Scope

If MVP is complete:

- Add model evaluation page.
- Add cohort comparison.
- Add downloadable CSV of high-risk learners.
- Add intervention recommendation logic.
- Add simple deployment for dashboard access.

## User Stories

### Academic Success Mentor

As a mentor, I want to see the learners most likely to drop off so that I can prioritize outreach.

As a mentor, I want to know why a learner is high risk so that I can send the right support message.

As a mentor, I want to filter by course and cohort so that I can focus on the learners I manage.

### Course Operations Lead

As an operations lead, I want to know which behaviours predict drop-off so that I can improve course design and support timing.

As an operations lead, I want to compare completion and drop-off patterns across courses so that I can identify weak spots.

### Data Team

As a data team member, I want the pipeline to fail clearly on bad data so that the dashboard does not show misleading metrics.

As a data team member, I want reusable feature outputs so that analysis and dashboard numbers reconcile.

## Open Questions

1. What columns are available in the assigned dataset?
2. Is course completion explicitly recorded?
3. What is the latest complete activity date in the data?
4. What inactivity window should define silent drop-off?
5. Are courses self-paced or scheduled?
6. Is quiz difficulty comparable across courses?
7. Are multiple quiz attempts stored separately?
8. Does session activity include duration, content viewed, or only login timestamp?

## Key Risks

### Risk: No explicit completion flag

Mitigation:

- Use progress threshold and activity near course end as fallback.
- Document the assumption clearly.

### Risk: Activity data has missing or inconsistent timestamps

Mitigation:

- Add timestamp validation.
- Exclude impossible records from time-based features.
- Report excluded row counts.

### Risk: Model becomes hard to explain

Mitigation:

- Prefer interpretable models or rule-based scoring.
- Show feature direction and plain-language explanation.

### Risk: Dashboard shows numbers that do not reconcile

Mitigation:

- Use shared feature output and consistent filters.
- Add validation checks for row counts and label totals.

## Individual Viva Readiness

### Monesh Must Be Able To Explain

- Why the schema uses the chosen tables and keys.
- How raw data is cleaned before analysis.
- Which data quality checks protect the dashboard.
- How SQL aggregations support feature engineering.

### Shaswath Must Be Able To Explain

- How completion and silent drop-off are labeled.
- Which features were engineered and why.
- Which behaviours best predict completion/drop-off.
- What the analysis can and cannot prove.

### Jaswanth Must Be Able To Explain

- How the dashboard supports mentor decisions.
- How filters and charts connect to the data outputs.
- How GitHub Actions validates the pipeline.
- How a user should interpret the risk table.

## Approval Checklist

- PRD names the user, problem, and business question.
- PRD defines MVP scope and non-goals.
- Labeling logic is clear enough to implement.
- Three contribution lanes are visible and non-overlapping.
- Mock UI aligns with dashboard requirements.
- Open data questions are listed before implementation.
