"""Orchestration: iterate entity_review_queue, resolve, update."""

import sqlite3

from backend.db.connection import get_connection
from backend.resolve.entity import (
    _build_constituency_map,
    _build_ministry_map,
    _build_token_map,
    resolve_contribution_scalable,
)


def resolve_all(conn: sqlite3.Connection | None = None) -> dict:
    """Resolve all UNRESOLVED entities and update contributions."""
    close_conn = conn is None
    if conn is None:
        conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """SELECT eq.raw_match_name, c.raw_constituency, eq.id, eq.contribution_id
           FROM entity_review_queue eq
           JOIN contributions c ON eq.contribution_id = c.id
           WHERE eq.status='UNRESOLVED'""",
    )
    unresolved = cursor.fetchall()

    if not unresolved:
        if close_conn:
            conn.close()
        return {'total': 0, 'resolved': 0, 'unresolved': 0, 'rate': 0.0}

    constituency_map = _build_constituency_map(cursor)
    token_map = _build_token_map(cursor)
    ministry_map = _build_ministry_map(cursor)

    resolved_count = 0
    unresolved_list: list[dict] = []

    for row in unresolved:
        mp_id = resolve_contribution_scalable(
            cursor,
            row['raw_match_name'],
            row['raw_constituency'],
            constituency_map,
            token_map,
            ministry_map,
        )
        if mp_id is not None:
            cursor.execute(
                'UPDATE contributions SET mp_id = ? WHERE id = ?',
                (mp_id, row['contribution_id']),
            )
            cursor.execute(
                'UPDATE entity_review_queue SET status = ?, resolved_mp_id = ? WHERE id = ?',
                ('RESOLVED', mp_id, row['id']),
            )
            resolved_count += 1
        else:
            unresolved_list.append({
                'id': row['id'],
                'raw_match_name': row['raw_match_name'],
                'raw_constituency': row['raw_constituency'],
            })

    conn.commit()

    if close_conn:
        conn.close()

    rate = (resolved_count / len(unresolved)) * 100 if unresolved else 0.0

    return {
        'total': len(unresolved),
        'resolved': resolved_count,
        'unresolved': len(unresolved_list),
        'rate': round(rate, 1),
    }


if __name__ == '__main__':
    result = resolve_all()
    print(f'Result: {result}')
