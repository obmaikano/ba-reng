"""Seed parliamentary_glossary from data/botswana_gazetteer.json."""

import json
from pathlib import Path

from backend.db.connection import get_connection

GAZETTEER_PATH = Path(__file__).resolve().parent.parent.parent / 'data' / 'botswana_gazetteer.json'


def seed_glossary() -> int:
    """Insert gazetteer terms into parliamentary_glossary, skipping duplicates."""
    gazetteer = json.loads(GAZETTEER_PATH.read_text())
    entries = [
        entry
        for group in gazetteer.values()
        for entry in group
    ]

    conn = get_connection()
    try:
        cursor = conn.cursor()
        inserted = 0
        for entry in entries:
            cursor.execute(
                """INSERT INTO parliamentary_glossary (term_setswana, term_english, category)
                   VALUES (?, ?, ?)
                   ON CONFLICT(term_setswana) DO NOTHING""",
                (entry['term_setswana'], entry['term_english'], entry['category']),
            )
            inserted += cursor.rowcount
        conn.commit()
        return inserted
    finally:
        conn.close()


if __name__ == '__main__':
    count = seed_glossary()
    print(f'  Seeded {count} new parliamentary_glossary entries.')
