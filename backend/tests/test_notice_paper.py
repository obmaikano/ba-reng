"""Tests for the Notice Paper parser and orchestration."""

import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

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
        assert 'question' in types
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
        assert results[0]['ministry_addressed'] == 'Minister of Finance'

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
        assert results[1]['ministry_addressed'] == 'Minister of Finance'

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
        assert types.count('question') == 2
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


SCHEMA_SQL = (Path(__file__).resolve().parent.parent.parent
              / 'backend' / 'db' / 'migrations' / '001_initial.sql').read_text()


class TestParseAndStore:
    def test_stores_contributions_and_unresolved(self) -> None:
        conn = sqlite3.connect(':memory:')
        conn.execute('PRAGMA foreign_keys=ON')
        conn.row_factory = sqlite3.Row
        conn.executescript(SCHEMA_SQL)

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
            result = parse_and_store(doc_id, '/fake/path.pdf', 'https://x.com/doc', conn)

        assert result['parsed'] == 4
        assert result['stored'] == 4
        assert result['unresolved'] == 4

        rows = conn.execute('SELECT * FROM contributions').fetchall()
        assert len(rows) == 4

        q_count = conn.execute(
            "SELECT COUNT(*) FROM contributions WHERE contribution_type='question'"
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
        conn = sqlite3.connect(':memory:')
        conn.execute('PRAGMA foreign_keys=ON')
        conn.row_factory = sqlite3.Row
        conn.executescript(SCHEMA_SQL)

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

    def test_skips_non_notice_papers(self) -> None:
        conn = sqlite3.connect(':memory:')
        conn.execute('PRAGMA foreign_keys=ON')
        conn.row_factory = sqlite3.Row
        conn.executescript(SCHEMA_SQL)

        conn.execute(
            'INSERT INTO documents (id, title, doc_type, file_path, source_url) '
            'VALUES (?, ?, ?, ?, ?)',
            (1, 'Order Paper', 'order_paper', '/fake/op.pdf', ''),
        )
        conn.commit()

        with patch('pdfplumber.open') as mock_open:
            results = run_all(conn)

        assert len(results) == 0
        mock_open.assert_not_called()
