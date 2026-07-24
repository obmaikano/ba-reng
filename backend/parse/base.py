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
    r'^(?:(?:THE\s+)?(?:HONOURABLE|HON\.?)?\s*)?'
    r'(?:Minister\s+(?:of|for)(?:\s+State)?\s+)?\s*',
    re.IGNORECASE,
)

MINISTRY_CLEANUP_RE = re.compile(
    r'\s*:\s*\(?[ivx]+\)?\s*$',
)

MINISTRY_TRAILING = re.compile(r'[:,\s]+$')

MINISTRY_ARTIFACTS = re.compile(
    r'\s*(?:\b\d{4}(?:/\d{4})?\b|'
    r'\b(?:JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|'
    r'JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)'
    r'\s+\d{4}\b|'
    r'DELIVERED TO THE NATIONAL ASSEMBLY|'
    r'Page\s+\d+\s+of\s+\d+|'
    r'I\.\s+INTRODUCTION|'
    r'(?:HRS/MINS|COMMITTEE OF SUPPLY).*$)',
    re.IGNORECASE,
)

MINISTRY_LEAKED_SUBJECT = re.compile(
    r'\s+(?:if|whether|when|why|how|to\s+state|to\s+update|to\s+apprise|'
    r'to\s+explain|to\s+clarify|to\s+give|to\s+indicate|'
    r'to\s+confirm|to\s+provide|to\s+brief|to\s+inform|'
    r'what\s+plans|what\s+steps|what\s+action)\b.*$',
    re.IGNORECASE,
)

MINISTRY_BARE_ROMAN = re.compile(r'\s+\(?[ivx]+\)?\s*$', re.IGNORECASE)

CANONICAL_MINISTRY: dict[str, str] = {
    'finance': 'Finance',
    'health': 'Health',
    'president': 'President',
    'president, defence and security': 'President, Defence and Security',
    'president, defence': 'President, Defence and Security',
    'lands and agriculture': 'Lands and Agriculture',
    'local government and traditional affairs': 'Local Government and Traditional Affairs',
    'local government': 'Local Government and Traditional Affairs',
    'local government and': 'Local Government and Traditional Affairs',
    'child welfare and basic education': 'Child Welfare and Basic Education',
    'transport and infrastructure': 'Transport and Infrastructure',
    'trade and entrepreneurship': 'Trade and Entrepreneurship',
    'environment and tourism': 'Environment and Tourism',
    'minerals and energy': 'Minerals and Energy',
    'water and human settlement': 'Water and Human Settlement',
    'labour and home affairs': 'Labour and Home Affairs',
    'sport and arts': 'Sport and Arts',
    'sports and arts': 'Sport and Arts',
    'justice and correctional services': 'Justice and Correctional Services',
    'justice and correctional': 'Justice and Correctional Services',
    'justice and': 'Justice and Correctional Services',
    'justice': 'Justice and Correctional Services',
    'communications and innovation': 'Communications and Innovation',
    'communications and': 'Communications and Innovation',
    'higher education': 'Higher Education',
    'youth and gender affairs': 'Youth and Gender Affairs',
    'international relations': 'International Relations',
    'education': 'Education',
    'honourable minister': '',
    'minister': '',
    'honourable minister of justice': 'Justice and Correctional Services',
    'honourable minister of justice & correctional services': 'Justice and Correctional Services',
    'honourable minister of justice and correctional services': 'Justice and Correctional Services',
}


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
    """Normalise ministry name: strip prefixes, artifacts, subject leaks."""
    name = raw.strip()
    name = MINISTRY_NORMALISE_RE.sub('', name)
    name = MINISTRY_CLEANUP_RE.sub('', name).strip()
    name = MINISTRY_BARE_ROMAN.sub('', name).strip()
    name = MINISTRY_TRAILING.sub('', name).strip()

    name = re.sub(r'[\[\]\(\)]', '', name)
    name = re.sub(r'\s+for the\s*$', '', name, flags=re.IGNORECASE).strip()
    name = re.sub(r'\s+and$', '', name, flags=re.IGNORECASE).strip()
    name = re.sub(r'\s+&$', '', name).strip()
    name = re.sub(r'\s*&\s*', ' and ', name)

    name = re.sub(r'\b2O(\d)', r'20\1', name)

    name = MINISTRY_ARTIFACTS.sub('', name).strip()
    name = MINISTRY_LEAKED_SUBJECT.sub('', name).strip()
    name = re.sub(r'([a-z])(if|whether|when|why|how|to\s+)', r'\1 \2', name, flags=re.IGNORECASE)
    name = MINISTRY_BARE_ROMAN.sub('', name).strip()
    name = re.sub(r'\s+:\s*$', '', name)
    name = re.sub(r'[:\s]+$', '', name)

    name = re.sub(r'.*?\bMINISTER\s+(?:OF|FOR)(?:\s+STATE)?\s*', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\bMINISTER\s+(?:OF|FOR)(?:\s+STATE)?\s*', '', name, flags=re.IGNORECASE)
    name = re.sub(r'^MINISTER\b\s*', '', name, flags=re.IGNORECASE)

    name = re.sub(r'\s{2,}', ' ', name).strip()

    if not name:
        return ''

    lower = name.lower().strip().rstrip('.').rstrip(',')
    if lower in CANONICAL_MINISTRY:
        return CANONICAL_MINISTRY[lower]

    return name.title() if name.isupper() else name
