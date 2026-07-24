"""Multi-tier regex parser for Botswana Daily Hansard transcript PDFs.

Deterministic extraction pipeline:
1. Metadata: Hansard No., session date, meeting description, sitting time.
2. Agenda: Major section segmentation (ORAL ANSWER, BUSINESS MOTION, etc.).
3. Speaker Turns: Detects speaker changes and classifies turn types.
4. Procedural Events: Extracts parenthetical annotations (Applause, Laughter).
"""

import json
import re
from pathlib import Path
from typing import Any

import pdfplumber

from backend.narrative.evidence_classifier import classify_evidence
from backend.parse.base import _extract_date_from_header
from backend.parse.language_tagger import detect_language
from backend.parse.nlp_extract import extract_entities, strip_honorifics

STRADDLE_FRACTION_THRESHOLD = 0.05
# Running headers/footers (page-top date line, page-bottom folio number) sit
# in a thin band and can legitimately span the full page width; excluding
# that band from the straddle count keeps a few full-width header/footer
# words from skewing the ratio on pages with otherwise-sparse body content.
HEADER_FOOTER_MARGIN_FRACTION = 0.08


def _extract_hansard_text(pdf_path: str) -> str:
    """Extract Hansard PDF text in correct reading order.

    Daily Hansard body pages are two-column; pdfplumber's default
    page.extract_text() reads left-to-right across the full page width,
    interleaving both columns line-by-line into garbled text. Detects
    two-column pages (few/no body words straddle the page midline) and
    crops+extracts each column separately in reading order; single-column
    pages (title page, some front-matter) are left untouched.
    """
    pages: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            words = page.extract_words()
            mid = page.width / 2
            margin = page.height * HEADER_FOOTER_MARGIN_FRACTION
            body_words = [w for w in words if margin < w['top'] < page.height - margin]

            straddling = sum(1 for w in body_words if w['x0'] < mid < w['x1'])
            is_two_column = (
                bool(body_words) and (straddling / len(body_words)) < STRADDLE_FRACTION_THRESHOLD
            )

            if is_two_column:
                left = page.crop((0, 0, mid, page.height)).extract_text() or ''
                right = page.crop((mid, 0, page.width, page.height)).extract_text() or ''
                text = '\n'.join(t for t in (left, right) if t)
            else:
                text = page.extract_text() or ''

            if text:
                pages.append(text)

    return '\n'.join(pages)

HANSARD_NO_RE = re.compile(r'HANSARD\s+NO:\s*(\d+)', re.IGNORECASE)

DATE_LINE_RE = re.compile(
    r'(MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY)\s+(\d{1,2}(?:ST|ND|RD|TH)?)\s+'
    r'(JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|'
    r'OCTOBER|NOVEMBER|DECEMBER),?\s*(\d{4})',
    re.IGNORECASE,
)

ACT_RE = re.compile(r'ACT\s+NO\.?\s*\d{1,2}\s+OF\s+\d{4}', re.IGNORECASE)

ASSEMBLY_TIME_RE = re.compile(
    r'THE\s+ASSEMBLY\s+met\s+at\s*(\d{1,2}:\d{2}\s*[a-z\.]*)',
    re.IGNORECASE,
)

MEETING_DESC_RE = re.compile(
    r'(\w+)\s+(Meeting|Session)\s+of\s+the\s+(\w+)\s+(Session|Sitting)\s+'
    r'of\s+the\s+(\d+(?:ST|ND|RD|TH)?)\s+Parliament',
    re.IGNORECASE,
)

AGENDA_HEADERS: list[tuple[re.Pattern, str]] = [
    (re.compile(r'QUESTIONS?\s+FOR\s+ORAL\s+ANSWER', re.IGNORECASE), 'Questions for Oral Answer'),
    (re.compile(r'BUSINESS\s+MOTION', re.IGNORECASE), 'Business Motion'),
    (re.compile(r'SPEAKER[\'\u2019]S\s+ANNOUNCEMENTS?', re.IGNORECASE), "Speaker's Announcements"),
    (re.compile(r'STATEMENTS?\s+BY\s+(?:THE\s+)?MINISTERS?', re.IGNORECASE), 'Ministerial Statements'),
    (re.compile(r'COMMITTEE\s+OF\s+SUPPLY', re.IGNORECASE), 'Committee of Supply'),
    (re.compile(r'PRESENTATION\s+OF\s+(?:A\s+)?PETITIONS?', re.IGNORECASE), 'Petitions'),
    (re.compile(r'BILLS?\s*[–\u2013\u2014-]\s*(?:FIRST|SECOND|THIRD)\s+READING', re.IGNORECASE), 'Bill Readings'),
]

