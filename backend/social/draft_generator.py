"""Generate draft social posts for new contributions since last run.

Human-in-the-loop: drafts are written to a review queue table, never posted automatically.
"""

from datetime import datetime, timezone
from typing import Any

from backend.db.connection import get_connection

MAX_POST_LENGTH = 280
HASHTAGS = '#Botswana #Parliament #BaReng'


def _ensure_tables(conn: Any) -> None:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS social_review_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contribution_id INTEGER NOT NULL REFERENCES contributions(id),
            draft_text TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'PENDING',
            created_at TEXT DEFAULT (datetime('now')),
            reviewed_at TEXT,
            reviewed_by TEXT
        )"""
    )
    try:
        conn.execute('ALTER TABLE contributions ADD COLUMN social_drafted INTEGER DEFAULT 0')
    except Exception:
        pass


def generate_drafts() -> list[dict[str, Any]]:
    """Find contributions not yet drafted and produce draft social posts."""
    conn = get_connection()
    try:
        _ensure_tables(conn)

        rows = conn.execute(
            """SELECT c.id, c.contribution_type, c.subject_text, c.ministry_addressed,
                      c.raw_match_name, m.name AS mp_name
               FROM contributions c
               LEFT JOIN mps m ON c.mp_id = m.id
               WHERE c.social_drafted = 0
               ORDER BY c.date DESC
               LIMIT 20"""
        ).fetchall()

        drafts: list[dict[str, Any]] = []
        for row in rows:
            text = _draft_post(dict(row))
            if not text:
                continue
            conn.execute(
                'INSERT INTO social_review_queue (contribution_id, draft_text) VALUES (?, ?)',
                (row['id'], text),
            )
            conn.execute(
                'UPDATE contributions SET social_drafted = 1 WHERE id = ?',
                (row['id'],),
            )
            drafts.append({
                'contribution_id': row['id'],
                'draft_text': text,
                'mp_name': row['mp_name'],
                'contribution_type': row['contribution_type'],
            })
        conn.commit()
        return drafts
    finally:
        conn.close()


def list_drafts(status: str = 'PENDING') -> list[dict[str, Any]]:
    """Return drafts from the review queue."""
    conn = get_connection()
    try:
        _ensure_tables(conn)
        rows = conn.execute(
            """SELECT sq.id, sq.contribution_id, sq.draft_text, sq.status,
                      sq.created_at, sq.reviewed_at, sq.reviewed_by,
                      c.subject_text, c.contribution_type, m.name AS mp_name
               FROM social_review_queue sq
               JOIN contributions c ON sq.contribution_id = c.id
               LEFT JOIN mps m ON c.mp_id = m.id
               WHERE sq.status = ?
               ORDER BY sq.created_at DESC""",
            (status,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def approve_draft(draft_id: int, reviewer: str = 'admin') -> dict:
    """Approve a draft (marks as APPROVED, does not post)."""
    conn = get_connection()
    try:
        _ensure_tables(conn)
        row = conn.execute(
            'SELECT id FROM social_review_queue WHERE id = ? AND status = ?',
            (draft_id, 'PENDING'),
        ).fetchone()
        if not row:
            return {'detail': 'Draft not found or not pending'}
        now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        conn.execute(
            "UPDATE social_review_queue SET status = 'APPROVED', reviewed_at = ?, reviewed_by = ? WHERE id = ?",
            (now, reviewer, draft_id),
        )
        conn.commit()
        return {'detail': 'Approved', 'draft_id': draft_id}
    finally:
        conn.close()


def reject_draft(draft_id: int, reviewer: str = 'admin') -> dict:
    """Reject a draft (marks as REJECTED)."""
    conn = get_connection()
    try:
        _ensure_tables(conn)
        row = conn.execute(
            'SELECT id FROM social_review_queue WHERE id = ? AND status = ?',
            (draft_id, 'PENDING'),
        ).fetchone()
        if not row:
            return {'detail': 'Draft not found or not pending'}
        now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        conn.execute(
            "UPDATE social_review_queue SET status = 'REJECTED', reviewed_at = ?, reviewed_by = ? WHERE id = ?",
            (now, reviewer, draft_id),
        )
        conn.commit()
        return {'detail': 'Rejected', 'draft_id': draft_id}
    finally:
        conn.close()


_TYPE_LABELS: dict[str, str] = {
    'question': 'asked',
    'oral_question': 'asked',
    'motion': 'moved a motion on',
    'bill': 'introduced a bill about',
    'bill_2nd': 'spoke on the bill',
    'ministerial_statement': 'delivered a statement on',
    'committee_of_supply': 'debated the budget for',
}


def _draft_post(row: dict) -> str:
    mp = row.get('mp_name') or row.get('raw_match_name') or 'An MP'
    action = _TYPE_LABELS.get(row.get('contribution_type', ''), 'spoke about')
    subject = (row.get('subject_text') or '').strip()
    ministry = row.get('ministry_addressed', '')
    ministry_part = f' to the {ministry}' if ministry else ''
    if not subject:
        return ''
    available = MAX_POST_LENGTH - len(mp) - len(action) - (len(ministry_part) if ministry_part else 0) - len(HASHTAGS) - 10
    truncated = subject
    if len(truncated) > available:
        truncated = truncated[:available - 3] + '...'
    post = f'{mp} {action}{ministry_part}: {truncated}\\n\\n{HASHTAGS}'
    return post


if __name__ == '__main__':
    drafts = generate_drafts()
    print(f'Generated {len(drafts)} draft(s)')
    for d in drafts:
        print(f"\\n--- Draft for contribution {d['contribution_id']} ({d['mp_name']}) ---")
        print(d['draft_text'])
