"""Parser for Botswana Parliament Ministerial Statement & Policy Update documents."""

import json
import re

from backend.parse.base import _extract_date_from_header, extract_text, normalise_ministry

MINISTER_NAME_RE = re.compile(
    r'(?:THE\s+)?(?:HONOURABLE|HON\.?)?\s*'
    r'((?:MR\.?|MS\.?|DR\.?|PROF\.?|BRIGADIER\.?)\s+[A-Z][A-Za-z\'\s\.\-]{4,}(?:,\s*MP\.?)?)',
    re.IGNORECASE,
)

MINISTER_PORTFOLIO_RE = re.compile(
    r'(?:MINISTER|MINISTER\s+OF|MINISTER\s+FOR)\s+(.+?)(?:\s*\(|:|\n|\.|,)',
    re.IGNORECASE,
)

QUANTITY_RE = re.compile(
    r'(\d+(?:\.\d+)?)\s*(million|billion|thousand|litres?|barrels?|tons?|Pula|P)',
    re.IGNORECASE,
)

PERCENTAGE_RE = re.compile(r'(\d+(?:\.\d+)?)\s*(?:per\s*cent|%)\b', re.IGNORECASE)

CURRENCY_RE = re.compile(r'P(\d[\d,]*)\s*(million|billion|thousand)?', re.IGNORECASE)


def _extract_quantitative_metrics(text: str) -> dict[str, list[str]]:
    metrics: dict[str, list[str]] = {
        'quantities': [],
        'percentages': [],
        'currency_values': [],
    }

    for m in QUANTITY_RE.finditer(text):
        metrics['quantities'].append(m.group(0).strip())

    for m in PERCENTAGE_RE.finditer(text):
        metrics['percentages'].append(m.group(0).strip())

    for m in CURRENCY_RE.finditer(text):
        metrics['currency_values'].append(m.group(0).strip())

    return {k: sorted(set(v)) for k, v in metrics.items() if v}


def _extract_speech_body(text: str) -> str:
    body_start = 0
    for pattern in (MINISTER_PORTFOLIO_RE, MINISTER_NAME_RE):
        m = pattern.search(text)
        if m:
            body_start = max(body_start, m.end())

    if body_start > 50:
        return text[body_start:5000].strip()
    return text[:5000].strip()


def parse_pdf(pdf_path: str, source_url: str = '') -> list[dict]:
    text = extract_text(pdf_path)
    date = _extract_date_from_header(text)

    name_match = MINISTER_NAME_RE.search(text)
    minister = name_match.group(1).strip() if name_match else ''

    portfolio_match = MINISTER_PORTFOLIO_RE.search(text)
    ministry = normalise_ministry(portfolio_match.group(1).strip()) if portfolio_match else ''

    speech_body = _extract_speech_body(text)
    metrics = _extract_quantitative_metrics(text)

    if not minister and not ministry:
        return []

    return [{
        'contribution_type': 'ministerial_statement',
        'raw_match_name': minister,
        'raw_constituency': '',
        'ministry_addressed': ministry,
        'subject_text': speech_body,
        'date': date or '',
        'source_url': source_url,
        'quantitative_metrics': json.dumps(metrics) if any(metrics.values()) else None,
    }]


def run_for_document(file_path: str, source_url: str = '') -> list[dict]:
    return parse_pdf(file_path, source_url)