# Real speaker headers always start with one of these title words right at a
# line boundary (verified against Hansard No. 221 - the PLAN.md benchmark
# document, plus known Botswana parliamentary title variants). Anchoring on a
# known title prefix, rather than "any run of uppercase text ending in a
# colon", is what keeps this from matching agenda/question-title text that
# happens to precede a real speaker line (e.g. "QUESTIONS FOR ORAL ANSWER\n
# TOURISTIC DEVELOPMENTS...\nMR KAPINGA (...):") or from stopping mid-
# portfolio-name at a line wrap (e.g. "MINISTER FOR STATE PRESIDENT, DEFENCE\n
# AND SECURITY (MR MOHWASA):" previously matched as just "AND SECURITY"
# because a bare uppercase-run regex can restart at any line).
#
# Personal honorifics prefix an actual person's own name/surname (e.g. "MR
# K. K. KAPINGA" - the name itself, not a parenthetical, is the person).
PERSONAL_HONORIFICS = (
    'MR', 'MRS', 'MS', 'DR', 'PROF',
    'HON', 'HONOURABLE',
    'BRIG', 'BRIGADIER', 'COL', 'COLONEL', 'MAJOR GENERAL', 'LIEUTENANT GENERAL',
    'MADAM',
)

# Institutional role titles: the captured "name" is a chamber role, not a
# person - the real speaker's identity is in the parenthetical detail
# instead (e.g. speaker_name='MINISTER OF ENVIRONMENT AND TOURISM',
# detail='MR MMOLOTSI'). Single source of truth: backend.parse.run imports
# this tuple directly (rather than maintaining a second list) so the
# speaker-header regex and the run.py identity-resolution role check cannot
# drift out of sync with each other - this is exactly the class of bug an
# adversarial review caught for 'ATTORNEY GENERAL'/'ASSISTANT MINISTER'
# turns silently failing to resolve because the two lists had diverged.
INSTITUTIONAL_ROLE_TITLES = (
    'MINISTER', 'ASSISTANT MINISTER',
    'SPEAKER', 'DEPUTY SPEAKER',
    'PRESIDENT', 'VICE PRESIDENT',
    'ATTORNEY GENERAL',
)

CHAMBER_ROLE_TITLES = PERSONAL_HONORIFICS + INSTITUTIONAL_ROLE_TITLES

_ROLE_TITLE_ALTERNATION = '|'.join(
    re.escape(title).replace(r'\ ', r'\s+') for title in CHAMBER_ROLE_TITLES
)
SPEAKER_TITLE_PREFIX = (
    rf'(?:{_ROLE_TITLE_ALTERNATION})(?:\s+(?:FOR|OF))?'
)

SPEAKER_HEADER_RE = re.compile(
    rf"^(\d+\.\s*)?({SPEAKER_TITLE_PREFIX}[A-Z0-9\s,.\-']{{0,90}}?)"
    r'\s*(?:\(([^)]{1,60})\))?\s*:\s*',
    re.MULTILINE,
)

SPEECH_TYPE_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r'^(?:Main|Principal|Primary)\s*(?:Question|Answer)', re.IGNORECASE), 'main_question'),
    (re.compile(r'^(?:Further\s+)?Supplementary\.?\s*$', re.MULTILINE), 'supplementary_question'),
    (re.compile(r'^On\s+a\s+point\s+of\s+(?:order|procedure)\.?\s*$', re.IGNORECASE | re.MULTILINE), 'point_of_procedure'),
    (re.compile(r'^(?:Later\s+Date|Deferred)\.?\s*$', re.IGNORECASE | re.MULTILINE), 'question_deferral'),
]

PROCEDURAL_NOTES_RE = re.compile(r'\.\.\.\(([^)]*)\)\.\.\.', re.DOTALL)


def _extract_metadata(text: str) -> dict[str, Any]:
    meta: dict[str, Any] = {}
    hn_match = HANSARD_NO_RE.search(text)
    if hn_match:
        meta['hansard_no'] = int(hn_match.group(1))

    date_str = _extract_date_from_header(text)
    if date_str:
        meta['session_date'] = date_str

    amt_match = ASSEMBLY_TIME_RE.search(text)
    if amt_match:
        meta['sitting_time'] = amt_match.group(1).strip()

    meeting_match = MEETING_DESC_RE.search(text)
    if meeting_match:
        meta['meeting_description'] = meeting_match.group(0).strip()

    return meta


