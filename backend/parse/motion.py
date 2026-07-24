"""Parser for Botswana Parliament Motion documents (private members' and government motions).

Real "Notice of Motions" PDFs list one or more motions as a numbered sequence,
each closed by a "(Mr. X, MP. - Constituency)" signature -- identical in shape
to the motion section of a Notice Paper. `parse_numbered_motions` (shared with
`notice_paper.py`) handles that format. A "MOVED BY: ... SECONDED BY: ..."
debate-transcript format is kept as a fallback for standalone motion documents
that use that structure instead.
"""

import re

from backend.parse.base import (
    _extract_date_from_header,
    extract_text,
    parse_numbered_motions,
)

MOVER_RE = re.compile(
    r'\bMOVED(?:\s+BY)?\s*:?\s*'
    r'((?:HON\.?|MR\.?|MS\.?|DR\.?|PROF\.?|BRIGADIER\.?)\s+.+?)\s*(?:MP\.?)?\s*'
    r'(?:\(([^)]+)\))?$',
    re.IGNORECASE | re.MULTILINE,
)

SECONDER_RE = re.compile(
    r'\bSECONDED(?:\s+BY)?\s*:?\s*'
    r'((?:HON\.?|MR\.?|MS\.?|DR\.?|PROF\.?|BRIGADIER\.?)\s+.+?)\s*(?:MP\.?)?\s*'
    r'(?:\(([^)]+)\))?$',
    re.IGNORECASE | re.MULTILINE,
)

MOTION_TITLE_RE = re.compile(
    r'\b(?:PRIVATE\s+MEMBERS?[\'\u2019]?\s+MOTION|MOTION)\s*(?:\u2014|\u2013|-|:)\s*(.+)',
    re.IGNORECASE,
)


def _parse_debate_transcript(text: str, date: str | None, source_url: str) -> list[dict]:
    """Fallback parser for a standalone motion with MOVED BY / SECONDED BY fields."""
    t_match = MOTION_TITLE_RE.search(text)
    m_match = MOVER_RE.search(text)

    if not t_match or not m_match:
        return []

    title = t_match.group(1).strip()
    mover = m_match.group(1).strip()
    mover_const = (m_match.group(2) or '').strip()

    base = {
        'contribution_type': 'motion',
        'subject_text': title,
        'date': date or '',
        'source_url': source_url,
    }

    contributions = [{
        **base,
        'raw_match_name': mover,
        'raw_constituency': mover_const,
        'ministry_addressed': '',
    }]

    s_match = SECONDER_RE.search(text)
    if s_match:
        contributions.append({
            **base,
            'raw_match_name': s_match.group(1).strip(),
            'raw_constituency': (s_match.group(2) or '').strip(),
            'ministry_addressed': '',
        })

    return contributions


def parse_pdf(pdf_path: str, source_url: str = '') -> list[dict]:
    """Parse a standalone motion PDF and return a list of contribution dicts."""
    text = extract_text(pdf_path)
    date = _extract_date_from_header(text)

    contributions = parse_numbered_motions(text, date)
    if not contributions:
        return _parse_debate_transcript(text, date, source_url)

    for c in contributions:
        c['source_url'] = source_url

    return contributions


def run_for_document(file_path: str, source_url: str = '') -> list[dict]:
    """Parse a single document and return contributions."""
    return parse_pdf(file_path, source_url)
