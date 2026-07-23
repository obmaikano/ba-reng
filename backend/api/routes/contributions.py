"""Contribution endpoints."""
from fastapi import APIRouter, HTTPException, Query

from backend.db.connection import get_connection

router = APIRouter(prefix='/api/v1/contributions', tags=['contributions'])


@router.get('')
def list_contributions(
    contribution_type: str | None = Query(None, alias='type'),
    ministry: str | None = None,
    party: str | None = None,
    constituency: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[dict]:
    conn = get_connection()
    try:
        clauses = ['1=1']
        params: list = []
        if contribution_type:
            clauses.append('c.contribution_type = ?')
            params.append(contribution_type)
        if ministry:
            clauses.append('c.ministry_addressed = ?')
            params.append(ministry)
        if party:
            clauses.append('m.party = ?')
            params.append(party)
        if constituency:
            clauses.append('m.constituency = ?')
            params.append(constituency)
        where = ' AND '.join(clauses)
        rows = conn.execute(
            f'''
            SELECT c.*, m.name AS mp_name, m.party, m.constituency,
                   d.source_url AS doc_source_url
            FROM contributions c
            LEFT JOIN mps m ON m.id = c.mp_id
            LEFT JOIN documents d ON d.id = c.document_id
            WHERE {where}
            ORDER BY c.date DESC
            LIMIT ? OFFSET ?
            ''',
            (*params, limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@router.get('/{contribution_id}')
def get_contribution(contribution_id: int) -> dict:
    conn = get_connection()
    try:
        row = conn.execute(
            '''
            SELECT c.*, m.name AS mp_name, m.party, m.constituency,
                   d.source_url AS doc_source_url
            FROM contributions c
            LEFT JOIN mps m ON m.id = c.mp_id
            LEFT JOIN documents d ON d.id = c.document_id
            WHERE c.id = ?
            ''',
            (contribution_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail='Contribution not found')
        return dict(row)
    finally:
        conn.close()
