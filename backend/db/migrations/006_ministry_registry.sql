-- Migration 006: Dynamic ministry registry, auto-harvested keywords, deferred questions tracker
CREATE TABLE IF NOT EXISTS ministries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_name TEXT UNIQUE NOT NULL,
    short_code TEXT,
    source_type TEXT NOT NULL,
    first_seen_date TEXT NOT NULL,
    last_seen_date TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS ministry_keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ministry_id INTEGER NOT NULL REFERENCES ministries(id) ON DELETE CASCADE,
    keyword TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    source_type TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(ministry_id, keyword)
);

CREATE TABLE IF NOT EXISTS deferred_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contribution_id INTEGER REFERENCES contributions(id),
    ministry_id INTEGER REFERENCES ministries(id),
    notice_number INTEGER,
    original_date TEXT NOT NULL,
    deferred_date TEXT,
    status TEXT DEFAULT 'DEFERRED',
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS parliamentary_glossary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term_setswana TEXT UNIQUE NOT NULL,
    term_english TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'general',
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_ministries_name ON ministries(canonical_name);
CREATE INDEX IF NOT EXISTS idx_ministries_active ON ministries(is_active);
CREATE INDEX IF NOT EXISTS idx_keywords_term ON ministry_keywords(keyword);
CREATE INDEX IF NOT EXISTS idx_deferred_status ON deferred_questions(status);
CREATE INDEX IF NOT EXISTS idx_glossary_setswana ON parliamentary_glossary(term_setswana);
CREATE INDEX IF NOT EXISTS idx_glossary_english ON parliamentary_glossary(term_english);
