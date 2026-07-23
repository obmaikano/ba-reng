CREATE TABLE IF NOT EXISTS mps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    constituency TEXT NOT NULL UNIQUE,
    party TEXT NOT NULL,
    photo_url TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_url TEXT NOT NULL,
    title TEXT NOT NULL,
    doc_type TEXT NOT NULL,
    published_date TEXT,
    raw_text_hash TEXT UNIQUE,
    file_path TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS contributions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id),
    mp_id INTEGER REFERENCES mps(id),
    contribution_type TEXT NOT NULL,
    subject_text TEXT NOT NULL,
    ministry_addressed TEXT,
    date TEXT NOT NULL,
    raw_match_name TEXT NOT NULL,
    raw_constituency TEXT,
    source_url TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS crawl_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    source TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'RUNNING',
    new_documents INTEGER DEFAULT 0,
    errors INTEGER DEFAULT 0,
    run_type TEXT DEFAULT 'scheduled'
);

CREATE TABLE IF NOT EXISTS entity_review_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_match_name TEXT NOT NULL,
    document_id INTEGER REFERENCES documents(id),
    contribution_id INTEGER REFERENCES contributions(id),
    status TEXT NOT NULL DEFAULT 'UNRESOLVED',
    resolved_mp_id INTEGER REFERENCES mps(id),
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sit_calendar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sitting_date TEXT NOT NULL UNIQUE,
    parliament_session TEXT,
    source_url TEXT
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    display_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'viewer',
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    last_login_at TEXT
);

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    token TEXT NOT NULL UNIQUE,
    expires_at TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_contributions_mp_id ON contributions(mp_id);
CREATE INDEX IF NOT EXISTS idx_contributions_date ON contributions(date);
CREATE INDEX IF NOT EXISTS idx_contributions_type ON contributions(contribution_type);
CREATE INDEX IF NOT EXISTS idx_entity_review_status ON entity_review_queue(status);
