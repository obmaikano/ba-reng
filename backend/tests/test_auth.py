"""Tests for authentication: login, logout, JWT cookies, and role-gating."""

import bcrypt
import pytest
from fastapi.testclient import TestClient

from backend.db import migrate as migrate_module
from backend.db.connection import get_connection
from backend.main import app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client(tmp_path, monkeypatch) -> TestClient:
    """Fresh migrated DB with seeded users."""
    db_path = tmp_path / 'test.db'
    monkeypatch.setenv('DATABASE_PATH', str(db_path))
    monkeypatch.setenv('ENV', 'development')

    migrate_module.migrate()

    conn = get_connection()
    try:
        # Active admin
        password_hash = bcrypt.hashpw(b'admin-pass', bcrypt.gensalt()).decode()
        conn.execute(
            'INSERT INTO users (email, password_hash, display_name, role, is_active) '
            'VALUES (?, ?, ?, ?, ?)',
            ('admin@bareng.bw', password_hash, 'Admin', 'admin', 1),
        )
        # Active editor
        password_hash2 = bcrypt.hashpw(b'editor-pass', bcrypt.gensalt()).decode()
        conn.execute(
            'INSERT INTO users (email, password_hash, display_name, role, is_active) '
            'VALUES (?, ?, ?, ?, ?)',
            ('editor@bareng.bw', password_hash2, 'Editor', 'editor', 1),
        )
        # Active viewer
        password_hash3 = bcrypt.hashpw(b'viewer-pass', bcrypt.gensalt()).decode()
        conn.execute(
            'INSERT INTO users (email, password_hash, display_name, role, is_active) '
            'VALUES (?, ?, ?, ?, ?)',
            ('viewer@bareng.bw', password_hash3, 'Viewer', 'viewer', 1),
        )
        # Inactive user
        password_hash4 = bcrypt.hashpw(b'inactive-pass', bcrypt.gensalt()).decode()
        conn.execute(
            'INSERT INTO users (email, password_hash, display_name, role, is_active) '
            'VALUES (?, ?, ?, ?, ?)',
            ('inactive@bareng.bw', password_hash4, 'Inactive', 'viewer', 0),
        )
        conn.commit()
    finally:
        conn.close()

    return TestClient(app)


def _login(client: TestClient, email: str, password: str) -> tuple:
    """Helper: login and return (status, body, cookie_value_if_present)."""
    resp = client.post(
        '/api/v1/auth/login',
        json={'email': email, 'password': password},
    )
    cookie = resp.cookies.get('access_token', '')
    if resp.status_code == 200:
        return resp.status_code, resp.json(), cookie
    return resp.status_code, None, cookie


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


class TestLogin:
    """PLAN.md 4.0 AC: Login with valid/invalid credentials."""

    def test_login_valid_credentials(self, client):
        status, body, cookie = _login(client, 'admin@bareng.bw', 'admin-pass')
        assert status == 200
        assert body['role'] == 'admin'
        assert body['display_name'] == 'Admin'
        assert 'id' in body
        assert cookie
        assert len(cookie) > 20

    def test_login_invalid_password_returns_401(self, client):
        status, _, cookie = _login(client, 'admin@bareng.bw', 'wrong-pass')
        assert status == 401
        assert cookie == ''

    def test_login_unknown_email_returns_401(self, client):
        status, _, cookie = _login(client, 'nobody@bareng.bw', 'anything')
        assert status == 401
        assert cookie == ''

    def test_login_inactive_user_returns_401(self, client):
        status, _, cookie = _login(client, 'inactive@bareng.bw', 'inactive-pass')
        assert status == 401
        assert cookie == ''

    def test_login_missing_email_and_password_returns_400(self, client):
        resp = client.post('/api/v1/auth/login', json={})
        assert resp.status_code == 400

    def test_login_empty_email_returns_400(self, client):
        resp = client.post(
            '/api/v1/auth/login',
            json={'email': '', 'password': 'x'},
        )
        assert resp.status_code == 400

    def test_login_empty_password_returns_400(self, client):
        resp = client.post(
            '/api/v1/auth/login',
            json={'email': 'admin@bareng.bw', 'password': ''},
        )
        assert resp.status_code == 400

    def test_login_case_insensitive_email(self, client):
        status, body, _ = _login(client, 'ADMIN@bareng.bw', 'admin-pass')
        assert status == 200

    def test_login_whitespace_around_email(self, client):
        status, body, _ = _login(client, '  admin@bareng.bw  ', 'admin-pass')
        assert status == 200

    def test_login_short_password_returns_400(self, client):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@bareng.bw", "password": "short"},
        )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------


