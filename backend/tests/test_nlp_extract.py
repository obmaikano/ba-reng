"""Tests for the spaCy NLP entity extraction pipeline."""

import sqlite3

from backend.parse import nlp_extract
from backend.parse.nlp_extract import (
    _build_fallback_regex,
    _load_gazetteer_patterns,
    extract_entities_fallback,
    strip_honorifics,
)


def _in_memory_glossary_db() -> sqlite3.Connection:
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE parliamentary_glossary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            term_setswana TEXT UNIQUE NOT NULL,
            term_english TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'general'
        );
        """,
    )
    conn.executemany(
        'INSERT INTO parliamentary_glossary '
        '(term_setswana, term_english, category) VALUES (?, ?, ?)',
        [
            ('Gaborone', 'Gaborone', 'location'),
            ('BDP', 'Botswana Democratic Party', 'organization'),
            ('Temothuo', 'Agriculture', 'ministry'),
        ],
    )
    conn.commit()
    return conn


class TestStripHonorifics:
    def test_removes_english_and_setswana_honorifics(self) -> None:
        assert strip_honorifics('Motlotlegi Mr Kapinga said') == 'Kapinga said'

    def test_leaves_plain_text_unchanged(self) -> None:
        assert strip_honorifics('plain text here') == 'plain text here'


class TestLoadGazetteerPatterns:
    def test_loads_only_location_and_organization_categories(self) -> None:
        conn = _in_memory_glossary_db()
        patterns = _load_gazetteer_patterns(conn)
        gpe_terms = {p['pattern'] for p in patterns['GPE']}
        org_terms = {p['pattern'] for p in patterns['ORG']}
        assert gpe_terms == {'Gaborone'}
        assert org_terms == {'Botswana Democratic Party'}
        assert 'Agriculture' not in gpe_terms | org_terms


class TestExtractEntitiesFallback:
    def test_extracts_known_location_and_org_terms(self) -> None:
        conn = _in_memory_glossary_db()
        result = extract_entities_fallback(
            'The MP for Gaborone spoke about Botswana Democratic Party policy.', conn,
        )
        assert 'Gaborone' in result.get('locations', [])
        assert 'Botswana Democratic Party' in result.get('orgs', [])

    def test_extracts_money_mentions(self) -> None:
        conn = _in_memory_glossary_db()
        result = extract_entities_fallback('The budget was P1,140,549,410 this year.', conn)
        assert any('1,140,549,410' in m for m in result.get('money', []))

    def test_empty_dict_when_nothing_matches(self) -> None:
        conn = _in_memory_glossary_db()
        result = extract_entities_fallback('no relevant terms here', conn)
        assert result == {}


class TestBuildFallbackRegex:
    def test_returns_never_matching_regex_when_no_terms(self) -> None:
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        conn.executescript(
            """
            CREATE TABLE parliamentary_glossary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                term_setswana TEXT UNIQUE NOT NULL,
                term_english TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'general'
            );
            """,
        )
        pattern = _build_fallback_regex(conn)
        assert pattern.search('Gaborone Botswana anything') is None


class TestGazetteerPatternCaching:
    def test_ensure_patterns_loaded_only_queries_db_once(self, monkeypatch) -> None:
        monkeypatch.setattr(nlp_extract, '_gazetteer_patterns_loaded', False)

        conn = _in_memory_glossary_db()
        call_count = 0
        original_load = nlp_extract._load_gazetteer_patterns

        def counting_load(c):
            nonlocal call_count
            call_count += 1
            return original_load(c)

        monkeypatch.setattr(nlp_extract, '_load_gazetteer_patterns', counting_load)

        class FakeRuler:
            def __init__(self):
                self.added = []

            def add_patterns(self, patterns):
                self.added.append(patterns)

        ruler = FakeRuler()
        nlp_extract._ensure_gazetteer_patterns_loaded(ruler, conn)
        nlp_extract._ensure_gazetteer_patterns_loaded(ruler, conn)
        nlp_extract._ensure_gazetteer_patterns_loaded(ruler, conn)

        assert call_count == 1
        assert len(ruler.added) == 1
