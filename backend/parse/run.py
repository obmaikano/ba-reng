"""Orchestration: iterate notice paper documents, parse, insert contributions."""

import sqlite3

from backend.db.connection import get_connection
from backend.parse.notice_paper import parse_pdf


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
) -> None:
    if not raw_name:
        return
    cursor.execute(
        """INSERT INTO entity_review_queue
           (raw_match_name, document_id, contribution_id, status)
           VALUES (?, ?, ?, 'UNRESOLVED')""",
        (raw_name, doc_id, contribution_id),
    )


def parse_and_store(
    doc_id: int,
    file_path: str,
    source_url: str,
    conn: sqlite3.Connection | None = None,
) -> dict:
    """Parse a single document and store results in the database."""
    close_conn = conn is None
    if conn is None:
        conn = get_connection()

    cursor = conn.cursor()
    contributions = parse_pdf(file_path, source_url)

    parsed = 0
    stored = 0
    unresolved = 0

    for contrib in contributions:
        parsed += 1
        cid = _insert_contribution(cursor, doc_id, contrib)
        if cid is not None:
            stored += 1
            if not contrib['raw_match_name']:
                continue
            _insert_unresolved(cursor, contrib['raw_match_name'], doc_id, cid)
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
    """Parse all notice paper documents and store contributions."""
    close_conn = conn is None
    if conn is None:
        conn = get_connection()

    cursor = conn.cursor()
    docs = cursor.execute(
        """SELECT id, title, file_path, source_url
           FROM documents WHERE doc_type = 'notice_paper'
           ORDER BY id""",
    ).fetchall()

    results: list[dict] = []
    for doc in docs:
        result = parse_and_store(
            doc['id'], doc['file_path'], doc['source_url'], conn,
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
