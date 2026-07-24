"""Admin routes: ministry mapping CRUD, crawl control, dashboard data."""

import sqlite3
import threading
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from backend.api.middleware.auth import require_role
from backend.db.connection import get_connection
from backend.resolve.entity import _extract_surname

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


# ---------------------------------------------------------------------------
# Entity Review Queue
# ---------------------------------------------------------------------------


@router.get('/entity-review')
def list_unresolved_entities(
    current_user: dict[str, Any] = Depends(require_admin),
) -> list[dict]:
    """List unresolved entities with suggested MP matches."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT eq.id, eq.raw_match_name, eq.status, eq.resolved_mp_id, "
            "eq.document_id, eq.contribution_id, "
            "d.title AS document_title, d.source_url "
            "FROM entity_review_queue eq "
            "LEFT JOIN documents d ON eq.document_id = d.id "
            "WHERE eq.status = 'UNRESOLVED' "
            "ORDER BY eq.id",
        ).fetchall()

        result: list[dict] = []
        for row in rows:
            entity = dict(row)
            # Suggestion engine: try constituency match first, then surname fallback
            entity['suggestions'] = _suggest_mp(entity['raw_match_name'], conn)
            result.append(entity)

        return result
    finally:
        conn.close()


@router.post('/entity-review/{entity_id}/resolve')
def resolve_entity(
    entity_id: int,
    body: dict[str, Any],
    current_user: dict[str, Any] = Depends(require_admin),
) -> dict:
    """Resolve an entity by assigning it to an MP."""
    mp_id = body.get('mp_id')
    if not mp_id:
        raise HTTPException(status_code=400, detail='mp_id is required')

    conn = get_connection()
    try:
        existing = conn.execute(
            'SELECT id, status FROM entity_review_queue WHERE id = ?',
            (entity_id,),
        ).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail='Entity not found')
        if existing['status'] != 'UNRESOLVED':
            raise HTTPException(status_code=409, detail='Entity is no longer unresolved')

        # Verify MP exists
        mp = conn.execute('SELECT id, name FROM mps WHERE id = ?', (mp_id,)).fetchone()
        if not mp:
            raise HTTPException(status_code=400, detail='MP not found')

        conn.execute(
            "UPDATE entity_review_queue SET status = 'RESOLVED', resolved_mp_id = ? "
            "WHERE id = ?",
            (mp_id, entity_id),
        )
        conn.commit()

        return {
            'detail': 'Resolved',
            'entity_id': entity_id,
            'mp_name': mp['name'],
        }
    finally:
        conn.close()


@router.post('/entity-review/{entity_id}/skip')
def skip_entity(
    entity_id: int,
    current_user: dict[str, Any] = Depends(require_admin),
) -> dict:
    """Skip an entity — mark it as IGNORED."""
    conn = get_connection()
    try:
        existing = conn.execute(
            'SELECT id, status FROM entity_review_queue WHERE id = ?',
            (entity_id,),
        ).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail='Entity not found')

        conn.execute(
            "UPDATE entity_review_queue SET status = 'IGNORED' WHERE id = ?",
            (entity_id,),
        )
        conn.commit()

        return {'detail': 'Skipped', 'entity_id': entity_id}
    finally:
        conn.close()


def _suggest_mp(raw_name: str, conn: Any) -> list[dict]:
    """Return candidate MP matches for a raw name string.

    Strategy: extract surname, try constituency text search, then
    fall back to surname-based match.
    """
    from backend.resolve.entity import _extract_surname

    surname = _extract_surname(raw_name)
    suggestions: list[dict] = []

    if not surname:
        return suggestions

    # Try surname match first
    rows = conn.execute(
        'SELECT id, name, constituency, party FROM mps '
        'WHERE name LIKE ? COLLATE NOCASE '
        'ORDER BY name LIMIT 5',
        (f'%{surname}%',),
    ).fetchall()

    for r in rows:
        suggestions.append(dict(r))

    return suggestions


# ---------------------------------------------------------------------------
# User Management (admin only)
# ---------------------------------------------------------------------------

require_admin_only = require_role('admin')


@router.get('/users')
def list_users(current_user: dict[str, Any] = Depends(require_admin_only)) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            'SELECT id, email, display_name, role, is_active, created_at, last_login_at '
            'FROM users ORDER BY created_at DESC',
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@router.post('/users', status_code=201)
def create_user(
    body: dict[str, Any],
    current_user: dict[str, Any] = Depends(require_admin_only),
) -> dict:
    email = (body.get('email') or '').strip().lower()
    display_name = (body.get('display_name') or '').strip()
    role = (body.get('role') or 'viewer').strip().lower()
    password = (body.get('password') or '').strip()

    if not email or not display_name:
        raise HTTPException(status_code=400, detail='Email and display name required')
    if role not in ('admin', 'editor', 'viewer'):
        raise HTTPException(status_code=400, detail='Role must be admin, editor, or viewer')
    if not password or len(password) < 8:
        raise HTTPException(status_code=400, detail='Password must be at least 8 characters')

    import bcrypt
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    conn = get_connection()
    try:
        conn.execute(
            'INSERT INTO users (email, password_hash, display_name, role, is_active) '
            'VALUES (?, ?, ?, ?, 1)',
            (email, password_hash, display_name, role),
        )
        conn.commit()
        user_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        return {
            'id': user_id, 'email': email, 'display_name': display_name, 'role': role,
        }
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail='User with this email already exists') from exc
    finally:
        conn.close()


@router.put('/users/{user_id}')
def update_user(
    user_id: int,
    body: dict[str, Any],
    current_user: dict[str, Any] = Depends(require_admin_only),
) -> dict:
    conn = get_connection()
    try:
        existing = conn.execute(
            'SELECT id FROM users WHERE id = ?', (user_id,),
        ).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail='User not found')

        updates: list[str] = []
        params: list[Any] = []

        if 'role' in body:
            role = body['role'].strip().lower()
            if role not in ('admin', 'editor', 'viewer'):
                raise HTTPException(status_code=400, detail='Invalid role')
            updates.append('role = ?')
            params.append(role)

        if 'is_active' in body:
            updates.append('is_active = ?')
            params.append(1 if body['is_active'] else 0)

        if 'display_name' in body:
            updates.append('display_name = ?')
            params.append(body['display_name'].strip())

        if not updates:
            raise HTTPException(status_code=400, detail='No fields to update')

        params.append(user_id)
        conn.execute(
            f"UPDATE users SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        conn.commit()
        return {'detail': 'Updated'}
    finally:
        conn.close()
