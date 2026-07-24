"""Nearest-match entity resolver using Levenshtein + Jaccard token similarity.

Resolves raw speaker names from entity_review_queue against the canonical
MP roster. No LLM required — purely deterministic string matching.
"""

import re
from Levenshtein import ratio as levenshtein_ratio


GARBAGE_PATTERNS: list[re.Pattern] = [
    re.compile(r'SERVICES,?\s*MP\.?$', re.IGNORECASE),
    re.compile(r'CORRECTIONAL\s+SERVICES', re.IGNORECASE),
    re.compile(r'SECURITY,?\s*MP\.?$', re.IGNORECASE),
    re.compile(r'OF\s+JUSTICE', re.IGNORECASE),
    re.compile(r'Honourable\s+Members?', re.IGNORECASE),
    re.compile(r'Honourable\s+Minister', re.IGNORECASE),
    re.compile(r'Acting\s+Minister', re.IGNORECASE),
    re.compile(r'^Minister\s+of\s+', re.IGNORECASE),
]

HONORIFIC_CLEAN = re.compile(
    r'\b(HONOURABLE|HON|MINISTER|MP|DR|MR|MS|MRS|BRIGADIER|PROF)\b[\.\,]?\s*', re.IGNORECASE,
)
WHITESPACE = re.compile(r'\s+')


def clean_name(raw: str) -> str:
    name = HONORIFIC_CLEAN.sub('', raw)
    name = WHITESPACE.sub(' ', name).strip()
    return name


def is_garbage(raw: str) -> bool:
    for pat in GARBAGE_PATTERNS:
        if pat.search(raw):
            return True
    return False


def resolve_nearest(
    raw: str,
    mp_names: list[tuple[int, str]],
    threshold: float = 0.55,
) -> tuple[int | None, float]:
    """Find the nearest canonical MP name using token Jaccard + Levenshtein.

    Args:
        raw: Raw speaker name from Hansard or Notice Paper.
        mp_names: List of (mp_id, mp_name_upper) tuples.
        threshold: Minimum similarity score to auto-resolve.

    Returns:
        (mp_id, score) or (None, score) if below threshold.
    """
    clean = clean_name(raw).upper()
    if not clean:
        return None, 0.0

    best_score = 0.0
    best_id: int | None = None

    for mp_id, mp_name in mp_names:
        mp_tokens = set(mp_name.split())
        raw_tokens = set(clean.split())
        common = mp_tokens & raw_tokens

        if common:
            jaccard = len(common) / max(len(mp_tokens | raw_tokens), 1)
            lev = levenshtein_ratio(clean, mp_name)
            score = jaccard * 0.6 + lev * 0.4
            if score > best_score:
                best_score = score
                best_id = mp_id

    if best_score >= threshold and best_id is not None:
        return best_id, best_score
    return None, best_score
