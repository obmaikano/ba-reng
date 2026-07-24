-- Migration 011: Add procedural_score column to contribution_intents
ALTER TABLE contribution_intents ADD COLUMN procedural_score REAL DEFAULT 0.0;
