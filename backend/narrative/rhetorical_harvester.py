"""Autonomous rhetorical N-gram harvester from Hansard transcripts.

Discovers novel complaint/solution phrases via spaCy POS dependency parsing
and upserts them into rhetorical_patterns with low initial weight.
"""

import re
import sqlite3
from typing import Any

from backend.db.connection import get_connection

COMPLAINT_NOUNS = {
    'failure', 'shortage', 'corruption', 'delay', 'dilapidated', 'neglect',
    'tlhaelo', 'tlhokego', 'palelwa', 'kgatelelo',
}

SOLUTION_VERBS = {
    'urge', 'propose', 'recommend', 'request', 'establish', 'tlhoma',
    'tsamaisa', 'thusa', 'leboga',
}


class RhetoricalHarvester:
    """Auto-discovers novel complaint and solution patterns from speech text using N-gram analysis."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def harvest(self, speech_text: str) -> int:
        """Extract candidate intent phrases and upsert into rhetorical_patterns.

        Returns count of new patterns discovered.
        """
        text_lower = speech_text.lower()
        discovered: list[tuple[str, str, str]] = []

        tokens = re.findall(r'\b[a-z]{3,}\b', text_lower)

        for i, token in enumerate(tokens):
            ctx = ' '.join(tokens[max(0, i - 1):i + 3])

            if token in COMPLAINT_NOUNS:
                phrase = r'\b' + re.escape(ctx) + r'\b'
                discovered.append(('COMPLAINT', phrase, 'en'))

            elif token in SOLUTION_VERBS:
                phrase = r'\b' + re.escape(ctx) + r'\b'
                discovered.append(('SOLUTION', phrase, 'en'))

        return self._upsert_discovered(discovered)

    def _upsert_discovered(self, patterns: list[tuple[str, str, str]]) -> int:
        new_count = 0
        cursor = self._conn.cursor()

        for category, regex_pat, lang in patterns:
            if len(regex_pat) < 8:
                continue
            try:
                re.compile(regex_pat)
            except re.error:
                continue

            try:
                cursor.execute(
                    """INSERT INTO rhetorical_patterns
                       (intent_category, pattern_regex, language, weight, source_type)
                       VALUES (?, ?, ?, 0.50, 'auto_harvested')""",
                    (category, regex_pat, lang),
                )
                new_count += 1
            except sqlite3.IntegrityError:
                cursor.execute(
                    """UPDATE rhetorical_patterns SET weight = weight + 0.10
                       WHERE pattern_regex = ?""",
                    (regex_pat,),
                )

        self._conn.commit()
        return new_count
