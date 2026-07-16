-- Populate learner-course aggregate metrics for the analysis handoff.
-- Owner: Monesh

DELETE FROM learner_course_aggregates;

WITH session_aggregates AS (
    SELECT
        learner_id,
        course_id,
        COUNT(session_id) AS total_sessions,
        COUNT(DISTINCT DATE(session_start_time)) AS active_days,
        AVG(
            CASE
                WHEN CAST(session_duration_minutes AS REAL) >= 0
                THEN CAST(session_duration_minutes AS REAL)
                ELSE NULL
            END
        ) AS average_session_duration,
        MAX(session_start_time) AS latest_activity_date
    FROM sessions
    GROUP BY learner_id, course_id
),
normalized_quiz_attempts AS (
    SELECT
        quiz_attempt_id,
        learner_id,
        course_id,
        attempt_time,
        attempt_number,
        CASE
            WHEN max_score IS NOT NULL AND CAST(max_score AS REAL) > 0
            THEN (CAST(score AS REAL) * 100.0) / CAST(max_score AS REAL)
            ELSE CAST(score AS REAL)
        END AS score_percent
    FROM quizzes
),
quiz_aggregates AS (
    SELECT
        learner_id,
        course_id,
        COUNT(quiz_attempt_id) AS quiz_attempt_count,
        AVG(score_percent) AS average_quiz_score
    FROM normalized_quiz_attempts
    GROUP BY learner_id, course_id
),
latest_quiz_attempts AS (
    SELECT
        learner_id,
        course_id,
        score_percent,
        ROW_NUMBER() OVER (
            PARTITION BY learner_id, course_id
            ORDER BY attempt_time DESC, CAST(attempt_number AS INTEGER) DESC
        ) AS latest_rank
    FROM normalized_quiz_attempts
),
latest_quiz_scores AS (
    SELECT
        learner_id,
        course_id,
        score_percent AS latest_quiz_score
    FROM latest_quiz_attempts
    WHERE latest_rank = 1
)
INSERT INTO learner_course_aggregates (
    learner_id,
    course_id,
    enrollment_date,
    completion_status,
    completion_date,
    progress_percent,
    total_sessions,
    active_days,
    average_session_duration,
    latest_activity_date,
    quiz_attempt_count,
    average_quiz_score,
    latest_quiz_score
)
SELECT
    e.learner_id,
    e.course_id,
    e.enrollment_date,
    e.completion_status,
    e.completion_date,
    CAST(e.progress_percent AS REAL) AS progress_percent,
    COALESCE(sa.total_sessions, 0) AS total_sessions,
    COALESCE(sa.active_days, 0) AS active_days,
    sa.average_session_duration,
    sa.latest_activity_date,
    COALESCE(qa.quiz_attempt_count, 0) AS quiz_attempt_count,
    qa.average_quiz_score,
    lq.latest_quiz_score
FROM enrollments e
LEFT JOIN session_aggregates sa
    ON e.learner_id = sa.learner_id
    AND e.course_id = sa.course_id
LEFT JOIN quiz_aggregates qa
    ON e.learner_id = qa.learner_id
    AND e.course_id = qa.course_id
LEFT JOIN latest_quiz_scores lq
    ON e.learner_id = lq.learner_id
    AND e.course_id = lq.course_id;
