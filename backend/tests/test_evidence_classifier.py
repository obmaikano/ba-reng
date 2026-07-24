"""Tests for evidence classification and speaker scorecard."""

from backend.narrative.evidence_classifier import classify_evidence, compute_scorecard


def test_empirical_numeric_percentage() -> None:
    result = classify_evidence('Inflation fell by 1.2% in Q3 according to Bank of Botswana data.')
    assert result['primary_type'] == 'EMPIRICAL'
    assert result['confidence'] > 0


def test_empirical_currency_budget() -> None:
    result = classify_evidence('The budget allocation of P1.53 billion for water projects.')
    assert result['primary_type'] == 'EMPIRICAL'


def test_statutory_section_citation() -> None:
    result = classify_evidence('Section 14 of the 2018 Public Service Act requires compliance.')
    assert result['primary_type'] == 'STATUTORY'


def test_statutory_standing_order() -> None:
    result = classify_evidence('Pursuant to Standing Order 36 of the National Assembly.')
    assert result['primary_type'] == 'STATUTORY'


def test_anecdotal_constituent_story() -> None:
    result = classify_evidence('A farmer in my constituency told me his cattle died from drought.')
    assert result['primary_type'] == 'ANECDOTAL'


def test_anecdotal_office_visit() -> None:
    result = classify_evidence('A teacher came to my office crying about school conditions.')
    assert result['primary_type'] == 'ANECDOTAL'


def test_normative_value_judgment() -> None:
    result = classify_evidence('This government lacks moral clarity and must be held accountable.')
    assert result['primary_type'] == 'NORMATIVE'


def test_normative_should_must() -> None:
    result = classify_evidence('We should prioritize healthcare over vanity projects.')
    assert result['primary_type'] == 'NORMATIVE'


def test_mixed_signals_prefers_empirical() -> None:
    result = classify_evidence(
        'P1.53 billion allocated under Section 14 — a farmer in Maun told me it is insufficient.',
    )
    assert result['primary_type'] == 'EMPIRICAL'


def test_empty_text_defaults_normative() -> None:
    result = classify_evidence('')
    assert result['primary_type'] == 'NORMATIVE'
    assert result['confidence'] == 0.0


def test_scorecard_zero_utterances() -> None:
    scorecard = compute_scorecard([], 0, 0, 0)
    assert scorecard['total_words'] == 0
    assert 0 <= scorecard['overall_score'] <= 100


def test_scorecard_high_substance() -> None:
    utterances = [
        {'speech_text': 'Section 14 of the Act requires budget allocation of P10 million for the project.',
         'primary_type': 'EMPIRICAL', 'speech_type': 'main_question', 'agenda_title': 'Budget Debate'},
    ] * 10
    scorecard = compute_scorecard(utterances, 200, 0, 0)
    assert scorecard['dimensions']['substance_depth'] > 50
    assert scorecard['dimensions']['evidence_density'] > 50
    assert scorecard['dimensions']['decorum_compliance'] == 100


def test_scorecard_decorum_violations_penalize() -> None:
    utterances = [
        {'speech_text': 'This is an outrage.',
         'primary_type': 'NORMATIVE', 'speech_type': 'main_question', 'agenda_title': 'Motion'},
    ] * 5
    scorecard = compute_scorecard(utterances, 100, 1, 3)
    assert scorecard['dimensions']['decorum_compliance'] < 100
    assert scorecard['decorum_violations'] == 3
