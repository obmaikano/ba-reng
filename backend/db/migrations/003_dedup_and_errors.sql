-- Migration 003: dedup + crawl error logging
ALTER TABLE contributions ADD COLUMN subject_hash TEXT;
CREATE UNIQUE INDEX IF NOT EXISTS idx_contributions_dedup ON contributions(document_id, subject_hash);

-- Populate subject_hash for existing rows (must match hashlib.sha256(...).hexdigest()
-- computed in backend/parse/run.py, so a re-parsed document dedupes against its
-- original insert instead of creating a duplicate row).
UPDATE contributions SET subject_hash = SHA256_HEX(substr(subject_text, 1, 200));

ALTER TABLE crawl_runs ADD COLUMN errors_detail TEXT;
