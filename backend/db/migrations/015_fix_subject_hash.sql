-- Migration 015: recompute subject_hash with SHA-256.
--
-- Migration 003 originally backfilled subject_hash with hex(substr(subject_text, 1, 200))
-- (a raw hex encoding of the text, not a hash), while every new insert since has used
-- hashlib.sha256(...).hexdigest() in backend/parse/run.py. The two schemes never match,
-- so re-parsing an already-imported document could not detect it as a duplicate against
-- the dedup UNIQUE(document_id, subject_hash) index. Recompute all rows with the same
-- SHA-256 formula so historical and future rows are dedupable against each other.
UPDATE contributions SET subject_hash = SHA256_HEX(substr(subject_text, 1, 200));
