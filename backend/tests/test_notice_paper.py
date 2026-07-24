"""Tests for the Notice Paper parser and orchestration."""

import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from backend.db.connection import _sha256_hex
from backend.parse.notice_paper import (
    _extract_date_from_header,
    _parse_motions,
    _parse_questions,
    _parse_tablings_and_bills,
    _split_sections,
    extract_text,
    parse_pdf,
)
from backend.parse.run import parse_and_store, run_all

# ---------------------------------------------------------------------------
# extract_text
# ---------------------------------------------------------------------------

SAMPLE_PAGE_TEXT = (
    'NOTICE PAPER\n'
    'FOR FRIDAY 24 JULY, 2026\n'
    'NOTICE OF QUESTIONS\n'
    '1. MR. J. DOE, MP. (CONST): To ask the Minister of Health\n'
    '   whether he has any plans to improve hospitals.\n'
)


class TestExtractText:
    def test_extracts_text_from_pdf(self) -> None:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = SAMPLE_PAGE_TEXT

        mock_pdf = MagicMock()
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.pages = [mock_page]

        with patch('pdfplumber.open', return_value=mock_pdf):
            result = extract_text('/fake/path.pdf')

        assert 'NOTICE PAPER' in result
        assert 'MR. J. DOE' in result

    def test_handles_empty_pages(self) -> None:
        mock_empty = MagicMock()
        mock_empty.extract_text.return_value = None

        mock_pdf = MagicMock()
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.pages = [mock_empty]

        with patch('pdfplumber.open', return_value=mock_pdf):
            result = extract_text('/fake/path.pdf')

        assert result == ''


# ---------------------------------------------------------------------------
# _extract_date_from_header
# ---------------------------------------------------------------------------


class TestExtractDateFromHeader:
    def test_standard_format(self) -> None:
        text = 'FOR FRIDAY 24 JULY, 2026\nNOTICE OF QUESTIONS'
        assert _extract_date_from_header(text) == '2026-07-24'

    def test_no_day_prefix(self) -> None:
        text = 'TUESDAY 1 JANUARY 2025\nNOTICE OF QUESTIONS'
        assert _extract_date_from_header(text) == '2025-01-01'

    def test_with_ordinal(self) -> None:
        text = 'FOR MONDAY 3RD MARCH 2025\nNOTICE OF QUESTIONS'
        assert _extract_date_from_header(text) == '2025-03-03'

    def test_no_date_found(self) -> None:
        text = 'NOTICE OF QUESTIONS\nSome random text'
        assert _extract_date_from_header(text) is None


# ---------------------------------------------------------------------------
# _split_sections
# ---------------------------------------------------------------------------

SPLIT_INPUT = (
    'NOTICE PAPER\n'
    'FOR FRIDAY 24 JULY, 2026\n'
    'NOTICE OF QUESTIONS\n'
    '1. MR. A, MP.: Question text\n'
    'NOTICE OF MOTIONS\n'
    '1. "That the House do now adjourn."\n'
    '(Mr. B, MP. - CONST)\n'
)


class TestSplitSections:
    def test_splits_by_section_type(self) -> None:
        sections = _split_sections(SPLIT_INPUT)
        types = [s[0] for s in sections]
        assert 'oral_question' in types
        assert 'motion' in types

    def test_ignores_header_text_before_first_section(self) -> None:
        sections = _split_sections(SPLIT_INPUT)
        combined = '\n'.join(s[2] for s in sections)
        assert 'NOTICE PAPER' not in combined

    def test_no_sections(self) -> None:
        sections = _split_sections('Just some random text\nNo sections here')
        assert sections == []


# ---------------------------------------------------------------------------
# _parse_questions
# ---------------------------------------------------------------------------


