"""Tests for the Order Paper parser."""

import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

from backend.parse.order_paper import (
    _extract_date_from_header,
    _parse_bills,
    _parse_questions,
    extract_text,
    parse_pdf,
)
from backend.parse.run import parse_and_store, run_all

# ---------------------------------------------------------------------------
# extract_text
# ---------------------------------------------------------------------------

SAMPLE_PAGE_TEXT = (
    'BOTSWANA NATIONAL ASSEMBLY\n'
    'O R D E R P A P E R\n'
    '(MONDAY 16 FEBRUARY, 2026)\n'
    '1. MR. J. DOE, MP. (CONST): To ask the Minister of Health\n'
    'whether he has any plans.\n'
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

        assert 'O R D E R P A P E R' in result
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


class TestExtractDate:
    def test_parses_standard_date(self) -> None:
        text = 'ORDER PAPER (MONDAY 16 FEBRUARY, 2026)'
        assert _extract_date_from_header(text) == '2026-02-16'

    def test_parses_without_comma(self) -> None:
        text = 'ORDER PAPER (THURSDAY 23 JULY 2026)'
        assert _extract_date_from_header(text) == '2026-07-23'

    def test_returns_none_for_no_date(self) -> None:
        assert _extract_date_from_header('no date here') is None

    def test_parses_ordinal_day(self) -> None:
        text = 'ORDER PAPER (WEDNESDAY 3RD DECEMBER 2025)'
        assert _extract_date_from_header(text) == '2025-12-03'


# ---------------------------------------------------------------------------
# _parse_questions
# ---------------------------------------------------------------------------


SAMPLE_QUESTIONS = (
    'BOTSWANA NATIONAL ASSEMBLY\n'
    'O R D E R P A P E R\n'
    '(MONDAY 16 FEBRUARY, 2026)\n'
    'QUESTIONS HRS/MINS\n'
    '1400 \u2013 1445\n'
    '1. MR. J. DOE, MP. (GABORONE CENTRAL): To ask the Minister of Health\n'
    'whether he has any plans to improve hospitals.\n'
    '2. MS. A. SMITH, MP. (FRANCISTOWN): To ask the Minister of Education\n'
    'to state if schools have enough textbooks.\n'
    '3. DR. P. JONES, MP. (MAUN): To ask the Minister of Finance\n'
    'to update this House on the budget status.\n'
)


class TestParseQuestions:
    def test_extracts_name_and_constituency(self) -> None:
        results = _parse_questions(SAMPLE_QUESTIONS, '2026-02-16')
        assert len(results) == 3

        assert results[0]['raw_match_name'] == 'MR. J. DOE, MP.'
        assert results[0]['raw_constituency'] == 'GABORONE CENTRAL'
        assert results[1]['raw_match_name'] == 'MS. A. SMITH, MP.'
        assert results[1]['raw_constituency'] == 'FRANCISTOWN'

    def test_extracts_ministry(self) -> None:
        results = _parse_questions(SAMPLE_QUESTIONS, '2026-02-16')

        assert results[0]['ministry_addressed'] == 'Health'
        assert results[1]['ministry_addressed'] == 'Education'
        assert results[2]['ministry_addressed'] == 'Finance'

    def test_extracts_subject_text(self) -> None:
        results = _parse_questions(SAMPLE_QUESTIONS, '2026-02-16')

        assert 'improve hospitals' in results[0]['subject_text']
        assert 'textbooks' in results[1]['subject_text']
        assert 'budget status' in results[2]['subject_text']

    def test_sets_contribution_type(self) -> None:
        results = _parse_questions(SAMPLE_QUESTIONS, '2026-02-16')
        assert all(r['contribution_type'] == 'oral_question' for r in results)

    def test_sets_date(self) -> None:
        results = _parse_questions(SAMPLE_QUESTIONS, '2026-02-16')
        assert all(r['date'] == '2026-02-16' for r in results)

    def test_date_is_none_fallback(self) -> None:
        results = _parse_questions(SAMPLE_QUESTIONS, None)
        assert all(r['date'] == '' for r in results)

    def test_handles_empty_text(self) -> None:
        assert _parse_questions('', None) == []

    def test_handles_multi_page_with_ref_numbers(self) -> None:
        text = (
            '1. MR. X. Y, MP. (CONST): To ask the Minister of Works (123)\n'
            'and Transport to state when the road will be completed.\n'
            '2. MS. Z. W, MP. (CONST2): To ask the Minister of Health\n'
            'to update on vaccine rollout.\n'
        )
        results = _parse_questions(text, '2026-07-01')
        assert len(results) == 2
        assert results[0]['ministry_addressed'] == 'Works and Transport'

    def test_handles_brigadier_title(self) -> None:
        text = (
            '1. BRIGADIER D. MOKGWATHI, MP. (LETLHAKENG): To ask the Minister of Defence\n'
            'to state the readiness of the armed forces.\n'
        )
        results = _parse_questions(text, '2026-07-01')
        assert len(results) == 1
        assert results[0]['raw_match_name'] == 'BRIGADIER D. MOKGWATHI, MP.'

    def test_handles_minister_for_state(self) -> None:
        text = (
            '1. MR. A. B, MP. (CONST): To ask the Minister for State\n'
            'President to state if the policy will change.\n'
        )
        results = _parse_questions(text, '2026-07-01')
        assert len(results) == 1
        assert 'President' in results[0]['ministry_addressed']


# ---------------------------------------------------------------------------
# _parse_bills
# ---------------------------------------------------------------------------


SAMPLE_BILLS = (
    'NOTICE OF MOTIONS AND ORDERS OF THE DAY HRS/MINS\n'
    'SECOND READING 1445 \u2013 1830\n'
    '\u2022 Appropriation (2026/2027) Bill, An Act to authorise the payment out of the\n'
    '2026 (Bill No. 1 of 2026) Consolidated Fund and the Development\n'
    '(Minister of Finance)\n'
    '(Published on 23rd January, 2026)\n'
)


class TestParseBills:
    def test_extracts_bill_items(self) -> None:
        results = _parse_bills(SAMPLE_BILLS, '2026-07-23')
        assert len(results) >= 1

    def test_assigns_bill_stage(self) -> None:
        results = _parse_bills(SAMPLE_BILLS, '2026-07-23')
        if results:
            assert 'bill_2nd' in results[0]['contribution_type']

    def test_empty_when_no_bill_section(self) -> None:
        results = _parse_bills('just regular questions', '2026-07-23')
        assert results == []

    def test_empty_text(self) -> None:
        assert _parse_bills('', '2026-07-23') == []


# ---------------------------------------------------------------------------
# parse_pdf integration
# ---------------------------------------------------------------------------


class TestParsePdf:
    def test_parses_questions_and_bills(self) -> None:
        full_text = SAMPLE_QUESTIONS + '\n' + SAMPLE_BILLS

        mock_page = MagicMock()
        mock_page.extract_text.return_value = full_text

        mock_pdf = MagicMock()
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.pages = [mock_page]

        with patch('pdfplumber.open', return_value=mock_pdf):
            results = parse_pdf('/fake/op.pdf', 'https://example.com/doc')

        questions = [r for r in results if r['contribution_type'] == 'oral_question']
        assert len(questions) == 3
        assert all(r['source_url'] == 'https://example.com/doc' for r in results)


# ---------------------------------------------------------------------------
# parse_and_store / run_all
# ---------------------------------------------------------------------------

SCHEMA_SQL = (Path(__file__).resolve().parent.parent.parent
              / 'backend' / 'db' / 'migrations' / '001_initial.sql').read_text()


class TestParseAndStore:
    def test_stores_order_paper_contributions(self) -> None:
        conn = sqlite3.connect(':memory:')
        conn.execute('PRAGMA foreign_keys=ON')
        conn.row_factory = sqlite3.Row
        conn.executescript(SCHEMA_SQL)

        doc_id = 1
        conn.execute(
            'INSERT INTO documents (id, title, doc_type, file_path, source_url) '
            'VALUES (?, ?, ?, ?, ?)',
            (doc_id, 'Test OP', 'order_paper', '/fake/op.pdf', 'https://x.com/doc'),
        )
        conn.commit()

        mock_page = MagicMock()
        mock_page.extract_text.return_value = SAMPLE_QUESTIONS

        mock_pdf = MagicMock()
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.pages = [mock_page]

        with patch('pdfplumber.open', return_value=mock_pdf):
            result = parse_and_store(
                doc_id, '/fake/op.pdf', 'https://x.com/doc', conn, doc_type='order_paper',
            )

        assert result['parsed'] == 3
        assert result['stored'] == 3

        rows = conn.execute('SELECT * FROM contributions').fetchall()
        assert len(rows) == 3

        types = {r['contribution_type'] for r in rows}
        assert types == {'oral_question'}
