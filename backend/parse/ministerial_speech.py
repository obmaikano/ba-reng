"""Parser for Botswana Parliament Ministerial Statement & Policy Update documents."""

import re

from backend.parse.base import _extract_date_from_header, extract_text
from backend.parse.committee_of_supply import _extract_minister_and_ministry

QUANTITY_RE = re.compile(
    r'(\d+(?:\.\d+)?)\s*(million|billion|thousand|litres?|barrels?|tons?|Pula|P)',
    re.IGNORECASE,
)

PERCENTAGE_RE = re.compile(r'(\d+(?:\.\d+)?)\s*(?:per\s*cent|%)\b', re.IGNORECASE)

CURRENCY_RE = re.compile(r'P(\d[\d,]*)\s*(million|billion|thousand)?', re.IGNORECASE)

# These three patterns are anchored to the exact sentence wording of the one
# real ministerial statement in the current corpus (Hon. Bogolo Kenewendo's
# fuel supply update) and are not verified against any other real document -
# see ISSUE-004 in .vibe/STATE.md. They will very likely extract nothing on a
# statement about a different topic with different phrasing; the generic
# quantities/percentages/currency_values bag below is the only extraction
# that generalises.
STORAGE_CAPACITY_RE = re.compile(
    r'total\s+of\s+([\d.]+)\s*million\s+litres\s+of\s+strategic\s+storage\s+capacity',
    re.IGNORECASE,
)

DEPOT_EXPANSION_RE = re.compile(
    r'([A-Z][a-z]+)\s+depot\s+is\s+being\s+expanded\s+by\s+([\d.]+)\s*million\s+litres',
    re.IGNORECASE,
)

STOCK_LEVEL_RE = re.compile(
    r'current\s+volume\s+of\s+fuel\s+stocks\s+held\s+by\s+importers\s+and\s+wholesalers\s+is\s+'
    r'([\d.]+)\s*million\s+litres',
    re.IGNORECASE,
)


def _extract_quantitative_metrics(text: str) -> dict:
    metrics: dict = {}

    quantities = sorted({m.group(0).strip() for m in QUANTITY_RE.finditer(text)})
    if quantities:
        metrics['quantities'] = quantities

    percentages = sorted({m.group(0).strip() for m in PERCENTAGE_RE.finditer(text)})
    if percentages:
        metrics['percentages'] = percentages

    currency_values = sorted({m.group(0).strip() for m in CURRENCY_RE.finditer(text)})
    if currency_values:
        metrics['currency_values'] = currency_values

    storage_match = STORAGE_CAPACITY_RE.search(text)
    if storage_match:
        metrics['strategic_storage_capacity_million_litres'] = float(storage_match.group(1))

    depot_match = DEPOT_EXPANSION_RE.search(text)
    if depot_match:
        metrics['depot_expansion'] = {
            'location': depot_match.group(1),
            'million_litres': float(depot_match.group(2)),
        }

    stock_match = STOCK_LEVEL_RE.search(text)
    if stock_match:
        metrics['current_stock_million_litres'] = float(stock_match.group(1))

    return metrics


SPEAKER_SALUTATION_RE = re.compile(r'\bM(?:r|ister)\.?\s+Speaker\b', re.IGNORECASE)
PARAGRAPH_START_RE = re.compile(r'^\s*\d+\.\s+\S', re.MULTILINE)


def _extract_speech_body(text: str) -> str:
    """Find where the speech proper begins, independent of how the
    minister's name/ministry get normalised (_extract_minister_and_ministry's
    output can differ from the source text - e.g. a synthesised "HON. X, MP."
    - so re-finding those strings in the raw text is not reliable and can
    silently leave the whole document masthead in subject_text instead).
    Uses the "Mr Speaker" salutation, or a numbered paragraph opener as a
    fallback, both structural cues independent of extractor output.
    """
    salutation_match = SPEAKER_SALUTATION_RE.search(text)
    if salutation_match:
        return text[salutation_match.start():5000].strip()

    paragraph_match = PARAGRAPH_START_RE.search(text)
    if paragraph_match:
        return text[paragraph_match.start():5000].strip()

    return text[:5000].strip()


def parse_pdf(pdf_path: str, source_url: str = '') -> list[dict]:
    text = extract_text(pdf_path)
    date = _extract_date_from_header(text)

    minister, ministry = _extract_minister_and_ministry(text)

    if not minister and not ministry:
        return []

    speech_body = _extract_speech_body(text)
    metrics = _extract_quantitative_metrics(text)

    return [{
        'contribution_type': 'ministerial_statement',
        'raw_match_name': minister,
        'raw_constituency': '',
        'ministry_addressed': ministry,
        'subject_text': speech_body,
        'date': date or '',
        'source_url': source_url,
        'extracted_data': metrics or None,
    }]


def run_for_document(file_path: str, source_url: str = '') -> list[dict]:
    return parse_pdf(file_path, source_url)
