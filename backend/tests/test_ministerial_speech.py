"""Tests for the Ministerial Statement & Policy Update parser."""

from unittest.mock import MagicMock, patch

from backend.parse.ministerial_speech import (
    _extract_quantitative_metrics,
    _extract_speech_body,
    parse_pdf,
)

SAMPLE_STATEMENT = (
    'Republic of Botswana\n'
    'MINISTRY OF MINERALS AND ENERGY\n'
    'FUEL SUPPLY STATUS UPDATE\n'
    'BY\n'
    'HONOURABLE BOGOLO J. KENEWENDO\n'
    '1\n'
    'Mr Speaker,\n'
    '1. I wish to update this Honourable House on the status of fuel supply.\n'
    '2. Government has a total of 62.5 million litres of strategic storage\n'
    'capacity for petroleum strategic stocks. The Francistown depot is being\n'
    'expanded by 60 million litres. The current volume of fuel stocks held\n'
    'by importers and wholesalers is 43.5 million litres.\n'
)


class TestExtractQuantitativeMetrics:
    def test_extracts_strategic_storage_capacity(self) -> None:
        metrics = _extract_quantitative_metrics(SAMPLE_STATEMENT)
        assert metrics['strategic_storage_capacity_million_litres'] == 62.5

    def test_extracts_depot_expansion_with_location(self) -> None:
        metrics = _extract_quantitative_metrics(SAMPLE_STATEMENT)
        assert metrics['depot_expansion'] == {
            'location': 'Francistown', 'million_litres': 60.0,
        }

    def test_extracts_current_stock_level(self) -> None:
        metrics = _extract_quantitative_metrics(SAMPLE_STATEMENT)
        assert metrics['current_stock_million_litres'] == 43.5

    def test_extracts_generic_quantities(self) -> None:
        metrics = _extract_quantitative_metrics(SAMPLE_STATEMENT)
        assert '62.5 million' in metrics['quantities']

    def test_empty_dict_on_text_with_no_metrics(self) -> None:
        assert _extract_quantitative_metrics('no numbers here') == {}


class TestExtractSpeechBody:
    def test_starts_at_speaker_salutation(self) -> None:
        body = _extract_speech_body(SAMPLE_STATEMENT)
        assert body.startswith('Mr Speaker')
        assert 'KENEWENDO' not in body

    def test_not_confused_by_normalised_name_mismatching_source_text(self) -> None:
        # _extract_minister_and_ministry can synthesise a name like
        # "HON. John Doe, MP." that never appears verbatim in the source
        # text (e.g. the PDF just says "HON JOHN DOE"). Body-start detection
        # must not depend on re-finding that string in the raw text, or the
        # whole masthead leaks into subject_text (the bug this test guards).
        text = (
            'Republic of Botswana\n'
            'MINISTRY OF HEALTH\n'
            'BY\n'
            'HON JOHN DOE\n'
            '1\n'
            'Mr Speaker,\n'
            'Body text here.\n'
        )
        body = _extract_speech_body(text)
        assert body.startswith('Mr Speaker')
        assert 'Republic of Botswana' not in body
        assert 'MINISTRY OF HEALTH' not in body

    def test_falls_back_to_paragraph_number_without_speaker_salutation(self) -> None:
        text = 'Some header text\nBY\nHON JOHN DOE\n1. First paragraph of the speech.\n'
        body = _extract_speech_body(text)
        assert body.startswith('1. First paragraph')

    def test_falls_back_to_full_text_when_no_structural_cue_found(self) -> None:
        assert _extract_speech_body('just some text') == 'just some text'


class TestParsePdf:
    def test_parses_full_statement(self) -> None:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = SAMPLE_STATEMENT

        mock_pdf = MagicMock()
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.pages = [mock_page]

        with patch('pdfplumber.open', return_value=mock_pdf):
            results = parse_pdf('/fake/path.pdf', 'https://x.com/doc')

        assert len(results) == 1
        result = results[0]
        assert result['contribution_type'] == 'ministerial_statement'
        assert 'KENEWENDO' in result['raw_match_name']
        assert result['ministry_addressed'] == 'Minerals and Energy'
        assert result['source_url'] == 'https://x.com/doc'
        assert result['extracted_data']['strategic_storage_capacity_million_litres'] == 62.5
        assert result['extracted_data']['depot_expansion']['million_litres'] == 60.0
        assert result['extracted_data']['current_stock_million_litres'] == 43.5

    def test_handles_empty_pdf(self) -> None:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = ''

        mock_pdf = MagicMock()
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.pages = [mock_page]

        with patch('pdfplumber.open', return_value=mock_pdf):
            results = parse_pdf('/fake/path.pdf')

        assert results == []
