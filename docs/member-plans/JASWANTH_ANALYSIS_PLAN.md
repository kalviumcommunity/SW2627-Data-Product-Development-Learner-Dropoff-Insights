# Jaswanth - Data Analyst Plan

## Role

Jaswanth owns feature engineering, completion/drop-off labeling, and behaviour insight generation for Learner Drop-off Insights.

Primary responsibility:

- Convert clean learner activity data into explainable behaviour features and identify which behaviours predict completion versus silent drop-off.

## Why This Role Matters

The project is not only a dashboard project. The main intellectual output is the answer to the problem statement: which learning behaviours actually separate course completers from silent drop-offs.

## Owned Deliverables

### 1. Labeling Logic

Define learner-course status labels:

- completed
- active
- at_risk
- silent_dropoff
- unstarted, if needed

Initial working definition:

- Completed: learner has explicit completion flag or reaches the agreed completion threshold.
- Silent drop-off: learner is not completed, had meaningful earlier activity, and has no recent activity beyond the inactivity threshold.
- Active: learner is not completed but has recent activity.
- At risk: learner is active or inactive and shows behaviours associated with future drop-off.

Expected output:

- Labeling logic document.
- Label generation script under `src/features/`.
- One status per learner-course row.

### 2. Feature Engineering

Build features such as:

- total_sessions
- active_days
- sessions_per_week
- average_session_duration
- days_since_last_activity
- longest_inactivity_gap
- current_inactivity_gap
- session_streak_max
- quiz_attempt_count
- average_quiz_score
- latest_quiz_score
- quiz_score_trend
- retry_rate
- progress_velocity
- activity_decay_rate
- early_engagement_score
- consistency_score

Expected output:

- Feature engineering script.
- Feature table with one row per learner-course pair.
- Feature dictionary explaining meaning and calculation.

### 3. Comparative Analysis

Compare completed learners and silent drop-offs across:

- session consistency
- inactivity gaps
- quiz performance
- retry behaviour
- progress velocity
- early engagement

Expected output:

- Summary tables.
- Ranked difference table.
- Short written findings.

### 4. Predictive Behaviour Ranking

Use an interpretable method:

- correlation ranking
- logistic regression
- simple decision tree
- rule-based risk score, if data volume is too small for modeling

Expected output:

- behaviour_driver_rankings table
- risk_score per learner-course
- risk_bucket: high, medium, low
- primary_risk_reason
- suggested_action

## Handoff Contracts

### From Monesh

Needs a clean learner-course aggregate table containing:

- learner_id
- course_id
- completion_status
- progress_percent
- latest_activity_date
- session aggregates
- quiz aggregates

### To Shaswath

Provide dashboard-ready outputs:

- learner_features.csv or SQLite table
- behaviour_driver_rankings.csv or SQLite table
- learner_risk_scores.csv or SQLite table

Required learner risk fields:

- learner_id
- course_id
- risk_score
- risk_bucket
- last_activity_date
- days_inactive
- latest_quiz_score
- primary_risk_reason
- suggested_action

## First PR Scope

Branch name suggestion:

```text
jaswanth/analysis-plan
```

PR title:

```text
Add analysis plan for learner drop-off behaviour features
```

This PR includes:

- Jaswanth's analysis responsibilities.
- Label definitions.
- Feature list.
- Behaviour ranking method.
- Handoff contract for dashboard outputs.

## Future Implementation PRs

1. Add label generation script.
2. Add feature engineering script.
3. Add completed versus drop-off comparison.
4. Add behaviour driver ranking.
5. Add risk score and suggested action outputs.

## Acceptance Criteria

- Every learner-course row receives exactly one label.
- Feature output has one row per learner-course pair.
- Top behaviour drivers include direction and interpretation.
- Risk scores are explainable.
- Findings separate correlation from causation.

## Viva Preparation

Jaswanth should be ready to explain:

- Why the label definition is defensible.
- How silent drop-off differs from not started.
- How each major feature is calculated.
- Which behaviours best predict completion or drop-off.
- Why the selected analysis method is interpretable.
- What limitations remain in the analysis.

## Current Open Questions

1. Does the dataset include an explicit completion flag?
2. What inactivity threshold is fair for the course duration?
3. Are quiz attempts comparable across courses?
4. Is there enough data for a model, or should we use rule-based scoring?
5. Which risk reasons are most actionable for mentors?
