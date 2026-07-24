"""Parser for Botswana Parliament Committee of Supply speeches.

Extracts organisation codes, recurrent/development budget figures,
and operational performance metrics.
"""

import re
from typing import Any

from backend.parse.base import (
    _extract_date_from_header,
    extract_text,
    normalise_ministry,
)

ORG_CODE_RE = re.compile(r'(?:ORGANISATION|ORG|ORGANIZATION)\s*(?:CODE)?:?\s*(\d{4})', re.IGNORECASE)

PULA_FIGURE = r'Pula\s*\(P\s*([\d][\d,\s]*\d(?:\.\d+)?)\)'

# Committee of Supply speeches restate prior-year budget allocations as
# context before stating the current request, using near-identical wording
# ("...was allocated a recurrent budget of ... Pula (PNNN)"). Anchoring to a
# first-person or passive request verb distinguishes the actual ask from that
# historical reference. Only "I request" is verified against real benchmark
# PDFs; the other alternatives are plausible formal-English variants for the
# same document type but unverified — see ISSUE in .vibe/STATE.md.
REQUEST_PREFIX = (
    r'(?:(?:I|We)\s+request\b|(?:is|are)\s+(?:hereby\s+)?(?:requested|sought)\b)'
)

RECURRENT_RE = re.compile(
    REQUEST_PREFIX + r'.{0,160}?Recurrent\s+Budget\s+(?:of|in\s+the\s+sum\s+of)\s+.{0,200}?'
    + PULA_FIGURE
    + r'|' + REQUEST_PREFIX + r'.{0,160}?' + PULA_FIGURE + r'\s+for\s+the\s+recurrent\s+budget',
    re.IGNORECASE | re.DOTALL,
)

DEVELOPMENT_RE = re.compile(
    REQUEST_PREFIX
    + r'.{0,160}?Development\s+Budget\s+(?:of|in\s+the\s+sum\s+of|amounting\s+to)\s+.{0,200}?'
    + PULA_FIGURE
    + r'|' + REQUEST_PREFIX + r'.{0,160}?' + PULA_FIGURE
    + r'\s+for\s+the\s+[Dd]evelopment\s+[Bb]udget',
    re.IGNORECASE | re.DOTALL,
)

TOTAL_RE = re.compile(
    r'(?:Total|Total\s*Budget|Aggregate):?\s*'
    r'P?([\d,]+(?:\.\d+)?)\s*(million|billion|thousand)?',
    re.IGNORECASE,
)

PERCENT_MENTION_RE = re.compile(r'(\d+(?:\.\d+)?)\s*%')

BACKLOG_PARENTHETICAL_RE = re.compile(
    r'\((\d+)\)\s*of\s+the\s+pending\s+cases\s+(?:are\s+)?considered\s+backlog',
    re.IGNORECASE,
)

CASE_BACKLOG_RE = re.compile(
    r'(?:backlog|pending)\s*(?:of\s*)?(\d+(?:,\d{3})*)\s*(?:cases?|files?)',
    re.IGNORECASE,
)

COLLECTION_TARGET_RE = re.compile(
    r'target\s+of\s+(P[\d][\d,.\s]*\d\s*(?:billion|million|thousand)?)',
    re.IGNORECASE,
)


def _clean_pula_digits(raw: str) -> int:
    return int(float(re.sub(r'[,\s]', '', raw)))


def _parse_budget_value(text: str) -> dict[str, Any]:
    budget: dict[str, Any] = {}

    rec_match = RECURRENT_RE.search(text)
    if rec_match:
        raw = rec_match.group(1) or rec_match.group(2)
        budget['recurrent'] = _clean_pula_digits(raw)

    dev_match = DEVELOPMENT_RE.search(text)
    if dev_match:
        raw = dev_match.group(1) or dev_match.group(2)
        budget['development'] = _clean_pula_digits(raw)

    total_match = TOTAL_RE.search(text)
    if total_match:
        budget['total'] = f'P{total_match.group(1)}{total_match.group(2) or ""}'.strip()

    return budget


def _extract_performance_metrics(text: str) -> dict[str, Any]:
    metrics: dict[str, Any] = {}

    percentages = sorted({float(m) for m in PERCENT_MENTION_RE.findall(text)})
    if percentages:
        metrics['percentage_mentions'] = percentages

    backlog_match = BACKLOG_PARENTHETICAL_RE.search(text)
    if backlog_match:
        metrics['case_backlog'] = int(backlog_match.group(1))
    else:
        fallback = CASE_BACKLOG_RE.search(text)
        if fallback:
            metrics['case_backlog'] = int(fallback.group(1).replace(',', ''))

    targets = COLLECTION_TARGET_RE.findall(text)
    if targets:
        metrics['collection_targets'] = [re.sub(r'\s+', ' ', t).strip() for t in targets]

    return metrics


def _extract_org_code(text: str) -> str | None:
    m = ORG_CODE_RE.search(text)
    return m.group(1) if m else None


