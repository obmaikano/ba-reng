"""Narrative API — weekly digest and story endpoints."""

from fastapi import APIRouter, Query

from backend.db.connection import get_connection
from backend.narrative.engine import NarrativeEngine

router = APIRouter(prefix='/api/v1/narrative', tags=['narrative'])


@router.get('/weekly')
def narrative_weekly(
    start: str | None = Query(None, description='Start date YYYY-MM-DD'),
    end: str | None = Query(None, description='End date YYYY-MM-DD'),
) -> dict:
    conn = get_connection()
    try:
        engine = NarrativeEngine(conn)
        return engine.weekly_digest(start, end)
    finally:
        conn.close()