def _segment_agenda(text: str) -> list[tuple[str, str, str]]:
    sections: list[tuple[str, str, str]] = []
    lines = text.split('\n')
    current_cat = ''
    current_header = ''
    current_lines: list[str] = []

    for line in lines:
        ls = line.strip()
        matched = None
        for pattern, cat in AGENDA_HEADERS:
            if pattern.search(ls):
                matched = cat
                break

        if matched is not None:
            if current_cat and current_lines:
                sections.append((current_cat, current_header, '\n'.join(current_lines)))
            current_cat = matched
            current_header = ls
            current_lines = []
        elif current_cat:
            current_lines.append(ls)

    if current_cat and current_lines:
        sections.append((current_cat, current_header, '\n'.join(current_lines)))

    return sections


def _extract_utterances(section_text: str, agenda_id: int) -> list[dict[str, Any]]:
    utterances: list[dict[str, Any]] = []
    turns = _split_turns(section_text)

    seq = 0
    for name, detail, speech_text in turns:
        seq += 1
        speaker_name, constituency = _parse_speaker(name, detail)
        speaker_raw = f'{name} ({detail})' if detail else name
        speech_type = _classify_turn_type(speaker_name, speech_text)
        language = detect_language(speech_text)
        procedural = _extract_procedural(speech_text)
        cleaned = strip_honorifics(speech_text)
        entities = extract_entities(speech_text)
        evidence = classify_evidence(speech_text)

        utterances.append({
            'agenda_id': agenda_id,
            'speaker_raw_title': speaker_raw.strip(),
            'speaker_name': speaker_name,
            'speaker_detail': constituency,
            'speech_type': speech_type,
            'speech_text': speech_text.strip(),
            'cleaned_text': cleaned,
            'language': language,
            'procedural_notes': procedural if procedural else None,
            'extracted_entities': json.dumps(entities) if any(entities.values()) else None,
            'evidence_type': evidence['primary_type'],
            'evidence_confidence': evidence['confidence'],
            'word_count': len(speech_text.split()),
            'sequence_order': seq,
        })

    return utterances


def _split_turns(text: str) -> list[tuple[str, str, str]]:
    """Split text into (speaker_name, constituency_or_portfolio, speech_body) turns."""
    matches = list(SPEAKER_HEADER_RE.finditer(text))
    turns: list[tuple[str, str, str]] = []

    for i, m in enumerate(matches):
        name = re.sub(r'\s+', ' ', m.group(2)).strip()
        detail = re.sub(r'\s+', ' ', m.group(3) or '').strip()
        next_start = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[m.end():next_start].strip()
        if body:
            turns.append((name, detail, body))

    return turns


def _parse_speaker(name: str, detail: str) -> tuple[str, str]:
    return name.strip(), detail.strip()


def _classify_turn_type(speaker_name: str, text: str) -> str:
    text_clean = text.strip()
    for pattern, label in SPEECH_TYPE_PATTERNS:
        if pattern.match(text_clean):
            return label

    name_upper = speaker_name.strip().upper()
    if name_upper.startswith(('MINISTER', 'ASSISTANT MINISTER')):
        return 'minister_answer'
    if re.match(r'^(?:Supplementary|Further\s+Supplementary)', text_clean, re.IGNORECASE):
        return 'supplementary_question'

    return 'main_question'


def _extract_procedural(text: str) -> str | None:
    matches = PROCEDURAL_NOTES_RE.findall(text)
    if matches:
        return '; '.join(m.strip() for m in matches)
    return None


def parse_pdf(pdf_path: str, source_url: str = '') -> list[dict]:
    path = Path(pdf_path).resolve()
    if not str(path).startswith(str(Path.cwd())):
        raise ValueError(f'Hansard PDF path must be within project directory: {pdf_path}')
    if not path.is_file():
        raise FileNotFoundError(f'Hansard PDF not found: {pdf_path}')

    text = _extract_hansard_text(str(path))
    meta = _extract_metadata(text)
    agenda_sections = _segment_agenda(text)

    results: list[dict] = []

    if not agenda_sections:
        utterances = _extract_utterances(text, 1)
        for u in utterances:
            u['_meta'] = meta
            u['_agenda_category'] = 'General Proceedings'
            u['_agenda_title'] = 'General Proceedings'
            u['_agenda_sequence'] = 1
            u['source_url'] = source_url
        return utterances

    for ag_idx, (cat, title, section_text) in enumerate(agenda_sections, start=1):
        utterances = _extract_utterances(section_text, ag_idx)
        for u in utterances:
            u['_meta'] = meta
            u['_agenda_category'] = cat
            u['_agenda_title'] = title
            u['_agenda_sequence'] = ag_idx
            u['source_url'] = source_url
        results.extend(utterances)

    return results


def run_for_document(file_path: str, source_url: str = '') -> list[dict]:
    return parse_pdf(file_path, source_url)
