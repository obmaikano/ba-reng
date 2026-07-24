"""Parser for Botswana National Assembly Notice Paper PDFs."""

import re

from backend.parse.base import (
    DATE_PATTERN,
    _extract_date_from_header,
    extract_text,
    normalise_ministry,
    parse_numbered_motions,
)

SECTION_TYPES: list[tuple[re.Pattern, str]] = [
    (re.compile(r'NOTICE\s+OF\s+QUESTIONS', re.IGNORECASE), 'oral_question'),
    (re.compile(r"NOTICE\s+OF\s+MINISTERS['\u2019]\s*QUESTION\s+TIME", re.IGNORECASE), 'oral_question'),
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

TABLING_ENTRY = re.compile(r'^\s*\u2022\s+(.+)')
TABLING_MINISTER = re.compile(r'\((.+?)\)')
PETITION_MP = re.compile(
    r'PRESENTATION OF A PETITION BY ((?:MR|MS|MRS|DR|HON)\.\s+.+?MP\.)',
    re.IGNORECASE,
)

PAGE_NUM = re.compile(r'\((\d+)\)\s*')

NOTICE_NUMBER = re.compile(r'\((\d{2,4})\)')
SUB_QUESTION_MARKER = re.compile(r'\((i{1,3}|iv|vi?)\)\s*')


def _remove_inline_page_numbers(text: str) -> str:
    """Remove parenthesized page numbers inserted during PDF text extraction."""
    return PAGE_NUM.sub('', text)


def _extract_sub_questions(text: str) -> tuple[str, list[str]]:
    """Split a question body into its preamble and (i)-(vi) sub-questions, if any."""
    markers = list(SUB_QUESTION_MARKER.finditer(text))
    if not markers:
        return text, []

    sub_questions = []
    for i, marker in enumerate(markers):
        start = marker.end()
        end = markers[i + 1].start() if i + 1 < len(markers) else len(text)
        sub_questions.append(text[start:end].strip())

    preamble = text[:markers[0].start()].strip()
    return preamble, sub_questions


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
    r'((?:MR|MS|MRS|DR|HON|BRIGADIER)\.?\s+.+?MP\.)'
    r'\s*\(([^)]+)\):\s*To ask the (?:Minister of |Minister for State)'
    r'\s*(.+?)(?=\d+\.\s+(?:MR|MS|MRS|DR|HON|BRIGADIER)\.?\s|\Z|(?:\n(?:NOTICE|$)))',
    re.IGNORECASE | re.DOTALL,
)


QUESTION_HEADER = re.compile(
    r'\d+\.\s+(?:MR|MS|MRS|DR|HON|BRIGADIER)\.?\s+.+?MP\.\s*\([^)]+\):',
    re.IGNORECASE | re.DOTALL,
)


def _extract_notice_numbers(text: str) -> list[int | None]:
    """Return one notice number per question header, scoped to that question's own span.

    Notice Numbers (e.g. "(381)") are injected mid-sentence at unpredictable
    points during PDF text extraction — sometimes inside "Minister of",
    sometimes further along in the ministry name. Scoping the search to the
    span between one question's header and the next bounds the blast radius
    of any stray parenthetical number elsewhere in the section (a page
    number, a year, a statute reference) to at most the one question it
    falls within, instead of desyncing every question that follows it.
    """
    headers = list(QUESTION_HEADER.finditer(text))
    numbers: list[int | None] = []
    for i, header in enumerate(headers):
        span_end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        window = text[header.end():span_end]
        match = NOTICE_NUMBER.search(window)
        numbers.append(int(match.group(1)) if match else None)
    return numbers


def _parse_questions(text: str, date: str | None) -> list[dict]:
    contributions: list[dict] = []
    text = re.sub(r'\n\s*([a-z(])', r' \1', text)

    notice_numbers = _extract_notice_numbers(text)
    text = _remove_inline_page_numbers(text)

    for idx, match in enumerate(QUESTION_BLOCK.finditer(text)):
        raw_name = match.group(2).strip()
        constituency = match.group(3).strip()
        block_text = match.group(4).strip()
        notice_number = notice_numbers[idx] if idx < len(notice_numbers) else None

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
        _, sub_questions = _extract_sub_questions(subject_text)

        extracted_data: dict = {}
        if notice_number is not None:
            extracted_data['notice_number'] = notice_number
        if sub_questions:
            extracted_data['sub_questions'] = sub_questions

        contributions.append({
            'contribution_type': 'oral_question',
            'raw_match_name': raw_name,
            'raw_constituency': constituency,
            'ministry_addressed': normalise_ministry(ministry),
            'subject_text': subject_text,
            'date': date or '',
            'source_url': '',
            'extracted_data': extracted_data or None,
        })

    return contributions


def _parse_motions(text: str, date: str | None) -> list[dict]:
    return parse_numbered_motions(_remove_inline_page_numbers(text), date)


def _finalize_tabling(
    contributions: list[dict], ctype: str, title: list[str],
    minister: str, date: str | None,
) -> None:
    subject_text = ' '.join(title).strip()

    raw_match_name = ''
    raw_constituency = ''

    if ctype == 'petition':
        pet_match = PETITION_MP.search(subject_text)
        if pet_match:
            raw_match_name = pet_match.group(1).strip()

    if not raw_match_name and minister:
        raw_match_name = minister

    contributions.append({
        'contribution_type': ctype,
        'raw_match_name': raw_match_name,
        'raw_constituency': raw_constituency,
        'ministry_addressed': normalise_ministry(minister) if minister else '',
        'subject_text': subject_text,
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
        if ctype in ('oral_question',):
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
