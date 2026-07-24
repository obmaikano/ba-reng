"""Tests for the Order Paper parser."""

import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

from backend.db.connection import _sha256_hex
from backend.parse.order_paper import (
    _extract_date_from_header,
    _parse_bill_amendments,
    _parse_bills,
    _parse_motions,
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

    def test_marks_questions_after_qwn_header_as_question_without_notice(self) -> None:
        text = (
            'QUESTIONS\n'
            '1. MR. A. B, MP. (CONST1): To ask the Minister of Health\n'
            'whether he has any plans.\n'
            'QUESTION WITHOUT NOTICE\n'
            '2. MS. C. D, MP. (CONST2): To ask the Minister for State\n'
            'President, Defence and Security to brief this House.\n'
        )
        results = _parse_questions(text, '2026-07-01')
        assert len(results) == 2
        assert results[0]['contribution_type'] == 'oral_question'
        assert results[1]['contribution_type'] == 'question_without_notice'

    def test_no_qwn_header_means_all_oral_questions(self) -> None:
        results = _parse_questions(SAMPLE_QUESTIONS, '2026-02-16')
        assert all(r['contribution_type'] == 'oral_question' for r in results)

    def test_qwn_section_does_not_bleed_into_later_questions_section(self) -> None:
        text = (
            'QUESTIONS\n'
            '1. MR. A. B, MP. (CONST1): To ask the Minister of Health\n'
            'whether he has any plans.\n'
            'QUESTION WITHOUT NOTICE\n'
            '2. MS. C. D, MP. (CONST2): To ask the Minister for State\n'
            'President, Defence and Security to brief this House.\n'
            'QUESTIONS\n'
            '3. MR. E. F, MP. (CONST3): To ask the Minister of Education\n'
            'if schools have enough textbooks.\n'
        )
        results = _parse_questions(text, '2026-07-01')
        assert len(results) == 3
        assert results[0]['contribution_type'] == 'oral_question'
        assert results[1]['contribution_type'] == 'question_without_notice'
        assert results[2]['contribution_type'] == 'oral_question'


# ---------------------------------------------------------------------------
# _parse_motions
# ---------------------------------------------------------------------------


SAMPLE_MOTIONS = (
    'MOTIONS\n'
    '1. “That this Honourable House requests Government to do the first thing.”\n'
    '(Mr. S. O. Mapulanga, MP. – Chobe)\n'
    '2. "That this Honourable House requests Government to do the second thing."\n'
    '(Mr. C. K. Jacobs, MP. – Lobatse)\n'
)


class TestParseMotions:
    def test_parses_curly_and_straight_quoted_motions(self) -> None:
        results = _parse_motions(SAMPLE_MOTIONS, '2026-04-10')
        assert len(results) == 2
        assert results[0]['raw_match_name'] == 'Mr. S. O. Mapulanga'
        assert results[0]['raw_constituency'] == 'Chobe'
        assert 'first thing' in results[0]['subject_text']
        assert results[1]['raw_match_name'] == 'Mr. C. K. Jacobs'
        assert results[1]['raw_constituency'] == 'Lobatse'
        assert 'second thing' in results[1]['subject_text']
        assert all(r['contribution_type'] == 'motion' for r in results)

    def test_handles_empty_text(self) -> None:
        assert _parse_motions('', '2026-04-10') == []


# ---------------------------------------------------------------------------
# _parse_bill_amendments
# ---------------------------------------------------------------------------


SAMPLE_AMENDMENTS = (
    'Cinematograph Bill, 2025 (Bill No. 31 of 2025)\n'
    'AMENDMENTS\n'
    '1. The Bill is amended in clause 25 appearing at page B.719 by substituting for the\n'
    'clause, the following new clause.\n'
    '(Minister of Sport and Arts)\n'
    '2. The Bill is amended in clause 28 appearing at page B.720 by deleting the\n'
    'words appearing in subclause (1).\n'
    '(Minister of Sport and Arts)\n'
    '3. Clause 15 appearing on page B264 is amended by deleting sub-clause (5).\n'
    '(Mr. S. O. Mapulanga, MP. – Chobe)\n'
)


class TestParseBillAmendments:
    def test_extracts_clause_page_and_action(self) -> None:
        results = _parse_bill_amendments(SAMPLE_AMENDMENTS, '2026-04-09')
        assert len(results) == 3
        assert all(r['contribution_type'] == 'bill_amendment' for r in results)
        assert results[0]['extracted_data'] == {
            'clause_number': '25', 'page_reference': 'B.719', 'action': 'substituting',
        }
        assert results[1]['extracted_data'] == {
            'clause_number': '28', 'page_reference': 'B.720', 'action': 'deleting',
        }

    def test_handles_clause_first_phrasing(self) -> None:
        results = _parse_bill_amendments(SAMPLE_AMENDMENTS, '2026-04-09')
        assert results[2]['extracted_data']['clause_number'] == '15'
        assert results[2]['extracted_data']['action'] == 'deleting'
        assert results[2]['raw_match_name'] == 'Mr. S. O. Mapulanga'
        assert results[2]['raw_constituency'] == 'Chobe'

    def test_no_amendments_section_returns_empty(self) -> None:
        assert _parse_bill_amendments('NOTICE OF MOTIONS\n1. Some motion.', '2026-04-09') == []

    def test_handles_empty_text(self) -> None:
        assert _parse_bill_amendments('', '2026-04-09') == []


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

    def test_motion_scan_does_not_bleed_into_later_amendments_section(self) -> None:
        # A clause substitution can quote new clause text that itself starts
        # with a bare "N. " numbering (e.g. "25. The Commission may..."), which
        # would look like a motion's numbered-quote opener if the motion scan
        # ran unbounded to end of document instead of stopping at AMENDMENTS.
        full_text = (
            'NOTICE OF MOTIONS AND ORDERS OF THE DAY\n'
            'MOTIONS\n'
            '1. “That this Honourable House requests Government to act.”\n'
            '(Mr. S. O. Mapulanga, MP. – Chobe)\n'
            'Cinematograph Bill, 2025 (Bill No. 31 of 2025)\n'
            'AMENDMENTS\n'
            '1. The Bill is amended in clause 25 appearing at page B.719 by substituting for the\n'
            'clause, the following new clause.\n'
            '“25. The Commission may issue a film permit.”\n'
            '(Minister of Sport and Arts)\n'
        )

        mock_page = MagicMock()
        mock_page.extract_text.return_value = full_text

        mock_pdf = MagicMock()
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.pages = [mock_page]

        with patch('pdfplumber.open', return_value=mock_pdf):
            results = parse_pdf('/fake/op.pdf', 'https://example.com/doc')

        motions = [r for r in results if r['contribution_type'] == 'motion']
        assert len(motions) == 1
        assert motions[0]['raw_match_name'] == 'Mr. S. O. Mapulanga'


# ---------------------------------------------------------------------------
# parse_and_store / run_all
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
    def test_stores_order_paper_contributions(self) -> None:
        conn = _in_memory_db()

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
