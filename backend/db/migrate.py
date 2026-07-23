"""Migration runner for SQLite schema updates."""

import sqlite3
from pathlib import Path

from backend.db.connection import get_connection

MIGRATIONS_DIR = Path(__file__).resolve().parent / 'migrations'


def ensure_tracking_table(conn: sqlite3.Connection) -> None:
    """Create the applied_migrations tracking table if it does not exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS applied_migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE NOT NULL,
            applied_at TEXT DEFAULT (datetime('now'))
        )
    """)


def get_applied(conn: sqlite3.Connection) -> set[str]:
    """Return the set of already-applied migration filenames."""
    rows = conn.execute('SELECT filename FROM applied_migrations').fetchall()
    return {r['filename'] for r in rows}


def migrate() -> None:
    """Apply all pending migrations in order."""
    conn = get_connection()
    ensure_tracking_table(conn)
    applied = get_applied(conn)

    migrations = sorted(MIGRATIONS_DIR.glob('*.sql'))
    for path in migrations:
        if path.name in applied:
            continue
        sql = path.read_text()
        conn.executescript(sql)
        conn.execute(
            'INSERT INTO applied_migrations (filename) VALUES (?)',
            (path.name,),
        )
        print(f'  Applied: {path.name}')

    conn.commit()
    conn.close()


if __name__ == '__main__':
    migrate()
