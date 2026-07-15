# Labeling Logic

Owner: Jaswanth

## Purpose

This document defines how each learner-course record will be labeled for analysis.

The labels are required before we can compare completed learners against silent drop-offs or build risk buckets for the dashboard.

## Output Grain

One row per learner-course enrollment.

## Labels

### completed

A learner is labeled `completed` when any of the following is true:

- `completion_status` is one of `completed`, `complete`, `passed`, or `certified`.
- `completion_date` is present.
- `progress_percent >= 90`.

### silent_dropoff

A learner is labeled `silent_dropoff` when all conditions are true:

- The learner is not completed.
- The learner had meaningful earlier activity.
- `days_since_last_activity >= inactivity_threshold_days`.

Initial threshold:

- 21 days.

This threshold can be adjusted after inspecting course duration and activity date range.

### at_risk

A learner is labeled `at_risk` when the learner is not completed and shows warning behaviour, such as:

- `days_since_last_activity >= 10`
- latest quiz score is below 50 percent
- progress appears stalled
- session activity has dropped sharply

### active

A learner is labeled `active` when the learner is not completed, not a silent drop-off, and not currently at risk.

### unstarted

A learner is labeled `unstarted` when there is an enrollment but no meaningful session, quiz, or progress activity.

## Meaningful Activity

Meaningful activity exists when at least one of these is true:

- total sessions is greater than zero
- quiz attempts are greater than zero
- progress percentage is greater than zero

## Label Priority

Labels must be assigned in this order:

1. completed
2. unstarted
3. silent_dropoff
4. at_risk
5. active

This prevents one learner-course row from receiving multiple statuses.

## Caveats

- The labels identify behavioural patterns, not causal proof.
- The inactivity threshold must be validated against the dataset date range.
- A learner can be inactive for valid reasons outside the dataset, so the dashboard should show risk reasons rather than final judgments.