class TestParseQuestions:
    def test_parses_single_question(self) -> None:
        text = (
            '1. MR. J. DOE, MP. (CONST): To ask the Minister of Health\n'
            'whether he has any plans to improve hospitals.'
        )
        results = _parse_questions(text, '2026-07-24')
        assert len(results) == 1
        assert results[0]['raw_match_name'] == 'MR. J. DOE, MP.'
        assert results[0]['raw_constituency'] == 'CONST'
        assert results[0]['ministry_addressed'] == 'Health'
        assert 'improve hospitals' in results[0]['subject_text']

    def test_parses_multiple_questions(self) -> None:
        text = (
            '1. MR. A, MP. (CONST1): To ask the Minister of Health\n'
            'whether there are enough nurses.\n'
            '2. MS. B, MP. (CONST2): To ask the Minister of Education\n'
            'if schools have enough textbooks.'
        )
        results = _parse_questions(text, '2026-07-24')
        assert len(results) == 2
        assert results[0]['raw_match_name'] == 'MR. A, MP.'
        assert results[1]['raw_match_name'] == 'MS. B, MP.'

    def test_handles_minister_for_state(self) -> None:
        text = (
            '1. HON. C, MP. (CONST): To ask the Minister for State\n'
            'President, Defence and Security what steps have been taken.'
        )
        results = _parse_questions(text, '2026-07-24')
        assert len(results) == 1
        assert 'President' in results[0]['ministry_addressed']

    def test_empty_text(self) -> None:
        assert _parse_questions('', '2026-07-24') == []

    def test_extracts_trailing_notice_number(self) -> None:
        text = (
            '1. MR. G. KEKGONEGILE, MP. (MAUN EAST): To ask the Minister of Trade and\n'
            '(381)\n'
            'Entrepreneurship to brief this Honourable House on progress made.'
        )
        results = _parse_questions(text, '2026-03-25')
        assert len(results) == 1
        assert results[0]['ministry_addressed'] == 'Trade and Entrepreneurship'
        assert results[0]['extracted_data']['notice_number'] == 381
        assert '(381)' not in results[0]['subject_text']

    def test_extracts_notice_number_when_interrupting_minister_of(self) -> None:
        text = (
            '1. MR. P. K. MOTAOSANE, MP. (THAMAGA - KUMAKWANE): To ask the Minister\n'
            '(391)\n'
            'of Lands and Agriculture whether it is lawful to employ a Landboard\n'
            'Chairperson when the substantive one is on suspension.'
        )
        results = _parse_questions(text, '2026-03-25')
        assert len(results) == 1
        assert results[0]['ministry_addressed'] == 'Lands and Agriculture'
        assert results[0]['extracted_data']['notice_number'] == 391

    def test_recognises_brigadier_honorific(self) -> None:
        text = (
            '1. BRIGADIER D. MOKGWATHI, MP. (LETLHAKENG): To ask the Minister of\n'
            '(425)\n'
            'Child Welfare and Basic Education to apprise this Honourable House.'
        )
        results = _parse_questions(text, '2026-04-01')
        assert len(results) == 1
        assert results[0]['raw_match_name'] == 'BRIGADIER D. MOKGWATHI, MP.'
        assert results[0]['raw_constituency'] == 'LETLHAKENG'
        assert results[0]['extracted_data']['notice_number'] == 425

    def test_captures_sub_questions_i_through_vi(self) -> None:
        text = (
            '1. MR. A. K. KHAN, MP. (MOLEPOLOLE NORTH): To ask the Minister of Lands\n'
            '(384)\n'
            'and Agriculture to state:\n'
            '(i) whether ground fissures are present;\n'
            '(ii) the current position on assessments;\n'
            '(iii) technical considerations relied upon;\n'
            '(iv) whether the road project is affected;\n'
            '(v) whether a moratorium is in place; and\n'
            '(vi) how long residents must wait for clearance.'
        )
        results = _parse_questions(text, '2026-03-25')
        assert len(results) == 1
        sub_questions = results[0]['extracted_data']['sub_questions']
        assert len(sub_questions) == 6
        assert sub_questions[0] == 'whether ground fissures are present;'
        assert sub_questions[5] == 'how long residents must wait for clearance.'
        # subject_text retains the full inline text for search/feed rendering
        assert '(i)' in results[0]['subject_text']

    def test_stray_parenthetical_number_does_not_shift_later_questions(self) -> None:
        # A stray 2-4 digit parenthetical elsewhere in a question's own text
        # (e.g. a page number, a statute reference) must not desync the
        # notice numbers attributed to subsequent questions — each question's
        # notice number is scoped to its own header-to-next-header window.
        text = (
            '1. MR. A, MP. (CONST1): To ask the Minister of Health\n'
            '(381)\n'
            'whether Act No. 12 of (2024) requires review.\n'
            '2. MS. B, MP. (CONST2): To ask the Minister of Education\n'
            '(382)\n'
            'if schools have enough textbooks.'
        )
        results = _parse_questions(text, '2026-07-24')
        assert len(results) == 2
        assert results[0]['extracted_data']['notice_number'] == 381
        assert results[1]['extracted_data']['notice_number'] == 382

    def test_no_extracted_data_when_no_notice_number_or_sub_questions(self) -> None:
        text = (
            '1. MR. J. DOE, MP. (CONST): To ask the Minister of Health\n'
            'whether he has any plans to improve hospitals.'
        )
        results = _parse_questions(text, '2026-07-24')
        assert results[0]['extracted_data'] is None


# ---------------------------------------------------------------------------
# _parse_motions
# ---------------------------------------------------------------------------


