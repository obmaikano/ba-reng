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

from backend.parse.base import DATE_PATTERN, _extract_date_from_header, extract_text
from backend.parse.language_tagger import detect_language
from backend.parse.nlp_extract import extract_entities, strip_honorifics
from backend.narrative.evidence_classifier import classify_evidence

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

SPEAKER_WITH_CONSTITUENCY = re.compile(
    r'^(\d+\.\s*)?([A-Z][A-Z\s\.\-]{2,}(?:MP\.)?)\s*\(([^)]+)\):\s*',
    re.MULTILINE,
)

SPEAKER_WITH_PORTFOLIO = re.compile(
    r'^([A-Z\s]{10,})\s*\(([A-Z\s\.]+)\):\s*',
    re.MULTILINE,
)

ABBREVIATED_SPEAKER = re.compile(
    r'^([A-Z][A-Z\s\.]{3,}):\s*',
    re.MULTILINE,
)

SPEECH_TYPE_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r'^(?:Main|Principal|Primary)\s*(?:Question|Answer)', re.IGNORECASE), 'main_question'),
    (re.compile(r'^(?:Further\s+)?Supplementary\.?\s*$', re.MULTILINE), 'supplementary_question'),
    (re.compile(r'^On\s+a\s+point\s+of\s+(?:order|procedure)\.?\s*$', re.IGNORECASE | re.MULTILINE), 'point_of_procedure'),
    (re.compile(r'^(?:Later\s+Date|Deferred)\.?\s*$', re.IGNORECASE | re.MULTILINE), 'question_deferral'),
]

PROCEDURAL_NOTES_RE = re.compile(r'\(\.\.\.(.*?)\.\.\.\)', re.DOTALL)


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
    for speaker_raw, speech_text in turns:
        seq += 1
        speaker_name, constituency = _parse_speaker(speaker_raw)
        speech_type = _classify_turn_type(speech_text)
        language = detect_language(speech_text)
        procedural = _extract_procedural(speech_text)
        cleaned = strip_honorifics(speech_text)
        entities = extract_entities(speech_text)
        evidence = classify_evidence(speech_text)

        utterances.append({
            'agenda_id': agenda_id,
            'speaker_raw_title': speaker_raw.strip(),
            'speaker_name': speaker_name,
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


def _split_turns(text: str) -> list[tuple[str, str]]:
    speaker_positions: list[tuple[int, int, str]] = []

    for m in SPEAKER_WITH_CONSTITUENCY.finditer(text):
        speaker_positions.append((m.start(), m.end(), m.group(2).strip()))

    for m in SPEAKER_WITH_PORTFOLIO.finditer(text):
        pos = (m.start(), m.end(), m.group(0).rstrip(':').strip())
        overlapping = any(p[0] <= m.start() < p[1] for p in speaker_positions)
        if not overlapping:
            speaker_positions.append(pos)

    if not speaker_positions:
        for m in ABBREVIATED_SPEAKER.finditer(text):
            speaker_positions.append((m.start(), m.end(), m.group(1).strip()))

    speaker_positions.sort(key=lambda x: x[0])
    turns: list[tuple[str, str]] = []

    for i, (start, end, speaker) in enumerate(speaker_positions):
        next_start = speaker_positions[i + 1][0] if i + 1 < len(speaker_positions) else len(text)
        body = text[end:next_start].strip()
        if body:
            turns.append((speaker, body))

    return turns


def _parse_speaker(raw: str) -> tuple[str, str]:
    raw = raw.strip()
    const_match = re.search(r'\(([^)]+)\)', raw)
    if const_match:
        const = const_match.group(1).strip()
        name = raw[:const_match.start()].strip()
        return name, const

    name = re.sub(r'^\d+\.\s*', '', raw).strip()
    if re.match(r'^[A-Z\s\.]{5,}$', name):
        return name, ''
    return raw, ''


def _classify_turn_type(text: str) -> str:
    text_clean = text.strip()
    for pattern, label in SPEECH_TYPE_PATTERNS:
        if pattern.match(text_clean):
            return label

    if re.match(r'^MINISTER\s+(?:OF|FOR)\b', text_clean, re.IGNORECASE):
        return 'minister_answer'
    if SPEAKER_WITH_PORTFOLIO.match(text_clean):
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

    text = extract_text(str(path))
    meta = _extract_metadata(text)
    agenda_sections = _segment_agenda(text)

    results: list[dict] = []

    if not agenda_sections:
        utterances = _extract_utterances(text, 0)
        for u in utterances:
            u['_meta'] = meta
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
