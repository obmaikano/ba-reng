"""Ministerial Deferral & Responsiveness Scorecard — answer-or-dodge analytics."""

import sqlite3
from typing import Any


def deferral_scorecard(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Calculate deferral rates per ministry from deferred_questions table.

    Returns a list of ministry scorecard objects with:
      - ministry: canonical ministry name
      - deferred_count: questions marked 'Later Date' / DEFERRED
      - total_questions: all questions addressed to this ministry
      - deferral_rate_pct: (deferred / total) * 100
      - backlog_count: DEFERRED questions older than 30 days
    """
    cursor = conn.cursor()

    rows = cursor.execute(
        """SELECT dq.id, m.canonical_name AS ministry, dq.original_date, dq.status
           FROM deferred_questions dq
           JOIN ministries m ON dq.ministry_id = m.id
           WHERE dq.status = 'DEFERRED'""",
    ).fetchall()

    if not rows:
        return []

    by_ministry: dict[str, dict[str, Any]] = {}
    for row in rows:
        ministry = row['ministry']
        if ministry not in by_ministry:
            by_ministry[ministry] = {
                'ministry': ministry,
                'deferred_count': 0,
                'backlog_count': 0,
                'total_questions': 0,
            }
        by_ministry[ministry]['deferred_count'] += 1

        if row['original_date']:
            days_old = cursor.execute(
                "SELECT julianday('now') - julianday(?)", (row['original_date'],),
            ).fetchone()
            if days_old and days_old[0] > 30:
                by_ministry[ministry]['backlog_count'] += 1

    for ministry in by_ministry:
        total = cursor.execute(
            """SELECT COUNT(*) AS cnt FROM contributions
               WHERE ministry_addressed = ? AND contribution_type IN
               ('oral_question', 'question', 'question_without_notice')""",
            (ministry,),
        ).fetchone()
        by_ministry[ministry]['total_questions'] = total['cnt'] if total else 0

        tq = by_ministry[ministry]['total_questions']
        dc = by_ministry[ministry]['deferred_count']
        by_ministry[ministry]['deferral_rate_pct'] = round(dc / tq * 100, 1) if tq > 0 else 0.0

    return sorted(
        by_ministry.values(),
        key=lambda x: x['deferral_rate_pct'],
        reverse=True,
    )


def deferral_alert(scorecard: list[dict[str, Any]]) -> str | None:
    """Generate a single-line alert for the worst offender, if any."""
    if not scorecard:
        return None

    worst = scorecard[0]
    if worst['deferral_rate_pct'] == 0:
        return None

    return (
        f'{worst["ministry"]} has a {worst["deferral_rate_pct"]}% deferral rate '
        f'({worst["deferred_count"]} of {worst["total_questions"]} questions deferred), '
        f'with {worst["backlog_count"]} unanswered past 30 days.'
    )
