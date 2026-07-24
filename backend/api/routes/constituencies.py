"""Constituency endpoints."""
from fastapi import APIRouter

from backend.db.connection import get_connection

router = APIRouter(prefix='/api/v1/constituencies', tags=['constituencies'])


@router.get('')
def list_constituencies() -> list[dict]:
    """List all constituencies with their MP, contribution count, and type breakdown."""
    conn = get_connection()
    try:
        rows = conn.execute(
            '''
            SELECT m.constituency, m.name AS mp_name, m.party,
                   COUNT(c.id) AS contribution_count,
                   SUM(CASE WHEN c.contribution_type = 'oral_question' THEN 1 ELSE 0 END) AS oral_question_count,
                   SUM(CASE WHEN c.contribution_type = 'question_without_notice' THEN 1 ELSE 0 END) AS question_without_notice_count,
                   SUM(CASE WHEN c.contribution_type = 'motion' THEN 1 ELSE 0 END) AS motion_count
            FROM mps m
            LEFT JOIN contributions c ON c.mp_id = m.id
            GROUP BY m.constituency
            ORDER BY m.constituency
            ''',
        ).fetchall()
        results: list[dict] = []
        for r in rows:
            d = dict(r)
            d['oral_question_count'] = (d['oral_question_count'] or 0) + (d['question_without_notice_count'] or 0)
            del d['question_without_notice_count']
            results.append(d)
        return results
    finally:
        conn.close()


@router.get('/{constituency_name}')
def get_constituency(constituency_name: str) -> dict:
    """Get a single constituency's MP, contribution count, and type breakdown."""
    conn = get_connection()
    try:
        row = conn.execute(
            '''
            SELECT m.constituency, m.name AS mp_name, m.party,
                   COUNT(c.id) AS contribution_count,
                   SUM(CASE WHEN c.contribution_type = 'oral_question' THEN 1 ELSE 0 END) AS oral_question_count,
                   SUM(CASE WHEN c.contribution_type = 'question_without_notice' THEN 1 ELSE 0 END) AS question_without_notice_count,
                   SUM(CASE WHEN c.contribution_type = 'motion' THEN 1 ELSE 0 END) AS motion_count
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
                'oral_question_count': 0,
                'motion_count': 0,
            }
        d = dict(row)
        d['oral_question_count'] = (d['oral_question_count'] or 0) + (d['question_without_notice_count'] or 0)
        del d['question_without_notice_count']
        return d
    finally:
        conn.close()
