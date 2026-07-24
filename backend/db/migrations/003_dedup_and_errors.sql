-- Migration 003: dedup + crawl error logging
ALTER TABLE contributions ADD COLUMN subject_hash TEXT;
CREATE UNIQUE INDEX IF NOT EXISTS idx_contributions_dedup ON contributions(document_id, subject_hash);

-- Populate subject_hash for existing rows
UPDATE contributions SET subject_hash = hex(substr(subject_text, 1, 200));

ALTER TABLE crawl_runs ADD COLUMN errors_detail TEXT;
