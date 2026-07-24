"""MP Parliamentary Persona Classifier — deterministic decision tree from contribution ratios."""

from collections import Counter


PERSONA_RULES = {
    'THE WATCHDOG': {
        'description': 'Focuses on executive oversight & local grievances via oral questions.',
        'condition': lambda ratios, total: ratios.get('oral_question', 0) >= 70 and total >= 3,
    },
    'THE INITIATOR': {
        'description': 'Focuses on policy reform & new legislative funds via motions.',
        'condition': lambda ratios, total: ratios.get('motion', 0) >= 25 and total >= 3,
    },
    'THE LEGISLATOR': {
        'description': 'Focuses on refining statutory details via bill amendments.',
        'condition': lambda ratios, total: (
            ratios.get('bill_presentation', 0) + ratios.get('bill_1st', 0)
            + ratios.get('bill_2nd', 0) + ratios.get('bill_3rd', 0)
        ) >= 15 and total >= 3,
    },
    'THE SCRUTINEER': {
        'description': 'Focuses on budget oversight via committee of supply interventions.',
        'condition': lambda ratios, total: ratios.get('committee_of_supply', 0) >= 20 and total >= 3,
    },
    'EMERGING VOICE': {
        'description': 'New or low-activity MP still developing a parliamentary footprint.',
        'condition': lambda ratios, total: total < 3,
    },
    'THE GENERALIST': {
        'description': 'Balanced portfolio spanning questions, motions, and legislative work.',
        'condition': lambda ratios, total: True,
    },
}


PERSONA_ORDER = ['THE WATCHDOG', 'THE INITIATOR', 'THE LEGISLATOR', 'THE SCRUTINEER', 'EMERGING VOICE', 'THE GENERALIST']


def classify_persona(contribution_types: list[str]) -> dict[str, str]:
    """Classify an MP's parliamentary persona from their contribution type list.

    Returns dict with 'persona' and 'description' keys.
    """
    total = len(contribution_types)
    if total == 0:
        return {'persona': 'EMERGING VOICE', 'description': 'No recorded contributions yet.'}

    counts = Counter(contribution_types)
    ratios = {k: round(v / total * 100, 1) for k, v in counts.items()}

    for persona in PERSONA_ORDER:
        rule = PERSONA_RULES[persona]
        if rule['condition'](ratios, total):
            return {'persona': persona, 'description': rule['description']}

    return {'persona': 'THE GENERALIST', 'description': PERSONA_RULES['THE GENERALIST']['description']}
