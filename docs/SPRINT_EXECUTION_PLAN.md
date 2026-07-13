# Sprint Execution Plan

## Purpose

This plan turns the PRD into three visible contribution lanes. Use it for standups, weekly check-ins, PR planning, and viva preparation.

## Working Agreement

- No direct pushes to main.
- Every implementation change goes through a pull request.
- Each person should raise at least one meaningful PR every two sessions during implementation.
- Each PR should mention the concept or skill being demonstrated.
- Each person owns a named lane, but the team reviews shared decisions like label definitions and dashboard metrics.

## Week 1: Learning, PRD, and System Design

### Team Output

- Approved PRD.
- Approved system design.
- Mock UI aligned with PRD.
- Initial repo structure.

### Monesh: Data Engineer

Own by end of Week 1:

- Proposed SQLite schema.
- Data dictionary draft.
- Raw data inspection notes.
- Data quality checklist.

First PR ideas:

- Add schema draft and data contracts.
- Add raw data profiling script skeleton.

### Jaswanth: Data Analyst

Own by end of Week 1:

- Completion/drop-off label proposal.
- Feature list.
- Analysis method proposal.
- Initial hypothesis list.

First PR ideas:

- Add label logic document.
- Add feature engineering plan or notebook scaffold.

### Shaswath: Dashboard and Automation

Own by end of Week 1:

- Mock UI.
- Streamlit page structure plan.
- CI workflow plan.
- README and setup instructions.

First PR ideas:

- Add dashboard scaffold.
- Add GitHub Actions workflow skeleton.

## Week 2: Approval and Setup

### Team Output

- Mentor feedback resolved.
- Final schema and data contracts approved.
- Implementation tasks split into small PRs.

### Monesh

- Create SQLite database setup script.
- Build ingestion flow for raw CSV files.
- Add validation for required columns and duplicate keys.

### Jaswanth

- Implement label generation on top of clean data.
- Implement first version of feature generation.
- Validate feature output grain: one row per learner-course.

### Shaswath

- Create Streamlit app shell with navigation.
- Connect dashboard to placeholder or sample processed outputs.
- Add basic CI command that can run locally and in GitHub Actions.

## Weeks 3 to 5: Implementation

## PR Sequence

### PR A: Data Layer Foundation

Owner: Monesh

Includes:

- SQLite schema.
- Ingestion script.
- Required column checks.
- Initial row count checks.

Review focus:

- Does the schema match the PRD?
- Are keys stable?
- Are bad rows handled clearly?

### PR B: SQL Aggregates

Owner: Monesh

Includes:

- Session aggregates.
- Quiz aggregates.
- Latest activity calculation.
- Inactivity gap query.

Review focus:

- Do aggregate outputs have correct grain?
- Are date calculations consistent?
- Can Jaswanth use the outputs directly?

### PR C: Labels and Feature Engineering

Owner: Jaswanth

Includes:

- Completion, active, at-risk, and silent drop-off labels.
- Behaviour feature table.
- Missing data handling rules.

Review focus:

- Is labeling defensible?
- Does every learner-course receive one status?
- Are features documented?

### PR D: Behaviour Driver Analysis

Owner: Jaswanth

Includes:

- Completed versus drop-off comparison.
- Driver ranking method.
- Findings table.
- Caveats.

Review focus:

- Are the insights tied to the problem statement?
- Are conclusions explainable?
- Are correlation and causation separated?

### PR E: Dashboard MVP

Owner: Shaswath

Includes:

- Streamlit overview page.
- Behaviour drivers page.
- Learner risk table.
- Initial filters.

Review focus:

- Does the default screen answer the stakeholder question?
- Do charts use the same metrics as analysis output?
- Is the risk table actionable?

### PR F: Automation and Documentation

Owner: Shaswath

Includes:

- GitHub Actions workflow.
- Test or validation command.
- README setup steps.
- Dashboard usage notes.

Review focus:

- Does CI catch broken data or pipeline failures?
- Can a teammate run the project locally from README?
- Are limitations documented?

## Suggested Standup Answers

### Monesh

Yesterday:

- Inspected source columns and drafted the SQLite schema for learner, course, session, quiz, and enrollment tables.

Today:

- Build the ingestion script and required-column validation.

Blocker:

- Need final raw CSV column names before locking schema.

### Jaswanth

Yesterday:

- Defined the first version of completion and silent drop-off labels and mapped required features.

Today:

- Implement learner-course labels and generate first feature table.

Blocker:

- Need latest activity date and course duration fields to set inactivity threshold.

### Shaswath

Yesterday:

- Created the dashboard mock UI and planned Streamlit pages.

Today:

- Scaffold Streamlit app and connect it to placeholder feature outputs.

Blocker:

- Need feature output schema from Jaswanth before final table wiring.

## Showcase Storyline

Use this narrative on Day 20:

1. The platform had activity, quiz, and completion data but no way to identify behaviours behind silent drop-off.
2. We built a data pipeline that cleans and aggregates learner-course activity.
3. We defined completion and silent drop-off labels.
4. We engineered behaviour features and ranked the strongest predictors.
5. We turned the analysis into a mentor-facing dashboard with risk reasons and intervention priorities.
6. We added validation so the dashboard does not silently trust bad data.

## Viva Preparation By Person

### Monesh

Bring:

- Schema explanation.
- One SQL query walkthrough.
- Data quality check examples.
- Example of a bad row and how the pipeline handles it.

### Jaswanth

Bring:

- Labeling rule explanation.
- Feature engineering walkthrough.
- Top three behaviour findings.
- Model or scoring method explanation.

### Shaswath

Bring:

- Dashboard walkthrough.
- Explanation of each screen's stakeholder purpose.
- GitHub Actions workflow explanation.
- README/deployment explanation.

## Daily Journal Prompts

Use specific entries, not generic ones.

Good examples:

- Today I inspected the session activity file and found that learner activity is stored at event level, so our feature table needs aggregation to learner-course level.
- I learned that silent drop-off cannot be defined only by completion status because some learners may still be active.
- The difficult part is choosing an inactivity threshold that is fair across course durations.
- Next session I will compare 14-day, 21-day, and 30-day inactivity windows before finalizing the label.
