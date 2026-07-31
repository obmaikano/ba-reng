"""Orchestration: iterate documents, parse, insert contributions."""

import hashlib
import json
import logging
import re
import sqlite3
from collections.abc import Callable

from backend.db.connection import get_connection
from backend.parse.bill import parse_pdf as parse_bill
from backend.parse.committee_of_supply import parse_pdf as parse_committee_of_supply
from backend.parse.hansard import INSTITUTIONAL_ROLE_TITLES
from backend.parse.hansard import parse_pdf as parse_hansard
from backend.parse.ministerial_speech import parse_pdf as parse_ministerial_speech
from backend.parse.motion import parse_pdf as parse_motion
from backend.parse.notice_paper import parse_pdf as parse_notice_paper
from backend.parse.order_paper import parse_pdf as parse_order_paper
from backend.parse.ministry_harvester import MinistryHarvester
from backend.resolve.entity import resolve_contribution

logger = logging.getLogger(__name__)

# Collective/procedural speaker attributions, not individual MPs - never a
# real person to resolve or queue for review.
_COLLECTIVE_SPEAKERS = {'HONOURABLE MEMBERS', 'HONOURABLE MEMBER'}

_PARSERS: dict[str, Callable[..., list[dict]]] = {
    'notice_paper': parse_notice_paper,
    'order_paper': parse_order_paper,
    'committee_of_supply': parse_committee_of_supply,
    'bill': parse_bill,
    'motion': parse_motion,
    'ministerial_statement': parse_ministerial_speech,
    'ministerial_speech': parse_ministerial_speech,
}

_PARSABLE_TYPES = (*tuple(_PARSERS.keys()), 'hansard')


def _insert_contribution(
    cursor: sqlite3.Cursor,
    doc_id: int,
    contrib: dict,
) -> int | None:
    extracted_data = contrib.get('extracted_data')
    try:
        cursor.execute(
            """INSERT INTO contributions
               (document_id, contribution_type, subject_text, ministry_addressed,
                date, raw_match_name, raw_constituency, source_url, subject_hash,
                extracted_data)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                doc_id,
                contrib['contribution_type'],
                contrib['subject_text'],
                contrib['ministry_addressed'],
                contrib['date'],
                contrib['raw_match_name'],
                contrib['raw_constituency'],
                contrib['source_url'],
                hashlib.sha256(contrib['subject_text'][:200].encode()).hexdigest(),
                json.dumps(extracted_data) if extracted_data else None,
            ),
        )
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None


def _insert_unresolved(
    cursor: sqlite3.Cursor,
    raw_name: str,
    doc_id: int,
    contribution_id: int | None,
) -> bool:
    cursor.execute(
        """INSERT INTO entity_review_queue
           (raw_match_name, document_id, contribution_id, status)
           SELECT ?, ?, ?, 'UNRESOLVED'
           WHERE NOT EXISTS (
               SELECT 1 FROM entity_review_queue WHERE raw_match_name = ?
           )""",
        (raw_name, doc_id, contribution_id, raw_name),
    )
    return cursor.rowcount > 0


def _hansard_speaker_identity(speaker_name: str, detail: str) -> tuple[str, str]:
    """Return (raw_match_name, raw_constituency) for resolve_contribution.

    For chamber-role turns (e.g. speaker_name='MINISTER OF ENVIRONMENT AND
    TOURISM', detail='MR MMOLOTSI'), the real person's name is in the
    parenthetical detail, not the role title. For ordinary MP turns
    (speaker_name='MR K. K. KAPINGA', detail='OKAVANGO WEST'), detail is the
    constituency and resolve_contribution's constituency-first match applies.
    """
    name_upper = speaker_name.strip().upper()
    name_upper = re.sub(r'^MADAM\s+', '', name_upper)
    is_role_title = any(name_upper.startswith(p) for p in INSTITUTIONAL_ROLE_TITLES)
    if is_role_title and detail:
        return detail, ''
    return speaker_name, detail


def _store_hansard_document(
    cursor: sqlite3.Cursor,
    doc_id: int,
    file_path: str,
    source_url: str,
) -> dict:
    """Parse a Hansard PDF and store it into hansard_sessions/agenda_items/utterances."""
    existing_session = cursor.execute(
        'SELECT session_id FROM hansard_sessions WHERE document_id = ?', (doc_id,),
    ).fetchone()
    if existing_session is not None:
        logger.warning(
            'Skipping document %s: already has a hansard_sessions row (session_id=%s).',
            doc_id, existing_session['session_id'],
        )
        return {'doc_id': doc_id, 'parsed': 0, 'stored': 0, 'unresolved': 0}

    utterances = parse_hansard(file_path, source_url)

    parsed = len(utterances)
    stored = 0
    unresolved = 0

    if not utterances:
        return {'doc_id': doc_id, 'parsed': 0, 'stored': 0, 'unresolved': 0}

    meta = utterances[0]['_meta']
    cursor.execute(
        """INSERT INTO hansard_sessions
           (document_id, hansard_no, session_date, meeting_description, sitting_time)
           VALUES (?, ?, ?, ?, ?)""",
        (
            doc_id,
            meta.get('hansard_no', 0),
            meta.get('session_date', ''),
            meta.get('meeting_description'),
            meta.get('sitting_time'),
        ),
    )
    session_id = cursor.lastrowid

    agenda_id_by_sequence: dict[int, int] = {}

    for u in utterances:
        seq = u['_agenda_sequence']
        if seq not in agenda_id_by_sequence:
            cursor.execute(
                """INSERT INTO agenda_items (session_id, title, category, sequence_order)
                   VALUES (?, ?, ?, ?)""",
                (session_id, u['_agenda_title'], u['_agenda_category'], seq),
            )
            agenda_id_by_sequence[seq] = cursor.lastrowid

        agenda_id = agenda_id_by_sequence[seq]
        speaker_name = u['speaker_name']
        is_collective = speaker_name.strip().upper() in _COLLECTIVE_SPEAKERS

        mp_id = None
        if not is_collective:
            raw_match_name, raw_constituency = _hansard_speaker_identity(
                speaker_name, u.get('speaker_detail', ''),
            )
            mp_id = resolve_contribution(cursor, raw_match_name, raw_constituency)

        cursor.execute(
            """INSERT INTO utterances
               (agenda_id, mp_id, speaker_raw_title, speaker_name, speech_type,
                speech_text, procedural_notes, extracted_entities, sequence_order,
                language, cleaned_text, evidence_type, evidence_confidence, word_count)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                agenda_id, mp_id, u['speaker_raw_title'], speaker_name, u['speech_type'],
                u['speech_text'], u['procedural_notes'], u['extracted_entities'],
                u['sequence_order'], u['language'], u['cleaned_text'], u['evidence_type'],
                u['evidence_confidence'], u['word_count'],
            ),
        )
        stored += 1

        if mp_id is None and not is_collective:
            raw_match_name, _ = _hansard_speaker_identity(speaker_name, u.get('speaker_detail', ''))
            if _insert_unresolved(cursor, raw_match_name, doc_id, None):
                unresolved += 1

    return {'doc_id': doc_id, 'parsed': parsed, 'stored': stored, 'unresolved': unresolved}


