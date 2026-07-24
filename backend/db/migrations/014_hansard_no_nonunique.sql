-- Migration 014: Remove UNIQUE constraint on hansard_no (duplicate variant PDFs exist)
PRAGMA foreign_keys=OFF;
CREATE TABLE IF NOT EXISTS hansard_sessions_v2 (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id),
    hansard_no INTEGER NOT NULL,
    session_date TEXT NOT NULL,
    meeting_description TEXT,
    sitting_time TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
INSERT INTO hansard_sessions_v2 SELECT * FROM hansard_sessions;
DROP TABLE hansard_sessions;
ALTER TABLE hansard_sessions_v2 RENAME TO hansard_sessions;
CREATE INDEX IF NOT EXISTS idx_hansard_sessions_date ON hansard_sessions(session_date);
PRAGMA foreign_keys=ON;
