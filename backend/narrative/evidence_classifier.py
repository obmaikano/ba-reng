"""Evidence classification engine — categorizes Hansard speech turns into 4 evidence types.

1. EMPIRICAL — numeric data, percentages, currency figures, research citations
2. STATUTORY — legal references, section numbers, act citations, standing orders
3. ANECDOTAL — personal stories, constituent reports, local observations
4. NORMATIVE — value judgments, ideological statements, party rhetoric
"""

import re
from collections import Counter
from typing import Any


EMPIRICAL_PATTERNS: list[re.Pattern] = [
    re.compile(r'\b\d+(?:\.\d+)?\s*%', re.IGNORECASE),
    re.compile(r'\b(?:P\d[\d,]*|Pula)\s*\d*', re.IGNORECASE),
    re.compile(r'\b\d+(?:,\d{3})*(?:\.\d+)?\s*(?:million|billion|thousand)\b', re.IGNORECASE),
    re.compile(r'\b(?:increased\s+by|decreased\s+by|fell\s+by|rose\s+by|dropped\s+by)\s+\d+', re.IGNORECASE),
    re.compile(r'\b(?:Q[1-4]|quarter|fiscal\s+year|FY)\s*\d{2,4}', re.IGNORECASE),
    re.compile(r'\b(?:survey|study|research|data\s+shows|statistics|according\s+to\s+(?:the\s+)?(?:bank|imf|world\s+bank|stats\s+bots))', re.IGNORECASE),
    re.compile(r'\b(?:rate\s+of|index\s+of|per\s+capita|annual|monthly|quarterly)\b', re.IGNORECASE),
]

STATUTORY_PATTERNS: list[re.Pattern] = [
    re.compile(r'\b(?:section|subsection|clause|paragraph)\s+\d+', re.IGNORECASE),
    re.compile(r'\b(?:Act\s+No\.?|Bill\s+No\.?|Statutory\s+Instrument)\s*\d+', re.IGNORECASE),
    re.compile(r'\b(?:standing\s+order|constitution|constitutional|provision)\s+\d+', re.IGNORECASE),
    re.compile(r'\b(?:pursuant\s+to|in\s+accordance\s+with|as\s+provided\s+(?:for\s+)?under)\b', re.IGNORECASE),
    re.compile(r'\b(?:Cap\.?\s*\d+|Chapter\s+\d+|Part\s+[IVX]+)\b', re.IGNORECASE),
    re.compile(r'\b(?:Amendment|amended|amending|repeal|repealed)\s+(?:Act|Bill|section|provision)\b', re.IGNORECASE),
    re.compile(r'\b(?:Regulations?\s+\d+|Rules?\s+\d+|Code\s+\d+)\b', re.IGNORECASE),
]

ANECDOTAL_PATTERNS: list[re.Pattern] = [
    re.compile(r'\b(?:my\s+constituen(?:cy|t)|my\s+district|my\s+village|in\s+my\s+area)\b', re.IGNORECASE),
    re.compile(r'\b(?:a\s+(?:farmer|business\s*owner|teacher|nurse|worker|resident|constituent|voter)\s+(?:in|from|told|said|reported))\b', re.IGNORECASE),
    re.compile(r'\b(?:came\s+to\s+my\s+office|visited\s+my\s+clinic|approached\s+me)\b', re.IGNORECASE),
    re.compile(r'\b(?:i\s+(?:met|spoke\s+to|visited|saw|witnessed)\s+(?:a|the|several|many))\b', re.IGNORECASE),
    re.compile(r'\b(?:for\s+example,?\s+(?:in|at|when))\b', re.IGNORECASE),
    re.compile(r'\b(?:let\s+me\s+(?:tell|share|give)\s+(?:you|this\s+house)\s+(?:a\s+story|an\s+example))\b', re.IGNORECASE),
]

NORMATIVE_PATTERNS: list[re.Pattern] = [
    re.compile(r'\b(?:should|must|ought\s+to|need\s+to|has\s+to|have\s+to)\b', re.IGNORECASE),
    re.compile(r'\b(?:unacceptable|disgrace|shame|outrage|scandal|incompetent)\b', re.IGNORECASE),
    re.compile(r'\b(?:moral|ethical|righteous|just|fair|unjust|unfair)\b', re.IGNORECASE),
    re.compile(r'\b(?:this\s+government|this\s+administration|the\s+opposition|the\s+ruling\s+party)\s+(?:has|is|must|should|fails)', re.IGNORECASE),
    re.compile(r'\b(?:we\s+believe|we\s+demand|we\s+call\s+(?:on|upon)|we\s+insist)\b', re.IGNORECASE),
    re.compile(r'\b(?:for\s+the\s+sake\s+of|in\s+the\s+interest\s+of|the\s+people\s+deserve|batswana\s+deserve)\b', re.IGNORECASE),
]


