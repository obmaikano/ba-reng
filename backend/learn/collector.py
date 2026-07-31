"""System collectors — harvest durable knowledge from the live database.

The system learns from its own operational data:
  - Entity resolutions (raw_match_name -> resolved MP) from the review queue
  - Canonical ministry keyword mappings from the static seed
  - Data quality snapshot facts (coverage, resolution rate)
"""

from __future__ import annotations

import json
import logging
import sqlite3
from typing import Any

from backend.learn.connection import LearnConnection
from backend.learn.memory import Memory

logger = logging.getLogger(__name__)


class SystemCollector:
    """Collect durable facts from the app database into the memory store."""

    def __init__(self) -> None:
        """Initialize the collector with the shared connection and memory."""
        self._conn = LearnConnection.get()
        self._memory = Memory()

    def collect_entity_resolutions(self) -> int:
        """Store resolved entity-review entries as memory facts.

        Returns:
            Number of entity-resolution facts stored.
        """
        try:
            rows = self._conn.execute(
                """
                SELECT q.raw_match_name, m.name
                FROM entity_review_queue q
                JOIN mps m ON m.id = q.resolved_mp_id
                WHERE q.status = 'RESOLVED' AND q.resolved_mp_id IS NOT NULL
                """,
            ).fetchall()
        except sqlite3.Error as exc:
            logger.error('Entity resolution collect failed: %s', exc)
            return 0

        n = 0
        for row in rows:
            raw = (row['raw_match_name'] or '').strip()
            if not raw:
                continue
            self._memory.store(
                key=f'entity:{raw}',
                value=f'{raw} resolves to {row["name"]}',
                category='fact',
                confidence=0.95,
                source='entity_review_queue',
            )
            n += 1
        return n

    def collect_ministry_keywords(self) -> int:
        """Store canonical ministry keyword mappings as memory patterns.

        Returns:
            Number of ministry keyword patterns stored.
        """
        try:
            rows = self._conn.execute(
                """
                SELECT k.keyword, m.canonical_name
                FROM ministry_keywords k
                JOIN ministries m ON m.id = k.ministry_id
                WHERE k.source_type = 'static_seed'
                """,
            ).fetchall()
        except sqlite3.Error as exc:
            logger.error('Ministry keyword collect failed: %s', exc)
            return 0

        n = 0
        for row in rows:
            keyword = (row['keyword'] or '').strip()
            if not keyword:
                continue
            self._memory.store(
                key=f'ministry_keyword:{keyword}',
                value=f'Keyword "{keyword}" maps to {row["canonical_name"]}',
                category='pattern',
                confidence=0.9,
                source='static_seed',
            )
            n += 1
        return n

    def collect_glossary(self) -> int:
        """Store parliamentary glossary terms as memory facts.

        Returns:
            Number of glossary facts stored.
        """
        try:
            rows = self._conn.execute(
                """
                SELECT term_setswana, term_english
                FROM parliamentary_glossary
                """,
            ).fetchall()
        except sqlite3.Error as exc:
            logger.error('Glossary collect failed: %s', exc)
            return 0

        n = 0
        for row in rows:
            self._memory.store(
                key=f'glossary:{row["term_setswana"]}',
                value=f'{row["term_setswana"]} means {row["term_english"]}',
                category='fact',
                confidence=0.85,
                source='parliamentary_glossary',
            )
            n += 1
        return n

    def collect_data_quality(self) -> int:
        """Store data quality snapshot facts as memory entries.

        Returns:
            Number of data quality facts stored.
        """
        try:
            documents = self._conn.execute(
                'SELECT COUNT(*) AS c FROM documents',
            ).fetchone()['c']
            contributions = self._conn.execute(
                'SELECT COUNT(*) AS c FROM contributions',
            ).fetchone()['c']
            resolved = self._conn.execute(
                """
                SELECT COUNT(*) AS c FROM entity_review_queue
                WHERE status = 'RESOLVED'
                """,
            ).fetchone()['c']
            unresolved = self._conn.execute(
                """
                SELECT COUNT(*) AS c FROM entity_review_queue
                WHERE status = 'UNRESOLVED'
                """,
            ).fetchone()['c']
        except sqlite3.Error as exc:
            logger.error('Data quality collect failed: %s', exc)
            return 0

        facts: dict[str, Any] = {
            'documents_total': documents,
            'contributions_total': contributions,
            'entity_review_resolved': resolved,
            'entity_review_unresolved': unresolved,
        }
        for key, value in facts.items():
            self._memory.store(
                key=f'dqs:{key}',
                value=json.dumps({'key': key, 'value': value}, ensure_ascii=False),
                category='fact',
                confidence=1.0,
                source='data_quality',
            )
        return len(facts)

    def collect_all(self) -> dict[str, int]:
        """Run all collectors and return per-source counts.

        Returns:
            Dict of collector name to facts stored.
        """
        return {
            'entity_resolutions': self.collect_entity_resolutions(),
            'ministry_keywords': self.collect_ministry_keywords(),
            'glossary': self.collect_glossary(),
            'data_quality': self.collect_data_quality(),
        }
