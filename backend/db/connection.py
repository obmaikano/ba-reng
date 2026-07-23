"""SQLite connection management."""

import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / 'data'
DB_PATH = DATA_DIR / 'bareng.db'


def get_connection() -> sqlite3.Connection:
    """Get a SQLite connection with WAL mode and foreign keys enabled."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA foreign_keys=ON')
    conn.row_factory = sqlite3.Row
    return conn
