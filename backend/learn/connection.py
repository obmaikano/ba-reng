"""Thread-safe SQLite connection for the learn module.

Shared by Memory and Collector to avoid duplicated connection factories.
"""

from __future__ import annotations

import sqlite3

from backend.learn.config import get_config


class LearnConnection:
    """Singleton thread-safe SQLite connection for the learn module."""

    _instance: sqlite3.Connection | None = None

    @classmethod
    def get(cls) -> sqlite3.Connection:
        """Return or create the shared thread-safe connection."""
        if cls._instance is None:
            cfg = get_config()
            conn = sqlite3.connect(cfg.db_path, check_same_thread=False)
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA foreign_keys=ON')
            conn.execute('PRAGMA busy_timeout=5000')
            conn.row_factory = sqlite3.Row
            cls._instance = conn
        return cls._instance

    @classmethod
    def close(cls) -> None:
        """Close the shared connection."""
        if cls._instance is not None:
            cls._instance.close()
            cls._instance = None
