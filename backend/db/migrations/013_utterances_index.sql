-- Migration 013: Composite index for speaker scorecard JOIN path
CREATE INDEX IF NOT EXISTS idx_utterances_mp_agenda ON utterances(mp_id, agenda_id);
