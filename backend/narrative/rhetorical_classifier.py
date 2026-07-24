"""Pure DB-driven rhetorical intent classifier — zero hardcoded lists or dicts."""

import re
import sqlite3
from typing import Any

from backend.db.connection import get_connection

SCORE_CATEGORIES = ('COMPLAINT', 'SOLUTION', 'INQUIRY', 'ENDORSEMENT', 'PROCEDURAL')


class DBIntentClassifier:
    """Evaluates speech intent via dynamic SQL queries against rhetorical_patterns.

    Constructiveness Ratio = solution_score / (solution_score + complaint_score) * 100.
    Higher ratio = more constructive, proposal-oriented speech.
    """

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def classify(self, text: str) -> dict[str, Any]:
        clean = text.lower().strip()
        cursor = self._conn.cursor()

        cursor.execute(
            """SELECT intent_category, pattern_regex, weight
               FROM rhetorical_patterns WHERE weight > 0.3""",
        )
        patterns = cursor.fetchall()

        scores = dict.fromkeys(SCORE_CATEGORIES, 0.0)
        matched = 0

        for category, regex_pat, weight in patterns:
            if not regex_pat:
                continue
            try:
                matches = re.findall(regex_pat, clean, flags=re.IGNORECASE)
                if matches:
                    scores[category] += len(matches) * weight
                    matched += 1
            except re.error:
                continue

        best_category = max(scores, key=scores.get)
        best_score = scores[best_category]
        primary = best_category if best_score > 0.0 else 'INQUIRY'

        sol_complaint = scores['SOLUTION'] + scores['COMPLAINT']
        constructiveness = round(
            (scores['SOLUTION'] / sol_complaint * 100) if sol_complaint > 0 else 50.0,
            1,
        )

        return {
            'primary_intent': primary,
            'constructiveness_ratio': constructiveness,
            'complaint_score': round(scores['COMPLAINT'], 2),
            'solution_score': round(scores['SOLUTION'], 2),
            'inquiry_score': round(scores['INQUIRY'], 2),
            'endorsement_score': round(scores['ENDORSEMENT'], 2),
            'procedural_score': round(scores['PROCEDURAL'], 2),
            'matched_pattern_count': matched,
        }

    def classify_and_store(self, contribution_id: int, text: str) -> dict[str, Any] | None:
        """Classify a contribution and upsert the result into contribution_intents."""
        result = self.classify(text)
        cursor = self._conn.cursor()
        try:
            cursor.execute(
                """INSERT INTO contribution_intents
                   (contribution_id, primary_intent, constructiveness_ratio,
                    complaint_score, solution_score, inquiry_score, endorsement_score,
                    procedural_score, matched_pattern_count)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(contribution_id) DO UPDATE SET
                       primary_intent = excluded.primary_intent,
                       constructiveness_ratio = excluded.constructiveness_ratio,
                       complaint_score = excluded.complaint_score,
                       solution_score = excluded.solution_score,
                       inquiry_score = excluded.inquiry_score,
                       endorsement_score = excluded.endorsement_score,
                       procedural_score = excluded.procedural_score,
                       matched_pattern_count = excluded.matched_pattern_count""",
                (
                    contribution_id,
                    result['primary_intent'],
                    result['constructiveness_ratio'],
                    result['complaint_score'],
                    result['solution_score'],
                    result['inquiry_score'],
                    result['endorsement_score'],
                    result.get('procedural_score', 0.0),
                    result['matched_pattern_count'],
                ),
            )
            self._conn.commit()
            return result
        except sqlite3.IntegrityError:
            return None


