"""Full-text search endpoint with bilingual glossary expansion."""
from fastapi import APIRouter, Query

from backend.db.connection import get_connection

router = APIRouter(prefix='/api/v1/search', tags=['search'])


def _expand_query_bilingual(q: str, conn) -> list[str]:
    """Expand a search query to include matching terms from the parliamentary glossary.

    If the query matches an English term, add the Setswana equivalent.
    If it matches a Setswana term, add the English equivalent.
    Returns a list of terms to search for (always includes the original query).
    """
    terms = {q}
    rows = conn.execute(
        '''
        SELECT term_english, term_setswana
        FROM parliamentary_glossary
        WHERE term_english LIKE ? OR term_setswana LIKE ?
        ''',
        (f'%{q}%', f'%{q}%'),
    ).fetchall()
    for row in rows:
        if q.lower() in row['term_english'].lower():
            terms.add(row['term_setswana'])
        if q.lower() in row['term_setswana'].lower():
            terms.add(row['term_english'])
    return list(terms)


@router.get('')
def search(q: str = Query(..., min_length=1)) -> list[dict]:
    """Search contributions and Hansard utterances with bilingual expansion."""
    conn = get_connection()
    try:
        search_terms = _expand_query_bilingual(q, conn)

        results: list[dict] = []

        for term in search_terms:
            pattern = f'%{term}%'

            # Search contributions
            contrib_rows = conn.execute(
                '''
                SELECT c.id, c.contribution_type, c.subject_text, c.date,
                       c.ministry_addressed, c.source_url, c.mp_id,
                       m.name AS mp_name, m.party, m.constituency
                FROM contributions c
                LEFT JOIN mps m ON m.id = c.mp_id
                WHERE c.subject_text LIKE ?
                   OR m.name LIKE ?
                   OR c.ministry_addressed LIKE ?
                   OR m.constituency LIKE ?
                ORDER BY c.date DESC
                LIMIT 50
                ''',
                (pattern, pattern, pattern, pattern),
            ).fetchall()

            for row in contrib_rows:
                d = dict(row)
                d['result_type'] = 'contribution'
                # Deduplicate by id
                if not any(r.get('id') == d['id'] and r.get('result_type') == 'contribution' for r in results):
                    results.append(d)

            # Search Hansard utterances
            utterance_rows = conn.execute(
                '''
                SELECT u.utterance_id AS id, u.speaker_name AS mp_name, '' AS party,
                       '' AS constituency, u.speech_text AS subject_text,
                       u.speech_type AS contribution_type, u.created_at AS date,
                       '' AS ministry_addressed, '' AS source_url, u.mp_id,
                       u.procedural_notes, u.language
                FROM utterances u
                WHERE u.speech_text LIKE ?
                   OR u.speaker_name LIKE ?
                ORDER BY u.created_at DESC
                LIMIT 50
                ''',
                (pattern, pattern),
            ).fetchall()

            for row in utterance_rows:
                d = dict(row)
                d['result_type'] = 'utterance'
                if not any(r.get('id') == d['id'] and r.get('result_type') == 'utterance' for r in results):
                    results.append(d)

        # Sort combined results by date descending
        results.sort(key=lambda r: r.get('date', ''), reverse=True)

        # Limit to 50 total results
        return results[:50]
    finally:
        conn.close()
