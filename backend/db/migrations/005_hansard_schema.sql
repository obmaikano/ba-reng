-- Migration 005: Hansard free-text transcript schema
CREATE TABLE IF NOT EXISTS hansard_sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id),
    hansard_no INTEGER UNIQUE NOT NULL,
    session_date TEXT NOT NULL,
    meeting_description TEXT,
    sitting_time TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS agenda_items (
    agenda_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES hansard_sessions(session_id),
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    sequence_order INTEGER NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS utterances (
    utterance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    agenda_id INTEGER NOT NULL REFERENCES agenda_items(agenda_id),
    mp_id INTEGER REFERENCES mps(id),
    speaker_raw_title TEXT,
    speaker_name TEXT NOT NULL,
    speech_type TEXT NOT NULL,
    speech_text TEXT NOT NULL,
    procedural_notes TEXT,
    extracted_entities TEXT,
    sequence_order INTEGER NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_utterances_agenda_id ON utterances(agenda_id);
CREATE INDEX IF NOT EXISTS idx_utterances_mp_id ON utterances(mp_id);
CREATE INDEX IF NOT EXISTS idx_utterances_speech_type ON utterances(speech_type);
CREATE INDEX IF NOT EXISTS idx_agenda_items_session_id ON agenda_items(session_id);
CREATE INDEX IF NOT EXISTS idx_hansard_sessions_date ON hansard_sessions(session_date);
