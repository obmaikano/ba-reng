"""Shared parsing utilities for Botswana Parliament document parsers."""

import re
from datetime import datetime

import pdfplumber

DATE_PATTERN = re.compile(
    r'(?:FOR\s+)?'
    r'(?:MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY)'
    r'\s+\d{1,2}(?:ST|ND|RD|TH)?\s+'
    r'(?:JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|'
    r'OCTOBER|NOVEMBER|DECEMBER),?\s+\d{4}',
    re.IGNORECASE,
)

MINISTRY_NORMALISE_RE = re.compile(
    r'^(?:Minister\s+(?:of|for)(?:\s+State)?\s+)?\s*',
    re.IGNORECASE,
)

MINISTRY_CLEANUP_RE = re.compile(
    r'\s*:\s*\(?[ivx]+\)?\s*$',
)

MINISTRY_TRAILING = re.compile(r'[:,\s]+$')


def extract_text(pdf_path: str) -> str:
    """Extract and concatenate text from all PDF pages."""
    with pdfplumber.open(pdf_path) as pdf:
        lines: list[str] = []
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines.append(text)
    return '\n'.join(lines)


def _extract_date_from_header(text: str) -> str | None:
    match = DATE_PATTERN.search(text)
    if not match:
        return None
    raw = match.group(0).strip().upper()
    raw = raw.removeprefix('FOR ')
    raw = re.sub(r'\b(\d+)(ST|ND|RD|TH)\b', r'\1', raw)
    raw = raw.replace(',', '').strip()
    try:
        dt = datetime.strptime(raw, '%A %d %B %Y')
        return dt.strftime('%Y-%m-%d')
    except ValueError:
        return None


def normalise_ministry(raw: str) -> str:
    """Strip inconsistent Minister prefixes and trailing artifacts.

    'Minister of Finance' → 'Finance'
    'Minister for State President, Defence' → 'President, Defence'
    'President, Defence and Security: (i)' → 'President, Defence and Security'
    """
    name = raw.strip()
    name = MINISTRY_NORMALISE_RE.sub('', name)
    name = MINISTRY_CLEANUP_RE.sub('', name).strip()
    name = MINISTRY_TRAILING.sub('', name).strip()
    name = re.sub(r'\s+for the\s*$', '', name, flags=re.IGNORECASE).strip()
    return name
