"""Parser for Botswana Parliament Bill documents."""

import re

from backend.parse.base import (
    _extract_date_from_header,
    extract_text,
    normalise_ministry,
)

BILL_NO_RE = re.compile(r'Bill\s+No\.\s*(\d+)\s+of\s+(\d{4})', re.IGNORECASE)
PUBLISHED_RE = re.compile(r'Published on\s+(.+)', re.IGNORECASE)
DATE_LINE = re.compile(
    r'(\d{1,2})(?:ST|ND|RD|TH)?\s+(JANUARY|FEBRUARY|MARCH|APRIL|MAY|'
    r'JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)\s*,?\s*(\d{4})',
    re.IGNORECASE,
)
MINISTER_RE = re.compile(
    r'^([A-Z][A-Z.\']{1,}(?:\s+[A-Z][A-Z.\']{1,}){1,3}),?\s*$'
    r'\n(Minister\s+(?:of|for)(?:\s+State)?\s+[A-Z][A-Za-z\s&,]+?)\s*\.?\s*$',
    re.IGNORECASE | re.MULTILINE,
)

MINISTER_MULTILINE_RE = re.compile(
    r'^([A-Z][A-Z.\']{1,}(?:\s+[A-Z][A-Z.\']{1,}){1,3}),?\s*$'
    r'\n(Minister\s+(?:of|for)(?:\s+State)?\s+[A-Z][A-Za-z\s&,]+?)'
    r'\n([A-Z][A-Za-z\s&,]+?)\s*\.?\s*$',
    re.IGNORECASE | re.MULTILINE,
)


def _extract_title(text: str) -> str:
    lines = text.split('\n')
    for i, line in enumerate(lines):
        ls = line.strip()
        if BILL_NO_RE.search(ls) and i + 1 < len(lines):
            title = lines[i + 1].strip()
            if title:
                return title
    return ''


def _extract_bill_no(text: str) -> str:
    m = BILL_NO_RE.search(text)
    if m:
        return f'Bill No. {m.group(1)} of {m.group(2)}'
    return ''


def _extract_bill_identity(text: str) -> tuple[int, int] | None:
    m = BILL_NO_RE.search(text)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def _extract_minister_and_ministry(text: str) -> tuple[str, str]:
    # Minister signature appears at the END of bills
    # Use rfind instead of search to get the last occurrence
    for regex in (MINISTER_MULTILINE_RE, MINISTER_RE):
        matches = list(regex.finditer(text))
        if matches:
            m = matches[-1]  # last match
            name = m.group(1).strip()
            name = re.sub(r'^BY\s*', '', name).strip()
            role_parts = [m.group(2).strip()]
            if m.lastindex and m.lastindex >= 3:
                role_parts.append(m.group(3).strip())
            role = ' '.join(role_parts).strip()
            return f'HON. {name}, MP.', normalise_ministry(role)

    return '', ''


def _extract_date(text: str) -> str:
    m = DATE_LINE.search(text)
    if m:
        from datetime import datetime
        raw = f'{m.group(1)} {m.group(2)} {m.group(3)}'
        try:
            return datetime.strptime(raw, '%d %B %Y').strftime('%Y-%m-%d')
        except ValueError:
            pass
    return _extract_date_from_header(text) or ''


def parse_pdf(pdf_path: str, source_url: str = '') -> list[dict]:
    text = extract_text(pdf_path)
    title = _extract_title(text)
    bill_no = _extract_bill_no(text)
    date = _extract_date(text)
    minister, ministry = _extract_minister_and_ministry(text)

    if not minister and not ministry:
        return []

    subject = title
    if bill_no:
        subject = f'{title} ({bill_no})'

    # Every standalone Bill document observed in the corpus is the initial
    # gazettal publication ("A draft of the above Bill... is set out below"),
    # with "Date of Assent"/"Date of Commencement" left blank -- i.e. always
    # the pre-first-reading "introduced" stage, before any Order Paper
    # reading. bill_no/bill_year let this record be grouped with the
    # bill_1st/bill_2nd/bill_3rd/committee_stage records order_paper.py
    # produces for the same bill into a single stage chronology.
    identity = _extract_bill_identity(text)
    extracted_data = None
    if identity:
        extracted_data = {
            'bill_no': identity[0],
            'bill_year': identity[1],
            'stage': 'introduced',
        }

    return [{
        'contribution_type': 'bill_presentation',
        'raw_match_name': minister,
        'raw_constituency': '',
        'ministry_addressed': ministry,
        'subject_text': subject,
        'date': date,
        'source_url': source_url,
        'extracted_data': extracted_data,
    }]


def run_for_document(file_path: str, source_url: str = '') -> list[dict]:
    return parse_pdf(file_path, source_url)
