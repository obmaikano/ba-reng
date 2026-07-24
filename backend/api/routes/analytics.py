"""Analytics API — executive accountability, topic velocity, and constituency alignment."""

from fastapi import APIRouter, Query

from backend.db.connection import get_connection

router = APIRouter(prefix='/api/v1/analytics', tags=['analytics'])


@router.get('/ministerial-dodge')
def ministerial_dodge_scorecard(days: int = Query(30, ge=1, le=365)) -> list[dict]:
    """Deferral rate and response lag per ministry over the lookback window."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT
                   COALESCE(m.canonical_name, 'Unassigned') AS ministry,
                   COUNT(c.id) AS total_questions,
                   SUM(CASE WHEN dq.status = 'DEFERRED' THEN 1 ELSE 0 END) AS deferred_count,
                   ROUND(CAST(SUM(CASE WHEN dq.status = 'DEFERRED' THEN 1 ELSE 0 END) AS FLOAT)
                         / NULLIF(COUNT(c.id), 0) * 100, 1) AS deferral_rate_pct,
                   ROUND(COALESCE(AVG(
                       CASE WHEN dq.deferred_date IS NOT NULL
                       THEN julianday(dq.deferred_date) - julianday(c.date)
                       ELSE NULL END), 0), 1) AS avg_response_lag_days
               FROM contributions c
               LEFT JOIN ministries m ON c.ministry_addressed = m.canonical_name
               LEFT JOIN deferred_questions dq ON c.id = dq.contribution_id
               WHERE c.date >= date('now', '-' || ? || ' days')
               GROUP BY m.canonical_name
               HAVING COUNT(c.id) > 0
               ORDER BY deferral_rate_pct DESC""",
            (days,),
        )
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


@router.get('/topic-velocity')
def topic_velocity_radar() -> list[dict]:
    """Week-over-week keyword frequency delta — crisis/trend spike detection."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """WITH CurrentWeek AS (
                   SELECT mk.keyword, SUM(mk.weight) AS current_freq
                   FROM ministry_keywords mk
                   JOIN contributions c ON mk.ministry_id =
                       (SELECT id FROM ministries WHERE canonical_name = c.ministry_addressed AND is_active = 1)
                   WHERE c.date >= date('now', '-7 days')
                   GROUP BY mk.keyword
               ),
               PriorWeeks AS (
                   SELECT mk.keyword, SUM(mk.weight) / 4.0 AS avg_prior_freq
                   FROM ministry_keywords mk
                   JOIN contributions c ON mk.ministry_id =
                       (SELECT id FROM ministries WHERE canonical_name = c.ministry_addressed AND is_active = 1)
                   WHERE c.date BETWEEN date('now', '-35 days') AND date('now', '-7 days')
                   GROUP BY mk.keyword
               )
               SELECT
                   cw.keyword,
                   ROUND(cw.current_freq, 2) AS current_frequency,
                   ROUND(COALESCE(pw.avg_prior_freq, 0), 2) AS prior_avg_frequency,
                   ROUND(((cw.current_freq - COALESCE(pw.avg_prior_freq, 0))
                          / NULLIF(COALESCE(pw.avg_prior_freq, 0.1), 0)) * 100, 1) AS velocity_delta_pct
               FROM CurrentWeek cw
               LEFT JOIN PriorWeeks pw ON cw.keyword = pw.keyword
               WHERE cw.current_freq > 1.0
               ORDER BY velocity_delta_pct DESC
               LIMIT 10""",
        )
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


@router.get('/constituency-alignment/{mp_id}')
def constituency_alignment(mp_id: int) -> dict:
    """Constituency Local Alignment Index — how much of an MP's work targets local areas."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT
                   m.id AS mp_id,
                   m.name,
                   m.constituency,
                   COUNT(c.id) AS total_contributions,
                   SUM(
                       CASE WHEN EXISTS (
                           SELECT 1 FROM parliamentary_glossary g
                           WHERE g.category = 'location'
                             AND c.subject_text LIKE '%' || g.term_english || '%'
                       ) THEN 1 ELSE 0 END
                   ) AS local_mentions
               FROM mps m
               LEFT JOIN contributions c ON m.id = c.mp_id
               WHERE m.id = ?
               GROUP BY m.id""",
            (mp_id,),
        )
        row = cursor.fetchone()
        if not row:
            return {'error': 'MP not found'}

        data = dict(row)
        total = data['total_contributions'] or 1
        mentions = data['local_mentions'] or 0

        return {
            'mp_id': data['mp_id'],
            'name': data['name'],
            'constituency': data['constituency'],
            'total_contributions': total,
            'local_mentions': mentions,
            'clai_score_pct': round((mentions / total) * 100, 1),
        }
    finally:
        conn.close()
