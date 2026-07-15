# Dashboard Requirements

Owner: Jaswanth

## Purpose

The Streamlit dashboard turns the learner drop-off analysis into a mentor-facing product.

The dashboard should answer:

- How serious is the current drop-off problem?
- Which behaviours are most linked to drop-off?
- Which learners need attention first?

## Pages

### Overview

Required components:

- Completion rate
- Silent drop-off rate
- High-risk learner count
- Median inactivity gap
- Risk bucket distribution

Input data:

- `data/processed/learner_features.csv`

### Behaviour Drivers

Required components:

- Ranked behaviour driver chart
- Completed versus silent drop-off comparison
- Plain-language interpretation

Input data:

- `data/processed/behaviour_driver_rankings.csv`

Fallback:

- If the rankings file does not exist yet, show a waiting state.

### Learner Risk List

Required components:

- Learner ID
- Course ID
- Risk bucket
- Risk score
- Days inactive
- Latest quiz score
- Primary risk reason
- Suggested action

Input data:

- `data/processed/learner_features.csv`

## MVP Acceptance Criteria

- Dashboard opens with `streamlit run src/dashboard/app.py`.
- If processed data files are missing, the dashboard shows useful placeholder messages instead of crashing.
- Learner risk list defaults to highest risk first.
- Main pages match the approved mock UI.
- README explains the local dashboard command.

## Handoff Needed From Team

From Monesh:

- clean SQLite database or aggregate CSV

From Shaswath:

- learner feature output
- behaviour driver ranking output
- risk score and risk reason fields
