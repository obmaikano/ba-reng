"""Hansard utterances API — paginated, filterable debate transcript feed + speaker scorecard."""

from fastapi import APIRouter, Query

from backend.db.connection import get_connection
from backend.narrative.evidence_classifier import classify_evidence, compute_scorecard

router = APIRouter(prefix='/api/v1/hansard', tags=['hansard'])


@router.get('/utterances')
def list_utterances(
    mp_id: int | None = None,
    language: str | None = Query(None, pattern='^(en|tn|mixed)$'),
    speech_type: str | None = None,
    q: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict:
    """Paginated, filterable Hansard dialogue turns.

    Filters: ?mp_id=, ?language=en|tn|mixed, ?speech_type=, ?q= (full-text)
    """
    conn = get_connection()
    try:
        clauses = ['1=1']
        params: list = []

        if mp_id:
            clauses.append('u.mp_id = ?')
            params.append(mp_id)
        if language:
            clauses.append('u.language = ?')
            params.append(language)
        if speech_type:
            clauses.append('u.speech_type = ?')
            params.append(speech_type)
        if q and q.strip():
            clauses.append('(u.speech_text LIKE ? OR u.cleaned_text LIKE ? OR u.speaker_name LIKE ?)')
            like = f'%{q.strip()}%'
            params.extend([like, like, like])

        where = ' AND '.join(clauses)

        total = conn.execute(
            f'SELECT COUNT(*) FROM utterances u JOIN agenda_items a ON u.agenda_id = a.agenda_id WHERE {where}',
            params,
        ).fetchone()[0]

        rows = conn.execute(
            f"""SELECT u.*, m.name AS mp_name, m.party, m.constituency,
                       a.title AS agenda_title, a.category AS agenda_category
                FROM utterances u
                JOIN agenda_items a ON u.agenda_id = a.agenda_id
                LEFT JOIN mps m ON u.mp_id = m.id
                WHERE {where}
                ORDER BY u.sequence_order
                LIMIT ? OFFSET ?""",
            (*params, limit, offset),
        ).fetchall()

        return {
            'total_records': total,
            'returned_records': len(rows),
            'data': [dict(r) for r in rows],
        }
    finally:
        conn.close()


@router.get('/sessions')
def list_sessions() -> list[dict]:
    """List all parsed Hansard sessions with metadata."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT s.*, d.title AS document_title, d.source_url
               FROM hansard_sessions s
               JOIN documents d ON s.document_id = d.id
               ORDER BY s.session_date DESC""",
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@router.get('/scorecard/{mp_id}')
def speaker_scorecard(
    mp_id: int,
    session_id: int = Query(..., description='Hansard session ID — scorecard is per-debate'),
) -> dict:
    """Speaker Scorecard — 5-dimension weighted evaluation for a single debate session."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT u.speech_text, u.speech_type, u.evidence_type,
                      u.word_count, a.title AS agenda_title
               FROM utterances u
               JOIN agenda_items a ON u.agenda_id = a.agenda_id
               WHERE u.mp_id = ? AND a.session_id = ?
               ORDER BY u.sequence_order""",
            (mp_id, session_id),
        ).fetchall()

        if not rows:
            return {'error': f'No utterances found for MP {mp_id} in session {session_id}.'}

        utterances = [dict(r) for r in rows]
        total_words = sum(r['word_count'] or len((r['speech_text'] or '').split()) for r in utterances)
        interventions = sum(1 for r in utterances if r['speech_type'] in ('point_of_procedure', 'supplementary_question'))
        violations = sum(1 for r in utterances if 'procedural' in (r['speech_type'] or '').lower())

        scorecard = compute_scorecard(utterances, total_words, interventions, violations)

        mp = conn.execute('SELECT name, constituency, party FROM mps WHERE id = ?', (mp_id,)).fetchone()
        if mp:
            scorecard['mp_name'] = mp['name']
            scorecard['constituency'] = mp['constituency']
            scorecard['party'] = mp['party']

        session = conn.execute(
            'SELECT hansard_no, session_date, meeting_description FROM hansard_sessions WHERE session_id = ?',
            (session_id,),
        ).fetchone()
        if session:
            scorecard['session'] = dict(session)

        return scorecard
    finally:
        conn.close()


@router.get('/evidence-breakdown/{mp_id}')
def evidence_breakdown(
    mp_id: int,
    session_id: int = Query(..., description='Hansard session ID — breakdown is per-debate'),
) -> dict:
    """Evidence type distribution for an MP's utterances within a specific debate session."""
    conn = get_connection()
    try:
        types = conn.execute(
            """SELECT u.evidence_type, COUNT(*) AS cnt
               FROM utterances u
               JOIN agenda_items a ON u.agenda_id = a.agenda_id
               WHERE u.mp_id = ? AND a.session_id = ?
               GROUP BY u.evidence_type""",
            (mp_id, session_id),
        ).fetchall()

        breakdown = {r['evidence_type']: r['cnt'] for r in types}
        total = sum(breakdown.values())

        return {
            'mp_id': mp_id,
            'session_id': session_id,
            'total_utterances': total,
            'breakdown': breakdown,
            'empirical_pct': round(breakdown.get('EMPIRICAL', 0) / max(total, 1) * 100, 1),
            'statutory_pct': round(breakdown.get('STATUTORY', 0) / max(total, 1) * 100, 1),
            'anecdotal_pct': round(breakdown.get('ANECDOTAL', 0) / max(total, 1) * 100, 1),
            'normative_pct': round(breakdown.get('NORMATIVE', 0) / max(total, 1) * 100, 1),
        }
    finally:
        conn.close()
