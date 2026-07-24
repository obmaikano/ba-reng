"""Auth middleware: JWT handling, user dependency, role guard."""

import os
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt

from backend.db.connection import get_connection

SECRET_KEY: str = os.environ.get(
    'JWT_SECRET_KEY',
    'ba-reng-dev-secret-do-not-use-in-production',
)
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 480

# Cookies must be Secure (HTTPS-only) once this runs anywhere but local plain-HTTP dev.
# Opt in explicitly with ENV=production rather than defaulting to secure=True, which
# would silently break login on a bare `docker compose up` over http://localhost.
COOKIE_SECURE: bool = os.environ.get('ENV', 'development').strip().lower() == 'production'


def create_access_token(user_id: int, role: str) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {'sub': str(user_id), 'role': role, 'iat': now, 'exp': expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(request: Request) -> dict[str, Any]:
    token = request.cookies.get('access_token')
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Not authenticated',
        )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get('sub', ''))
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid token',
        ) from None

    conn = get_connection()
    try:
        row = conn.execute(
            'SELECT id, email, display_name, role, is_active FROM users WHERE id = ?',
            (user_id,),
        ).fetchone()
        if not row or not row['is_active']:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='User not found or inactive',
            )
        return {
            'id': row['id'],
            'email': row['email'],
            'display_name': row['display_name'],
            'role': row['role'],
        }
    finally:
        conn.close()


def require_role(*roles: str) -> Callable[[dict[str, Any]], dict[str, Any]]:
    def _checker(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        if current_user['role'] not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f'Role {current_user["role"]} not permitted',
            )
        return current_user
    return _checker
