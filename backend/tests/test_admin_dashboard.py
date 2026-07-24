"""Tests for admin dashboard, crawl trigger, and crawl-runs endpoints."""

import bcrypt
import pytest
from fastapi.testclient import TestClient

from backend.db import migrate as migrate_module
from backend.db.connection import get_connection
from backend.main import app


@pytest.fixture
def admin_client(tmp_path, monkeypatch) -> TestClient:
    """Fresh DB with admin user, returns logged-in TestClient."""
    db_path = tmp_path / 'test.db'
    monkeypatch.setenv('DATABASE_PATH', str(db_path))
    monkeypatch.setenv('ENV', 'development')

    migrate_module.migrate()

    conn = get_connection()
    try:
        password_hash = bcrypt.hashpw(b'admin-pass', bcrypt.gensalt()).decode()
        conn.execute(
            'INSERT INTO users (email, password_hash, display_name, role, is_active) '
            'VALUES (?, ?, ?, ?, ?)',
            ('admin@bareng.bw', password_hash, 'Admin', 'admin', 1),
        )
        password_hash2 = bcrypt.hashpw(b'editor-pass', bcrypt.gensalt()).decode()
        conn.execute(
            'INSERT INTO users (email, password_hash, display_name, role, is_active) '
            'VALUES (?, ?, ?, ?, ?)',
            ('editor@bareng.bw', password_hash2, 'Editor', 'editor', 1),
        )
        conn.commit()
    finally:
        conn.close()

    client = TestClient(app)
    resp = client.post(
        '/api/v1/auth/login',
        json={'email': 'admin@bareng.bw', 'password': 'admin-pass'},
    )
    assert resp.status_code == 200
    cookie = resp.cookies.get('access_token', '')
    client.cookies.set('access_token', cookie)
    return client


@pytest.fixture
def editor_client(tmp_path, monkeypatch) -> TestClient:
    """Fresh DB with editor user, returns logged-in TestClient."""
    db_path = tmp_path / 'test.db'
    monkeypatch.setenv('DATABASE_PATH', str(db_path))
    monkeypatch.setenv('ENV', 'development')

    migrate_module.migrate()

    conn = get_connection()
    try:
        password_hash = bcrypt.hashpw(b'admin-pass', bcrypt.gensalt()).decode()
        conn.execute(
            'INSERT INTO users (email, password_hash, display_name, role, is_active) '
            'VALUES (?, ?, ?, ?, ?)',
            ('admin@bareng.bw', password_hash, 'Admin', 'admin', 1),
        )
        password_hash2 = bcrypt.hashpw(b'editor-pass', bcrypt.gensalt()).decode()
        conn.execute(
            'INSERT INTO users (email, password_hash, display_name, role, is_active) '
            'VALUES (?, ?, ?, ?, ?)',
            ('editor@bareng.bw', password_hash2, 'Editor', 'editor', 1),
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


class TestAdminDashboard:
    def test_dashboard_returns_counts(self, admin_client):
        resp = admin_client.get('/api/v1/admin/dashboard')
        assert resp.status_code == 200
        body = resp.json()
        assert 'mp_count' in body
        assert 'contribution_count' in body
        assert 'document_count' in body
        assert 'unresolved_entity_count' in body
        assert 'resolved_entity_count' in body
        assert 'last_crawl' in body
        assert 'crawl_running' in body

    def test_dashboard_empty_state(self, admin_client):
        resp = admin_client.get('/api/v1/admin/dashboard')
        assert resp.status_code == 200
        body = resp.json()
        assert body['mp_count'] == 0
        assert body['contribution_count'] == 0
        assert body['document_count'] == 0
        assert body['unresolved_entity_count'] == 0
        assert body['last_crawl'] is None

    def test_dashboard_editor_can_access(self, editor_client):
        resp = editor_client.get('/api/v1/admin/dashboard')
        assert resp.status_code == 200

    def test_dashboard_unauthenticated_blocked(self, tmp_path, monkeypatch):
        db_path = tmp_path / 'test.db'
        monkeypatch.setenv('DATABASE_PATH', str(db_path))
        monkeypatch.setenv('ENV', 'development')
        migrate_module.migrate()
        client = TestClient(app)
        resp = client.get('/api/v1/admin/dashboard')
        assert resp.status_code == 401


class TestCrawlRuns:
    def test_crawl_runs_returns_list(self, admin_client):
        resp = admin_client.get('/api/v1/admin/crawl-runs')
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_crawl_runs_empty(self, admin_client):
        resp = admin_client.get('/api/v1/admin/crawl-runs')
        assert resp.status_code == 200
        assert resp.json() == []

    def test_crawl_runs_editor_can_access(self, editor_client):
        resp = editor_client.get('/api/v1/admin/crawl-runs')
        assert resp.status_code == 200


class TestCrawlTrigger:
    def test_trigger_crawl_as_admin(self, admin_client, monkeypatch):
        # Mock crawl_all to avoid actually running crawlers
        monkeypatch.setattr(
            'backend.crawl.crawl_all',
            lambda: {'test': {'status': 'SUCCESS', 'new_documents': 5}},
        )
        resp = admin_client.post('/api/v1/admin/crawl/trigger', json={})
        assert resp.status_code == 200
        assert resp.json()['status'] == 'RUNNING'

    def test_trigger_crawl_as_editor_blocked(self, editor_client):
        resp = editor_client.post('/api/v1/admin/crawl/trigger', json={})
        assert resp.status_code == 403

    def test_trigger_crawl_unauthenticated_blocked(self, tmp_path, monkeypatch):
        db_path = tmp_path / 'test.db'
        monkeypatch.setenv('DATABASE_PATH', str(db_path))
        monkeypatch.setenv('ENV', 'development')
        migrate_module.migrate()
        client = TestClient(app)
        resp = client.post('/api/v1/admin/crawl/trigger', json={})
        assert resp.status_code == 401

    def test_trigger_crawl_twice_returns_409(self, admin_client, monkeypatch):
        # Replace the background thread target to block, simulating a running crawl
        import backend.api.admin.routes as admin_routes
        admin_routes._crawl_running = True
        try:
            resp = admin_client.post('/api/v1/admin/crawl/trigger', json={})
            assert resp.status_code == 409
        finally:
            admin_routes._crawl_running = False