class TestParseMotions:
    def test_parses_motion_with_signature(self) -> None:
        text = (
            '1. \u201cThat the House do now adjourn.\u201d\n'
            '(Mr. A. B. Person, MP. - Gaborone Central)\n'
        )
        results = _parse_motions(text, '2026-07-24')
        assert len(results) == 1
        assert results[0]['raw_match_name'] == 'Mr. A. B. Person'
        assert results[0]['raw_constituency'] == 'Gaborone Central'
        assert 'adjourn' in results[0]['subject_text']

    def test_handles_unclosed_motion(self) -> None:
        text = '1. \u201cThat the House do now adjourn.\u201d\nSome follow-up.\n'
        results = _parse_motions(text, '2026-07-24')
        assert len(results) == 1
        assert 'adjourn' in results[0]['subject_text']
        assert results[0]['raw_match_name'] == ''

    def test_handles_multiple_motions(self) -> None:
        text = (
            '1. \u201cMotion one.\u201d\n'
            '(Mr. A, MP. - C1)\n'
            '2. \u201cMotion two.\u201d\n'
            '(Ms. B, MP. - C2)\n'
        )
        results = _parse_motions(text, '2026-07-24')
        assert len(results) == 2

    def test_empty_text(self) -> None:
        assert _parse_motions('', '2026-07-24') == []


# ---------------------------------------------------------------------------
# _parse_tablings_and_bills
# ---------------------------------------------------------------------------


class TestParseTablings:
    def test_parses_tabling_entry(self) -> None:
        text = (
            '\u2022 Financial Report for 2023/2024\n'
            '(Minister of Finance)\n'
        )
        results = _parse_tablings_and_bills(text, '2026-07-24', 'tabling')
        assert len(results) == 1
        assert results[0]['subject_text'] == 'Financial Report for 2023/2024'
        assert results[0]['ministry_addressed'] == 'Finance'
        assert results[0]['raw_match_name'] == 'Minister of Finance'

    def test_parses_petition_with_name(self) -> None:
        text = (
            '\u2022 PRESENTATION OF A PETITION BY MR. M. MOALOSI, MP. '
            '\u2013 NKANGE 8\n'
            '(Mr. M. Moalosi)\n'
        )
        results = _parse_tablings_and_bills(text, '2026-07-24', 'petition')
        assert len(results) == 1
        assert results[0]['raw_match_name'] == 'MR. M. MOALOSI, MP.'
        assert results[0]['ministry_addressed'] == ''

    def test_multiple_entries(self) -> None:
        text = (
            '\u2022 Report A\n(Minister A)\n'
            '\u2022 Report B\n(Minister B)\n'
        )
        results = _parse_tablings_and_bills(text, '2026-07-24', 'tabling')
        assert len(results) == 2
        assert results[0]['subject_text'] == 'Report A'
        assert results[1]['subject_text'] == 'Report B'

    def test_handles_entry_without_minister(self) -> None:
        text = (
            '\u2022 Report A (no minister)\n'
            '\u2022 Report B\n(Minister of Finance)\n'
        )
        results = _parse_tablings_and_bills(text, '2026-07-24', 'tabling')
        assert len(results) == 2
        assert results[0]['subject_text'] == 'Report A (no minister)'
        assert results[0]['ministry_addressed'] == ''
        assert results[1]['subject_text'] == 'Report B'
        assert results[1]['ministry_addressed'] == 'Finance'

    def test_empty_text(self) -> None:
        assert _parse_tablings_and_bills('', '2026-07-24', 'tabling') == []


# ---------------------------------------------------------------------------
# parse_pdf (integration)
# ---------------------------------------------------------------------------


FULL_NOTICE_PAPER = (
    'NOTICE PAPER\n'
    'FOR FRIDAY 24 JULY, 2026\n'
    '\n'
    'NOTICE OF QUESTIONS\n'
    '1. MR. J. DOE, MP. (CONST): To ask the Minister of Health\n'
    'whether he has any plans to improve hospitals.\n'
    '\n'
    '2. MS. A. SMITH, MP. (CONST2): To ask the Minister of Education\n'
    'if schools have enough textbooks.\n'
    '\n'
    'NOTICE OF MOTIONS\n'
    '1. \u201cThat the House do now adjourn.\u201d\n'
    '(Mr. A. B. Person, MP. - Gaborone Central)\n'
    '\n'
    '2. \u201cThat the report be adopted.\u201d\n'
    '(Ms. C. D. Leader, MP. - Francistown)\n'
)


