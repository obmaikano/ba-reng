-- Migration 012: Add evidence_type column to utterances for Hansard debate analysis
ALTER TABLE utterances ADD COLUMN evidence_type TEXT DEFAULT 'NORMATIVE'
    CHECK (evidence_type IN ('EMPIRICAL', 'STATUTORY', 'ANECDOTAL', 'NORMATIVE'));
ALTER TABLE utterances ADD COLUMN evidence_confidence REAL DEFAULT 0.0;
ALTER TABLE utterances ADD COLUMN word_count INTEGER DEFAULT 0;
CREATE INDEX IF NOT EXISTS idx_utterances_evidence ON utterances(evidence_type);
