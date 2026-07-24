"""Tests for the Committee of Supply speech parser."""

from unittest.mock import MagicMock, patch

from backend.parse.committee_of_supply import (
    _clean_name,
    _extract_minister_and_ministry,
    parse_pdf,
)

SAMPLE_COS = (
    'REPUBLIC OF BOTSWANA\n'
    'COMMITTEE OF SUPPLY SPEECH\n'
    'ORGANIZATION 9100\n'
    'APPROPRIATIONS FROM REVENUE\n'
    '2026/2027\n'
    'BY\n'
    'NDABA NKOSINATHI GAOLATHE\n'
    'MINISTER OF FINANCE\n'
    '1. Mr. Chairman, I present the budget.\n'
)

SAMPLE_COS_HONOURABLE = (
    'REPUBLIC OF BOTSWANA\n'
    'MINISTRY OF HEALTH\n'
    'ORGANISATION: 1100\n'
    '2026/2027 COMMITTEE OF SUPPLY SPEECH\n'
    'PRESENTED BY\n'
    'HONOURABLE LAWRENCE OOKEDITSE\n'
    'ASSISTANT MINISTER OF HEALTH\n'
    '5th March 2026\n'
    '1. Mr. Chairman, I have the honour.\n'
)

SAMPLE_COS_MINISTER_TITLE = (
    'REPUBLIC OF BOTSWANA\n'
    'STATEMENT ON THE\n'
    'RECURRENT AND DEVELOPMENT BUDGET PROPOSALS\n'
    'TO THE COMMITTEE OF SUPPLY\n'
    'ORGANISATION 2200\n'
    'BY\n'
    'THE MINISTER OF YOUTH AND GENDER AFFAIRS\n'
    'HONOURABLE LESEGO CHOMBO\n'
    '24TH MARCH 2026\n'
    '1. Chairperson, it is my pleasure.\n'
)


class TestExtractMinister:
    def test_extracts_name_and_role_standard(self) -> None:
        name, ministry = _extract_minister_and_ministry(SAMPLE_COS)
        assert 'GAOLATHE' in name
        assert 'Finance' in ministry

    def test_extracts_with_honourable_prefix(self) -> None:
        name, ministry = _extract_minister_and_ministry(SAMPLE_COS_HONOURABLE)
        assert 'OOKEDITSE' in name
        assert 'Health' in ministry

    def test_extracts_when_minister_title_before_name(self) -> None:
        name, ministry = _extract_minister_and_ministry(SAMPLE_COS_MINISTER_TITLE)
        assert 'CHOMBO' in name
        assert 'Youth' in ministry or 'Gender' in ministry

    def test_returns_empty_on_generic_text(self) -> None:
        name, ministry = _extract_minister_and_ministry('just random text\ngoing nowhere\n')
        assert name == '' or ministry == ''


class TestCleanName:
    def test_strips_honourable_minister(self) -> None:
        assert 'LAWRENCE' in _clean_name('HONOURABLE MINISTER LAWRENCE OOKEDITSE')

    def test_rejects_pure_role(self) -> None:
        assert _clean_name('HONOURABLE MINISTER OF FINANCE') == ''

    def test_adds_hon_prefix(self) -> None:
        result = _clean_name('NDABA GAOLATHE')
        assert 'HON.' in result

    def test_preserves_existing_hon(self) -> None:
        result = _clean_name('HON. NDABA GAOLATHE')
        assert 'HON.' in result


class TestParsePdf:
    def test_parses_full_speech(self) -> None:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = SAMPLE_COS

        mock_pdf = MagicMock()
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.pages = [mock_page]

        with patch('pdfplumber.open', return_value=mock_pdf):
            results = parse_pdf('/fake/path.pdf', 'https://x.com/doc')

        assert len(results) == 1
        assert results[0]['contribution_type'] == 'committee_of_supply'
        assert 'GAOLATHE' in results[0]['raw_match_name']
        assert results[0]['source_url'] == 'https://x.com/doc'

    def test_handles_empty_pdf(self) -> None:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = ''

        mock_pdf = MagicMock()
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.pages = [mock_page]

        with patch('pdfplumber.open', return_value=mock_pdf):
            results = parse_pdf('/fake/path.pdf')

        assert results == []
