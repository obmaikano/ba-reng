"""Metadata API — contribution type labels, party colors, and lookup tables."""

from fastapi import APIRouter

from backend.db.connection import get_connection

router = APIRouter(prefix='/api/v1/metadata', tags=['metadata'])

# Stable colour palette for deterministic party colour assignment.
PARTY_PALETTE = [
    'var(--accent-blue)',    # #2965CC
    'var(--accent-amber)',   # #F5A623
    'var(--accent-green)',   # #16A34A
    'var(--accent-red)',     # #EF4444
    '#8B5CF6',               # violet
    '#EC4899',               # pink
    '#06B6D4',               # cyan
    '#F97316',               # orange
    '#84CC16',               # lime
    '#6366F1',               # indigo
]


def _party_short(name: str) -> str:
    """Derive a short label from a full party name."""
    # Known acronyms that need manual handling.
    KNOWN: dict[str, str] = {
        'Umbrella for Democratic Change (UDC)': 'UDC',
        'Botswana Democratic Party (BDP)': 'BDP',
        'Botswana Congress Party (BCP)': 'BCP',
        'Botswana Patriotic Front (BPF)': 'BPF',
        'Alliance for Progressives (AP)': 'AP',
        'Botswana Republican Party (BRP)': 'BRP',
        'Real Alternative Party (RAP)': 'RAP',
        'Independent': 'IND',
        'Specially Elected': 'SE',
        'Ex-officio': 'EXO',
    }
    if name in KNOWN:
        return KNOWN[name]
    # Fall back: extract uppercase letters inside parentheses, or acronym.
    import re
    m = re.search(r'\(([A-Z]+)\)', name)
    if m:
        return m.group(1)
    # Acronym from capital letters.
    acronym = ''.join(c for c in name if c.isupper())
    if len(acronym) >= 2:
        return acronym[:5]
    return name[:5].upper()


@router.get('/parties')
def party_metadata() -> dict[str, dict]:
    """Return party short-names and colours for every party in the database."""
    conn = get_connection()
    try:
        rows = conn.execute(
            'SELECT DISTINCT party FROM mps WHERE party IS NOT NULL AND party != \'\' ORDER BY party'
        ).fetchall()
        parties: dict[str, dict] = {}
        for i, row in enumerate(rows):
            name = row['party']
            parties[name] = {
                'short': _party_short(name),
                'color': PARTY_PALETTE[i % len(PARTY_PALETTE)],
            }
        return parties
    finally:
        conn.close()


@router.get('/contribution-types')
def contribution_type_metadata() -> dict[str, dict]:
    """Return label and colour for every contribution type seen in the database."""
    conn = get_connection()
    try:
        rows = conn.execute(
            'SELECT DISTINCT contribution_type FROM contributions '
            'WHERE contribution_type IS NOT NULL AND contribution_type != \'\' '
            'ORDER BY contribution_type'
        ).fetchall()

        LABELS: dict[str, str] = {
            'question': 'Question',
            'oral_question': 'Question',
            'oral_q': 'Question',
            'minist_question': "Minister's Q&A",
            'minist_q': "Minister's Q&A",
            'motion': 'Motion',
            'bill_presentation': 'New Bill',
            'bill_1st': 'Bill: Introduced',
            'bill_2nd': 'Bill: Debated',
            'bill_3rd': 'Bill: Final Vote',
            'bill_reading': 'Bill: Reading',
            'bill_amendment': 'Bill Change',
            'committee_of_supply': 'Budget Review',
            'tabling': 'Document Filed',
            'amendment': 'Bill Change',
            'petition': 'Petition',
            'ministerial_statement': "Minister's Update",
            'question_without_notice': 'Question',
            'member_statement': 'Statement',
            'point_of_procedure': 'Point of Procedure',
            'supplementary_question': 'Supplementary Q',
            'minister_answer': 'Minister Answer',
            'motion_detail': 'Motion Detail',
            'bill_detail': 'Bill Detail',
        }

        TAG_COLORS: dict[str, str] = {
            'question': 'var(--accent-blue)',
            'oral_question': 'var(--accent-blue)',
            'oral_q': 'var(--accent-blue)',
            'minist_question': 'var(--accent-red)',
            'minist_q': 'var(--accent-red)',
            'motion': 'var(--accent-amber)',
            'tabling': 'var(--accent-green)',
            'bill_presentation': 'var(--accent-green)',
            'bill_1st': 'var(--accent-green)',
            'bill_2nd': 'var(--accent-green)',
            'bill_3rd': 'var(--accent-green)',
            'bill_reading': 'var(--accent-green)',
            'bill_amendment': 'var(--accent-red)',
            'committee_of_supply': 'var(--accent-amber)',
            'amendment': 'var(--accent-red)',
            'petition': 'var(--text-secondary)',
            'ministerial_statement': 'var(--text-secondary)',
            'question_without_notice': 'var(--accent-blue)',
            'member_statement': 'var(--text-secondary)',
            'point_of_procedure': 'var(--accent-amber)',
            'supplementary_question': 'var(--accent-blue)',
            'minister_answer': 'var(--accent-green)',
            'motion_detail': 'var(--accent-amber)',
            'bill_detail': 'var(--accent-green)',
        }

        types: dict[str, dict] = {}
        for row in rows:
            ct = row['contribution_type']
            types[ct] = {
                'type': ct,
                'label': LABELS.get(ct, ct.replace('_', ' ').title()),
                'color': TAG_COLORS.get(ct, 'var(--text-secondary)'),
            }
        return types
    finally:
        conn.close()
