"""Dynamic Ministry Harvester — auto-discovers ministries and keywords from source documents."""

import re
import sqlite3
import logging
from typing import List

from backend.db.connection import get_connection

logger = logging.getLogger('bareng.ministry_harvester')

MINISTRY_HEADER_RE = re.compile(
    r'(?:To ask|TO ASK)\s+the\s+Minister\s+(?:of|for)\s+(.+?)(?:\s*\(\d{1,4}\)|:|\n|$)',
    re.IGNORECASE,
)

STOP_WORDS: set[str] = {
    'the', 'to', 'ask', 'minister', 'state', 'whether', 'he', 'she', 'aware',
    'honourable', 'house', 'further', 'measures', 'plans', 'government', 'botswana',
    'that', 'for', 'from', 'will', 'with', 'this', 'have', 'been', 'off', 'what',
    'then', 'their', 'could', 'would', 'should', 'about', 'also',
}


class MinistryHarvester:
    """Harvests new ministries, topic keywords, and deferred questions from source text."""

    def __init__(self, conn: sqlite3.Connection | None = None):
        self._conn = conn or get_connection()
        self._own_conn = conn is None

    def close(self) -> None:
        if self._own_conn:
            self._conn.close()

    def harvest_from_order_paper(self, document_text: str, doc_date: str) -> list[str]:
        """Scan Order Paper / Notice Paper text for ministry references and register them."""
        found: set[str] = set()

        for match in MINISTRY_HEADER_RE.finditer(document_text):
            raw = match.group(1).strip()
            clean = re.sub(r'\s+', ' ', raw).strip().rstrip(',').rstrip('.')
            if len(clean) > 4 and not clean.lower().startswith('minister'):
                name = f'Ministry of {clean}' if not clean.lower().startswith('state') else clean
                found.add(name)

        self._upsert_ministries(list(found), doc_date)
        return list(found)

    def _upsert_ministries(self, ministries: list[str], doc_date: str) -> None:
        cursor = self._conn.cursor()
        for name in ministries:
            cursor.execute(
                """INSERT INTO ministries (canonical_name, source_type, first_seen_date, last_seen_date)
                   VALUES (?, 'order_paper_harvest', ?, ?)
                   ON CONFLICT(canonical_name) DO UPDATE SET
                       last_seen_date = excluded.last_seen_date""",
                (name, doc_date, doc_date),
            )
        self._conn.commit()
        if ministries:
            logger.info('Upserted %d harvested ministries.', len(ministries))

    def harvest_topic_keywords(self, subject_text: str, ministry_name: str) -> None:
        """Extract significant keywords from question subject and associate with ministry."""
        words = re.findall(r'\b[a-z]{4,}\b', subject_text.lower())
        keywords = [w for w in words if w not in STOP_WORDS]

        cursor = self._conn.cursor()
        row = cursor.execute(
            'SELECT id FROM ministries WHERE canonical_name = ?', (ministry_name,),
        ).fetchone()
        if not row:
            return
        ministry_id = row['id']

        for kw in set(keywords):
            cursor.execute(
                """INSERT INTO ministry_keywords (ministry_id, keyword, weight, source_type)
                   VALUES (?, ?, 1.0, 'auto_harvested')
                   ON CONFLICT(ministry_id, keyword) DO UPDATE SET
                       weight = weight + 0.5""",
                (ministry_id, kw),
            )
        self._conn.commit()

    def record_deferred(
        self,
        notice_number: int | None = None,
        original_date: str = '',
        status_note: str = '',
        contribution_id: int | None = None,
        ministry_id: int | None = None,
    ) -> None:
        """Record a question deferred to 'Later Date'."""
        cursor = self._conn.cursor()
        cursor.execute(
            """INSERT INTO deferred_questions
               (notice_number, original_date, status, notes, contribution_id, ministry_id)
               VALUES (?, ?, 'DEFERRED', ?, ?, ?)""",
            (notice_number, original_date, status_note, contribution_id, ministry_id),
        )
        self._conn.commit()

    def seed_static_ministries(self, mapping: dict[str, str]) -> None:
        """Bootstrap the dynamic registry from a static canonical mapping.

        mapping: {lower_canonical_key: display_name}

        Only inserts ministries not already present in the table.
        """
        cursor = self._conn.cursor()
        count = 0
        for lower, display in mapping.items():
            if not display:
                continue
            row = cursor.execute(
                'SELECT id FROM ministries WHERE canonical_name = ?', (display,),
            ).fetchone()
            if row:
                continue
            cursor.execute(
                """INSERT INTO ministries
                   (canonical_name, source_type, first_seen_date, last_seen_date)
                   VALUES (?, 'manual_seed', date('now'), date('now'))""",
                (display,),
            )
            count += 1
        self._conn.commit()
        logger.info('Seeded %d static ministries.', count)

    def auto_harvest_existing_contributions(self) -> int:
        """Scan all existing contributions for ministry names and keywords.

        Runs once as a backfill — harvests ministries and keywords from
        contributions already in the database.
        """
        cursor = self._conn.cursor()
        rows = cursor.execute(
            """SELECT id, subject_text, ministry_addressed, date
               FROM contributions ORDER BY date""",
        ).fetchall()

        harvested = 0
        ministries_seen: set[str] = set()

        for row in rows:
            subject = row['subject_text'] or ''
            ministry = row['ministry_addressed'] or ''

            if ministry and ministry not in ministries_seen:
                harvested += 1
                ministries_seen.add(ministry)
                self._upsert_ministries([ministry], row['date'])
                self.harvest_topic_keywords(subject, ministry)

        self._conn.commit()
        logger.info('Auto-harvested keywords from %d contributions across %d ministries.',
                     len(rows), len(ministries_seen))
        return len(ministries_seen)
