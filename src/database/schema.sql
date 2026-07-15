-- SQLite schema for Learner Drop-off Insights.
-- Owner: Monesh

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS learners (
    learner_id TEXT PRIMARY KEY,
    signup_date TEXT,
    cohort TEXT,
    region TEXT
);

CREATE TABLE IF NOT EXISTS courses (
    course_id TEXT PRIMARY KEY,
    course_name TEXT NOT NULL,
    category TEXT,
    expected_duration_days INTEGER
);

CREATE TABLE IF NOT EXISTS enrollments (
    learner_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    enrollment_date TEXT,
    progress_percent REAL,
    completion_status TEXT,
    completion_date TEXT,
    PRIMARY KEY (learner_id, course_id),
    FOREIGN KEY (learner_id) REFERENCES learners (learner_id),
    FOREIGN KEY (course_id) REFERENCES courses (course_id)
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    learner_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    session_start_time TEXT NOT NULL,
    session_duration_minutes REAL,
    module_id TEXT,
    content_type TEXT,
    FOREIGN KEY (learner_id) REFERENCES learners (learner_id),
    FOREIGN KEY (course_id) REFERENCES courses (course_id)
);

CREATE TABLE IF NOT EXISTS quizzes (
    quiz_attempt_id TEXT PRIMARY KEY,
    learner_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    quiz_id TEXT NOT NULL,
    attempt_time TEXT NOT NULL,
    score REAL,
    max_score REAL,
    attempt_number INTEGER,
    FOREIGN KEY (learner_id) REFERENCES learners (learner_id),
    FOREIGN KEY (course_id) REFERENCES courses (course_id)
);

CREATE TABLE IF NOT EXISTS learner_course_aggregates (
    learner_id TEXT NOT NULL,
    course_id TEXT NOT NULL,
    enrollment_date TEXT,
    completion_status TEXT,
    completion_date TEXT,
    progress_percent REAL,
    total_sessions INTEGER DEFAULT 0,
    active_days INTEGER DEFAULT 0,
    average_session_duration REAL,
    latest_activity_date TEXT,
    quiz_attempt_count INTEGER DEFAULT 0,
    average_quiz_score REAL,
    latest_quiz_score REAL,
    refreshed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (learner_id, course_id),
    FOREIGN KEY (learner_id) REFERENCES learners (learner_id),
    FOREIGN KEY (course_id) REFERENCES courses (course_id)
);

CREATE TABLE IF NOT EXISTS data_quality_results (
    check_id INTEGER PRIMARY KEY AUTOINCREMENT,
    check_name TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('blocking', 'warning')),
    status TEXT NOT NULL CHECK (status IN ('passed', 'failed', 'warning')),
    failed_row_count INTEGER NOT NULL DEFAULT 0,
    message TEXT,
    checked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sessions_learner_course
ON sessions (learner_id, course_id);

CREATE INDEX IF NOT EXISTS idx_sessions_start_time
ON sessions (session_start_time);

CREATE INDEX IF NOT EXISTS idx_quizzes_learner_course
ON quizzes (learner_id, course_id);

CREATE INDEX IF NOT EXISTS idx_quizzes_attempt_time
ON quizzes (attempt_time);
