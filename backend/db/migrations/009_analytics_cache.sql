-- Migration 009: Analytics cache table for pre-computed query results
CREATE TABLE IF NOT EXISTS analytics_cache (
    cache_key TEXT PRIMARY KEY,
    json_payload TEXT NOT NULL,
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cache_expires ON analytics_cache(expires_at);
