-- Migration 008: Add language + cleaned_text columns to utterances per architecture spec
ALTER TABLE utterances ADD COLUMN language TEXT DEFAULT 'en' CHECK (language IN ('en', 'tn', 'mixed'));
ALTER TABLE utterances ADD COLUMN cleaned_text TEXT;
CREATE INDEX IF NOT EXISTS idx_utterances_language ON utterances(language);
