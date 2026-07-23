"""MP endpoints."""
from fastapi import APIRouter, HTTPException, Query

from backend.api.metrics.participation_index import compute as compute_index
from backend.db.connection import get_connection

router = APIRouter(prefix='/api/v1/mps', tags=['mps'])


@router.get('')
def list_mps() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            '''
            SELECT m.id, m.name, m.constituency, m.party, m.photo_url,
                   COUNT(c.id) AS contribution_count
            FROM mps m
            LEFT JOIN contributions c ON c.mp_id = m.id
            GROUP BY m.id
            ORDER BY m.name
            ''',
        ).fetchall()
        breakdowns: dict[int, list[dict]] = {}
        for r in conn.execute(
            'SELECT mp_id, contribution_type, COUNT(*) AS cnt '
            'FROM contributions WHERE mp_id IS NOT NULL '
            'GROUP BY mp_id, contribution_type',
        ).fetchall():
            breakdowns.setdefault(r['mp_id'], []).append(
                {'contribution_type': r['contribution_type'], 'cnt': r['cnt']},
            )
        result = []
        for row in rows:
            mp = dict(row)
            mp['participation_index'] = compute_index(breakdowns.get(mp['id'], []))
            result.append(mp)
        return result
    finally:
        conn.close()


@router.get('/{mp_id}')
def get_mp(mp_id: int) -> dict:
    conn = get_connection()
    try:
        row = conn.execute(
            '''
            SELECT m.*, COUNT(c.id) AS contribution_count
            FROM mps m
            LEFT JOIN contributions c ON c.mp_id = m.id
            WHERE m.id = ?
            GROUP BY m.id
            ''',
            (mp_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail='MP not found')
        result = dict(row)
        type_rows = conn.execute(
            'SELECT contribution_type, COUNT(*) AS cnt '
            'FROM contributions WHERE mp_id = ? '
            'GROUP BY contribution_type ORDER BY cnt DESC',
            (mp_id,),
        ).fetchall()
        result['breakdown_by_type'] = [dict(r) for r in type_rows]
        result['participation_index'] = compute_index([dict(r) for r in type_rows])
        return result
    finally:
        conn.close()


@router.get('/{mp_id}/contributions')
def get_mp_contributions(
    mp_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            '''
            SELECT c.*, d.source_url AS doc_source_url
            FROM contributions c
            LEFT JOIN documents d ON d.id = c.document_id
            WHERE c.mp_id = ?
            ORDER BY c.date DESC
            LIMIT ? OFFSET ?
            ''',
            (mp_id, limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
