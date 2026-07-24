"""Parser for Botswana Parliament Committee of Supply speeches."""

import re

from backend.parse.base import (
    _extract_date_from_header,
    extract_text,
    normalise_ministry,
)


def _extract_minister_and_ministry(text: str) -> tuple[str, str]:
    lines = [l.strip() for l in text.split('\n')[:25] if l.strip()]

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

    # Ministry from MINISTRY OF header
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

    return [{
        'contribution_type': 'committee_of_supply',
        'raw_match_name': minister,
        'raw_constituency': '',
        'ministry_addressed': ministry,
        'subject_text': _clean_speech(text)[:8000],
        'date': date or '',
        'source_url': source_url,
    }]


def run_for_document(file_path: str, source_url: str = '') -> list[dict]:
    return parse_pdf(file_path, source_url)