class TestParsePdf:
    def test_full_integration(self) -> None:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = FULL_NOTICE_PAPER

        mock_pdf = MagicMock()
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.pages = [mock_page]

        with patch('pdfplumber.open', return_value=mock_pdf):
            results = parse_pdf('/fake/path.pdf', 'https://example.com/doc')

        assert len(results) == 4
        types = [c['contribution_type'] for c in results]
        assert types.count('oral_question') == 2
        assert types.count('motion') == 2
        assert all(c['source_url'] == 'https://example.com/doc' for c in results)

    def test_empty_pdf(self) -> None:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = ''

        mock_pdf = MagicMock()
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.pages = [mock_page]

        with patch('pdfplumber.open', return_value=mock_pdf):
            results = parse_pdf('/fake/path.pdf')

        assert results == []


# ---------------------------------------------------------------------------
# run.py orchestration
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


class TestParseAndStore:
    def test_stores_contributions_and_unresolved(self) -> None:
        conn = _in_memory_db()

        doc_id = 1
        conn.execute(
            'INSERT INTO documents (id, title, doc_type, file_path, source_url) '
            'VALUES (?, ?, ?, ?, ?)',
            (doc_id, 'Test NP', 'notice_paper', '/fake/path.pdf', 'https://x.com/doc'),
        )
        conn.commit()

        mock_page = MagicMock()
        mock_page.extract_text.return_value = FULL_NOTICE_PAPER

        mock_pdf = MagicMock()
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.pages = [mock_page]

        with patch('pdfplumber.open', return_value=mock_pdf):
            result = parse_and_store(doc_id, '/fake/path.pdf', 'https://x.com/doc', conn, doc_type='notice_paper')

        assert result['parsed'] == 4
        assert result['stored'] == 4
        assert result['unresolved'] == 4

        rows = conn.execute('SELECT * FROM contributions').fetchall()
        assert len(rows) == 4

        q_count = conn.execute(
            "SELECT COUNT(*) FROM contributions WHERE contribution_type='oral_question'"
        ).fetchone()[0]
        assert q_count == 2

        m_count = conn.execute(
            "SELECT COUNT(*) FROM contributions WHERE contribution_type='motion'"
        ).fetchone()[0]
        assert m_count == 2

        un_resolved = conn.execute('SELECT COUNT(*) FROM entity_review_queue').fetchone()[0]
        assert un_resolved == 4


class TestRunAll:
    def test_processes_all_notice_papers(self) -> None:
        conn = _in_memory_db()

        for i in range(1, 4):
            conn.execute(
                'INSERT INTO documents (id, title, doc_type, file_path, source_url) '
                'VALUES (?, ?, ?, ?, ?)',
                (i, f'NP {i}', 'notice_paper', f'/fake/path{i}.pdf', 'https://x.com/doc'),
            )
        conn.commit()

        mock_page = MagicMock()
        mock_page.extract_text.return_value = FULL_NOTICE_PAPER

        mock_pdf = MagicMock()
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.pages = [mock_page]

        with patch('pdfplumber.open', return_value=mock_pdf):
            results = run_all(conn)

        assert len(results) == 3
        assert all(r['parsed'] == 4 for r in results)
        assert all(r['stored'] == 4 for r in results)

        total = conn.execute('SELECT COUNT(*) FROM contributions').fetchone()[0]
        assert total == 12

    def test_skips_unsupported_doc_types(self) -> None:
        conn = _in_memory_db()

        conn.execute(
            'INSERT INTO documents (id, title, doc_type, file_path, source_url) '
            'VALUES (?, ?, ?, ?, ?)',
            (1, 'Unknown', 'unknown_type', '/fake/unknown.pdf', ''),
        )
        conn.commit()

        with patch('pdfplumber.open') as mock_open:
            results = run_all(conn)

        assert len(results) == 0
        mock_open.assert_not_called()

    def test_processes_order_papers(self) -> None:
        conn = _in_memory_db()

        conn.execute(
            'INSERT INTO documents (id, title, doc_type, file_path, source_url) '
            'VALUES (?, ?, ?, ?, ?)',
            (1, 'Test OP', 'order_paper', '/fake/op.pdf', ''),
        )
        conn.commit()

        order_paper_text = (
            'BOTSWANA NATIONAL ASSEMBLY\n'
            'O R D E R P A P E R\n'
            '(MONDAY 16 FEBRUARY, 2026)\n'
            '1. MR. J. DOE, MP. (CONST): To ask the Minister of Health\n'
            'whether he has any plans.\n'
        )

        mock_page = MagicMock()
        mock_page.extract_text.return_value = order_paper_text

        mock_pdf = MagicMock()
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.pages = [mock_page]

        with patch('pdfplumber.open', return_value=mock_pdf):
            results = run_all(conn)

        assert len(results) == 1
        assert results[0]['parsed'] == 1