def classify_evidence(text: str) -> dict[str, Any]:
    """Classify speech turn into evidence type with confidence scores.

    Returns dict with primary_type and score breakdown across all 4 types.
    """
    scores = {
        'EMPIRICAL': sum(len(p.findall(text)) for p in EMPIRICAL_PATTERNS),
        'STATUTORY': sum(len(p.findall(text)) for p in STATUTORY_PATTERNS),
        'ANECDOTAL': sum(len(p.findall(text)) for p in ANECDOTAL_PATTERNS),
        'NORMATIVE': sum(len(p.findall(text)) for p in NORMATIVE_PATTERNS),
    }

    total_matches = sum(scores.values())
    if total_matches == 0:
        return {'primary_type': 'NORMATIVE', 'scores': scores, 'confidence': 0.0}

    best_type = max(scores, key=scores.__getitem__)
    confidence = round(scores[best_type] / total_matches * 100, 1)

    return {
        'primary_type': best_type,
        'scores': scores,
        'confidence': confidence,
    }


def compute_scorecard(
    utterances: list[dict],
    word_count: int,
    interventions: int,
    decorum_violations: int,
) -> dict[str, Any]:
    """Compute Speaker Scorecard across 5 weighted dimensions.

    Args:
        utterances: List of utterance dicts with evidence_type and speech_text.
        word_count: Total words spoken.
        interventions: Count of procedural interventions (points of order, etc.).
        decorum_violations: Count of Speaker calls to order or rulings against.

    Returns scorecard dict with per-dimension scores (0-100) and weighted total.
    """
    evidence_types = Counter(u.get('primary_type', 'NORMATIVE') for u in utterances)
    total = len(utterances) or 1

    substance_keywords = ['section', 'clause', 'amendment', 'bill', 'act',
                          'budget', 'allocation', 'provision', 'regulation', 'policy']
    substance_count = sum(
        1 for u in utterances
        if any(kw in (u.get('speech_text', '') or '').lower() for kw in substance_keywords)
    )
    substance_pct = round(substance_count / total * 100, 1)
    substance_score = min(100, round(substance_pct * 1.2))

    empirical_count = evidence_types.get('EMPIRICAL', 0)
    anecdotal_count = evidence_types.get('ANECDOTAL', 0)
    normative_count = evidence_types.get('NORMATIVE', 0)
    fact_weighted = empirical_count * 1.5 + anecdotal_count * 0.5
    noise_weighted = normative_count * 0.3
    evidence_ratio = fact_weighted / max(fact_weighted + noise_weighted, 1)
    evidence_score = min(100, round(evidence_ratio * 100))

    total_utterances = total
    unique_topics = len(set(
        (u.get('agenda_title', '') or '')[:80] for u in utterances if u.get('agenda_title')
    )) or 1
    topic_focus = min(1.0, unique_topics / max(total_utterances * 0.3, 1))
    relevance_score = min(100, round((1.0 - topic_focus) * 100 + 60))

    substantive_turns = substance_count + evidence_types.get('STATUTORY', 0) + empirical_count
    efficiency = substantive_turns / max(word_count / 50, 1)
    efficiency_score = min(100, round(efficiency * 100))

    decorum_score = 100 - min(100, decorum_violations * 15)

    weights = {'substance_depth': 0.30, 'evidence_density': 0.25, 'relevance_focus': 0.20,
               'intervention_efficiency': 0.15, 'decorum_compliance': 0.10}

    dimension_scores = {
        'substance_depth': substance_score,
        'evidence_density': evidence_score,
        'relevance_focus': relevance_score,
        'intervention_efficiency': efficiency_score,
        'decorum_compliance': decorum_score,
    }

    weighted_total = round(sum(
        dimension_scores[k] * weights[k] for k in weights
    ), 1)

    return {
        'overall_score': weighted_total,
        'dimensions': dimension_scores,
        'evidence_breakdown': dict(evidence_types),
        'total_utterances': total,
        'total_words': word_count,
        'interventions': interventions,
        'decorum_violations': decorum_violations,
    }
