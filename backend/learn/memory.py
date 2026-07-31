"""Persistent memory store backed by SQLite.

Stores facts, decisions, patterns, and preferences learned over time.
Auto-prunes low-confidence and stale entries.
"""

from __future__ import annotations

import logging
import sqlite3
import time
from typing import Any

from backend.learn.config import get_config
from backend.learn.connection import LearnConnection

logger = logging.getLogger(__name__)


class Memory:
    """Persistent knowledge store that accumulates learnings over sessions."""

    def __init__(self) -> None:
        """Initialize the memory store and ensure the table exists."""
        self._cfg = get_config()
        self._conn = LearnConnection.get()
        self._ensure_table()

    def _ensure_table(self) -> None:
        """Create the memory table if it does not exist."""
        self._conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self._cfg.memory_table} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL DEFAULT '',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                category TEXT NOT NULL DEFAULT 'fact',
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                confidence REAL NOT NULL DEFAULT 0.5,
                source TEXT NOT NULL DEFAULT 'inferred',
                access_count INTEGER NOT NULL DEFAULT 0,
                last_accessed REAL NOT NULL DEFAULT 0.0
            )
        """)
        self._conn.execute(f"""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_memory_key
            ON {self._cfg.memory_table} (key)
        """)
        self._conn.commit()

    def store(
        self,
        key: str,
        value: str,
        category: str = 'fact',
        confidence: float = 0.5,
        source: str = 'inferred',
        session_id: str = '',
    ) -> int:
        """Store or update a memory entry.

        Args:
            key: Unique identifier for this memory.
            value: The memory content.
            category: Type of memory (fact, decision, pattern, preference).
            confidence: Confidence score 0.0-1.0.
            source: Where this memory came from.
            session_id: Session that created/updated this memory.

        Returns:
            The memory entry ID.
        """
        try:
            now = time.time()
            self._conn.execute(
                f"""INSERT INTO {self._cfg.memory_table}
                    (session_id, created_at, updated_at, category, key, value, confidence, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(key) DO UPDATE SET
                        value = excluded.value,
                        updated_at = excluded.updated_at,
                        confidence = (confidence + excluded.confidence) / 2.0,
                        source = excluded.source,
                        session_id = excluded.session_id
                """,
                (session_id, now, now, category, key, value, confidence, source),
            )
            self._conn.commit()
            row = self._conn.execute(
                f'SELECT id FROM {self._cfg.memory_table} WHERE key = ?', (key,),
            ).fetchone()
            return row['id'] if row else -1
        except sqlite3.Error as exc:
            logger.error('Memory store failed for key=%s: %s', key, exc)
            return -1

    def retrieve(self, key: str) -> dict[str, Any] | None:
        """Retrieve a memory entry by key.

        Args:
            key: The memory key to look up.

        Returns:
            Memory dict or None if not found.
        """
        try:
            row = self._conn.execute(
                f"""SELECT * FROM {self._cfg.memory_table} WHERE key = ?
                """,
                (key,),
            ).fetchone()
            if row is None:
                return None
            self._conn.execute(
                f"""UPDATE {self._cfg.memory_table}
                    SET access_count = access_count + 1, last_accessed = ?
                    WHERE key = ?
                """,
                (time.time(), key),
            )
            self._conn.commit()
            return dict(row)
        except sqlite3.Error as exc:
            logger.error('Memory retrieve failed for key=%s: %s', key, exc)
            return None

    def search(
        self,
        query: str | None = None,
        category: str | None = None,
        min_confidence: float = 0.3,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Search memories by text query and/or category.

        Args:
            query: Substring to search in key and value.
            category: Filter by category.
            min_confidence: Minimum confidence threshold.
            limit: Maximum results.

        Returns:
            List of matching memory dicts.
        """
        try:
            sql = f"""SELECT * FROM {self._cfg.memory_table}
                      WHERE confidence >= ?
            """
            params: list[Any] = [min_confidence]
            if query:
                sql += ' AND (key LIKE ? OR value LIKE ?)'
                q = f'%{query}%'
                params.extend([q, q])
            if category:
                sql += ' AND category = ?'
                params.append(category)
            sql += ' ORDER BY confidence DESC, access_count DESC LIMIT ?'
            params.append(limit)

            rows = self._conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]
        except sqlite3.Error as exc:
            logger.error('Memory search failed: %s', exc)
            return []

    def forget(self, key: str) -> bool:
        """Remove a memory entry.

        Args:
            key: The memory key to remove.

        Returns:
            True if the entry was deleted.
        """
        try:
            cursor = self._conn.execute(
                f'DELETE FROM {self._cfg.memory_table} WHERE key = ?', (key,),
            )
            self._conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as exc:
            logger.error('Memory forget failed for key=%s: %s', key, exc)
            return False

    def get_context_block(self, query: str, limit: int | None = None) -> str:
        """Get relevant memories formatted as a context block for the model.

        Args:
            query: Search query to find relevant memories.
            limit: Maximum number of memories to include.

        Returns:
            Formatted context string.
        """
        n = limit if limit is not None else self._cfg.memory_retrieve_limit
        try:
            memories = self.search(query=query, min_confidence=0.3, limit=n)
        except sqlite3.Error as exc:
            logger.error('Memory context build failed: %s', exc)
            return ''
        if not memories:
            return ''
        lines = ['## Learned Knowledge', '']
        for m in memories:
            lines.append(f'- [{m["category"]}] {m["key"]}: {m["value"]}')
        return '\n'.join(lines)

    def prune(self) -> int:
        """Remove stale and low-confidence memories.

        Only removes entries that are BOTH old and low-confidence or unused.
        Fresh entries with low confidence are preserved.

        Returns:
            Number of memories pruned.
        """
        if self._cfg.memory_prune_age_days <= 0:
            return 0
        try:
            cutoff = time.time() - (self._cfg.memory_prune_age_days * 86400)
            cursor = self._conn.execute(
                f"""DELETE FROM {self._cfg.memory_table}
                    WHERE last_accessed < ? AND access_count < 3 AND confidence < 0.3
                """,
                (cutoff,),
            )
            self._conn.commit()
            n = cursor.rowcount
            if n > 0:
                logger.info('Pruned %d stale memory entries', n)
            return n
        except sqlite3.Error as exc:
            logger.error('Memory prune failed: %s', exc)
            return 0

    def stats(self) -> dict[str, Any]:
        """Return memory store statistics."""
        try:
            row = self._conn.execute(
                f'SELECT COUNT(*) as total, AVG(confidence) as avg_conf '
                f'FROM {self._cfg.memory_table}',
            ).fetchone()
            return {
                'total_entries': row['total'],
                'avg_confidence': round(row['avg_conf'], 3) if row['avg_conf'] else 0.0,
            }
        except sqlite3.Error as exc:
            logger.error('Memory stats failed: %s', exc)
            return {'total_entries': 0, 'avg_confidence': 0.0}

    def close(self) -> None:
        """Close the database connection."""
        LearnConnection.close()
