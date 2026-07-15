# Feature Dictionary

Owner: Shaswath

## Purpose

This document defines the learner behaviour features used for completion and drop-off analysis.

All features are calculated at learner-course grain.

## Session Features

| Feature | Meaning | Direction to watch |
| --- | --- | --- |
| total_sessions | Number of recorded sessions | Higher usually supports completion |
| active_days | Number of unique active days | Higher usually supports completion |
| average_session_duration | Average minutes per session | Very low values may indicate weak engagement |
| days_since_last_activity | Days since latest known activity | Higher indicates drop-off risk |
| session_streak_max | Longest streak of active days | Higher usually supports completion |

## Quiz Features

| Feature | Meaning | Direction to watch |
| --- | --- | --- |
| quiz_attempt_count | Number of quiz attempts | Higher may indicate effort |
| average_quiz_score | Mean quiz score | Lower may indicate academic difficulty |
| latest_quiz_score | Most recent quiz score | Low latest score can signal risk |
| quiz_score_trend | Latest score minus average score | Negative trend may indicate declining performance |
| retry_rate | Attempts after weak quiz outcomes | Higher retry rate may support completion |

## Progress Features

| Feature | Meaning | Direction to watch |
| --- | --- | --- |
| progress_percent | Current course progress | Low or stalled progress indicates risk |
| progress_velocity | Progress per day since enrollment | Low values indicate slow movement |
| progress_stalled_flag | No recent activity with incomplete progress | True indicates risk |

## Combined Features

| Feature | Meaning | Direction to watch |
| --- | --- | --- |
| early_engagement_score | Combined early sessions, quiz attempts, and progress | Low score indicates weak activation |
| consistency_score | Activity consistency based on active days and inactivity gap | Lower score indicates drop-off risk |
| risk_score | Rule-based score from risk signals | Higher means higher intervention priority |
| primary_risk_reason | Main plain-language reason for risk | Used in dashboard table |

## First MVP Feature Output

The first implementation should produce:

- learner_id
- course_id
- learner_status
- risk_score
- risk_bucket
- days_since_last_activity
- total_sessions
- active_days
- average_quiz_score
- latest_quiz_score
- primary_risk_reason
- suggested_action
