"""Auto-harvester — extracts keywords from parsed contributions and trains the classifier."""

import re
import sqlite3

from backend.narrative.topic_classifier import STOP_WORDS


def auto_harvest_from_contribution(
    subject_text: str,
    ministry_name: str,
    conn: sqlite3.Connection,
) -> int:
    """Extract tokens from question subject and upsert into ministry_keywords.

    Returns the number of new keyword associations created.
    """
    if not ministry_name or ministry_name in ('General Parliamentary Oversight', 'General Parliamentary Business'):
        return 0

    tokens = set(re.findall(r'\b[a-z]{4,}\b', subject_text.lower())) - STOP_WORDS
    if not tokens:
        return 0

    cursor = conn.cursor()

    row = cursor.execute(
        'SELECT id FROM ministries WHERE canonical_name = ?', (ministry_name,),
    ).fetchone()

    if not row:
        cursor.execute(
            """INSERT INTO ministries (canonical_name, source_type, first_seen_date, last_seen_date)
               VALUES (?, 'order_paper_harvest', date('now'), date('now'))""",
            (ministry_name,),
        )
        ministry_id = cursor.lastrowid
    else:
        ministry_id = row['id']

    upsert = """
        INSERT INTO ministry_keywords (ministry_id, keyword, weight, source_type)
        VALUES (?, ?, 1.0, 'auto_harvested')
        ON CONFLICT(ministry_id, keyword) DO UPDATE SET
            weight = weight + 0.25
    """

    for token in tokens:
        cursor.execute(upsert, (ministry_id, token))

    conn.commit()
    return len(tokens)
