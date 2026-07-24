-- Migration 017: Enforce one hansard_sessions row per document_id, so
-- reprocessing a document (manual rerun, retry after partial failure) can be
-- detected and skipped instead of silently inserting a duplicate full set of
-- session/agenda_item/utterance rows.
PRAGMA foreign_keys=OFF;
CREATE TABLE IF NOT EXISTS hansard_sessions_v3 (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL UNIQUE REFERENCES documents(id),
    hansard_no INTEGER NOT NULL,
    session_date TEXT NOT NULL,
    meeting_description TEXT,
    sitting_time TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
INSERT INTO hansard_sessions_v3 SELECT * FROM hansard_sessions;
DROP TABLE hansard_sessions;
ALTER TABLE hansard_sessions_v3 RENAME TO hansard_sessions;
CREATE INDEX IF NOT EXISTS idx_hansard_sessions_date ON hansard_sessions(session_date);
PRAGMA foreign_keys=ON;
