"""Seed the database with initial admin user."""

import os
import secrets

import bcrypt

from backend.db.connection import get_connection


def seed() -> None:
    conn = get_connection()
    try:
        existing = conn.execute(
            "SELECT id FROM users WHERE email = 'admin@bareng.bw'",
        ).fetchone()
        if existing:
            print('  Admin user already exists, skipping.')
            return

        password = os.environ.get('ADMIN_PASSWORD', '').strip() or secrets.token_urlsafe(16)
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        conn.execute(
            "INSERT INTO users (email, password_hash, display_name, role) "
            "VALUES (?, ?, ?, 'admin')",
            ('admin@bareng.bw', password_hash, 'Admin'),
        )
        conn.commit()
        print(f'  Created admin user: admin@bareng.bw / {password}')
        print('  Set ADMIN_PASSWORD to control this, or rotate it after first login.')
    finally:
        conn.close()


if __name__ == '__main__':
    seed()
