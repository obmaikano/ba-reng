"""spaCy NLP extraction pipeline — all gazetteer patterns loaded from DB at runtime."""

import re
import sqlite3
from typing import Any

from backend.db.connection import get_connection

_nlp_cache: Any = None


def _get_nlp():
    global _nlp_cache
    if _nlp_cache is None:
        import spacy
        from spacy.pipeline import EntityRuler
        _nlp_cache = spacy.load('en_core_web_sm')
        if 'entity_ruler' not in _nlp_cache.pipe_names:
            _nlp_cache.add_pipe('entity_ruler', before='ner')
    return _nlp_cache

HONORIFIC_RE = re.compile(
    r'\b(Motlotlegi|Rre|Mma|Kgosi|Tona|Honourable|Hon\.?|Mr\.?|Mrs\.?|Ms\.?|Dr\.?|Brig\.?)\b',
    re.IGNORECASE,
)

MONEY_RE = re.compile(
    r'\b(?:P(?:ula)?\s*[\d,]+(?:\.\d+)?(?:\s*(?:billion|million|thousand))?)\b',
    re.IGNORECASE,
)


def _load_gazetteer_patterns(conn: sqlite3.Connection) -> dict[str, list[dict[str, str]]]:
    """Load entity patterns from parliamentary_glossary table — zero hardcoding.

    Returns dict with keys 'GPE' and 'ORG', each containing list of spaCy
    EntityRuler-compatible pattern dicts.
    """
    patterns: dict[str, list[dict[str, str]]] = {'GPE': [], 'ORG': []}

    rows = conn.execute(
        """SELECT term_english, category
           FROM parliamentary_glossary
           WHERE category IN ('location', 'organization')""",
    ).fetchall()

    for row in rows:
        term = row['term_english'].strip()
        if not term:
            continue
        label = 'GPE' if row['category'] == 'location' else 'ORG'
        patterns[label].append({'label': label, 'pattern': term})

    return patterns


def _build_fallback_regex(conn: sqlite3.Connection) -> re.Pattern:
    """Build a compiled regex from all glossary location + org terms for the fallback path."""
    rows = conn.execute(
        """SELECT term_english
           FROM parliamentary_glossary
           WHERE category IN ('location', 'organization')""",
    ).fetchall()

    terms = [r['term_english'] for r in rows if r['term_english'].strip()]
    if not terms:
        return re.compile(r'(?!)')

    escaped = sorted(terms, key=len, reverse=True)
    return re.compile(r'\b(?:' + '|'.join(re.escape(t) for t in escaped) + r')\b', re.IGNORECASE)


def strip_honorifics(text: str) -> str:
    """Remove English and Setswana honorifics for entity resolution matching."""
    return HONORIFIC_RE.sub('', text).strip()


def extract_entities_fallback(text: str, conn: sqlite3.Connection | None = None) -> dict[str, list[str]]:
    """Extract entities using regex fallback when spaCy is unavailable."""
    close_conn = conn is None
    if conn is None:
        conn = get_connection()

    try:
        patterns = _load_gazetteer_patterns(conn)
        fallback_re = _build_fallback_regex(conn)

        entities: dict[str, list[str]] = {
            'locations': [],
            'orgs': [],
            'money': [],
        }

        gpe_names = {p['pattern'] for p in patterns['GPE']}
        org_names = {p['pattern'] for p in patterns['ORG']}

        for match in fallback_re.finditer(text):
            term = match.group(0)
            if term in gpe_names:
                entities['locations'].append(term)
            elif term in org_names:
                entities['orgs'].append(term)

        money_matches = MONEY_RE.findall(text)
        entities['money'] = [m.strip() for m in money_matches]

        return {k: sorted(set(v)) for k, v in entities.items() if v}
    finally:
        if close_conn:
            conn.close()


def extract_entities(text: str, conn: sqlite3.Connection | None = None) -> dict[str, list[str]]:
    """Extract entities from speech text using spaCy + DB-loaded EntityRuler.

    All gazetteer patterns are loaded from parliamentary_glossary at runtime.
    Falls back to regex extraction if spaCy is unavailable.
    """
    close_conn = conn is None
    if conn is None:
        conn = get_connection()

    try:
        try:
            nlp = _get_nlp()
            ruler = nlp.get_pipe('entity_ruler')
            patterns = _load_gazetteer_patterns(conn)
            ruler.add_patterns(patterns['GPE'] + patterns['ORG'])

            doc = nlp(text)
            entities: dict[str, list[str]] = {
                'locations': [],
                'orgs': [],
                'money': [],
            }

            for ent in doc.ents:
                if ent.label_ in ('GPE', 'LOC'):
                    entities['locations'].append(ent.text)
                elif ent.label_ == 'ORG':
                    entities['orgs'].append(ent.text)
                elif ent.label_ == 'MONEY':
                    entities['money'].append(ent.text)

            money_matches = MONEY_RE.findall(text)
            for m in money_matches:
                entities['money'].append(m.strip())

            return {k: sorted(set(v)) for k, v in entities.items() if v}
        except Exception:
            return extract_entities_fallback(text, conn)
    finally:
        if close_conn:
            conn.close()
