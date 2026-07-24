"""Parser for Botswana National Assembly Order Paper PDFs."""

import re

from backend.parse.base import (
    _extract_date_from_header,
    extract_text,
    normalise_ministry,
    parse_numbered_motions,
)

QUESTION_HEADER = re.compile(
    r'^(\d+)\.\s+'
    r'((?:MR|MS|MRS|DR|BRIGADIER|HON|PROF)\.?\s+.+?,?\s*MP\.)\s*'
    r'\(([^)]+)\)',
    re.IGNORECASE | re.MULTILINE,
)

QWN_HEADER = re.compile(r'QUESTIONS?\s+WITHOUT\s+NOTICE', re.IGNORECASE)
QUESTIONS_RESTART_HEADER = re.compile(r'^QUESTIONS\b', re.IGNORECASE | re.MULTILINE)

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


def _normalise_block(block: str) -> str:
    block = re.sub(r'\(\d+\)', '', block)
    block = re.sub(r'\n+', ' ', block)
    block = re.sub(r'\s{2,}', ' ', block)
    return block.strip()


def _parse_questions(text: str, date: str | None) -> list[dict]:
    contributions: list[dict] = []

    headers = list(QUESTION_HEADER.finditer(text))
    qwn_match = QWN_HEADER.search(text)
    qwn_start = qwn_match.start() if qwn_match else None
    qwn_end = None
    if qwn_match:
        restart_match = QUESTIONS_RESTART_HEADER.search(text, qwn_match.end())
        qwn_end = restart_match.start() if restart_match else len(text)

    for i, match in enumerate(headers):
        qnum = match.group(1)
        raw_name = match.group(2).strip()
        constituency = match.group(3).strip()
        is_qwn = (
            qwn_start is not None
            and match.start() > qwn_start
            and match.start() < qwn_end
        )

        start = match.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        after_header = text[start:end].strip()

        after_header = _normalise_block(after_header)

        after_header = re.sub(r'^:\s*To ask the\s*', '', after_header)

        delim_match = MINISTRY_DELIM.search(after_header)
        if delim_match:
            ministry = after_header[:delim_match.start()].strip()
            ministry = normalise_ministry(ministry)
            subject_text = after_header[delim_match.start():].strip()
        else:
            ministry = after_header
            subject_text = ''

        contributions.append({
            'contribution_type': 'question_without_notice' if is_qwn else 'oral_question',
            'raw_match_name': raw_name,
            'raw_constituency': constituency,
            'ministry_addressed': ministry,
            'subject_text': subject_text,
            'date': date or '',
            'source_url': '',
        })

    return contributions


def _parse_motions(text: str, date: str | None) -> list[dict]:
    return parse_numbered_motions(text, date)


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
    r'[•\-\*\u2022]\s+(.+?)'
    r'(?:\s*\(?(?:Bill\s+No\.?\s*(\d+)\s+of\s+(\d{4}))\)?)?'
    r'(?:\s*\(Published on\s+[^)]+\))?'
    r'(?:\s*\(([^)]*Minister[^)]*)\))?'
    r'\s*$',
    re.IGNORECASE | re.MULTILINE,
)

# PDF line-wrap can split "(Bill No. 31 of 2025)" across two lines as
# "...(Bill" / "No. 31 of 2025)", which BILL_ITEM (no DOTALL, so its title
# capture can't cross that line break) then reports as having no bill
# number at all. Recovered by searching a bounded window after the bullet
# separately, rather than rewriting BILL_ITEM's anchoring to allow
# arbitrary DOTALL spans (which would risk the title capture swallowing
# far more than one bullet item).
BILL_NO_FALLBACK = re.compile(r'No\.?\s*(\d+)\s+of\s+(\d{4})\s*\)', re.IGNORECASE)


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


