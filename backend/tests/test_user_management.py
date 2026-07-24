"""Tests for user management CRUD endpoints (admin only)."""

import bcrypt
import pytest
from fastapi.testclient import TestClient

from backend.db import migrate as migrate_module
from backend.db.connection import get_connection
from backend.main import app


@pytest.fixture
def admin_client(tmp_path, monkeypatch) -> TestClient:
    """Logged-in admin."""
    db_path = tmp_path / 'test.db'
    monkeypatch.setenv('DATABASE_PATH', str(db_path))
    monkeypatch.setenv('ENV', 'development')
    migrate_module.migrate()
    conn = get_connection()
    try:
        pw = bcrypt.hashpw(b'admin-pass', bcrypt.gensalt()).decode()
        conn.execute(
            'INSERT INTO users (email, password_hash, display_name, role, is_active) '
            'VALUES (?, ?, ?, ?, ?)',
            ('admin@bareng.bw', pw, 'Admin', 'admin', 1),
        )
        conn.commit()
    finally:
        conn.close()

    client = TestClient(app)
    resp = client.post('/api/v1/auth/login', json={'email': 'admin@bareng.bw', 'password': 'admin-pass'})
    client.cookies.set('access_token', resp.cookies.get('access_token', ''))
    return client


@pytest.fixture
def editor_client(tmp_path, monkeypatch) -> TestClient:
    """Logged-in editor."""
    db_path = tmp_path / 'test.db'
    monkeypatch.setenv('DATABASE_PATH', str(db_path))
    monkeypatch.setenv('ENV', 'development')
    migrate_module.migrate()
    conn = get_connection()
    try:
        pw = bcrypt.hashpw(b'editor-pass', bcrypt.gensalt()).decode()
        conn.execute(
            'INSERT INTO users (email, password_hash, display_name, role, is_active) '
            'VALUES (?, ?, ?, ?, ?)',
            ('editor@bareng.bw', pw, 'Editor', 'editor', 1),
        )
        conn.commit()
    finally:
        conn.close()

    client = TestClient(app)
    resp = client.post('/api/v1/auth/login', json={'email': 'editor@bareng.bw', 'password': 'editor-pass'})
    client.cookies.set('access_token', resp.cookies.get('access_token', ''))
    return client


class TestListUsers:
    def test_admin_lists_users(self, admin_client):
        resp = admin_client.get('/api/v1/admin/users')
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]['email'] == 'admin@bareng.bw'

    def test_editor_blocked_from_users(self, editor_client):
        resp = editor_client.get('/api/v1/admin/users')
        assert resp.status_code == 403

    def test_unauthenticated_blocked(self, tmp_path, monkeypatch):
        db_path = tmp_path / 'test.db'
        monkeypatch.setenv('DATABASE_PATH', str(db_path))
        monkeypatch.setenv('ENV', 'development')
        migrate_module.migrate()
        client = TestClient(app)
        resp = client.get('/api/v1/admin/users')
        assert resp.status_code == 401


class TestCreateUser:
    def test_create_user(self, admin_client):
        resp = admin_client.post('/api/v1/admin/users', json={
            'email': 'new@bareng.bw',
            'display_name': 'New User',
            'role': 'editor',
            'password': 'new-pass-123',
        })
        assert resp.status_code == 201
        assert resp.json()['email'] == 'new@bareng.bw'
        assert resp.json()['role'] == 'editor'

        # Verify can login
        client2 = TestClient(app)
        resp2 = client2.post('/api/v1/auth/login', json={
            'email': 'new@bareng.bw',
            'password': 'new-pass-123',
        })
        assert resp2.status_code == 200

    def test_create_duplicate_email_409(self, admin_client):
        resp = admin_client.post('/api/v1/admin/users', json={
            'email': 'admin@bareng.bw',
            'display_name': 'Dup',
            'role': 'viewer',
            'password': 'dup-pass-123',
        })
        assert resp.status_code == 409

    def test_create_no_email_400(self, admin_client):
        resp = admin_client.post('/api/v1/admin/users', json={
            'display_name': 'No Email',
            'role': 'viewer',
            'password': 'pass-12345',
        })
        assert resp.status_code == 400

    def test_create_invalid_role_400(self, admin_client):
        resp = admin_client.post('/api/v1/admin/users', json={
            'email': 'bad@bareng.bw',
            'display_name': 'Bad Role',
            'role': 'superadmin',
            'password': 'pass-12345',
        })
        assert resp.status_code == 400

    def test_create_short_password_400(self, admin_client):
        resp = admin_client.post('/api/v1/admin/users', json={
            'email': 'short@bareng.bw',
            'display_name': 'Short PW',
            'role': 'viewer',
            'password': 'short',
        })
        assert resp.status_code == 400

    def test_editor_blocked_from_create(self, editor_client):
        resp = editor_client.post('/api/v1/admin/users', json={
            'email': 'x@bareng.bw',
            'display_name': 'X',
            'role': 'viewer',
            'password': 'pass-12345',
        })
        assert resp.status_code == 403


class TestUpdateUser:
    def test_update_role(self, admin_client):
        # Create a user first
        admin_client.post('/api/v1/admin/users', json={
            'email': 'torole@bareng.bw',
            'display_name': 'To Role',
            'role': 'viewer',
            'password': 'pass-12345',
        })
        # Get user ID
        resp = admin_client.get('/api/v1/admin/users')
        uid = next(u['id'] for u in resp.json() if u['email'] == 'torole@bareng.bw')

        # Update role
        resp2 = admin_client.put(f'/api/v1/admin/users/{uid}', json={'role': 'editor'})
        assert resp2.status_code == 200

        # Verify
        resp3 = admin_client.get('/api/v1/admin/users')
        user = next(u for u in resp3.json() if u['id'] == uid)
        assert user['role'] == 'editor'

    def test_deactivate_user(self, admin_client):
        admin_client.post('/api/v1/admin/users', json={
            'email': 'todeact@bareng.bw',
            'display_name': 'To Deact',
            'role': 'viewer',
            'password': 'pass-12345',
        })
        resp = admin_client.get('/api/v1/admin/users')
        uid = next(u['id'] for u in resp.json() if u['email'] == 'todeact@bareng.bw')

        resp2 = admin_client.put(f'/api/v1/admin/users/{uid}', json={'is_active': False})
        assert resp2.status_code == 200

        resp3 = admin_client.get('/api/v1/admin/users')
        user = next(u for u in resp3.json() if u['id'] == uid)
        assert user['is_active'] == 0

    def test_update_not_found_404(self, admin_client):
        resp = admin_client.put('/api/v1/admin/users/99999', json={'role': 'editor'})
        assert resp.status_code == 404

    def test_editor_blocked_from_update(self, editor_client):
        resp = editor_client.put('/api/v1/admin/users/1', json={'role': 'editor'})
        assert resp.status_code == 403
