"""Admin routes: ministry mapping CRUD, crawl control, dashboard data."""

import sqlite3
import threading
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from backend.api.middleware.auth import require_role
from backend.db.connection import get_connection

router = APIRouter(prefix='/api/v1/admin', tags=['admin'])

require_admin = require_role('admin', 'editor')
require_admin_only = require_role('admin')

# Track in-flight crawl so we don't launch two at once.
_crawl_lock = threading.Lock()
_crawl_running = False


def _run_crawl_background() -> None:
    """Run crawl_all in a background thread and record the outcome."""
    global _crawl_running
    from backend.crawl import crawl_all

    conn = get_connection()
    try:
        started = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        conn.execute(
            "INSERT INTO crawl_runs (started_at, source, status, run_type) "
            "VALUES (?, 'manual', 'RUNNING', 'manual')",
            (started,),
        )
        conn.commit()
        run_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]

        results = crawl_all()

        total_new = sum(r.get('new_documents', 0) for r in results.values())
        total_errors = sum(1 for r in results.values() if r.get('status') == 'ERROR')
        overall = 'SUCCESS' if total_errors == 0 else 'PARTIAL'

        conn.execute(
            'UPDATE crawl_runs SET finished_at = ?, status = ?, new_documents = ?, errors = ? '
            'WHERE id = ?',
            (
                datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
                overall,
                total_new,
                total_errors,
                run_id,
            ),
        )
        conn.commit()
    except Exception:
        pass  # Background failure is logged by crawl_all
    finally:
        conn.close()
        _crawl_running = False


# ---------------------------------------------------------------------------
# Crawl trigger (admin only)
# ---------------------------------------------------------------------------


@router.post('/crawl/trigger')
def trigger_crawl(current_user: dict[str, Any] = Depends(require_admin_only)) -> dict:
    global _crawl_running
    with _crawl_lock:
        if _crawl_running:
            raise HTTPException(status_code=409, detail='A crawl is already in progress')
        _crawl_running = True

    thread = threading.Thread(target=_run_crawl_background, daemon=True)
    thread.start()
    return {'detail': 'Crawl started', 'status': 'RUNNING'}


# ---------------------------------------------------------------------------
# Crawl runs history
# ---------------------------------------------------------------------------


@router.get('/crawl-runs')
def list_crawl_runs(
    current_user: dict[str, Any] = Depends(require_admin),
) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            'SELECT id, started_at, finished_at, source, status, new_documents, errors, run_type '
            'FROM crawl_runs ORDER BY started_at DESC LIMIT 20',
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Dashboard summary (aggregated for the dashboard page)
# ---------------------------------------------------------------------------


@router.get('/dashboard')
def admin_dashboard(current_user: dict[str, Any] = Depends(require_admin)) -> dict:
    conn = get_connection()
    try:
        mp_count = conn.execute('SELECT COUNT(*) AS cnt FROM mps').fetchone()['cnt']
        contribution_count = conn.execute(
            'SELECT COUNT(*) AS cnt FROM contributions',
        ).fetchone()['cnt']
        doc_count = conn.execute('SELECT COUNT(*) AS cnt FROM documents').fetchone()['cnt']
        unresolved = conn.execute(
            "SELECT COUNT(*) AS cnt FROM entity_review_queue WHERE status = 'UNRESOLVED'",
        ).fetchone()['cnt']
        total_unresolved = conn.execute(
            'SELECT COUNT(*) AS cnt FROM entity_review_queue',
        ).fetchone()['cnt']
        resolved = total_unresolved - unresolved

        last_crawl = conn.execute(
            'SELECT started_at, finished_at, status, new_documents, errors '
            'FROM crawl_runs ORDER BY started_at DESC LIMIT 1',
        ).fetchone()

        return {
            'mp_count': mp_count,
            'contribution_count': contribution_count,
            'document_count': doc_count,
            'unresolved_entity_count': unresolved,
            'resolved_entity_count': resolved,
            'last_crawl': dict(last_crawl) if last_crawl else None,
            'crawl_running': _crawl_running,
        }
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# MPs
# ---------------------------------------------------------------------------


@router.get('/mps')
def list_mps(current_user: dict[str, Any] = Depends(require_admin)) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            'SELECT id, name, constituency, party FROM mps ORDER BY name',
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Ministry mappings CRUD
# ---------------------------------------------------------------------------


@router.get('/ministry-mappings')
def list_ministry_mappings(
    current_user: dict[str, Any] = Depends(require_admin),
) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            'SELECT mm.id, mm.normalized_title, mm.mp_id, m.name AS mp_name, '
            'm.constituency, m.party '
            'FROM ministry_mapping mm '
            'JOIN mps m ON mm.mp_id = m.id '
            'ORDER BY mm.normalized_title',
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@router.post('/ministry-mappings', status_code=201)
def create_ministry_mapping(
    body: dict,
    current_user: dict[str, Any] = Depends(require_admin),
) -> dict:
    normalized_title = body.get('normalized_title', '').strip().lower()
    mp_id = body.get('mp_id')

    if not normalized_title or not mp_id:
        raise HTTPException(status_code=400, detail='normalized_title and mp_id required')

    conn = get_connection()
    try:
        cursor = conn.execute(
            'INSERT INTO ministry_mapping (normalized_title, mp_id) VALUES (?, ?)',
            (normalized_title, mp_id),
        )
        conn.commit()
        return {'id': cursor.lastrowid, 'normalized_title': normalized_title, 'mp_id': mp_id}
    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail='Ministry mapping already exists',
        ) from exc
    finally:
        conn.close()


@router.put('/ministry-mappings/{mapping_id}')
def update_ministry_mapping(
    mapping_id: int,
    body: dict,
    current_user: dict[str, Any] = Depends(require_admin),
) -> dict:
    conn = get_connection()
    try:
        existing = conn.execute(
            'SELECT id FROM ministry_mapping WHERE id = ?', (mapping_id,),
        ).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail='Mapping not found')

        normalized_title = body.get('normalized_title', '').strip().lower()
        mp_id = body.get('mp_id')

        if normalized_title:
            conn.execute(
                'UPDATE ministry_mapping SET normalized_title = ?, updated_at = datetime("now") '
                'WHERE id = ?',
                (normalized_title, mapping_id),
            )
        if mp_id is not None:
            conn.execute(
                'UPDATE ministry_mapping SET mp_id = ?, updated_at = datetime("now") '
                'WHERE id = ?',
                (mp_id, mapping_id),
            )
        conn.commit()
        return {'detail': 'Updated'}
    finally:
        conn.close()


@router.delete('/ministry-mappings/{mapping_id}')
def delete_ministry_mapping(
    mapping_id: int,
    current_user: dict[str, Any] = Depends(require_admin),
) -> dict:
    conn = get_connection()
    try:
        existing = conn.execute(
            'SELECT id FROM ministry_mapping WHERE id = ?', (mapping_id,),
        ).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail='Mapping not found')
        conn.execute('DELETE FROM ministry_mapping WHERE id = ?', (mapping_id,))
        conn.commit()
        return {'detail': 'Deleted'}
    finally:
        conn.close()