def _extract_minister_and_ministry(text: str) -> tuple[str, str]:
    lines = [l.strip() for l in text.split('\n')[:100] if l.strip()]

    name = ''
    ministry = ''

    # Find all HON/HONOURABLE mentions
    for i, line in enumerate(lines):
        m = re.search(r'HON(?:OURABLE|\.?)\s+([A-Z][A-Za-z.\s]{4,}(?:,\s*MP)?)', line)
        if m:
            candidate = m.group(0).strip()
            # Filter out role descriptions like "HONOURABLE MINISTER OF X"
            if re.search(r'MINISTER\s+(?:OF|FOR)', candidate, re.IGNORECASE):
                # Extract just the minister role from this line
                for j in range(i + 1, min(i + 4, len(lines))):
                    nl = lines[j]
                    if re.match(r'^(?:HON|DR|MR|MS|PROF)', nl, re.IGNORECASE):
                        name = nl.strip()
                        break
                    elif re.match(r'^[A-Z][A-Za-z]{2,}(?:\s+[A-Z][A-Za-z]{2,}){1,4}$', nl):
                        name = nl.strip()
                        break
                    elif re.match(r'^[A-Z][A-Z.]{2,}(?:\s+[A-Z][A-Z.]{2,}){1,4}$', nl):
                        name = nl.strip()
                        break
                continue

            name = candidate
            # If there's a role line right after, capture it
            if name and i + 1 < len(lines):
                nl = lines[i + 1]
                if re.match(r'^(?:THE )?(?:HONOURABLE\s+)?MINISTER\b', nl, re.IGNORECASE):
                    role_parts = [nl]
                    for j in range(i + 2, min(i + 4, len(lines))):
                        nl2 = lines[j]
                        if re.match(r'^(?:COMMITTEE|ORGANI|REPUBLIC|\d+)', nl2, re.IGNORECASE):
                            break
                        if nl2[0].isupper() and not re.match(r'^(?:HON|MR|MS|DR|PROF)', nl2, re.IGNORECASE):
                            role_parts.append(nl2)
                        else:
                            break
                    role = ' '.join(role_parts).strip()
                    ministry = normalise_ministry(role)
            break

    # Clean name
    name = _clean_name(name)

    # Fallback: BY line without HON prefix — plain name block
    if not name and not ministry:
        for i, line in enumerate(lines):
            if line.upper().strip() in ('BY', 'PRESENTED BY', 'DELIVERED BY', 'SPEECH BY'):
                for j in range(i + 1, min(i + 5, len(lines))):
                    nl = lines[j]
                    if re.match(r'^(?:COMMITTEE|ORGANI|REPUBLIC|\d|I\.|Mr\.\s)', nl, re.IGNORECASE):
                        break
                    if re.match(r'^(?:THE )?MINISTER\b', nl, re.IGNORECASE):
                        role_parts = [nl]
                        for k in range(j + 1, min(j + 3, len(lines))):
                            if lines[k][0].isupper() and not re.match(r'^(?:HON|MR|MS|DR|PROF|\d)', lines[k]):
                                role_parts.append(lines[k])
                            else:
                                break
                        ministry = normalise_ministry(' '.join(role_parts))
                        break
                    if re.match(r'^[A-Z][A-Za-z]{2,}(?:\s+[A-Z][A-Za-z]{2,}){1,4}$', nl):
                        name = nl
                        break
                break
    if not ministry:
        for line in lines[:8]:
            m = re.search(r'MINISTRY\s+(?:OF|FOR(?:\s+STATE)?)\s+([A-Z][A-Z\s,&-]+)', line, re.IGNORECASE)
            if m:
                ministry = normalise_ministry(f'Minister of {m.group(1).strip()}')
                break

    if not ministry:
        for line in lines[:8]:
            m = re.search(r'(?:THE )?MINISTER\s+(?:OF|FOR(?:\s+STATE)?)\s+([A-Z][A-Z\s,&-]+)', line, re.IGNORECASE)
            if m:
                ministry = normalise_ministry(f'Minister of {m.group(1).strip()}')
                break

    if not ministry:
        for line in lines[:8]:
            m = re.search(r'(?:THE )?(?:HONOURABLE\s+)?MINISTER\s+(?:OF|FOR|AND)\s+([A-Z][A-Z\s,&]+)', line, re.IGNORECASE)
            if m:
                ministry = normalise_ministry(m.group(0))
                break

    return name, ministry


def _clean_name(raw: str) -> str:
    name = raw.strip()
    # Filter pure role descriptions
    if re.match(r'^(?:HONOURABLE|HON\.?)\s+MINISTER\s+(?:OF|FOR)\b', name, re.IGNORECASE):
        return ''
    name = re.sub(r'\s+', ' ', name)
    name = re.sub(r'^HON(?:OURABLE|\.?)\s+MINISTER\s+', 'HON. ', name, flags=re.IGNORECASE)
    if name and not re.match(r'^(MR|MS|DR|HON)', name.upper()):
        name = f'HON. {name}, MP.'
    return name


def _clean_speech(text: str) -> str:
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'\s{2,}', ' ', text)
    text = re.sub(r' +\|\s*P\s*a\s*g\s*e.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\d+\s*\|\s*P\s*a\s*g\s*e\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'Page\s+\d+\s+of\s+\d+', '', text, flags=re.IGNORECASE)
    return text.strip()


def parse_pdf(pdf_path: str, source_url: str = '') -> list[dict]:
    text = extract_text(pdf_path)
    date = _extract_date_from_header(text)
    minister, ministry = _extract_minister_and_ministry(text)

    if not minister and not ministry:
        return []

    org_code = _extract_org_code(text)
    budget = _parse_budget_value(text)
    performance = _extract_performance_metrics(text)

    extracted_data: dict[str, Any] = {}
    if org_code:
        extracted_data['org_code'] = org_code
    if budget:
        extracted_data['budget'] = budget
    if performance:
        extracted_data['performance'] = performance

    payload: dict[str, Any] = {
        'contribution_type': 'committee_of_supply',
        'raw_match_name': minister,
        'raw_constituency': '',
        'ministry_addressed': ministry,
        'subject_text': _clean_speech(text)[:8000],
        'date': date or '',
        'source_url': source_url,
        'extracted_data': extracted_data or None,
    }

    return [payload]


def run_for_document(file_path: str, source_url: str = '') -> list[dict]:
    return parse_pdf(file_path, source_url)
