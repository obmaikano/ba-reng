"""System status endpoint."""
from fastapi import APIRouter, Depends

import aiosqlite
from backend.db.connection import get_async_db

router = APIRouter(prefix='/api/v1/status', tags=['status'])


@router.get('')
async def system_status(conn: aiosqlite.Connection = Depends(get_async_db)) -> dict:
    """Report system health: record counts and last crawl outcome."""
    cursor = await conn.execute('SELECT COUNT(*) AS cnt FROM mps')
    mp_count = (await cursor.fetchone())['cnt']

    cursor = await conn.execute('SELECT COUNT(*) AS cnt FROM contributions')
    contribution_count = (await cursor.fetchone())['cnt']

    cursor = await conn.execute('SELECT COUNT(*) AS cnt FROM documents')
    doc_count = (await cursor.fetchone())['cnt']

    cursor = await conn.execute(
        "SELECT COUNT(*) AS cnt FROM entity_review_queue WHERE status = 'UNRESOLVED'",
    )
    unresolved = (await cursor.fetchone())['cnt']

    cursor = await conn.execute(
        'SELECT started_at, status, new_documents FROM crawl_runs '
        'ORDER BY started_at DESC LIMIT 1',
    )
    last_crawl = await cursor.fetchone()

    return {
        'status': 'ok',
        'mp_count': mp_count,
        'contribution_count': contribution_count,
        'document_count': doc_count,
        'unresolved_entity_count': unresolved,
        'last_crawl': dict(last_crawl) if last_crawl else None,
    }
