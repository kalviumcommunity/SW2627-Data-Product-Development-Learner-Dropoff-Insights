# Mock UI Specification

## Dashboard Name

Learner Drop-off Insights

## Primary Dashboard Job

Help academic success mentors identify which learners are at risk of silent drop-off and understand which behaviours explain that risk.

## Design Principles

- Summary first: the first screen should answer "How serious is the drop-off problem right now?"
- Explainable risk: every risk score must have a plain-language reason.
- Actionable table: mentors should be able to decide who to contact next.
- Three-way ownership: each screen should show visible contribution from the assigned team roles.

## Global Navigation

### Dashboard Sections

1. Overview
2. Behaviour Drivers
3. Learner Risk List

### Global Filters

- Course
- Cohort
- Date range
- Risk bucket
- Completion status

Filters should update KPI cards, charts, and learner table.

## Screen 1: Overview

### Purpose

Give mentors and operations leads a fast read on completion, drop-off, and risk.

### Layout

Top row:

- Completion rate
- Silent drop-off rate
- High-risk learners
- Median inactivity gap

Middle row:

- Completion versus drop-off trend by week
- Risk bucket distribution

Bottom row:

- Top predictive behaviours
- Current intervention queue preview

### Ownership

- Monesh provides SQL aggregates for learner counts, statuses, and inactivity gaps.
- Shaswath provides risk labels, behaviour driver ranking, and interpretation.
- Jaswanth builds cards, charts, filters, and layout in Streamlit.

### Acceptance Criteria

- Stakeholder can identify current risk level without scrolling.
- At least one chart explains trend or distribution.
- At least one element links risk to behaviour, not just status.

## Screen 2: Behaviour Drivers

### Purpose

Explain which behaviours are most associated with course completion or silent drop-off.

### Layout

Left:

- Ranked behaviour driver chart.
- Driver direction: completion predictor or drop-off predictor.

Right:

- Completed versus drop-off comparison table.
- Short insight notes.

Lower section:

- Quiz score trend comparison.
- Inactivity gap distribution.
- Session consistency comparison.

### Example Drivers

- Long inactivity gap after early engagement.
- Declining quiz score trend.
- Low retry behaviour after failed quiz.
- High activity in first week.
- Consistent session streaks.

### Ownership

- Monesh provides clean aggregate input tables.
- Shaswath owns feature ranking and findings.
- Jaswanth owns visual encoding and interaction.

### Acceptance Criteria

- Chart makes it clear whether a behaviour predicts completion or drop-off.
- Each top driver has a plain-language interpretation.
- The page avoids claiming causation unless the analysis supports it.

## Screen 3: Learner Risk List

### Purpose

Turn the analysis into a weekly action list for mentors.

### Layout

Controls:

- Course filter
- Cohort filter
- Risk bucket filter
- Primary risk reason filter

Table columns:

- Learner ID
- Course
- Risk bucket
- Risk score
- Last activity date
- Days inactive
- Latest quiz score
- Primary risk reason
- Suggested action

Row styling:

- High risk: strong warning style.
- Medium risk: moderate warning style.
- Low risk: neutral style.

### Suggested Actions

- Send reminder after inactivity.
- Offer quiz support.
- Recommend next module.
- Review course difficulty.

### Ownership

- Monesh ensures learner-course keys and latest activity are accurate.
- Shaswath generates risk score, risk bucket, reason, and suggested action logic.
- Jaswanth builds the searchable and sortable table.

### Acceptance Criteria

- Table defaults to highest risk first.
- Every high-risk learner has a reason.
- Users can filter down to one course or cohort.

## Static Mock

A low-fidelity static mock is available at:

```text
mock-ui/index.html
```

It is not connected to real data. It is a visual and interaction reference for the future Streamlit dashboard.

## Streamlit Implementation Notes

Suggested folder:

```text
src/dashboard/app.py
```

Suggested Streamlit pages:

```text
src/dashboard/pages/1_Overview.py
src/dashboard/pages/2_Behaviour_Drivers.py
src/dashboard/pages/3_Learner_Risk_List.py
```

Suggested shared data loading:

```text
src/dashboard/data_access.py
```

Dashboard inputs:

- SQLite DB from Monesh.
- Feature table from Shaswath.
- Behaviour driver table from Shaswath.

## Mock Data Fields Needed

### KPI Layer

- total_learners
- completed_learners
- silent_dropoff_learners
- active_learners
- high_risk_learners
- median_inactivity_gap

### Behaviour Driver Layer

- feature_name
- driver_direction
- strength_score
- completed_group_value
- dropoff_group_value
- interpretation

### Learner Risk Layer

- learner_id
- course_id
- course_name
- cohort
- risk_score
- risk_bucket
- last_activity_date
- days_inactive
- latest_quiz_score
- primary_risk_reason
- suggested_action

## PR Breakdown Suggestion

### PR 1: Planning Artifacts

Owner: Any member, reviewed by team.

- README
- PRD
- Mock UI spec
- Static mock UI

### PR 2: SQLite Schema and Data Contracts

Owner: Monesh.

- Schema script.
- Data dictionary.
- Required column checks.

### PR 3: Labeling and Feature Contract

Owner: Shaswath.

- Label definitions.
- Feature list.
- Initial feature generation script or notebook.

### PR 4: Dashboard Scaffold and CI Plan

Owner: Jaswanth.

- Streamlit app shell.
- Page structure.
- GitHub Actions workflow skeleton.

## Mentor Review Questions

1. Does the mock UI answer the stakeholder question clearly?
2. Are the data requirements realistic for the assigned dataset?
3. Is each team member's contribution visible and testable?
4. Are the labels and features defensible?
5. Is the dashboard actionable, or is it only descriptive?
