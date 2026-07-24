"""Admin routes: ministry mapping CRUD."""

import sqlite3
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from backend.api.middleware.auth import require_role
from backend.db.connection import get_connection

router = APIRouter(prefix='/api/v1/admin', tags=['admin'])

require_admin = require_role('admin', 'editor')


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
