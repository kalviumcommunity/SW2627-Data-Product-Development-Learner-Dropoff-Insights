# Feature Dictionary

Owner: Shaswath

## Purpose

This document defines the learner behaviour features used for completion and drop-off analysis. All features are calculated at the learner-course grain (`learner_id`, `course_id`).

To ensure clarity in ownership and data dependencies, features are categorized by their origin: **Core Aggregates** (from the data engineering stage), **Engineered Risk Features** (calculated in Python), and **Advanced Features** (post-MVP/future roadmap).

---

## 1. Core Aggregates (Direct Database Fields)
These features are pre-aggregated by the data engineer (Monesh) and provided in the staging input table `learner_course_aggregates`.

| Feature | Origin / Source Table Column | Meaning / Description | Direction to Watch |
| --- | --- | --- | --- |
| `total_sessions` | `total_sessions` | Total number of recorded user sessions. | Higher values strongly correlate with completion. |
| `active_days` | `active_days` | Count of unique calendar days on which the user had active sessions. | High active days indicate persistent learning. |
| `average_session_duration` | `average_session_duration` | Mean duration (in minutes) across all sessions. | Extremely low averages (<2-3 min) suggest weak engagement. |
| `latest_activity_date` | `latest_activity_date` | Date of the learner's most recent session activity. | Primary marker for computing inactivity. |
| `quiz_attempt_count` | `quiz_attempt_count` | Number of quiz attempts recorded for the learner. | Reflects effort and course interaction. |
| `average_quiz_score` | `average_quiz_score` | Mean score across all quizzes attempted. | Low scores indicate academic struggles. |
| `latest_quiz_score` | `latest_quiz_score` | Score of the most recent quiz attempt. | Drop in latest score signals sudden difficulty. |
| `progress_percent` | `progress_percent` | The current percent completion of the course (0.0 to 1.0). | Lower or stalled progress indicates drop-off risk. |
| `enrollment_date` | `enrollment_date` | The date the student enrolled in the course. | Used to define the start of active learning. |
| `completion_status` | `completion_status` | Text status indicating completion (e.g. `'completed'`). | Direct label source for successful learners. |
| `completion_date` | `completion_date` | Date when the course was finished. | Used as verification of completion. |

---

## 2. Engineered Risk Features (Calculated in Python)
These features are calculated dynamically by `src/features/build_features.py`.

| Feature | Type | Formula / Source | Meaning |
| --- | --- | --- | --- |
| `days_since_last_activity` | Integer | `anchor_date - latest_activity_date` (where `anchor_date` is the max active date in the dataset) | Time elapsed since the user last accessed the course. Higher values indicate drop-off. |
| `learner_status` | String | Evaluated sequentially: `completed`, `unstarted`, `silent_dropoff`, `at_risk`, `active` | The resolved status bucket of the learner. |
| `risk_score` | Integer | Rule-based sum (0 to 100) based on inactivity gap, stalled progress, and poor quiz performance. | Metric of risk severity; used for sorting outreach lists. |
| `risk_bucket` | String | Categorized: `low` (0-39), `medium` (40-69), `high` (70-100) | Simplified triage level for success mentors. |
| `primary_risk_reason` | String | High-scoring risk trigger (e.g. `'Activity gap is growing'`) | Plain-language reason explaining the risk score. |
| `suggested_action` | String | Mapping from the primary risk reason | Actionable outreach task for success mentors. |

---

## 3. Advanced Features (Post-MVP Roadmap)
These features require granular, raw event logs rather than pre-aggregated counts. They are out-of-scope for the first MVP release but are planned for future iterations.

- **`session_streak_max`**: Longest consecutive daily streak of session activity. Requires profiling the full `sessions` event table.
- **`quiz_score_trend`**: Slope of quiz scores over time (latest score minus average score). Signals whether performance is improving or declining.
- **`retry_rate`**: The ratio of quiz attempts to unique quiz IDs, especially following a failing score. Measures resilience.
- **`progress_velocity`**: Progress percent divided by days since enrollment. Shows how quickly the learner moves through modules.

---

## 4. MVP Output Schema (`learner_features.csv`)

The feature engineering output file **`data/processed/learner_features.csv`** is guaranteed to produce the following 12 columns to support dashboard metrics and filters:

1. **`learner_id`**: Learner identifier.
2. **`course_id`**: Course identifier.
3. **`learner_status`**: Segment classification (`completed`, `unstarted`, `silent_dropoff`, `at_risk`, `active`).
4. **`risk_score`**: Priority risk number (0-100).
5. **`risk_bucket`**: Classification (`low`, `medium`, `high`).
6. **`days_since_last_activity`**: Computed days inactive.
7. **`total_sessions`**: User activity count.
8. **`active_days`**: Unique days active.
9. **`average_quiz_score`**: Learner academic average.
10. **`latest_quiz_score`**: Last quiz result.
11. **`primary_risk_reason`**: Explanatory reason for risk.
12. **`suggested_action`**: Mentor recommended action.

---

## 5. Potential Blockers

> [!WARNING]
> **Schema Dependability**:
> If the data engineer's schema lacks the core metrics `progress_percent`, `latest_activity_date`, or `latest_quiz_score`, the Python scripts will fall back to safety defaults (`0.0`, `None`, and `None` respectively), which will result in default neutral values (e.g., low risk, no action suggested). Please coordinate schema alignment on these fields to guarantee insight validity.
