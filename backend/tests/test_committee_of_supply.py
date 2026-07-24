"""Tests for the Committee of Supply speech parser."""

from unittest.mock import MagicMock, patch

from backend.parse.committee_of_supply import (
    _clean_name,
    _extract_minister_and_ministry,
    _extract_org_code,
    _extract_performance_metrics,
    _parse_budget_value,
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


class TestExtractOrgCode:
    def test_extracts_four_digit_code(self) -> None:
        assert _extract_org_code('Committee of Supply Speech for Organisation 0300') == '0300'

    def test_returns_none_when_absent(self) -> None:
        assert _extract_org_code('no org code here') is None


class TestParseBudgetValue:
    def test_extracts_recurrent_budget_stated_before_pula_figure(self) -> None:
        # Mirrors data/pdfs/3a3f134497b9d75e.pdf (Org 0300): "I request ...
        # Recurrent Budget of [spelled amount] Pula (PNNN) for the Financial Year"
        text = (
            'Mr. Chairman, I request the Honourable Committee to approve a total '
            'Recurrent Budget of One Billion, One Hundred and Forty Million, Five '
            'Hundred and Forty-Nine Thousand, Four Hundred and Ten Pula '
            '(P1,140,549,410) for the Financial Year 2026/2027.'
        )
        budget = _parse_budget_value(text)
        assert budget['recurrent'] == 1140549410

    def test_extracts_development_budget_stated_after_pula_figure(self) -> None:
        # Mirrors data/pdfs/3a3f134497b9d75e.pdf: "I request the approval of
        # [amount] Pula (PNNN) for the Development Budget."
        text = (
            'Mr. Chairman, for financial year 2026/2027, I request the approval of '
            'Three Hundred and Ninety-Three Million, One Hundred and Twelve Thousand '
            'and Four Hundred Pula (P393,112,400) for the Development Budget.'
        )
        budget = _parse_budget_value(text)
        assert budget['development'] == 393112400

    def test_extracts_recurrent_budget_with_keyword_after_pula_figure(self) -> None:
        # Mirrors data/pdfs/160a51108b5fd23f.pdf (Org 2100): "I request an
        # amount of [spelled amount] Pula (PNNN) for the recurrent budget."
        text = (
            'Mr. Chairman, I request an amount of Sixty-Two Million, Two Hundred '
            'and Eighteen Thousand, One Hundred and Forty Pula (P62,218,140) for '
            'the recurrent budget.'
        )
        budget = _parse_budget_value(text)
        assert budget['recurrent'] == 62218140

    def test_ignores_prior_year_historical_allocation(self) -> None:
        # The real Org 2100 speech restates last year's allocation
        # ("...was allocated a recurrent budget of ... Pula (P62,493,310)")
        # before stating the actual request. Without the "I request" anchor,
        # this historical figure would be picked up instead of the real ask.
        text = (
            'Mr. Chairman, for the 2025/2026 financial year, the Industrial '
            'Court was allocated a recurrent budget of Sixty-Two Million, Four '
            'Hundred and Ninety-Three Thousand, Three Hundred and Ten Pula '
            '(P62,493,310). To date, expenditure has been at 72%.\n'
            'Mr. Chairman, I request an amount of Sixty-Two Million, Two Hundred '
            'and Eighteen Thousand, One Hundred and Forty Pula (P62,218,140) for '
            'the recurrent budget.'
        )
        budget = _parse_budget_value(text)
        assert budget['recurrent'] == 62218140

    def test_handles_pula_figure_with_internal_whitespace(self) -> None:
        text = (
            'I request an amount of Sixty-Two Million Pula (P62, 218 ,140) for '
            'the recurrent budget.'
        )
        budget = _parse_budget_value(text)
        assert budget['recurrent'] == 62218140

    def test_empty_dict_when_no_budget_mentioned(self) -> None:
        assert _parse_budget_value('no budget figures here') == {}

    def test_handles_decimal_pula_figure(self) -> None:
        text = (
            'I request an amount of Forty-Four Million Pula (P44,835,294.01) for '
            'the recurrent budget.'
        )
        budget = _parse_budget_value(text)
        assert budget['recurrent'] == 44835294

    def test_accepts_we_request_phrasing(self) -> None:
        text = (
            'We request an amount of Sixty-Two Million Pula (P62,218,140) for '
            'the recurrent budget.'
        )
        budget = _parse_budget_value(text)
        assert budget['recurrent'] == 62218140

    def test_accepts_passive_is_requested_phrasing(self) -> None:
        text = (
            'It is hereby requested that an amount of Sixty-Two Million Pula '
            '(P62,218,140) for the recurrent budget be approved.'
        )
        budget = _parse_budget_value(text)
        assert budget['recurrent'] == 62218140


class TestExtractPerformanceMetrics:
    def test_extracts_case_backlog_from_parenthetical_count(self) -> None:
        text = (
            'a total of Ninety-One (91) of the pending cases are considered '
            'backlog as they are more than 24 months old.'
        )
        metrics = _extract_performance_metrics(text)
        assert metrics['case_backlog'] == 91

    def test_extracts_percentage_mentions(self) -> None:
        # Deliberately named percentage_mentions, not completion_percentages:
        # this captures every "%" figure in the text (expenditure rate here,
        # but could equally be a VAT rate or growth rate elsewhere) — it is
        # not semantically filtered to completion/achievement rates.
        text = 'spent, which translates to 72% expenditure, up from 51%.'
        metrics = _extract_performance_metrics(text)
        assert metrics['percentage_mentions'] == [51.0, 72.0]

    def test_extracts_collection_targets(self) -> None:
        text = 'reaching P11.948 billion, surpassing the target of P10.002 billion.'
        metrics = _extract_performance_metrics(text)
        assert metrics['collection_targets'] == ['P10.002 billion']

    def test_empty_dict_when_no_metrics_present(self) -> None:
        assert _extract_performance_metrics('no metrics here') == {}


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
