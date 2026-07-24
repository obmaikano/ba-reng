"""Tests for entity review queue endpoints."""

import bcrypt
import pytest
from fastapi.testclient import TestClient

from backend.db import migrate as migrate_module
from backend.db.connection import get_connection
from backend.main import app


@pytest.fixture
def editor_client(tmp_path, monkeypatch) -> TestClient:
    """Logged-in editor with seeded entities and MPs."""
    db_path = tmp_path / 'test.db'
    monkeypatch.setenv('DATABASE_PATH', str(db_path))
    monkeypatch.setenv('ENV', 'development')

    migrate_module.migrate()

    conn = get_connection()
    try:
        password_hash = bcrypt.hashpw(b'editor-pass', bcrypt.gensalt()).decode()
        conn.execute(
            'INSERT INTO users (email, password_hash, display_name, role, is_active) '
            'VALUES (?, ?, ?, ?, ?)',
            ('editor@bareng.bw', password_hash, 'Editor', 'editor', 1),
        )
        # Seed MPs for suggestion engine
        conn.executemany(
            'INSERT INTO mps (name, constituency, party) VALUES (?, ?, ?)',
            [
                ('Jane Motswana', 'Gaborone Central', 'BDP'),
                ('John Kgosi', 'Francistown East', 'UDC'),
            ],
        )
        # Seed a document
        conn.execute(
            'INSERT INTO documents (source_url, title, doc_type, raw_text_hash) '
            'VALUES (?, ?, ?, ?)',
            ('https://example.org/doc-1', 'Notice Paper 1', 'notice_paper', 'hash-x'),
        )
        doc_id = conn.execute(
            "SELECT id FROM documents WHERE raw_text_hash = 'hash-x'",
        ).fetchone()['id']
        # Seed unresolved entities
        conn.executemany(
            'INSERT INTO entity_review_queue '
            '(raw_match_name, document_id, status) VALUES (?, ?, ?)',
            [
                ('Mr. J. Motswana', doc_id, 'UNRESOLVED'),
                ('Dr. Unknown Person', doc_id, 'UNRESOLVED'),
                ('Ms. Already Resolved', doc_id, 'RESOLVED'),
            ],
        )
        conn.commit()
    finally:
        conn.close()

    client = TestClient(app)
    resp = client.post(
        '/api/v1/auth/login',
        json={'email': 'editor@bareng.bw', 'password': 'editor-pass'},
    )
    assert resp.status_code == 200
    cookie = resp.cookies.get('access_token', '')
    client.cookies.set('access_token', cookie)
    return client


class TestListEntities:
    def test_list_unresolved_entities(self, editor_client):
        resp = editor_client.get('/api/v1/admin/entity-review')
        assert resp.status_code == 200
        data = resp.json()
        # Only UNRESOLVED entities, not RESOLVED
        assert len(data) == 2
        names = {e['raw_match_name'] for e in data}
        assert 'Mr. J. Motswana' in names
        assert 'Dr. Unknown Person' in names
        assert 'Ms. Already Resolved' not in names

    def test_list_entities_has_suggestions(self, editor_client):
        resp = editor_client.get('/api/v1/admin/entity-review')
        data = resp.json()
        # Mr. J. Motswana should have a suggestion matching "Motswana"
        motswana = next(e for e in data if e['raw_match_name'] == 'Mr. J. Motswana')
        assert len(motswana['suggestions']) >= 1
        assert motswana['suggestions'][0]['name'] == 'Jane Motswana'

    def test_list_entities_includes_document_info(self, editor_client):
        resp = editor_client.get('/api/v1/admin/entity-review')
        data = resp.json()
        assert data[0]['document_title'] == 'Notice Paper 1'
        assert data[0]['source_url'] == 'https://example.org/doc-1'

    def test_list_unauthenticated_blocked(self, tmp_path, monkeypatch):
        db_path = tmp_path / 'test.db'
        monkeypatch.setenv('DATABASE_PATH', str(db_path))
        monkeypatch.setenv('ENV', 'development')
        migrate_module.migrate()
        client = TestClient(app)
        resp = client.get('/api/v1/admin/entity-review')
        assert resp.status_code == 401


class TestResolveEntity:
    def test_resolve_entity(self, editor_client):
        # Get entity IDs
        resp = editor_client.get('/api/v1/admin/entity-review')
        entities = resp.json()
        entity_id = entities[0]['id']

        # Get MP ID
        mp_id = entities[0]['suggestions'][0]['id']

        # Resolve
        resp2 = editor_client.post(
            f'/api/v1/admin/entity-review/{entity_id}/resolve',
            json={'mp_id': mp_id},
        )
        assert resp2.status_code == 200
        assert resp2.json()['mp_name'] == 'Jane Motswana'

        # Entity should no longer appear in list
        resp3 = editor_client.get('/api/v1/admin/entity-review')
        remaining_ids = {e['id'] for e in resp3.json()}
        assert entity_id not in remaining_ids

    def test_resolve_entity_not_found(self, editor_client):
        resp = editor_client.post(
            '/api/v1/admin/entity-review/99999/resolve',
            json={'mp_id': 1},
        )
        assert resp.status_code == 404

    def test_resolve_entity_no_mp_id(self, editor_client):
        resp = editor_client.get('/api/v1/admin/entity-review')
        entity_id = resp.json()[0]['id']

        resp2 = editor_client.post(
            f'/api/v1/admin/entity-review/{entity_id}/resolve',
            json={},
        )
        assert resp2.status_code == 400

    def test_resolve_already_resolved(self, editor_client):
        # Find the RESOLVED entity
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT id FROM entity_review_queue WHERE status = 'RESOLVED'",
            ).fetchone()
            resolved_id = row['id']
        finally:
            conn.close()

        resp = editor_client.post(
            f'/api/v1/admin/entity-review/{resolved_id}/resolve',
            json={'mp_id': 1},
        )
        assert resp.status_code == 409


class TestSkipEntity:
    def test_skip_entity(self, editor_client):
        resp = editor_client.get('/api/v1/admin/entity-review')
        entities = resp.json()
        entity_id = entities[0]['id']

        resp2 = editor_client.post(
            f'/api/v1/admin/entity-review/{entity_id}/skip',
            json={},
        )
        assert resp2.status_code == 200

        # Entity should no longer appear in list
        resp3 = editor_client.get('/api/v1/admin/entity-review')
        remaining_ids = {e['id'] for e in resp3.json()}
        assert entity_id not in remaining_ids

    def test_skip_entity_not_found(self, editor_client):
        resp = editor_client.post(
            '/api/v1/admin/entity-review/99999/skip',
            json={},
        )
        assert resp.status_code == 404
