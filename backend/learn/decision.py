"""Structured decision logger — captures reasoning chains for self-learning.

Captures the full decision context: files read, tests checked, constraints
identified, unknowns flagged, and outcomes. Successful decisions boost
memory confidence. Failed decisions are recorded as anti-patterns.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from hashlib import md5
from typing import Any, Literal

from backend.learn.config import get_config
from backend.learn.connection import LearnConnection
from backend.learn.memory import Memory

logger = logging.getLogger(__name__)

DECISION_TABLE = 'learn_decision'


class DecisionLog:
    """Structured capture of reasoning chains and outcomes."""

    def __init__(self) -> None:
        """Initialize the decision logger."""
        self._cfg = get_config()
        self._conn = LearnConnection.get()
        self._memory = Memory()
        self._ensure_table()

    def _ensure_table(self) -> None:
        """Create the decision table."""
        self._conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {DECISION_TABLE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL DEFAULT '',
                created_at REAL NOT NULL,
                summary TEXT NOT NULL DEFAULT '',
                files_read TEXT NOT NULL DEFAULT '[]',
                constraints_checked TEXT NOT NULL DEFAULT '[]',
                unknowns_flagged TEXT NOT NULL DEFAULT '[]',
                decision_made TEXT NOT NULL DEFAULT '',
                outcome TEXT NOT NULL DEFAULT 'pending',
                confidence_boost REAL NOT NULL DEFAULT 0.0,
                memory_keys TEXT NOT NULL DEFAULT '[]'
            )
        """)
        self._conn.commit()

    def record(
        self,
        summary: str,
        decision_made: str,
        files_read: list[str] | None = None,
        constraints_checked: list[str] | None = None,
        unknowns_flagged: list[str] | None = None,
        session_id: str = '',
    ) -> int:
        """Capture a reasoning step.

        Args:
            summary: One-line description of what was being reasoned about.
            decision_made: The conclusion or action taken.
            files_read: Files consulted during reasoning.
            constraints_checked: Constraints or tests verified.
            unknowns_flagged: Questions or gaps identified.
            session_id: Session identifier.

        Returns:
            Decision entry ID.
        """
        try:
            now = time.time()
            cursor = self._conn.execute(
                f"""INSERT INTO {DECISION_TABLE}
                    (session_id, created_at, summary, files_read,
                     constraints_checked, unknowns_flagged, decision_made)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id, now, summary,
                    json.dumps(files_read or [], ensure_ascii=False),
                    json.dumps(constraints_checked or [], ensure_ascii=False),
                    json.dumps(unknowns_flagged or [], ensure_ascii=False),
                    decision_made,
                ),
            )
            self._conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as exc:
            logger.error('Decision record failed: %s', exc)
            return -1

    def mark_outcome(
        self,
        decision_id: int,
        outcome: Literal['success', 'failure', 'partial', 'neutral'],
        details: str = '',
    ) -> None:
        """Mark the outcome of a decision.

        If successful, auto-creates a memory entry with boosted confidence.
        """
        try:
            self._conn.execute(
                f'UPDATE {DECISION_TABLE} SET outcome = ? WHERE id = ?',
                (outcome, decision_id),
            )
            self._conn.commit()
        except sqlite3.Error as exc:
            logger.error('Outcome update failed: %s', exc)
            return

        if outcome == 'success':
            try:
                row = self._conn.execute(
                    f'SELECT * FROM {DECISION_TABLE} WHERE id = ?', (decision_id,),
                ).fetchone()
                if row:
                    self._learn_from_success(dict(row), details)
            except sqlite3.Error as exc:
                logger.error('Learning from success failed for decision %d: %s', decision_id, exc)

    def _learn_from_success(self, decision: dict[str, Any], details: str) -> None:
        """Create boosted-confidence memory entries from a successful decision."""
        summary = decision['summary']
        summary_key = f'{summary[:50]}_{md5(summary.encode()).hexdigest()[:6]}'
        files = json.loads(decision['files_read'])
        constraints = json.loads(decision['constraints_checked'])
        decision_text = decision['decision_made']

        if files:
            self._memory.store(
                key=f'decision_files_{summary_key}',
                value=(
                    f'When reasoning about "{summary}", these files were '
                    f'relevant: {", ".join(files)}'
                ),
                category='pattern',
                confidence=0.85,
                source='decision_log',
                session_id=decision['session_id'],
            )

        if constraints:
            self._memory.store(
                key=f'decision_constraints_{summary_key}',
                value=f'When making "{summary}", these constraints apply: {"; ".join(constraints)}',
                category='decision',
                confidence=0.9,
                source='decision_log',
                session_id=decision['session_id'],
            )

        self._memory.store(
            key=f'decision_{summary_key}',
            value=f'Decision: {decision_text}. Outcome: success. Details: {details}',
            category='decision',
            confidence=0.9,
            source='decision_log',
            session_id=decision['session_id'],
        )

        key_list = json.loads(decision.get('memory_keys', '[]'))
        key_list.append(f'decision_{summary_key}')
        self._conn.execute(
            f'UPDATE {DECISION_TABLE} SET confidence_boost = 0.9, memory_keys = ? WHERE id = ?',
            (json.dumps(key_list), decision['id']),
        )
        self._conn.commit()

    def get_context_block(self, query: str, limit: int = 5) -> str:
        """Get recent decisions relevant to a query as context."""
        try:
            rows = self._conn.execute(
                f"""SELECT * FROM {DECISION_TABLE}
                    WHERE outcome = 'success'
                    AND (summary LIKE ? OR decision_made LIKE ?)
                    ORDER BY created_at DESC LIMIT ?
                """,
                (f'%{query}%', f'%{query}%', limit),
            ).fetchall()
        except sqlite3.Error:
            rows = []

        if not rows:
            return ''

        lines = ['## Prior Decisions', '']
        for r in rows:
            files = json.loads(r['files_read'])
            constraints = json.loads(r['constraints_checked'])
            unknowns = json.loads(r['unknowns_flagged'])
            lines.append(f'### {r["summary"]}')
            lines.append(f'Decision: {r["decision_made"]}')
            if files:
                lines.append(f'Files consulted: {", ".join(files)}')
            if constraints:
                lines.append(f'Constraints verified: {"; ".join(constraints)}')
            if unknowns:
                lines.append(f'Unknowns flagged: {"; ".join(unknowns)}')
            lines.append('')
        return '\n'.join(lines)

    def stats(self) -> dict[str, int]:
        """Return decision log statistics."""
        try:
            total = self._conn.execute(
                f'SELECT COUNT(*) as c FROM {DECISION_TABLE}',
            ).fetchone()
            successes = self._conn.execute(
                f"SELECT COUNT(*) as c FROM {DECISION_TABLE} WHERE outcome = 'success'",
            ).fetchone()
            return {
                'total_decisions': total['c'],
                'successful_decisions': successes['c'],
            }
        except sqlite3.Error:
            return {'total_decisions': 0, 'successful_decisions': 0}
