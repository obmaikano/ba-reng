-- Migration 016: structured storage for parser-extracted metadata.
--
-- committee_of_supply.py was concatenating budget/KPI figures as raw JSON strings
-- directly into subject_text (the same field rendered as prose in the feed/dashboard
-- and used for full-text search), which showed visible JSON syntax in the UI and
-- polluted FTS matching. Give parsers a dedicated column for structured extras instead.
ALTER TABLE contributions ADD COLUMN extracted_data TEXT;
