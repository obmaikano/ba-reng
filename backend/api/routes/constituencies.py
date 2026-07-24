"""Constituency endpoints."""
from fastapi import APIRouter

from backend.db.connection import get_connection

router = APIRouter(prefix='/api/v1/constituencies', tags=['constituencies'])


@router.get('')
def list_constituencies() -> list[dict]:
    """List all constituencies with their MP and contribution count."""
    conn = get_connection()
    try:
        rows = conn.execute(
            '''
            SELECT m.constituency, m.name AS mp_name, m.party,
                   COUNT(c.id) AS contribution_count
            FROM mps m
            LEFT JOIN contributions c ON c.mp_id = m.id
            GROUP BY m.constituency
            ORDER BY m.constituency
            ''',
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@router.get('/{constituency_name}')
def get_constituency(constituency_name: str) -> dict:
    """Get a single constituency's MP and contribution count."""
    conn = get_connection()
    try:
        row = conn.execute(
            '''
            SELECT m.constituency, m.name AS mp_name, m.party,
                   COUNT(c.id) AS contribution_count
            FROM mps m
            LEFT JOIN contributions c ON c.mp_id = m.id
            WHERE LOWER(m.constituency) = LOWER(?)
            GROUP BY m.constituency
            ''',
            (constituency_name,),
        ).fetchone()
        if not row:
            return {
                'constituency': constituency_name,
                'mp_name': None,
                'party': None,
                'contribution_count': 0,
            }
        return dict(row)
    finally:
        conn.close()
