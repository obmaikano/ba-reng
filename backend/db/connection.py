"""SQLite connection management."""

import hashlib
import os
import sqlite3
from pathlib import Path
from typing import AsyncGenerator

import aiosqlite


def get_db_path() -> str:
    """Return the database path from env, defaulting to data/bareng.db."""
    env_path = os.environ.get('DATABASE_PATH', '').strip()
    if env_path:
        return env_path
    data_dir = Path(__file__).resolve().parent.parent.parent / 'data'
    return str(data_dir / 'bareng.db')


def _sha256_hex(text: str | None) -> str | None:
    if text is None:
        return None
    return hashlib.sha256(text.encode()).hexdigest()


def get_connection() -> sqlite3.Connection:
    """Get a SQLite connection with WAL mode and foreign keys enabled."""
    db_path = get_db_path()
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA foreign_keys=ON')
    conn.row_factory = sqlite3.Row
    conn.create_function('SHA256_HEX', 1, _sha256_hex, deterministic=True)
    return conn


async def get_async_connection() -> aiosqlite.Connection:
    """Get an async SQLite connection with WAL mode and foreign keys enabled."""
    db_path = get_db_path()
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = await aiosqlite.connect(db_path)
    await conn.execute('PRAGMA journal_mode=WAL')
    await conn.execute('PRAGMA foreign_keys=ON')
    conn.row_factory = aiosqlite.Row
    await conn.create_function('SHA256_HEX', 1, _sha256_hex, deterministic=True)
    return conn


async def get_async_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    """FastAPI dependency: yields an async SQLite connection."""
    conn = await get_async_connection()
    try:
        yield conn
    finally:
        await conn.close()
