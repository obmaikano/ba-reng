"""Dynamic Cabinet Portfolio Fetcher — fetches live Botswana ministry data from Wikidata SPARQL."""

import logging
import sqlite3
from typing import Any

import requests

from backend.db.connection import get_connection

logger = logging.getLogger('bareng.cabinet_fetcher')

WIKIDATA_SPARQL_URL = 'https://query.wikidata.org/sparql'

BOTSWANA_MINISTRIES_SPARQL = """
SELECT ?ministry ?ministryLabel ?shortName WHERE {
  ?ministry wdt:P17 wd:Q963 .
  ?ministry wdt:P31/wdt:P279* wd:Q192350 .
  OPTIONAL { ?ministry rdfs:label ?ministryLabel . FILTER(LANG(?ministryLabel) = "en") }
  OPTIONAL { ?ministry wdt:P1813 ?shortName . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
"""


class CabinetSyncEngine:
    """Fetches government ministries from Wikidata SPARQL and syncs to SQLite."""

    def __init__(self, conn: sqlite3.Connection | None = None):
        self._conn = conn or get_connection()
        self._own_conn = conn is None

    def close(self) -> None:
        if self._own_conn:
            self._conn.close()

    def fetch_remote_cabinet(self) -> list[dict[str, Any]]:
        """Query Wikidata for current Botswana Cabinet ministry definitions."""
        headers = {'User-Agent': 'BaRengParliamentBot/1.0 (https://bareng.bw)'}
        try:
            response = requests.get(
                WIKIDATA_SPARQL_URL,
                params={'query': BOTSWANA_MINISTRIES_SPARQL, 'format': 'json'},
                headers=headers,
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()

            results: list[dict[str, Any]] = []
            for binding in data.get('results', {}).get('bindings', []):
                name = binding.get('ministryLabel', {}).get('value', '').strip()
                short = binding.get('shortName', {}).get('value', '').strip()
                if name:
                    results.append({
                        'canonical_name': name,
                        'short_code': short or None,
                        'source_type': 'wikidata_fetch',
                    })
            logger.info('Fetched %d ministries from Wikidata.', len(results))
            return results
        except Exception:
            logger.exception('Failed to fetch Cabinet portfolios from Wikidata.')
            return []

    def sync_to_db(self, ministries: list[dict[str, Any]]) -> int:
        """Upsert fetched ministries into SQLite. Returns count of new ministries."""
        cursor = self._conn.cursor()
        new_count = 0

        for min_info in ministries:
            name = min_info['canonical_name']
            existing = cursor.execute(
                'SELECT id FROM ministries WHERE canonical_name = ?', (name,),
            ).fetchone()

            if existing:
                cursor.execute(
                    """UPDATE ministries SET last_seen_date = date('now') WHERE id = ?""",
                    (existing['id'],),
                )
            else:
                cursor.execute(
                    """INSERT INTO ministries (canonical_name, short_code, source_type, first_seen_date, last_seen_date)
                       VALUES (?, ?, 'wikidata_fetch', date('now'), date('now'))""",
                    (name, min_info.get('short_code')),
                )
                new_count += 1

        self._conn.commit()
        logger.info('Synced %d ministries (%d new) from Wikidata.', len(ministries), new_count)
        return new_count
