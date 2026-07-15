# Jaswanth - Dashboard and Automation Plan

## Role

Jaswanth owns the user-facing dashboard, GitHub Actions automation, and project documentation for Learner Drop-off Insights.

Primary responsibility:

- Turn the processed analysis outputs into a usable Streamlit dashboard and keep the project runnable through clear documentation and CI checks.

## Why This Role Matters

The analysis only creates value if stakeholders can understand and act on it. This lane makes the data product usable for academic success mentors and reliable for team review.

## Owned Deliverables

### 1. Streamlit Dashboard Structure

Build dashboard pages:

- Overview
- Behaviour Drivers
- Learner Risk List

Expected output:

- Streamlit app under `src/dashboard/`.
- Page navigation.
- Shared data loading utility.
- Layout matching the mock UI direction.

### 2. Overview Page

Show:

- completion rate
- silent drop-off rate
- high-risk learner count
- median inactivity gap
- completion versus drop-off trend
- top predictive behaviours

Expected output:

- KPI cards.
- Summary charts.
- Global filters.

### 3. Behaviour Drivers Page

Show:

- ranked behaviour driver chart
- completed versus silent drop-off comparison
- quiz score trend comparison
- inactivity gap distribution

Expected output:

- Visuals based on Shaswath's driver ranking and feature outputs.
- Plain labels that stakeholders can understand.

### 4. Learner Risk List

Show:

- learner_id
- course
- risk_bucket
- risk_score
- days_inactive
- latest_quiz_score
- primary_risk_reason
- suggested_action

Expected output:

- Sortable table.
- Filter by course, cohort, risk bucket, and reason.
- High-risk learners visually highlighted.

### 5. Automation

Set up:

- GitHub Actions workflow.
- Pipeline validation command.
- Basic test command.
- README instructions.

Expected output:

- `.github/workflows/ci.yml`
- Test or validation command documented in README.

## Handoff Contracts

### From Monesh

Needs:

- SQLite database path.
- Overview KPI query or table.
- Stable table names.

### From Shaswath

Needs:

- learner_features output.
- behaviour_driver_rankings output.
- learner_risk_scores output.
- risk reason and suggested action fields.

## First PR Scope

Branch name suggestion:

```text
jaswanth/dashboard-automation-plan
```

PR title:

```text
Add dashboard and automation plan for learner drop-off product
```

This PR includes:

- Jaswanth's dashboard responsibilities.
- Planned dashboard screens.
- Automation responsibilities.
- Data contracts needed from Monesh and Shaswath.

## Future Implementation PRs

1. Add Streamlit app scaffold.
2. Add dashboard overview page.
3. Add behaviour drivers page.
4. Add learner risk table.
5. Add GitHub Actions workflow.
6. Add README setup and dashboard usage instructions.

## Acceptance Criteria

- Dashboard opens locally with one command.
- Overview answers the stakeholder question before interaction.
- Learner table defaults to highest risk first.
- Filters update the relevant charts and tables.
- CI checks run on push or pull request.
- README explains setup, commands, and dashboard purpose.

## Viva Preparation

Jaswanth should be ready to explain:

- How each dashboard page supports the stakeholder.
- Which data output powers each chart or table.
- How the risk table helps mentors take action.
- How GitHub Actions validates the project.
- How to run the dashboard locally.
- What dashboard limitations remain.

## Current Open Questions

1. Should the final dashboard use Streamlit only or include a static mock in docs?
2. What exact output file names will Monesh and Shaswath produce?
3. Which filters are available from the raw data: course, cohort, date range, or status?
4. Should high-risk learners be exportable as CSV?
5. Where should dashboard screenshots be stored for final documentation?
