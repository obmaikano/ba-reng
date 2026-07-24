"""Seed the database from remote/online sources.

Syncs Cabinet portfolios (Wikidata), gazetteer locations/organizations
(Wikidata), and Standing Orders procedural patterns (parliament.gov.bw).
"""

import logging

from backend.db.connection import get_connection
from backend.narrative.cabinet_fetcher import CabinetSyncEngine
from backend.narrative.gazetteer_fetcher import GazetteerSyncEngine
from backend.narrative.standing_orders_fetcher import StandingOrdersSyncEngine

logger = logging.getLogger('bareng.seed_remote')


def seed_remote() -> dict:
    """Fetch and sync remote data from online sources into the database.

    Returns counts of new records per source.
    """
    conn = get_connection()
    try:
        results: dict = {}

        # 1. Sync Cabinet ministries from Wikidata
        logger.info('Syncing Cabinet ministries from Wikidata...')
        cabinet = CabinetSyncEngine(conn)
        ministries = cabinet.fetch_remote_cabinet()
        cabinet_count = cabinet.sync_to_db(ministries)
        results['cabinet_ministries'] = cabinet_count
        logger.info('  %d new Cabinet ministries synced.', cabinet_count)

        # 2. Sync Gazetteer locations/organizations from Wikidata
        logger.info('Syncing gazetteer entities from Wikidata...')
        gazetteer = GazetteerSyncEngine(conn)
        gaz_count = gazetteer.update_gazetteer()
        results['gazetteer_entities'] = gaz_count
        logger.info('  Gazetteer sync complete: %s', gaz_count)

        # 3. Sync Standing Orders procedural patterns from parliament.gov.bw
        logger.info('Syncing Standing Orders patterns from parliament.gov.bw...')
        orders = StandingOrdersSyncEngine(conn)
        patterns = orders.fetch_remote_patterns()
        so_count = orders.sync_to_db(patterns)
        results['standing_orders_patterns'] = so_count
        logger.info('  %d Standing Orders patterns synced.', so_count)

        return results
    finally:
        conn.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    results = seed_remote()
    print(f'Remote seed complete: {results}')
