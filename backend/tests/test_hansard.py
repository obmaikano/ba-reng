"""Tests for the Daily Hansard multi-tier parser."""

import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from backend.db.connection import _sha256_hex
from backend.parse.hansard import (
    SPEAKER_HEADER_RE,
    _classify_turn_type,
    _extract_hansard_text,
    _extract_metadata,
    _extract_procedural,
    _segment_agenda,
    _split_turns,
    parse_pdf,
)
from backend.parse.run import _hansard_speaker_identity, parse_and_store

# Bug regression fixtures: real snippets (paraphrased for brevity, same
# structure) from Hansard No. 221 - the PLAN.md 1.9 benchmark document -
# that exposed the two speaker-detection bugs found during development.

# Bug 1: a ministerial portfolio name wraps across a line and contains a
# comma; the old SPEAKER_WITH_PORTFOLIO regex's uppercase-only character
# class broke at the comma and restarted mid-phrase, capturing "AND
# SECURITY" as the speaker name instead of the full portfolio.
WRAPPED_PORTFOLIO_TEXT = (
    'MR M. M. PULE (KGATLENG EAST): asked the Minister a question.\n'
    'MINISTER FOR STATE PRESIDENT, DEFENCE\n'
    'AND SECURITY (MR MOHWASA): Thank you Mr Speaker, Government\n'
    'recognises the importance of this matter.\n'
)

# Bug 2: a question/motion title (itself ALL CAPS across 2-3 lines) directly
# precedes a real speaker line; the old regex's unbounded uppercase span
# swallowed the title into the "speaker name" instead of stopping at MR.
TITLE_BLEED_TEXT = (
    'QUESTIONS FOR ORAL ANSWER\n'
    'TOURISTIC DEVELOPMENTS AROUND\n'
    'MOHEMBO OKAVANGO BRIDGE\n'
    'MR K. K. KAPINGA (OKAVANGO WEST): asked the Minister of\n'
    'Environment and Tourism to state when developments will begin.\n'
)

# Bug 3: an abbreviated re-reference (no parenthetical) after a full-form
# speaker header elsewhere in the same section; the old fallback-only-if-
# empty logic never ran once any full-form match existed anywhere in the
# text, silently merging this turn into the previous speaker's speech.
ABBREVIATED_REREFERENCE_TEXT = (
    'MR K. K. KAPINGA (OKAVANGO WEST): asked the Minister to state\n'
    'when developments will begin.\n'
    'MR KAPINGA: Thank you Mr Speaker. It is question number one.\n'
    'MR SPEAKER: Okay, it might be a mistake.\n'
)


class TestSpeakerHeaderRe:
    def test_captures_full_wrapped_portfolio_name_not_just_tail(self) -> None:
        turns = _split_turns(WRAPPED_PORTFOLIO_TEXT)
        names = [t[0] for t in turns]
        assert 'MINISTER FOR STATE PRESIDENT, DEFENCE AND SECURITY' in names
        assert 'AND SECURITY' not in names

    def test_does_not_swallow_question_title_into_speaker_name(self) -> None:
        turns = _split_turns(TITLE_BLEED_TEXT)
        names = [t[0] for t in turns]
        assert names == ['MR K. K. KAPINGA']
        assert 'QUESTIONS FOR ORAL ANSWER' not in names[0]

    def test_captures_abbreviated_reference_after_full_form_speaker(self) -> None:
        turns = _split_turns(ABBREVIATED_REREFERENCE_TEXT)
        names = [t[0] for t in turns]
        assert names == ['MR K. K. KAPINGA', 'MR KAPINGA', 'MR SPEAKER']

    def test_matches_speaker_with_constituency_detail(self) -> None:
        m = SPEAKER_HEADER_RE.search('MR K. K. KAPINGA (OKAVANGO WEST): asked')
        assert m is not None
        assert m.group(2).strip() == 'MR K. K. KAPINGA'
        assert m.group(3) == 'OKAVANGO WEST'

    def test_does_not_match_bare_uppercase_run_without_title_prefix(self) -> None:
        assert SPEAKER_HEADER_RE.search('HANSARD NO: 221') is None
        assert SPEAKER_HEADER_RE.search('BUSINESS MOTION') is None

    def test_matches_attorney_general_and_assistant_minister_titles(self) -> None:
        turns = _split_turns('ATTORNEY GENERAL (MR X): Thank you Mr Speaker.\n')
        assert turns[0][0] == 'ATTORNEY GENERAL'
        assert turns[0][1] == 'MR X'

        turns = _split_turns('ASSISTANT MINISTER OF HEALTH (MS Y): Thank you.\n')
        assert turns[0][0] == 'ASSISTANT MINISTER OF HEALTH'
        assert turns[0][1] == 'MS Y'

    def test_matches_madam_speaker_variant(self) -> None:
        turns = _split_turns('MADAM SPEAKER (MRS Z): Order, order.\n')
        assert turns[0][0] == 'MADAM SPEAKER'


