"""System status endpoint."""
from fastapi import APIRouter

from backend.db.connection import get_connection

router = APIRouter(prefix='/api/v1/status', tags=['status'])


@router.get('')
def system_status() -> dict:
    conn = get_connection()
    try:
        mp_count = conn.execute('SELECT COUNT(*) AS cnt FROM mps').fetchone()['cnt']
        contribution_count = conn.execute('SELECT COUNT(*) AS cnt FROM contributions').fetchone()['cnt']
        doc_count = conn.execute('SELECT COUNT(*) AS cnt FROM documents').fetchone()['cnt']
        unresolved = conn.execute(
            "SELECT COUNT(*) AS cnt FROM entity_review_queue WHERE status = 'UNRESOLVED'",
        ).fetchone()['cnt']
        last_crawl = conn.execute(
            'SELECT started_at, status, new_documents FROM crawl_runs ORDER BY started_at DESC LIMIT 1',
        ).fetchone()
        return {
            'status': 'ok',
            'mp_count': mp_count,
            'contribution_count': contribution_count,
            'document_count': doc_count,
            'unresolved_entity_count': unresolved,
            'last_crawl': dict(last_crawl) if last_crawl else None,
        }
    finally:
        conn.close()
