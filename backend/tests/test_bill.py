"""Tests for the Bill document parser."""

from unittest.mock import MagicMock, patch

from backend.parse.bill import (
    _extract_bill_no,
    _extract_date,
    _extract_minister_and_ministry,
    _extract_title,
    parse_pdf,
)

SAMPLE_BILL = (
    'Bill No. 5 of 2026\n'
    'PUBLIC SERVICE BILL, 2026\n'
    '(Published on 6th March, 2026)\n'
    'MEMORANDUM\n'
    '1. A draft of the above Bill is set out below.\n'
    '2. The objective of the Bill is to amend the Public Service Act.\n'
    'MOETI C. MOHWASA,\n'
    'Minister for State President,\n'
    'Defence and Security.\n'
)

SAMPLE_BILL_SINGLE_LINE = (
    'Bill No. 1 of 2026\n'
    'APPROPRIATION (2026/2027) BILL, 2026\n'
    '(Published on 23rd January, 2026)\n'
    'MEMORANDUM\n'
    '1. A draft of the above Bill.\n'
    'NDABA N. GAOLATHE,\n'
    'Minister of Finance.\n'
)


class TestExtractTitle:
    def test_extracts_title_after_bill_no(self) -> None:
        assert _extract_title(SAMPLE_BILL) == 'PUBLIC SERVICE BILL, 2026'

    def test_returns_empty_when_no_match(self) -> None:
        assert _extract_title('no bill here') == ''


class TestExtractBillNo:
    def test_extracts_number_and_year(self) -> None:
        result = _extract_bill_no(SAMPLE_BILL)
        assert 'Bill No. 5 of 2026' in result

    def test_returns_empty_when_no_match(self) -> None:
        assert _extract_bill_no('') == ''


class TestExtractDate:
    def test_extracts_published_date(self) -> None:
        assert _extract_date(SAMPLE_BILL) == '2026-03-06'

    def test_falls_back_to_header_date(self) -> None:
        assert _extract_date(SAMPLE_BILL_SINGLE_LINE) == '2026-01-23'


class TestExtractMinister:
    def test_extracts_multiline_minister(self) -> None:
        name, ministry = _extract_minister_and_ministry(SAMPLE_BILL)
        assert 'MOHWASA' in name
        assert 'President' in ministry

    def test_extracts_single_line_minister(self) -> None:
        name, ministry = _extract_minister_and_ministry(SAMPLE_BILL_SINGLE_LINE)
        assert 'GAOLATHE' in name
        assert 'Finance' in ministry

    def test_returns_empty_on_non_bill_text(self) -> None:
        name, ministry = _extract_minister_and_ministry('no minister here')
        assert name == '' and ministry == ''


class TestParsePdf:
    def test_parses_full_bill(self) -> None:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = SAMPLE_BILL

        mock_pdf = MagicMock()
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.pages = [mock_page]

        with patch('pdfplumber.open', return_value=mock_pdf):
            results = parse_pdf('/fake/path.pdf', 'https://x.com/doc')

        assert len(results) == 1
        assert results[0]['contribution_type'] == 'bill_presentation'
        assert 'MOHWASA' in results[0]['raw_match_name']
        assert 'PUBLIC SERVICE' in results[0]['subject_text']

    def test_handles_empty_pdf(self) -> None:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = ''

        mock_pdf = MagicMock()
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.pages = [mock_page]

        with patch('pdfplumber.open', return_value=mock_pdf):
            results = parse_pdf('/fake/path.pdf')

        assert results == []
