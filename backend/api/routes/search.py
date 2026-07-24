"""Full-text search endpoint."""
from fastapi import APIRouter, Query

from backend.db.connection import get_connection

router = APIRouter(prefix='/api/v1/search', tags=['search'])


@router.get('')
def search(q: str = Query(..., min_length=1)) -> list[dict]:
    """Search contributions by subject text, MP name, ministry, or constituency."""
    conn = get_connection()
    try:
        pattern = f'%{q}%'
        rows = conn.execute(
            '''
            SELECT c.id, c.contribution_type, c.subject_text, c.date,
                   c.ministry_addressed, c.source_url, c.mp_id,
                   m.name AS mp_name, m.party, m.constituency
            FROM contributions c
            LEFT JOIN mps m ON m.id = c.mp_id
            WHERE c.subject_text LIKE ?
               OR m.name LIKE ?
               OR c.ministry_addressed LIKE ?
               OR m.constituency LIKE ?
            ORDER BY c.date DESC
            LIMIT 50
            ''',
            (pattern, pattern, pattern, pattern),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