class TestHansardSpeakerIdentity:
    """Regression tests for the role-title-prefix drift an adversarial review
    caught between hansard.py's SPEAKER_HEADER_RE and run.py's identity
    resolution: both must agree on which speaker_name values are chamber
    roles (resolve via the parenthetical detail) vs personal names/honorifics
    (resolve directly), or a real speaker silently fails to resolve."""

    def test_attorney_general_resolves_via_detail(self) -> None:
        name, constituency = _hansard_speaker_identity('ATTORNEY GENERAL', 'MR X')
        assert (name, constituency) == ('MR X', '')

    def test_assistant_minister_resolves_via_detail(self) -> None:
        name, constituency = _hansard_speaker_identity('ASSISTANT MINISTER OF HEALTH', 'MS Y')
        assert (name, constituency) == ('MS Y', '')

    def test_madam_speaker_resolves_via_detail(self) -> None:
        name, constituency = _hansard_speaker_identity('MADAM SPEAKER', 'MRS Z')
        assert (name, constituency) == ('MRS Z', '')

    def test_ordinary_mp_resolves_via_own_name_and_constituency(self) -> None:
        name, constituency = _hansard_speaker_identity('MR K. K. KAPINGA', 'OKAVANGO WEST')
        assert (name, constituency) == ('MR K. K. KAPINGA', 'OKAVANGO WEST')


class TestSplitTurns:
    def test_splits_into_name_detail_body_tuples(self) -> None:
        turns = _split_turns(WRAPPED_PORTFOLIO_TEXT)
        assert len(turns) == 2
        name, detail, body = turns[1]
        assert name == 'MINISTER FOR STATE PRESIDENT, DEFENCE AND SECURITY'
        assert detail == 'MR MOHWASA'
        assert 'Government' in body

    def test_drops_trailing_header_with_no_speech_body(self) -> None:
        text = 'MR SPEAKER: Some remarks.\nMR KAPINGA:'
        turns = _split_turns(text)
        assert len(turns) == 1

    def test_normalises_whitespace_in_wrapped_detail_field(self) -> None:
        text = 'MR M. M. MOROLONG (KGATLENG\nCENTRAL): Thank you.\n'
        turns = _split_turns(text)
        assert turns[0][1] == 'KGATLENG CENTRAL'


class TestExtractMetadata:
    def test_extracts_hansard_number(self) -> None:
        meta = _extract_metadata('MIXED VERSION\nHANSARD NO: 221\n')
        assert meta['hansard_no'] == 221

    def test_extracts_sitting_time(self) -> None:
        meta = _extract_metadata('THE ASSEMBLY met at 2:00 p.m.\n')
        assert meta['sitting_time'] == '2:00 p.m.'

    def test_empty_dict_when_nothing_found(self) -> None:
        assert _extract_metadata('no metadata here') == {}


class TestSegmentAgenda:
    def test_splits_on_known_agenda_headers(self) -> None:
        text = (
            "SPEAKER'S ANNOUNCEMENTS\n"
            'Good afternoon.\n'
            'QUESTIONS FOR ORAL ANSWER\n'
            'MR KAPINGA: asked a question.\n'
        )
        sections = _segment_agenda(text)
        cats = [s[0] for s in sections]
        assert cats == ["Speaker's Announcements", 'Questions for Oral Answer']

    def test_text_before_first_header_is_dropped(self) -> None:
        text = 'preamble text\nQUESTIONS FOR ORAL ANSWER\nbody text\n'
        sections = _segment_agenda(text)
        assert len(sections) == 1
        assert 'preamble' not in sections[0][2]

    def test_empty_list_when_no_headers_found(self) -> None:
        assert _segment_agenda('no agenda headers in this text') == []