def parse_and_store(
    doc_id: int,
    file_path: str,
    source_url: str,
    conn: sqlite3.Connection | None = None,
    *,
    doc_type: str,
) -> dict:
    """Parse a single document and store results in the database."""
    close_conn = conn is None
    if conn is None:
        conn = get_connection()

    cursor = conn.cursor()
    if doc_type not in _PARSABLE_TYPES:
        raise ValueError(
            f'Unknown doc_type={doc_type} for document {doc_id}. '
            f'Known types: {", ".join(sorted(_PARSABLE_TYPES))}',
        )

    if doc_type == 'hansard':
        result = _store_hansard_document(cursor, doc_id, file_path, source_url)
        conn.commit()
        if close_conn:
            conn.close()
        return result

    # Look up published_date from documents table for date fallback
    cursor.execute('SELECT published_date FROM documents WHERE id = ?', (doc_id,))
    doc_row = cursor.fetchone()
    published_date = doc_row[0] if doc_row and doc_row[0] else ''

    parser = _PARSERS[doc_type]
    contributions = parser(file_path, source_url)

    parsed = 0
    stored = 0
    unresolved = 0

    for contrib in contributions:
        # Fallback: use document published_date when parser returns empty date
        if not contrib.get('date') and published_date:
            contrib['date'] = published_date
        parsed += 1
        cid = _insert_contribution(cursor, doc_id, contrib)
        if cid is not None:
            stored += 1
            raw_name = contrib['raw_match_name']
            if not raw_name:
                continue
            if _insert_unresolved(cursor, raw_name, doc_id, cid):
                unresolved += 1

    # Harvest ministries and keywords from stored contributions
    try:
        harvester = MinistryHarvester(conn)
        for contrib in contributions:
            subject = contrib.get('subject_text', '')
            ministry = contrib.get('ministry_addressed', '')
            if subject and ministry:
                harvester.harvest_topic_keywords(subject, ministry)
    except Exception:
        logger.warning('MinistryHarvester keyword harvest failed', exc_info=True)

    conn.commit()

    if close_conn:
        conn.close()

    return {
        'doc_id': doc_id,
        'parsed': parsed,
        'stored': stored,
        'unresolved': unresolved,
    }


def run_all(conn: sqlite3.Connection | None = None) -> list[dict]:
    """Parse all documents and store contributions."""
    close_conn = conn is None
    if conn is None:
        conn = get_connection()

    cursor = conn.cursor()
    placeholders = ','.join('?' * len(_PARSABLE_TYPES))
    docs = cursor.execute(
        f"""SELECT id, title, file_path, source_url, doc_type
           FROM documents WHERE doc_type IN ({placeholders})
           ORDER BY id""",
        list(_PARSABLE_TYPES),
    ).fetchall()

    results: list[dict] = []
    for doc in docs:
        result = parse_and_store(
            doc['id'], doc['file_path'], doc['source_url'],
            conn=conn, doc_type=doc['doc_type'],
        )
        results.append(result)

    if close_conn:
        conn.close()

    return results


if __name__ == '__main__':
    results = run_all()
    total_parsed = sum(r['parsed'] for r in results)
    total_stored = sum(r['stored'] for r in results)
    total_unresolved = sum(r['unresolved'] for r in results)
    print(f'Documents processed: {len(results)}')
    print(f'Contributions parsed: {total_parsed}')
    print(f'Contributions stored: {total_stored}')
    print(f'Unresolved entities:  {total_unresolved}')
    for r in results:
        print(
            f'  Doc {r["doc_id"]}: {r["parsed"]} parsed, '
            f'{r["stored"]} stored, {r["unresolved"]} unresolved',
        )