def _stage_to_chronology_key(stage: str) -> str:
    """Canonical stage label, shared with bill.py's 'introduced' stage.

    Lets a bill's introduction record (from bill.py) and its Order Paper
    reading records be grouped and ordered by (bill_no, bill_year, stage)
    into a single chronology, rather than each parser's own contribution_type
    taxonomy (which exists for UI tagging, not stage ordering).
    """
    stage = stage.upper()
    if 'FIRST' in stage:
        return 'first_reading'
    if 'SECOND' in stage:
        return 'second_reading'
    if 'THIRD' in stage:
        return 'third_reading'
    if 'COMMITTEE' in stage:
        return 'committee_stage'
    if 'ADOPTION' in stage:
        return 'motion_adoption'
    return 'reading'


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
                if not bill_no:
                    next_bullet = re.search(r'[•\-\*•]\s', part[item_match.end():])
                    window_end = (
                        item_match.end() + next_bullet.start()
                        if next_bullet
                        else len(part)
                    )
                    window_end = min(item_match.end() + 100, window_end)
                    fallback_match = BILL_NO_FALLBACK.search(
                        part, item_match.start(), window_end,
                    )
                    if fallback_match:
                        bill_no = fallback_match.group(1)
                        bill_year = fallback_match.group(2)
                if bill_no:
                    title = f'{title} (Bill No. {bill_no} of {bill_year})'.strip()
                if len(title) < 5:
                    continue

                extracted_data = None
                if bill_no and bill_year:
                    extracted_data = {
                        'bill_no': int(bill_no),
                        'bill_year': int(bill_year),
                        'stage': _stage_to_chronology_key(current_stage),
                    }

                contributions.append({
                    'contribution_type': _stage_to_type(current_stage),
                    'raw_match_name': minister.strip() if minister else '',
                    'raw_constituency': '',
                    'ministry_addressed': minister.strip() if minister else '',
                    'subject_text': title,
                    'date': date or '',
                    'source_url': '',
                    'extracted_data': extracted_data,
                })

    return contributions


AMENDMENT_SECTION = re.compile(r'\bAMENDMENTS\b', re.IGNORECASE)
AMENDMENT_ITEM_START = re.compile(r'^\s*(\d+)\.\s+', re.MULTILINE)
CLAUSE_REF = re.compile(
    r'[Cc]lause\s+(\d+(?:\s*\(\d+\))?)'
    r'(?:.{0,60}?[Pp]age\s+([A-Z]?\.?\s?\d+))?',
    re.DOTALL,
)
AMENDMENT_ACTION = re.compile(r'\b(substituting|deleting|inserting|adding)\b', re.IGNORECASE)
AMENDMENT_MINISTER_SIGNATURE = re.compile(
    r'\((Minister\s+(?:of|for)\s+[^)]+?)\)\s*$', re.IGNORECASE,
)
AMENDMENT_MP_SIGNATURE = re.compile(
    r'\(((?:MR|MS|MRS|DR|HON|BRIGADIER)\.?\s+.+?),\s+MP\.\s*[-–]\s*(.+?)\)\s*$', re.IGNORECASE,
)


def _parse_bill_amendments(text: str, date: str | None) -> list[dict]:
    """Parse per-clause Bill Stage Amendments (clause number, page, action)."""
    contributions: list[dict] = []

    section_match = AMENDMENT_SECTION.search(text)
    if not section_match:
        return contributions

    section_text = text[section_match.end():]
    items = list(AMENDMENT_ITEM_START.finditer(section_text))

    for i, item in enumerate(items):
        start = item.end()
        end = items[i + 1].start() if i + 1 < len(items) else len(section_text)
        body = section_text[start:end].strip()
        if not body:
            continue

        clause_match = CLAUSE_REF.search(body)
        clause_number = clause_match.group(1).strip() if clause_match else ''
        page_reference = (
            clause_match.group(2).strip()
            if clause_match and clause_match.group(2)
            else ''
        )

        action_match = AMENDMENT_ACTION.search(body)
        action = action_match.group(1).lower() if action_match else ''

        mover = ''
        constituency = ''
        mp_match = AMENDMENT_MP_SIGNATURE.search(body)
        if mp_match:
            mover = mp_match.group(1).strip()
            constituency = mp_match.group(2).strip()
        else:
            minister_match = AMENDMENT_MINISTER_SIGNATURE.search(body)
            if minister_match:
                mover = minister_match.group(1).strip()

        extracted_data = {}
        if clause_number:
            extracted_data['clause_number'] = clause_number
        if page_reference:
            extracted_data['page_reference'] = page_reference
        if action:
            extracted_data['action'] = action

        contributions.append({
            'contribution_type': 'bill_amendment',
            'raw_match_name': mover,
            'raw_constituency': constituency,
            'ministry_addressed': '',
            'subject_text': re.sub(r'\s+', ' ', body).strip(),
            'date': date or '',
            'source_url': '',
            'extracted_data': extracted_data or None,
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

    bill_match = BILL_SECTION.search(text)
    if bill_match:
        amendment_match = AMENDMENT_SECTION.search(text, bill_match.end())
        motions_end = amendment_match.start() if amendment_match else len(text)
        motions = _parse_motions(text[bill_match.end():motions_end], date)
        for m in motions:
            m['source_url'] = source_url
        contributions.extend(motions)

    amendments = _parse_bill_amendments(text, date)
    for a in amendments:
        a['source_url'] = source_url
    contributions.extend(amendments)

    return contributions


def run_for_document(file_path: str, source_url: str = '') -> list[dict]:
    return parse_pdf(file_path, source_url)