class TestClassifyTurnType:
    def test_minister_role_speaker_classified_as_minister_answer(self) -> None:
        result = _classify_turn_type('MINISTER OF ENVIRONMENT AND TOURISM', 'Some answer text.')
        assert result == 'minister_answer'

    def test_supplementary_marker_classified_regardless_of_speaker(self) -> None:
        result = _classify_turn_type('MR PULE', 'Supplementary.\nKe a leboga.')
        assert result == 'supplementary_question'

    def test_point_of_procedure_marker(self) -> None:
        result = _classify_turn_type('MR KEKGONEGILE', 'On a point of order.\nMr Speaker.')
        assert result == 'point_of_procedure'

    def test_defaults_to_main_question(self) -> None:
        result = _classify_turn_type('MR K. K. KAPINGA', 'asked the Minister to state something.')
        assert result == 'main_question'


class TestExtractProcedural:
    def test_extracts_applause_annotation(self) -> None:
        assert _extract_procedural('...(Applause!)...') == 'Applause!'

    def test_returns_none_when_no_annotation(self) -> None:
        assert _extract_procedural('plain speech text') is None


class TestExtractHansardText:
    def _fake_word(self, x0: float, x1: float, top: float = 400) -> dict:
        return {'x0': x0, 'x1': x1, 'top': top}

    def _fake_page(self, width: float, height: float, words: list[dict], text: str) -> MagicMock:
        page = MagicMock()
        page.width = width
        page.height = height
        page.extract_words.return_value = words
        page.extract_text.return_value = text
        crop_result = MagicMock()
        crop_result.extract_text.return_value = text
        page.crop.return_value = crop_result
        return page

    def test_single_column_page_not_cropped(self) -> None:
        words = [self._fake_word(100, 400) for _ in range(20)]
        page = self._fake_page(500, 800, words, 'single column text')
        mock_pdf = MagicMock()
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.pages = [page]

        with patch('backend.parse.hansard.pdfplumber.open', return_value=mock_pdf):
            text = _extract_hansard_text('fake.pdf')

        assert text == 'single column text'
        page.crop.assert_not_called()

    def test_two_column_page_is_cropped(self) -> None:
        left_words = [self._fake_word(10, 60) for _ in range(15)]
        right_words = [self._fake_word(300, 350) for _ in range(15)]
        page = self._fake_page(500, 800, left_words + right_words, 'full-width, should not be used')

        with patch('backend.parse.hansard.pdfplumber.open') as mock_open:
            mock_pdf = MagicMock()
            mock_pdf.__enter__.return_value = mock_pdf
            mock_pdf.pages = [page]
            mock_open.return_value = mock_pdf
            _extract_hansard_text('fake.pdf')

        assert page.crop.call_count == 2
        assert page.extract_text.called is False

    def test_full_width_header_words_do_not_skew_column_detection(self) -> None:
        """A running header/footer band (e.g. the page-top date line) can
        legitimately span the full page width. Regression test for the
        adversarial-review concern that a few full-width header words could
        push the straddle ratio over threshold on a page with sparse two-
        column body content, misclassifying it as single-column and
        reintroducing the garbling bug."""
        header_words = [self._fake_word(50, 450, top=10)]
        left_body = [self._fake_word(10, 60, top=400) for _ in range(10)]
        right_body = [self._fake_word(300, 350, top=400) for _ in range(10)]
        page = self._fake_page(
            500, 800, header_words + left_body + right_body, 'should not be used',
        )

        with patch('backend.parse.hansard.pdfplumber.open') as mock_open:
            mock_pdf = MagicMock()
            mock_pdf.__enter__.return_value = mock_pdf
            mock_pdf.pages = [page]
            mock_open.return_value = mock_pdf
            _extract_hansard_text('fake.pdf')

        assert page.crop.call_count == 2


