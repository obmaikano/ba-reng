-- Migration 010: Contribution performance indexes + data quality fixes
CREATE INDEX IF NOT EXISTS idx_contributions_mp_id ON contributions(mp_id);
CREATE INDEX IF NOT EXISTS idx_contributions_date ON contributions(date);
CREATE INDEX IF NOT EXISTS idx_contributions_type ON contributions(contribution_type);
CREATE INDEX IF NOT EXISTS idx_contributions_mp_date ON contributions(mp_id, date);
CREATE INDEX IF NOT EXISTS idx_contributions_doc_id ON contributions(document_id);
