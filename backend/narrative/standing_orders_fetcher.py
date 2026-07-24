"""Dynamic Standing Orders Sync Engine — fetches procedural debate formulas from Parliament."""

import logging
import sqlite3
from typing import Any

import requests

from backend.db.connection import get_connection

logger = logging.getLogger('bareng.procedural_sync')

PARLIAMENT_PROCEDURAL_ENDPOINT = 'https://www.parliament.gov.bw/api/v1/procedural-glossary'


class StandingOrdersSyncEngine:
    """Fetches Standing Orders debate rule patterns and syncs to SQLite."""

    def __init__(self, conn: sqlite3.Connection | None = None):
        self._conn = conn or get_connection()
        self._own_conn = conn is None

    def close(self) -> None:
        if self._own_conn:
            self._conn.close()

    def fetch_remote_patterns(self) -> list[dict[str, Any]]:
        """Fetch Standing Orders procedural formulas from Parliament API."""
        headers = {'User-Agent': 'BaRengParliamentBot/1.0 (https://bareng.bw)'}
        try:
            response = requests.get(
                PARLIAMENT_PROCEDURAL_ENDPOINT,
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            patterns = data.get('patterns', [])
            logger.info('Fetched %d patterns from Standing Orders API.', len(patterns))
            return patterns
        except Exception:
            logger.info('Standing Orders API unreachable — using DB-cached patterns.')
            return []

    def sync_to_db(self, patterns: list[dict[str, Any]]) -> int:
        """Upsert remote patterns into rhetorical_patterns."""
        if not patterns:
            return 0

        cursor = self._conn.cursor()
        upserted = 0

        for p in patterns:
            category = p.get('category', 'PROCEDURAL')
            regex_pat = p.get('pattern', '').strip()
            weight = float(p.get('weight', 1.0))
            lang = p.get('language', 'en')

            if not regex_pat or len(regex_pat) < 4:
                continue

            try:
                cursor.execute(
                    """INSERT INTO rhetorical_patterns
                       (intent_category, pattern_regex, language, weight, source_type)
                       VALUES (?, ?, ?, ?, 'standing_orders_fetch')
                       ON CONFLICT(pattern_regex) DO UPDATE SET
                           weight = excluded.weight,
                           last_synced_at = datetime('now')
                       WHERE source_type != 'manual_admin'""",
                    (category, regex_pat, lang, weight),
                )
                upserted += 1
            except sqlite3.IntegrityError:
                pass

        self._conn.commit()
        logger.info('Synced %d Standing Orders patterns to DB.', upserted)
        return upserted
