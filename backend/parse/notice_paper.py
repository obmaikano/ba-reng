"""Parser for Botswana National Assembly Notice Paper PDFs."""

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

SECTION_TYPES: list[tuple[re.Pattern, str]] = [
    (re.compile(r'NOTICE\s+OF\s+QUESTIONS', re.IGNORECASE), 'question'),
    (re.compile(r"NOTICE\s+OF\s+MINISTERS['\u2019]\s*QUESTION\s+TIME", re.IGNORECASE), 'question'),
    (re.compile(r'NOTICE\s+OF\s+A?\s*MOTION', re.IGNORECASE), 'motion'),
    (re.compile(r'NOTICE\s+OF\s+MOTIONS', re.IGNORECASE), 'motion'),
    (re.compile(r'NOTICE\s+OF\s+A?\s*TABLING', re.IGNORECASE), 'tabling'),
    (re.compile(r'NOTICE\s+OF\s+TABLING', re.IGNORECASE), 'tabling'),
    (re.compile(r'NOTICE\s+OF\s+PRESENTATION', re.IGNORECASE), 'bill_presentation'),
    (re.compile(r'NOTICE\s+OF\s+AMENDMENTS?', re.IGNORECASE), 'amendment'),
    (re.compile(r'NOTICE\s+OF\s+SECOND\s+READING', re.IGNORECASE), 'second_reading'),
    (re.compile(r'NOTICE\s+OF\s+THIRD\s+READING', re.IGNORECASE), 'third_reading'),
    (re.compile(r'NOTICE\s+OF\s+A\s+PETITION', re.IGNORECASE), 'petition'),
]

QUESTION_START = re.compile(r'^(\d+)\.\s+(.+)')

MP_QUESTION_LINE = re.compile(
    r'((?:MR|MS|MRS|DR|HON)\.\s+.+?MP\.)'
    r'\s*\(([^)]+)\):\s*To ask the (?:Minister of |Minister for State)'
    r'\s*(.+?)(?:\s+(?:if|whether|to\s+state|to\s+update|what\s+plans|'
    r'why|what\s+action|how\s+many|to\s+apprise|to\s+brief|to\s+update|'
    r'whether\s+he|if\s+so))',
    re.IGNORECASE | re.DOTALL,
)

MOTION_SIGNATURE = re.compile(
    r'\(((?:MR|MS|MRS|DR|HON)\.\s+.+?),\s+MP\.\s*[-\u2013]\s*(.+?)\)',
    re.IGNORECASE,
)

MOTION_LINE = re.compile(r'^\s*(\d+)\.\s*\u201c(.+)', re.DOTALL)

TABLING_ENTRY = re.compile(r'^\s*\u2022\s+(.+)')
TABLING_MINISTER = re.compile(r'\((.+?)\)')

PAGE_NUM = re.compile(r'\((\d+)\)\s*')


def _remove_inline_page_numbers(text: str) -> str:
    """Remove parenthesized page numbers inserted during PDF text extraction."""
    return PAGE_NUM.sub('', text)


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


def extract_text(pdf_path: str) -> str:
    """Extract and concatenate text from all PDF pages."""
    with pdfplumber.open(pdf_path) as pdf:
        lines: list[str] = []
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines.append(text)
    return '\n'.join(lines)


def _split_sections(text: str) -> list[tuple[str, str, str]]:
    sections: list[tuple[str, str, str]] = []
    lines = text.split('\n')
    current_type = ''
    current_header = ''
    current_lines: list[str] = []

    for line in lines:
        ls = line.strip()
        matched_type = None
        for pattern, ctype in SECTION_TYPES:
            if pattern.search(ls):
                matched_type = ctype
                break
        if matched_type is not None:
            if current_type and current_lines:
                sections.append((current_type, current_header, '\n'.join(current_lines)))
            current_type = matched_type
            current_header = ls
            current_lines = []
        elif current_type:
            current_lines.append(ls)

    if current_type and current_lines:
        sections.append((current_type, current_header, '\n'.join(current_lines)))

    return sections


QUESTION_BLOCK = re.compile(
    r'(\d+)\.\s+'
    r'((?:MR|MS|MRS|DR|HON)\.\s+.+?MP\.)'
    r'\s*\(([^)]+)\):\s*To ask the (?:Minister of |Minister for State)'
    r'\s*(.+?)(?=\d+\.\s+(?:MR|MS|MRS|DR|HON)\.|\Z|(?:\n(?:NOTICE|$)))',
    re.IGNORECASE | re.DOTALL,
)


