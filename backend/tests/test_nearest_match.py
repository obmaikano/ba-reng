"""Tests for the Levenshtein/Jaccard nearest-match entity resolver.

Regression guard: nearest_match.py imports the third-party ``Levenshtein``
package at module load time. If that dependency is ever undeclared or
uninstalled, every test in this file fails on collection with a clear
ModuleNotFoundError instead of the breakage going unnoticed until the
resolve pipeline runs against real data.
"""

from backend.resolve.nearest_match import clean_name, is_garbage, resolve_nearest


def test_clean_name_strips_honorifics_and_collapses_whitespace() -> None:
    assert clean_name('Hon.  Dr John   Smith') == 'John Smith'


def test_clean_name_leaves_plain_names_untouched() -> None:
    assert clean_name('John Smith') == 'John Smith'


def test_is_garbage_flags_ministry_boilerplate() -> None:
    assert is_garbage('MINISTER OF JUSTICE')
    assert is_garbage('HONOURABLE MEMBERS')


def test_is_garbage_ignores_real_names() -> None:
    assert not is_garbage('John Smith')


def test_resolve_nearest_matches_close_name_above_threshold() -> None:
    mp_names = [(1, 'JOHN SMITH'), (2, 'JANE DOE')]
    mp_id, score = resolve_nearest('Hon. John Smith', mp_names)
    assert mp_id == 1
    assert score >= 0.55


def test_resolve_nearest_returns_none_below_threshold() -> None:
    mp_names = [(1, 'JOHN SMITH'), (2, 'JANE DOE')]
    mp_id, score = resolve_nearest('Zebedee Nkomo', mp_names)
    assert mp_id is None
    assert score < 0.55


def test_resolve_nearest_returns_none_for_empty_cleaned_name() -> None:
    mp_names = [(1, 'JOHN SMITH')]
    mp_id, score = resolve_nearest('Hon. Minister', mp_names)
    assert mp_id is None
    assert score == 0.0
