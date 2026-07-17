# Learner Drop-off Insights

Sprint 1 data product for identifying which learning behaviours predict long-term course completion versus silent drop-offs on an edtech platform.

## Core Business Question

Which learner behaviours in sessions, quizzes, and course activity best predict whether a student will complete a course or silently drop off?

## Stakeholders

- Primary: Academic success mentors and course operations leads.
- Secondary: Product managers responsible for learner engagement and retention.
- Tertiary: Data team members maintaining reliable learner analytics pipelines.

## Product Direction

Build an end-to-end data product that:

1. Ingests raw course, quiz, and session data.
2. Cleans and validates the data into SQLite.
3. Engineers learner behaviour features in Pandas.
4. Labels learners as completed, active, at risk, or silent drop-off.
5. Ranks behaviours that predict completion or drop-off.
6. Shows insights in a Streamlit dashboard.
7. Runs data quality and pipeline checks through GitHub Actions.

## Three Contribution Lanes

### Monesh: Data Engineer - SQL and Data Layer

Owns the reliable data foundation.

- Design the SQLite schema for learners, courses, enrollments, sessions, quizzes, and feature outputs.
- Load raw CSV files into staging tables.
- Clean missing values, duplicate records, invalid timestamps, and type mismatches.
- Write SQL aggregation queries for session counts, quiz summaries, attendance consistency, and inactivity gaps.
- Add data quality checks that fail clearly when source data is not trustworthy.

Evidence for viva:

- Schema diagram or table documentation.
- PRs for ingestion scripts, SQL queries, and validation checks.
- Explanation of cleaning rules and why they are safe.

### Shaswath: Data Analyst - Feature and Insights Owner

Owns the analytical answer to the problem statement.

- Define completion, active learner, at-risk learner, and silent drop-off labels.
- Build engineered features in Pandas and NumPy.
- Compare completed learners against silent drop-offs.
- Run correlation, feature importance, or a simple interpretable model.
- Produce the final ranked behaviour drivers and written findings.

Evidence for viva:

- Notebook or script showing feature engineering.
- Labeling logic and assumptions.
- Ranked insights explaining which behaviours matter most.

### Jaswanth: Dashboard and Automation Owner

Owns the user-facing product and delivery workflow.

- Build the Streamlit dashboard from clean DB tables and feature outputs.
- Create charts, filters, learner risk table, and dashboard navigation views.
- Set up GitHub Actions for pipeline checks and basic tests.
- Own README updates, setup instructions, dashboard screenshots, and deployment notes.
- Keep the mock UI aligned with the final dashboard.

Evidence for viva:

- Streamlit app PRs.
- GitHub Actions workflow logs.
- Dashboard walkthrough showing how stakeholders act on insights.

## Current Planning Artifacts

- [PRD](docs/PRD.md)
- [Mock UI Spec](docs/MOCK_UI.md)
- [Sprint Execution Plan](docs/SPRINT_EXECUTION_PLAN.md)
- [Static Mock UI](mock-ui/index.html)

## Run The Dashboard Locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Start Streamlit:

```bash
streamlit run src/dashboard/app.py
```

Expected dashboard inputs:

- `data/processed/learner_features.csv`
- `data/processed/behaviour_driver_rankings.csv`

If these files are not generated yet, the dashboard opens with waiting states instead of crashing.

## Validation Commands

Run the same lightweight checks used by CI:

```bash
python -m compileall src
python -m unittest discover -s tests -p "test_*.py"
```

The test suite includes feature-output checks and dashboard helper checks against the sample learner aggregate fixture.

## Suggested Repository Structure

```text
data/
  raw/
  processed/
docs/
  PRD.md
  MOCK_UI.md
mock-ui/
  index.html
  styles.css
src/
  ingestion/
  database/
  features/
  analysis/
  dashboard/
tests/
  test_data_quality.py
  test_features.py
.github/
  workflows/
    data-quality.yml
```

## Day 1 to Day 5 Plan

### Day 1

- Confirm team members and contribution lanes.
- Add team charter and planning documents.
- Prepare first standup answer.

### Day 2

- Inspect available raw data columns and grain.
- Confirm label assumptions for completion and silent drop-off.
- Update PRD if the data shape changes the product scope.

### Day 3

- Draft system design with data flow, schema, feature table, and dashboard screens.
- Split first implementation PRs by lane.

### Day 4

- Mentor review for PRD and system design.
- Resolve feedback before coding.

### Day 5

- Start implementation only after approval.
- Raise small PRs for schema, feature design, and dashboard scaffold.

## First Standup Draft

Team problem statement: We are building a learner drop-off insights dashboard that identifies which session, quiz, and activity behaviours predict long-term course completion versus silent drop-offs.

Core business question: For academic success mentors, which learners are at risk of silently dropping off, and which behaviours explain that risk early enough to intervene?

Biggest open data question: What exact fields and timestamps are available to define course completion, inactivity gaps, quiz score trends, and session streaks?

Tonight's submission: Add team charter, PRD draft, mock UI draft, and initial project structure to the repository through a pull request.