def seed_initial_patterns(conn: sqlite3.Connection) -> int:
    """Seed the rhetorical_patterns table with parliamentary debate patterns.

    These cover Standing Orders 36–58 debate formulas in English and Setswana.
    Returns the count of patterns inserted.
    """
    seed = [
        # COMPLAINT — English
        ('COMPLAINT', r'\bfailure\s+to\b', 1.0, 'seed'),
        ('COMPLAINT', r'\b(?:shortage|dearth|lack)\s+of\b', 1.0, 'seed'),
        ('COMPLAINT', r'\b(?:delay|stalled|abandoned)\b', 1.0, 'seed'),
        ('COMPLAINT', r'\b(?:dilapidated|crumbling|broken)\b', 0.8, 'seed'),
        ('COMPLAINT', r'\b(?:corruption|mismanagement|maladministration)\b', 1.0, 'seed'),
        ('COMPLAINT', r'\b(?:neglect|failure|omission)\s+(?:to|of)\b', 1.0, 'seed'),
        ('COMPLAINT', r'\b(?:does not|doesn[\u2019]t|cannot|can[\u2019]t)\b', 0.5, 'seed'),
        ('COMPLAINT', r'\bsovereign\s+credit\s+rating\b', 1.0, 'seed'),
        # COMPLAINT — Setswana
        ('COMPLAINT', r'\btlhaelo\b', 1.0, 'seed'),
        ('COMPLAINT', r'\bgo\s+palelwa\b', 0.8, 'seed'),
        ('COMPLAINT', r'\btlhokego\b', 0.8, 'seed'),
        # SOLUTION — English
        ('SOLUTION', r'\b(?:urge|urges|urging)\s+(?:the\s+)?(?:government|ministry|minister)\b', 1.0, 'seed'),
        ('SOLUTION', r'\b(?:propose|proposes|proposing|moved?\s+that)\b', 1.0, 'seed'),
        ('SOLUTION', r'\b(?:recommend|recommends|advise|advises)\b', 1.0, 'seed'),
        ('SOLUTION', r'\b(?:establish|create|launch|introduce|implement)\s+(?:a\s+)?(?:fund|program|initiative|scheme)\b', 1.0, 'seed'),
        ('SOLUTION', r'\b(?:ring.?fence|allocate|earmark)\b', 0.8, 'seed'),
        ('SOLUTION', r'\b(?:statutory|automatic)\s+(?:fund|funding|allocation)\b', 0.8, 'seed'),
        ('SOLUTION', r'\b(?:will\s+commit|committed\s+to|undertakes\s+to)\b', 0.6, 'seed'),
        ('SOLUTION', r'\b(?:review|reform|overhaul|streamline)\b', 0.7, 'seed'),
        # SOLUTION — Setswana
        ('SOLUTION', r'\b(?:tlhoma|tsamaisa|thusa)\b', 0.8, 'seed'),
        ('SOLUTION', r'\bleboga\b', 0.5, 'seed'),
        # INQUIRY
        ('INQUIRY', r'\b(?:to\s+ask|to\s+state|to\s+update|to\s+apprise|to\s+explain|to\s+clarify|to\s+indicate|to\s+inform)\b', 1.0, 'seed'),
        ('INQUIRY', r'\b(?:if|whether)\s+(?:he|she|the|it)\b', 0.5, 'seed'),
        ('INQUIRY', r'\bwhat\s+(?:plans|steps|measures|action)\b', 1.0, 'seed'),
        ('INQUIRY', r'\bhow\s+(?:many|much|far|long)\b', 0.8, 'seed'),
        ('INQUIRY', r'\bwhen\s+(?:will|does|did)\b', 0.5, 'seed'),
        # ENDORSEMENT
        ('ENDORSEMENT', r'\b(?:commend|commends|applaud|praise|thank)\b', 0.8, 'seed'),
        ('ENDORSEMENT', r'\bwell\s+(?:done|received|noted)\b', 0.5, 'seed'),
        # PROCEDURAL
        ('PROCEDURAL', r'\bpoint\s+of\s+(?:order|procedure|information)\b', 1.0, 'seed'),
        ('PROCEDURAL', r'\b(?:motion\s+for\s+)?adjournment\b', 1.0, 'seed'),
    ]

    cursor = conn.cursor()
    inserted = 0
    for category, pattern, weight, source in seed:
        try:
            cursor.execute(
                """INSERT INTO rhetorical_patterns
                   (intent_category, pattern_regex, weight, source_type)
                   VALUES (?, ?, ?, ?)""",
                (category, pattern, weight, source),
            )
            inserted += 1
        except sqlite3.IntegrityError:
            pass

    conn.commit()
    return inserted
