"""Orchestration: iterate documents, parse, insert contributions."""

import logging
import sqlite3
from collections.abc import Callable

from backend.db.connection import get_connection
from backend.parse.notice_paper import parse_pdf as parse_notice_paper
from backend.parse.order_paper import parse_pdf as parse_order_paper
from backend.parse.committee_of_supply import parse_pdf as parse_committee_of_supply
from backend.parse.bill import parse_pdf as parse_bill

logger = logging.getLogger(__name__)

_PARSERS: dict[str, Callable[..., list[dict]]] = {
    'notice_paper': parse_notice_paper,
    'order_paper': parse_order_paper,
    'committee_of_supply': parse_committee_of_supply,
    'bill': parse_bill,
    'motion': parse_notice_paper,
}

_PARSABLE_TYPES = tuple(_PARSERS.keys())


def _insert_contribution(
    cursor: sqlite3.Cursor,
    doc_id: int,
    contrib: dict,
) -> int | None:
    try:
        cursor.execute(
            """INSERT INTO contributions
               (document_id, contribution_type, subject_text, ministry_addressed,
                date, raw_match_name, raw_constituency, source_url)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                doc_id,
                contrib['contribution_type'],
                contrib['subject_text'],
                contrib['ministry_addressed'],
                contrib['date'],
                contrib['raw_match_name'],
                contrib['raw_constituency'],
                contrib['source_url'],
            ),
        )
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None


def _insert_unresolved(
    cursor: sqlite3.Cursor,
    raw_name: str,
    doc_id: int,
    contribution_id: int,
) -> bool:
    cursor.execute(
        """INSERT INTO entity_review_queue
           (raw_match_name, document_id, contribution_id, status)
           SELECT ?, ?, ?, 'UNRESOLVED'
           WHERE NOT EXISTS (
               SELECT 1 FROM entity_review_queue WHERE raw_match_name = ?
           )""",
        (raw_name, doc_id, contribution_id, raw_name),
    )
    return cursor.rowcount > 0


def parse_and_store(
    doc_id: int,
    file_path: str,
    source_url: str,
    conn: sqlite3.Connection | None = None,
    *,
    doc_type: str,
) -> dict:
    """Parse a single document and store results in the database."""
    close_conn = conn is None
    if conn is None:
        conn = get_connection()

    cursor = conn.cursor()
    if doc_type not in _PARSERS:
        logger.warning('Unknown doc_type=%s for document %d, falling back to notice_paper parser', doc_type, doc_id)
    parser = _PARSERS.get(doc_type, parse_notice_paper)
    contributions = parser(file_path, source_url)

    parsed = 0
    stored = 0
    unresolved = 0

    for contrib in contributions:
        parsed += 1
        cid = _insert_contribution(cursor, doc_id, contrib)
        if cid is not None:
            stored += 1
            raw_name = contrib['raw_match_name']
            if not raw_name:
                continue
            if _insert_unresolved(cursor, raw_name, doc_id, cid):
                unresolved += 1

    conn.commit()

    if close_conn:
        conn.close()

    return {
        'doc_id': doc_id,
        'parsed': parsed,
        'stored': stored,
        'unresolved': unresolved,
    }


def run_all(conn: sqlite3.Connection | None = None) -> list[dict]:
    """Parse all documents and store contributions."""
    close_conn = conn is None
    if conn is None:
        conn = get_connection()

    cursor = conn.cursor()
    placeholders = ','.join('?' * len(_PARSERS))
    docs = cursor.execute(
        f"""SELECT id, title, file_path, source_url, doc_type
           FROM documents WHERE doc_type IN ({placeholders})
           ORDER BY id""",
        list(_PARSERS.keys()),
    ).fetchall()

    results: list[dict] = []
    for doc in docs:
        result = parse_and_store(
            doc['id'], doc['file_path'], doc['source_url'],
            conn=conn, doc_type=doc['doc_type'],
        )
        results.append(result)

    if close_conn:
        conn.close()

    return results


if __name__ == '__main__':
    results = run_all()
    total_parsed = sum(r['parsed'] for r in results)
    total_stored = sum(r['stored'] for r in results)
    total_unresolved = sum(r['unresolved'] for r in results)
    print(f'Documents processed: {len(results)}')
    print(f'Contributions parsed: {total_parsed}')
    print(f'Contributions stored: {total_stored}')
    print(f'Unresolved entities:  {total_unresolved}')
    for r in results:
        print(
            f'  Doc {r["doc_id"]}: {r["parsed"]} parsed, '
            f'{r["stored"]} stored, {r["unresolved"]} unresolved',
        )
