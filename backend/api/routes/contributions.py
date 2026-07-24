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
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict:
    """List contributions, optionally filtered by type, ministry, party, constituency, or date range."""
    conn = get_connection()
    try:
        clauses = ['1=1']
        params: list = []

        if contribution_type:
            clauses.append('UPPER(c.contribution_type) = UPPER(?)')
            params.append(contribution_type)

        if ministry:
            clauses.append('c.ministry_addressed = ?')
            params.append(ministry)

        if party:
            clauses.append('UPPER(m.party) = UPPER(?)')
            params.append(party)

        if constituency and constituency.strip():
            clauses.append('m.constituency LIKE ?')
            params.append(f'%{constituency.strip()}%')

        if start_date:
            clauses.append('c.date >= ?')
            params.append(start_date)

        if end_date:
            clauses.append('c.date <= ?')
            params.append(end_date if len(end_date) > 10 else f'{end_date} 23:59:59')

        where = ' AND '.join(clauses)

        total = conn.execute(
            f'SELECT COUNT(*) FROM contributions c LEFT JOIN mps m ON m.id = c.mp_id WHERE {where}',
            params,
        ).fetchone()[0]

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

        return {
            'total_records': total,
            'returned_records': len(rows),
            'data': [dict(r) for r in rows],
        }
    finally:
        conn.close()


@router.get('/{contribution_id}')
def get_contribution(contribution_id: int) -> dict:
    """Get a single contribution by id."""
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
