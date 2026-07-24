"""Dynamic Gazetteer Fetcher — fetches Botswana locations and organizations from Wikidata SPARQL."""

import logging
import sqlite3
from typing import Any

import requests

from backend.db.connection import get_connection

logger = logging.getLogger('bareng.gazetteer_fetcher')

WIKIDATA_SPARQL_URL = 'https://query.wikidata.org/sparql'

BOTSWANA_LOCATIONS_SPARQL = """
SELECT DISTINCT ?item ?itemLabel WHERE {
  ?item wdt:P17 wd:Q963 .
  ?item wdt:P31/wdt:P279* wd:Q486972 .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT 200
"""

BOTSWANA_ORGANIZATIONS_SPARQL = """
SELECT DISTINCT ?item ?itemLabel WHERE {
  ?item wdt:P17 wd:Q963 .
  ?item wdt:P31/wdt:P279* ?type .
  VALUES ?type { wd:Q327333 wd:Q43229 wd:Q2659904 wd:Q192350 wd:Q245065 }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT 100
"""

BOTSWANA_CONSTITUENCIES_SPARQL = """
SELECT DISTINCT ?item ?itemLabel WHERE {
  ?item wdt:P31 wd:Q5149480 .
  ?item wdt:P17 wd:Q963 .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
"""


class GazetteerSyncEngine:
    """Fetches Botswana place names and organizations from Wikidata SPARQL."""

    HEADERS = {'User-Agent': 'BaRengParliamentBot/1.0 (https://bareng.bw)'}

    def __init__(self, conn: sqlite3.Connection | None = None):
        self._conn = conn or get_connection()
        self._own_conn = conn is None

    def close(self) -> None:
        if self._own_conn:
            self._conn.close()

    def _run_sparql(self, query: str) -> list[dict[str, str]]:
        try:
            response = requests.get(
                WIKIDATA_SPARQL_URL,
                params={'query': query, 'format': 'json'},
                headers=self.HEADERS,
                timeout=20,
            )
            response.raise_for_status()
            data = response.json()
            results: list[dict[str, str]] = []
            for binding in data.get('results', {}).get('bindings', []):
                label = binding.get('itemLabel', {}).get('value', '').strip()
                if label and len(label) > 1:
                    results.append({'term': label})
            return results
        except Exception:
            logger.exception('Wikidata SPARQL query failed.')
            return []

    def fetch_locations(self) -> list[dict[str, str]]:
        """Fetch Botswana settlements (cities, towns, villages)."""
        logger.info('Fetching Botswana locations from Wikidata...')
        results = self._run_sparql(BOTSWANA_LOCATIONS_SPARQL)
        logger.info('Fetched %d locations.', len(results))
        return results

    def fetch_organizations(self) -> list[dict[str, str]]:
        """Fetch Botswana government bodies, agencies, and state-owned enterprises."""
        logger.info('Fetching Botswana organizations from Wikidata...')
        results = self._run_sparql(BOTSWANA_ORGANIZATIONS_SPARQL)
        logger.info('Fetched %d organizations.', len(results))
        return results

    def fetch_constituencies(self) -> list[dict[str, str]]:
        """Fetch Botswana parliamentary constituencies."""
        logger.info('Fetching Botswana constituencies from Wikidata...')
        results = self._run_sparql(BOTSWANA_CONSTITUENCIES_SPARQL)
        logger.info('Fetched %d constituencies.', len(results))
        return results

    def sync_all(self) -> dict[str, int]:
        """Fetch and sync all location + org entities into parliamentary_glossary."""
        cursor = self._conn.cursor()

        categories = [
            ('location', self.fetch_locations()),
            ('organization', self.fetch_organizations()),
            ('location', self.fetch_constituencies()),
        ]

        totals: dict[str, int] = {}
        for category, entities in categories:
            count = 0
            for entity in entities:
                term = entity['term']
                try:
                    cursor.execute(
                        """INSERT INTO parliamentary_glossary
                           (term_setswana, term_english, category)
                           VALUES (?, ?, ?)
                           ON CONFLICT(term_setswana) DO NOTHING""",
                        (term, term, category),
                    )
                    count += cursor.rowcount
                except sqlite3.IntegrityError:
                    pass
            totals[category] = count
            self._conn.commit()
            logger.info('Synced %d new %s entries to glossary.', count, category)

        return totals

    def update_gazetteer(self) -> dict[str, int]:
        """Public entry point: sync all gazetteer entities from Wikidata."""
        return self.sync_all()
