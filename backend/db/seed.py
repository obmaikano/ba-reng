"""Seed the database with initial admin user."""

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

        password_hash = bcrypt.hashpw(b'admin', bcrypt.gensalt()).decode()
        conn.execute(
            "INSERT INTO users (email, password_hash, display_name, role) "
            "VALUES (?, ?, ?, 'admin')",
            ('admin@bareng.bw', password_hash, 'Admin'),
        )
        conn.commit()
        print('  Created admin user: admin@bareng.bw / admin')
    finally:
        conn.close()


if __name__ == '__main__':
    seed()