class TestParsePdf:
    def test_rejects_path_outside_project_directory(self) -> None:
        with pytest.raises(ValueError, match='within project directory'):
            parse_pdf('/etc/passwd')

    def test_raises_file_not_found_for_missing_file(self) -> None:
        with pytest.raises(FileNotFoundError):
            parse_pdf('data/pdfs/does-not-exist-hansard.pdf')

    def test_full_pipeline_produces_expected_turns_and_metadata(self) -> None:
        text = (
            'MIXED VERSION\n'
            'HANSARD NO: 221\n'
            'TUESDAY 14 JULY 2026\n'
            'THE ASSEMBLY met at 2:00 p.m.\n'
            "SPEAKER'S ANNOUNCEMENTS\n"
            'MR SPEAKER (MR KEORAPETSE): Good afternoon, Honourable Members.\n'
            'HONOURABLE MEMBERS: ...(Applause!)...\n'
            'QUESTIONS FOR ORAL ANSWER\n'
            'MR K. K. KAPINGA (OKAVANGO WEST): asked the Minister a question.\n'
            'MINISTER OF ENVIRONMENT AND TOURISM (MR MMOLOTSI): Mr Speaker,\n'
            'I answered this before.\n'
        )
        page = MagicMock()
        page.width = 500
        page.height = 800
        page.extract_words.return_value = [{'x0': 100, 'x1': 400, 'top': 400} for _ in range(20)]
        page.extract_text.return_value = text

        mock_pdf = MagicMock()
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.pages = [page]

        with patch('backend.parse.hansard.pdfplumber.open', return_value=mock_pdf), \
             patch('backend.parse.hansard.detect_language', return_value='en'), \
             patch('backend.parse.hansard.extract_entities', return_value={}), \
             patch('backend.parse.hansard.strip_honorifics', side_effect=lambda t: t), \
             patch(
                 'backend.parse.hansard.classify_evidence',
                 return_value={'primary_type': 'NORMATIVE', 'confidence': 0.0},
             ):
            results = parse_pdf(__file__, 'https://x.com/doc')

        assert len(results) == 4
        assert results[0]['_meta']['hansard_no'] == 221
        assert results[0]['_agenda_category'] == "Speaker's Announcements"
        assert results[2]['_agenda_category'] == 'Questions for Oral Answer'
        assert results[3]['speech_type'] == 'minister_answer'
        assert results[3]['speaker_name'] == 'MINISTER OF ENVIRONMENT AND TOURISM'
        assert all(r['source_url'] == 'https://x.com/doc' for r in results)


# ---------------------------------------------------------------------------
# run.py hansard storage path (hansard_sessions / agenda_items / utterances)
# ---------------------------------------------------------------------------

MIGRATIONS_DIR = (
    Path(__file__).resolve().parent.parent.parent / 'backend' / 'db' / 'migrations'
)
SCHEMA_SQL = ''.join(p.read_text() for p in sorted(MIGRATIONS_DIR.glob('*.sql')))


def _in_memory_db() -> sqlite3.Connection:
    conn = sqlite3.connect(':memory:')
    conn.execute('PRAGMA foreign_keys=ON')
    conn.row_factory = sqlite3.Row
    conn.create_function('SHA256_HEX', 1, _sha256_hex, deterministic=True)
    conn.executescript(SCHEMA_SQL)
    return conn


def _fake_utterance(**overrides) -> dict:
    base = {
        'agenda_id': 1,
        'speaker_raw_title': 'MR K. K. KAPINGA (OKAVANGO WEST)',
        'speaker_name': 'MR K. K. KAPINGA',
        'speaker_detail': 'OKAVANGO WEST',
        'speech_type': 'main_question',
        'speech_text': 'asked the Minister a question.',
        'cleaned_text': 'asked the Minister a question.',
        'language': 'en',
        'procedural_notes': None,
        'extracted_entities': None,
        'evidence_type': 'NORMATIVE',
        'evidence_confidence': 0.0,
        'word_count': 5,
        'sequence_order': 1,
        '_meta': {'hansard_no': 221, 'session_date': '2026-07-14', 'sitting_time': '2:00 p.m.'},
        '_agenda_category': 'Questions for Oral Answer',
        '_agenda_title': 'QUESTIONS FOR ORAL ANSWER',
        '_agenda_sequence': 1,
        'source_url': 'https://x.com/doc',
    }
    base.update(overrides)
    return base


