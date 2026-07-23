"""Participation Index — weighted proxy metric."""

CAVEAT = 'Based on recorded contributions only. Not attendance data.'
WEIGHTS: dict[str, float] = {
    'motion': 1.5,
    'committee_of_supply': 1.5,
    'oral_question': 1.0,
    'question': 1.0,
    'petition': 1.0,
    'tabling': 1.0,
}


def compute(contributions_by_type: list[dict]) -> dict:
    """Compute the weighted Participation Index and per-type breakdown for one MP."""
    total = 0.0
    breakdown = []
    for item in contributions_by_type:
        ctype = item['contribution_type']
        cnt = item['cnt']
        weight = WEIGHTS.get(ctype, 1.0)
        weighted = cnt * weight
        total += weighted
        breakdown.append({
            'contribution_type': ctype,
            'count': cnt,
            'weight': weight,
            'weighted_score': weighted,
        })
    return {
        'participation_index': round(total, 2),
        'breakdown': breakdown,
        'is_proxy': True,
        'caveat': CAVEAT,
    }
