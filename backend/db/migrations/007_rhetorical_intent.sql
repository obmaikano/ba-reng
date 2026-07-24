-- Migration 007: Rhetorical intent classifier — patterns + per-contribution intent scoring

CREATE TABLE IF NOT EXISTS rhetorical_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    intent_category TEXT NOT NULL CHECK (intent_category IN ('COMPLAINT', 'SOLUTION', 'INQUIRY', 'ENDORSEMENT', 'PROCEDURAL')),
    pattern_regex TEXT NOT NULL UNIQUE,
    language TEXT NOT NULL DEFAULT 'en' CHECK (language IN ('en', 'tn', 'mixed')),
    weight REAL NOT NULL DEFAULT 1.0,
    source_type TEXT NOT NULL DEFAULT 'seed' CHECK (source_type IN ('seed', 'standing_orders_fetch', 'auto_harvested', 'manual_admin')),
    last_synced_at TEXT DEFAULT (datetime('now')),
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS contribution_intents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contribution_id INTEGER NOT NULL REFERENCES contributions(id) ON DELETE CASCADE,
    primary_intent TEXT NOT NULL CHECK (primary_intent IN ('COMPLAINT', 'SOLUTION', 'INQUIRY', 'ENDORSEMENT')),
    constructiveness_ratio REAL NOT NULL DEFAULT 50.0,
    complaint_score REAL NOT NULL DEFAULT 0.0,
    solution_score REAL NOT NULL DEFAULT 0.0,
    inquiry_score REAL NOT NULL DEFAULT 0.0,
    endorsement_score REAL NOT NULL DEFAULT 0.0,
    matched_pattern_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(contribution_id)
);

CREATE INDEX IF NOT EXISTS idx_rhet_patterns_category ON rhetorical_patterns(intent_category);
CREATE INDEX IF NOT EXISTS idx_rhet_patterns_weight ON rhetorical_patterns(weight);
CREATE INDEX IF NOT EXISTS idx_contribution_intents_intent ON contribution_intents(primary_intent);
CREATE INDEX IF NOT EXISTS idx_contribution_intents_ratio ON contribution_intents(constructiveness_ratio);
