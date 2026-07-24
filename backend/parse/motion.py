"""Parser for Botswana Parliament Motion documents (private members' and government motions)."""

import re

from backend.parse.base import _extract_date_from_header, extract_text, normalise_ministry

MOTION_TITLE_RE = re.compile(
    r'(?:MOTION|PRIVATE\s+MEMBERS?[\'\u2019]?\s+MOTION)\s*(?:—|–|-|:)?\s*(.+)',
    re.IGNORECASE,
)

MOVER_RE = re.compile(
    r'(?:MOVED|MOVED\s+BY|MOVER|BY|PRESENTED\s+BY)\s*:?\s*'
    r'((?:HON\.?|MR\.?|MS\.?|DR\.?|PROF\.?|BRIGADIER\.?)\s+.+?)\s*(?:MP\.?)?\s*'
    r'(?:\(([^)]+)\))?',
    re.IGNORECASE,
)

SECONDER_RE = re.compile(
    r'(?:SECONDED|SECONDED\s+BY|SECONDER)\s*:?\s*'
    r'((?:HON\.?|MR\.?|MS\.?|DR\.?|PROF\.?|BRIGADIER\.?)\s+.+?)\s*(?:MP\.?)?\s*'
    r'(?:\(([^)]+)\))?',
    re.IGNORECASE,
)


def _extract_motion_details(text: str) -> tuple[str, str, str, str, str]:
    title = ''
    mover = ''
    mover_constituency = ''
    seconder = ''
    seconder_constituency = ''

    t_match = MOTION_TITLE_RE.search(text)
    if t_match:
        title = t_match.group(1).strip()

    m_match = MOVER_RE.search(text)
    if m_match:
        mover = m_match.group(1).strip()
        mover_constituency = (m_match.group(2) or '').strip()

    s_match = SECONDER_RE.search(text)
    if s_match:
        seconder = s_match.group(1).strip()
        seconder_constituency = (s_match.group(2) or '').strip()

    return title, mover, mover_constituency, seconder, seconder_constituency


def parse_pdf(pdf_path: str, source_url: str = '') -> list[dict]:
    text = extract_text(pdf_path)
    date = _extract_date_from_header(text)
    title, mover, mover_const, seconder, seconder_const = _extract_motion_details(text)

    if not title and not mover:
        return []

    contributions: list[dict] = []

    base = {
        'contribution_type': 'motion',
        'subject_text': title,
        'date': date or '',
        'source_url': source_url,
    }

    contributions.append({
        **base,
        'raw_match_name': mover,
        'raw_constituency': mover_const,
        'ministry_addressed': '',
    })

    if seconder:
        contributions.append({
            **base,
            'raw_match_name': seconder,
            'raw_constituency': seconder_const,
            'ministry_addressed': '',
        })

    return contributions


def run_for_document(file_path: str, source_url: str = '') -> list[dict]:
    return parse_pdf(file_path, source_url)