class TestLogout:
    """PLAN.md 4.0: Logout clears JWT cookie."""

    def test_logout_clears_cookie(self, client):
        _, _, cookie = _login(client, 'admin@bareng.bw', 'admin-pass')
        resp = client.post(
            '/api/v1/auth/logout',
            cookies={'access_token': cookie},
        )
        assert resp.status_code == 200
        set_cookie = resp.headers.get('set-cookie', '')
        assert 'access_token=' in set_cookie

    def test_logout_without_cookie_returns_401(self, client):
        resp = client.post('/api/v1/auth/logout')
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# /me
# ---------------------------------------------------------------------------


class TestMe:
    """PLAN.md 4.0: GET /api/v1/auth/me returns current user."""

    def test_me_authenticated(self, client):
        _, _, cookie = _login(client, 'admin@bareng.bw', 'admin-pass')
        resp = client.get(
            '/api/v1/auth/me',
            cookies={'access_token': cookie},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body['role'] == 'admin'
        assert 'id' in body

    def test_me_unauthenticated_returns_401(self, client):
        resp = client.get('/api/v1/auth/me')
        assert resp.status_code == 401

    def test_me_invalid_token_returns_401(self, client):
        resp = client.get(
            '/api/v1/auth/me',
            cookies={'access_token': 'not-a-real-jwt-token'},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Role-gating on admin endpoints
# ---------------------------------------------------------------------------


class TestRoleGating:
    """PLAN.md 4.0 AC: Protected routes reject insufficient roles."""

    def test_editor_accesses_admin_endpoint(self, client):
        _, _, cookie = _login(client, 'editor@bareng.bw', 'editor-pass')
        resp = client.get(
            '/api/v1/admin/mps',
            cookies={'access_token': cookie},
        )
        assert resp.status_code == 200

    def test_viewer_blocked_from_admin_endpoint(self, client):
        _, _, cookie = _login(client, 'viewer@bareng.bw', 'viewer-pass')
        resp = client.get(
            '/api/v1/admin/mps',
            cookies={'access_token': cookie},
        )
        assert resp.status_code == 403

    def test_unauthenticated_blocked_from_admin_endpoint(self, client):
        resp = client.get('/api/v1/admin/mps')
        assert resp.status_code == 401

    def test_viewer_blocked_from_ministry_mappings(self, client):
        _, _, cookie = _login(client, 'viewer@bareng.bw', 'viewer-pass')
        resp = client.get(
            '/api/v1/admin/ministry-mappings',
            cookies={'access_token': cookie},
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Token security
# ---------------------------------------------------------------------------


class TestTokenSecurity:
    def test_expired_token_returns_401(self, client):
        from datetime import datetime, timedelta, timezone

        from jose import jwt as _jwt

        old = datetime(2020, 1, 1, tzinfo=timezone.utc)
        token = _jwt.encode(
            {'sub': '1', 'role': 'admin', 'iat': old, 'exp': old + timedelta(minutes=1)},
            'ba-reng-dev-secret-do-not-use-in-production',
            algorithm='HS256',
        )
        resp = client.get(
            '/api/v1/auth/me',
            cookies={'access_token': token},
        )
        assert resp.status_code == 401

    def test_tampered_token_returns_401(self, client):
        _, _, cookie = _login(client, 'admin@bareng.bw', 'admin-pass')
        parts = cookie.split('.')
        assert len(parts) == 3, f'Expected 3-part JWT, got {len(parts)} parts'
        tampered = f'{parts[0]}.{parts[1]}.{parts[2][:-1]}x'
        resp = client.get(
            '/api/v1/auth/me',
            cookies={'access_token': tampered},
        )
        assert resp.status_code == 401

    def test_token_with_deleted_user_returns_401(self, client):
        _, _, cookie = _login(client, 'admin@bareng.bw', 'admin-pass')
        conn = get_connection()
        try:
            conn.execute('DELETE FROM users WHERE email = ?', ('admin@bareng.bw',))
            conn.commit()
        finally:
            conn.close()
        resp = client.get(
            '/api/v1/auth/me',
            cookies={'access_token': cookie},
        )
        assert resp.status_code == 401

