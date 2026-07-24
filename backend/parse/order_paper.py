"""Parser for Botswana National Assembly Order Paper PDFs."""

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

QUESTION_HEADER = re.compile(
    r'^(\d+)\.\s+'
    r'((?:MR|MS|MRS|DR|BRIGADIER|HON|PROF)\.?\s+.+?,?\s*MP\.)\s*'
    r'\(([^)]+)\)',
    re.IGNORECASE | re.MULTILINE,
)

REF_NUM = re.compile(r'\s*\(\d+\)\s*$')
MINISTRY_DELIM = re.compile(
    r'\s+(?:to\s+state|to\s+update|to\s+apprise|to\s+brief|'
    r'to\s+explain|to\s+clarify|to\s+give|to\s+indicate|'
    r'to\s+provide|whether:?\s+|if:?\s+|'
    r'when\s+will|when\s*:|what\s+plans|'
    r'what\s+steps|what\s+action|why\s+|how\s+many|'
    r'if\s+so|whether\s+he|whether\s+she|'
    r'he\s+should|she\s+should|'
    r'and\s+further\s+state|and\s+to\s+state)',
    re.IGNORECASE,
)


def extract_text(pdf_path: str) -> str:
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


def _normalise_block(block: str) -> str:
    block = re.sub(r'\(\d+\)', '', block)
    block = re.sub(r'\n+', ' ', block)
    block = re.sub(r'\s{2,}', ' ', block)
    return block.strip()


def _parse_questions(text: str, date: str | None) -> list[dict]:
    contributions: list[dict] = []

    headers = list(QUESTION_HEADER.finditer(text))

    for i, match in enumerate(headers):
        qnum = match.group(1)
        raw_name = match.group(2).strip()
        constituency = match.group(3).strip()

        start = match.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        after_header = text[start:end].strip()

        after_header = _normalise_block(after_header)

        after_header = re.sub(r'^:\s*To ask the\s*', '', after_header)

        delim_match = MINISTRY_DELIM.search(after_header)
        if delim_match:
            ministry = after_header[:delim_match.start()].strip()
            ministry = re.sub(r'\s*:\s*\(?[ivx]+\)?\s*$', '', ministry).strip()
            ministry = re.sub(r'[:,\s]+$', '', ministry).strip()
            subject_text = after_header[delim_match.start():].strip()
        else:
            ministry = after_header
            subject_text = ''

        contributions.append({
            'contribution_type': 'oral_question',
            'raw_match_name': raw_name,
            'raw_constituency': constituency,
            'ministry_addressed': ministry,
            'subject_text': subject_text,
            'date': date or '',
            'source_url': '',
        })

    return contributions


BILL_SECTION = re.compile(
    r'(?:NOTICE\s+OF\s+MOTIONS?\s+AND\s+ORDERS?\s+OF\s+THE\s+DAY|'
    r'ORDERS?\s+OF\s+THE\s+DAY|'
    r'NOTICE\s+OF\s+(?:PRIVATE\s+MEMBERS[\'\u2019]?\s+)?MOTIONS?)',
    re.IGNORECASE,
)

BILL_READING_HEADER = re.compile(
    r'(FIRST\s+READING|SECOND\s+READING|THIRD\s+READING|'
    r'COMMITTEE\s+STAGE|CONSIDERATION\s+STAGE|MOTION\s+FOR\s+ADOPTION)',
    re.IGNORECASE,
)

BILL_ITEM = re.compile(
    r'[•\-\*\u2022]\s+(.+?)(?:\s*\(?(?:Bill\s+No\.?\s*(\d+)\s+of\s+(\d{4}))?\)?)'
    r'(?:\s*\(Published on\s+[^)]+\))?'
    r'(?:\s*\(([^)]*Minister[^)]*)\))?',
    re.IGNORECASE | re.DOTALL,
)


def _stage_to_type(stage: str) -> str:
    stage = stage.upper()
    if 'FIRST' in stage:
        return 'bill_1st'
    if 'SECOND' in stage:
        return 'bill_2nd'
    if 'THIRD' in stage:
        return 'bill_3rd'
    if 'COMMITTEE' in stage:
        return 'committee_stage'
    if 'ADOPTION' in stage:
        return 'motion_adoption'
    return 'bill_reading'


def _parse_bills(text: str, date: str | None) -> list[dict]:
    contributions: list[dict] = []

    bill_match = BILL_SECTION.search(text)
    if not bill_match:
        return contributions

    bill_text = text[bill_match.end():]
    current_stage = ''

    for part in BILL_READING_HEADER.split(bill_text):
        if BILL_READING_HEADER.match(part):
            current_stage = part.strip().upper()
        else:
            for item_match in BILL_ITEM.finditer(part):
                title = item_match.group(1).strip()
                bill_no = item_match.group(2) or ''
                bill_year = item_match.group(3) or ''
                minister = item_match.group(4) or ''
                if bill_no:
                    title = f'{title} (Bill No. {bill_no} of {bill_year})'.strip()
                contributions.append({
                    'contribution_type': _stage_to_type(current_stage),
                    'raw_match_name': minister.strip() if minister else '',
                    'raw_constituency': '',
                    'ministry_addressed': minister.strip() if minister else '',
                    'subject_text': title,
                    'date': date or '',
                    'source_url': '',
                })

    return contributions


def parse_pdf(pdf_path: str, source_url: str = '') -> list[dict]:
    text = extract_text(pdf_path)
    date = _extract_date_from_header(text)
    contributions: list[dict] = []

    parsed = _parse_questions(text, date)
    for p in parsed:
        p['source_url'] = source_url
    contributions.extend(parsed)

    bills = _parse_bills(text, date)
    for b in bills:
        b['source_url'] = source_url
    contributions.extend(bills)

    return contributions


def run_for_document(file_path: str, source_url: str = '') -> list[dict]:
    return parse_pdf(file_path, source_url)