def _parse_questions(text: str, date: str | None) -> list[dict]:
    contributions: list[dict] = []
    text = _remove_inline_page_numbers(text)
    text = re.sub(r'\n\s*([a-z(])', r' \1', text)

    for match in QUESTION_BLOCK.finditer(text):
        raw_name = match.group(2).strip()
        constituency = match.group(3).strip()
        block_text = match.group(4).strip()
        # Extract ministry (everything up to first question word)
        min_match = re.search(
            r'(.+?)(?:\s+(?:if|whether|to\s+state|to\s+update|what\s+plans|'
            r'why|what\s+action|how\s+many|to\s+apprise|to\s+brief|to\s+update|'
            r'whether\s+he|if\s+so|when\s*:|what\s+steps|to\s+provide|'
            r'to\s+explain|to\s+clarify|to\s+give|to\s+indicate))',
            block_text, re.IGNORECASE | re.DOTALL,
        )
        if min_match:
            ministry = min_match.group(1).strip()
            subject_text = block_text[min_match.end():].strip()
        else:
            ministry = ''
            subject_text = block_text.strip()

        subject_text = subject_text.lstrip(':').strip()

        contributions.append({
            'contribution_type': 'question',
            'raw_match_name': raw_name,
            'raw_constituency': constituency,
            'ministry_addressed': ministry,
            'subject_text': subject_text,
            'date': date or '',
            'source_url': '',
        })

    return contributions


def _parse_motions(text: str, date: str | None) -> list[dict]:
    contributions: list[dict] = []
    text = _remove_inline_page_numbers(text)
    lines = text.split('\n')

    current_motion_lines: list[str] = []
    in_motion = False

    for line in lines:
        ls = line.strip()
        if not ls:
            continue

        motion_match = MOTION_LINE.match(ls)
        if motion_match:
            if in_motion and current_motion_lines:
                _finalize_motion(contributions, current_motion_lines, date)
            current_motion_lines = [motion_match.group(2)]
            in_motion = True
        elif in_motion:
            sig_match = MOTION_SIGNATURE.search(ls)
            if sig_match:
                current_motion_lines.append(ls[:sig_match.start()].strip())
                full_text = ' '.join(current_motion_lines).strip()
                raw_name = sig_match.group(1).strip()
                constituency = sig_match.group(2).strip()
                contributions.append({
                    'contribution_type': 'motion',
                    'raw_match_name': raw_name,
                    'raw_constituency': constituency,
                    'ministry_addressed': '',
                    'subject_text': full_text,
                    'date': date or '',
                })
                in_motion = False
                current_motion_lines = []
            else:
                current_motion_lines.append(ls)

    if in_motion and current_motion_lines:
        _finalize_motion(contributions, current_motion_lines, date)

    return contributions


def _finalize_motion(
    contributions: list[dict], lines: list[str], date: str | None,
) -> None:
    full_text = ' '.join(lines).strip()
    contributions.append({
        'contribution_type': 'motion',
        'raw_match_name': '',
        'raw_constituency': '',
        'ministry_addressed': '',
        'subject_text': full_text,
        'date': date or '',
    })


def _finalize_tabling(
    contributions: list[dict], ctype: str, title: list[str],
    minister: str, date: str | None,
) -> None:
    contributions.append({
        'contribution_type': ctype,
        'raw_match_name': '',
        'raw_constituency': '',
        'ministry_addressed': minister,
        'subject_text': ' '.join(title).strip(),
        'date': date or '',
    })


def _parse_tablings_and_bills(text: str, date: str | None,
                              ctype: str) -> list[dict]:
    contributions: list[dict] = []
    text = _remove_inline_page_numbers(text)
    lines = text.split('\n')
    current_title: list[str] = []
    current_minister = ''

    for line in lines:
        ls = line.strip()
        if not ls:
            continue

        tab_match = TABLING_ENTRY.match(ls)
        if tab_match:
            if current_title:
                _finalize_tabling(contributions, ctype, current_title,
                                  current_minister, date)
            current_title = [tab_match.group(1).strip()]
            current_minister = ''
        elif current_title:
            min_match = TABLING_MINISTER.search(ls)
            if min_match and ('Minister' in ls
                              or 'Minister' in min_match.group(1)):
                current_minister = (
                    min_match.group(1).strip()
                    if 'Minister' in ls
                    else ls.strip('()').strip()
                )
            else:
                current_title.append(ls)

    if current_title:
        _finalize_tabling(contributions, ctype, current_title,
                          current_minister, date)

    return contributions


def parse_pdf(pdf_path: str, source_url: str = '') -> list[dict]:
    """Parse a Notice Paper PDF and return a list of contribution dicts."""
    text = extract_text(pdf_path)
    date = _extract_date_from_header(text)
    sections = _split_sections(text)
    contributions: list[dict] = []

    for ctype, header, section_text in sections:
        if ctype in ('question',):
            parsed = _parse_questions(section_text, date)
            for p in parsed:
                p['source_url'] = source_url
            contributions.extend(parsed)
        elif ctype in ('motion',):
            parsed = _parse_motions(section_text, date)
            for p in parsed:
                p['source_url'] = source_url
            contributions.extend(parsed)
        elif ctype in ('tabling', 'bill_presentation', 'amendment',
                       'second_reading', 'third_reading', 'petition'):
            parsed = _parse_tablings_and_bills(section_text, date, ctype)
            for p in parsed:
                p['source_url'] = source_url
            contributions.extend(parsed)

    return contributions


def run_for_document(file_path: str, source_url: str = '') -> list[dict]:
    """Parse a single document and return contributions."""
    return parse_pdf(file_path, source_url)
