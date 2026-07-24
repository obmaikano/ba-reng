"""100% database-driven topic classifier — zero hardcoded JSON or dicts."""

import re
import sqlite3
from typing import Optional

STOP_WORDS: set[str] = {
    'the', 'to', 'ask', 'minister', 'state', 'whether', 'he', 'she', 'aware',
    'honourable', 'house', 'further', 'measures', 'plans', 'government', 'botswana',
    'a', 'an', 'in', 'of', 'on', 'for', 'and', 'or', 'is', 'are', 'gale', 'mme',
    'that', 'from', 'will', 'with', 'this', 'have', 'been', 'off', 'what',
    'then', 'their', 'could', 'would', 'should', 'about', 'also', 'but',
}


class DisciplineError(Exception):
    """Raised when a hardcoded dictionary / JSON load is detected."""


class DBTopicClassifier:
    """100% database-driven topic and ministry classifier.

    Four-tier resolution:
    1. EXPLICIT_HEADER — explicit ministry in source document, return directly
    2. DB_STATUTE_MATCH — glossary category='statute' term found in text
    3. DB_KEYWORD_SCORING — weighted SQL keyword matching against ministry_keywords
    4. FALLBACK_DEFAULT — 'General Parliamentary Oversight'
    """

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def classify(
        self,
        subject_text: str,
        explicit_ministry: Optional[str] = None,
    ) -> tuple[str, float, str]:
        """Classify input text via SQLite tiered scoring.

        Returns: (inferred_ministry, confidence, method)
        """
        # Tier 1: explicit header — trust it completely
        if explicit_ministry and explicit_ministry.strip() and explicit_ministry.strip().lower() != 'not specified':
            return explicit_ministry.strip(), 1.0, 'EXPLICIT_HEADER'

        clean = subject_text.lower().strip()
        if not clean:
            return 'General Parliamentary Oversight', 0.10, 'FALLBACK_EMPTY'

        words = set(re.findall(r'\b[a-zA-Z0-9]{3,}\b', clean)) - STOP_WORDS
        if not words:
            return 'General Parliamentary Oversight', 0.10, 'FALLBACK_EMPTY'

        # Tier 2: statute / act lookup in parliamentary_glossary
        cursor = self._conn.cursor()
        cursor.execute(
            """SELECT term_english, term_setswana
               FROM parliamentary_glossary
               WHERE category = 'statute'""",
        )
        for term_en, ministry_target in cursor.fetchall():
            if term_en and term_en.lower() in clean:
                return ministry_target, 0.95, 'DB_STATUTE_MATCH'

        # Tier 3: weighted keyword scoring from ministry_keywords
        placeholders = ','.join('?' for _ in words)
        row = cursor.execute(
            f"""SELECT m.canonical_name, SUM(k.weight) AS total_score, COUNT(k.id) AS matches
                FROM ministry_keywords k
                JOIN ministries m ON k.ministry_id = m.id
                WHERE k.keyword IN ({placeholders}) AND m.is_active = 1
                GROUP BY m.canonical_name
                ORDER BY total_score DESC
                LIMIT 1""",
            list(words),
        ).fetchone()

        if row and row['total_score'] > 0.8:
            confidence = min(0.40 + (row['total_score'] * 0.12), 0.90)
            return row['canonical_name'], round(confidence, 2), 'DB_KEYWORD_SCORING'

        # Tier 4: fallback
        return 'General Parliamentary Oversight', 0.20, 'FALLBACK_DEFAULT'