class TestStoreHansardDocument:
    def _insert_document(self, conn: sqlite3.Connection, doc_id: int = 1) -> None:
        conn.execute(
            'INSERT INTO documents (id, title, doc_type, file_path, source_url) '
            'VALUES (?, ?, ?, ?, ?)',
            (doc_id, 'Hansard 221', 'hansard', '/fake/hansard.pdf', 'https://x.com/doc'),
        )
        conn.commit()

    def test_creates_session_agenda_and_utterance_rows(self) -> None:
        conn = _in_memory_db()
        self._insert_document(conn)

        utterances = [
            _fake_utterance(speaker_name='MR K. K. KAPINGA', sequence_order=1),
            _fake_utterance(
                speaker_name='MINISTER OF ENVIRONMENT AND TOURISM',
                speaker_raw_title='MINISTER OF ENVIRONMENT AND TOURISM (MR MMOLOTSI)',
                speaker_detail='MR MMOLOTSI',
                speech_type='minister_answer',
                sequence_order=2,
            ),
        ]

        with patch('backend.parse.run.parse_hansard', return_value=utterances):
            result = parse_and_store(
                1, '/fake/hansard.pdf', 'https://x.com/doc', conn, doc_type='hansard',
            )

        assert result == {'doc_id': 1, 'parsed': 2, 'stored': 2, 'unresolved': 2}

        session = conn.execute('SELECT * FROM hansard_sessions').fetchone()
        assert session['hansard_no'] == 221
        assert session['session_date'] == '2026-07-14'

        agenda_rows = conn.execute('SELECT * FROM agenda_items').fetchall()
        assert len(agenda_rows) == 1
        assert agenda_rows[0]['category'] == 'Questions for Oral Answer'

        utterance_rows = conn.execute(
            'SELECT speaker_name, speech_type, mp_id, agenda_id '
            'FROM utterances ORDER BY sequence_order',
        ).fetchall()
        assert len(utterance_rows) == 2
        assert utterance_rows[0]['agenda_id'] == agenda_rows[0]['agenda_id']
        assert utterance_rows[1]['speech_type'] == 'minister_answer'

    def test_resolves_minister_identity_from_parenthetical_detail(self) -> None:
        conn = _in_memory_db()
        self._insert_document(conn)
        conn.execute(
            'INSERT INTO mps (name, constituency, party) '
            "VALUES ('Onalenna Mmolotsi', 'Test Const', 'UDC')",
        )
        conn.commit()

        utterances = [
            _fake_utterance(
                speaker_name='MINISTER OF ENVIRONMENT AND TOURISM',
                speaker_raw_title='MINISTER OF ENVIRONMENT AND TOURISM (MR MMOLOTSI)',
                speaker_detail='MR MMOLOTSI',
                speech_type='minister_answer',
            ),
        ]

        with patch('backend.parse.run.parse_hansard', return_value=utterances):
            result = parse_and_store(
                1, '/fake/hansard.pdf', 'https://x.com/doc', conn, doc_type='hansard',
            )

        assert result['unresolved'] == 0
        row = conn.execute('SELECT mp_id FROM utterances').fetchone()
        assert row['mp_id'] is not None

    def test_collective_speaker_not_queued_as_unresolved(self) -> None:
        conn = _in_memory_db()
        self._insert_document(conn)

        utterances = [
            _fake_utterance(
                speaker_name='HONOURABLE MEMBERS',
                speaker_raw_title='HONOURABLE MEMBERS',
                speech_text='...(Applause!)...',
                procedural_notes='Applause!',
            ),
        ]

        with patch('backend.parse.run.parse_hansard', return_value=utterances):
            result = parse_and_store(
                1, '/fake/hansard.pdf', 'https://x.com/doc', conn, doc_type='hansard',
            )

        assert result['unresolved'] == 0
        assert conn.execute('SELECT COUNT(*) c FROM entity_review_queue').fetchone()['c'] == 0

    def test_empty_utterance_list_returns_zero_counts(self) -> None:
        conn = _in_memory_db()
        self._insert_document(conn)

        with patch('backend.parse.run.parse_hansard', return_value=[]):
            result = parse_and_store(
                1, '/fake/hansard.pdf', 'https://x.com/doc', conn, doc_type='hansard',
            )

        assert result == {'doc_id': 1, 'parsed': 0, 'stored': 0, 'unresolved': 0}
        assert conn.execute('SELECT COUNT(*) c FROM hansard_sessions').fetchone()['c'] == 0

    def test_reprocessing_same_document_does_not_duplicate_rows(self) -> None:
        """Regression test for the CRITICAL adversarial-review finding: a
        rerun (retry after partial failure, accidental double-invocation)
        must not silently insert a second full copy of a document's
        session/agenda/utterance rows."""
        conn = _in_memory_db()
        self._insert_document(conn)

        utterances = [_fake_utterance()]

        with patch('backend.parse.run.parse_hansard', return_value=utterances):
            first = parse_and_store(
                1, '/fake/hansard.pdf', 'https://x.com/doc', conn, doc_type='hansard',
            )
            second = parse_and_store(
                1, '/fake/hansard.pdf', 'https://x.com/doc', conn, doc_type='hansard',
            )

        assert first['stored'] == 1
        assert second == {'doc_id': 1, 'parsed': 0, 'stored': 0, 'unresolved': 0}
        assert conn.execute('SELECT COUNT(*) c FROM hansard_sessions').fetchone()['c'] == 1
        assert conn.execute('SELECT COUNT(*) c FROM utterances').fetchone()['c'] == 1
