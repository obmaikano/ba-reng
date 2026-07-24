"""Auth routes: login, logout, me."""

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Response

from backend.api.middleware.auth import COOKIE_SECURE, create_access_token, get_current_user
from backend.db.connection import get_connection

router = APIRouter(prefix='/api/v1/auth', tags=['auth'])

# Checked even when the email doesn't exist, so a login attempt against an unknown
# address takes the same time as one against a real account (avoids an email-
# enumeration timing side-channel on the bcrypt check).
_DUMMY_HASH = bcrypt.hashpw(b'not-a-real-password', bcrypt.gensalt()).decode()


@router.post('/login')
def login(body: dict, response: Response) -> dict:
    email = body.get('email', '').strip().lower()
    password = body.get('password', '')

    if not email or not password:
        raise HTTPException(status_code=400, detail='Email and password required')
    if len(password) < 8:
        raise HTTPException(status_code=400, detail='Password must be at least 8 characters')

    conn = get_connection()
    try:
        row = conn.execute(
            'SELECT id, email, display_name, password_hash, role, is_active '
            'FROM users WHERE email = ?',
            (email,),
        ).fetchone()

        password_hash = row['password_hash'] if row else _DUMMY_HASH
        password_ok = bcrypt.checkpw(password.encode(), password_hash.encode())

        if not row or not row['is_active'] or not password_ok:
            raise HTTPException(status_code=401, detail='Invalid credentials')

        token = create_access_token(row['id'], row['role'])

        response.set_cookie(
            key='access_token',
            value=token,
            httponly=True,
            samesite='lax',
            secure=COOKIE_SECURE,
            max_age=480 * 60,
        )

        conn.execute(
            'UPDATE users SET last_login_at = datetime("now") WHERE id = ?',
            (row['id'],),
        )
        conn.commit()

        return {
            'id': row['id'],
            'email': row['email'],
            'display_name': row['display_name'],
            'role': row['role'],
        }
    finally:
        conn.close()


@router.post('/logout')
def logout(response: Response, current_user: dict = Depends(get_current_user)) -> dict:
    response.delete_cookie(key='access_token', httponly=True, samesite='lax', secure=COOKIE_SECURE)
    return {'detail': 'Logged out'}


@router.get('/me')
def me(current_user: dict = Depends(get_current_user)) -> dict:
    return current_user
