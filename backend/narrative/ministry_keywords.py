"""Deterministic keyword-matching ministry inference rules."""

# DEPRECATED: The infer_ministry() function below uses a hardcoded dictionary.
# Use backend.narrative.ministerial_inference.dynamic_infer_ministry() instead,
# which delegates to DBTopicClassifier for DB-backed classification.
#
# The MINISTRY_KEYWORDS dictionary below is retained as a seed reference.
# To seed the DB from this dict, run: seed_keywords_from_static()

MINISTRY_KEYWORDS: dict[str, list[str]] = {
    'Environment and Tourism': [
        'eco-tourism', 'wildlife', 'hunting', 'concessions', 'mophane',
        'parks', 'tourism levy', 'tourism', 'eco tourism',
        'national park', 'game reserve', 'safari', 'biodiversity',
        'conservation', 'elephant', 'wild life',
    ],
    'Water and Human Settlement': [
        'housing', 'bonno', 'waterlogging', 'wetlands', 'oodi',
        'water supply', 'water', 'drought', 'settlement',
        'human settlement', 'sanitation', 'dam', 'borehole',
    ],
    'Minerals and Energy': [
        'fuel', 'brent crude', 'petroleum', 'debswana', 'meropa resources',
        'bpc', 'electricity', 'energy', 'minerals', 'mining',
        'coal', 'solar', 'power', 'oil', 'gas', 'diamond',
    ],
    'Finance': [
        'vat', 'pension', 'two pot', 'revenue', 'burs', 'tax debt',
        'budget', 'tax', 'fiscal', 'treasury', 'pula',
        'financial', 'appropriation', 'expenditure', 'fund',
    ],
    'Health': [
        'hospital', 'clinic', 'medicine', 'pharmaceutical', 'nhs',
        'disease', 'patient', 'nurse', 'doctor', 'healthcare',
        'covid', 'vaccine', 'epidemic', 'health',
    ],
    'Lands and Agriculture': [
        'farm', 'farming', 'crop', 'livestock', 'agriculture',
        'land', 'arable', 'ranch', 'cattle', 'plough',
        'harvest', 'irrigation', 'pastoral', 'temothuo',
    ],
    'Local Government and Traditional Affairs': [
        'council', 'municipal', 'district', 'traditional', 'kgosi',
        'ward', 'village development', 'community',
    ],
    'Transport and Infrastructure': [
        'road', 'bridge', 'transport', 'railway', 'airport',
        'highway', 'infrastructure', 'bypass', 'construction',
    ],
    'Child Welfare and Basic Education': [
        'school', 'education', 'student', 'teacher', 'curriculum',
        'classroom', 'bursary', 'scholarship', 'literacy',
        'primary school', 'secondary school',
    ],
    'Trade and Entrepreneurship': [
        'trade', 'business', 'sme', 'enterprise', 'commerce',
        'entrepreneur', 'industry', 'retail', 'export',
    ],
    'Labour and Home Affairs': [
        'labour', 'employment', 'worker', 'union', 'wage',
        'immigration', 'passport', 'visa', 'id card', 'omang',
    ],
    'Sports and Arts': [
        'sport', 'art', 'culture', 'athlete', 'stadium',
        'heritage', 'museum', 'gallery',
    ],
    'Justice and Correctional Services': [
        'court', 'prison', 'correctional', 'justice', 'judge',
        'magistrate', 'legal', 'law', 'attorney', 'police',
        'prosecution', 'trial',
    ],
    'Communications and Innovation': [
        'internet', 'digital', 'technology', 'innovation', 'telecom',
        'broadband', 'communications', 'data', 'cyber', 'ict',
        'botswana television', 'radio', 'broadcasting',
    ],
    'Higher Education': [
        'university', 'college', 'tertiary', 'degree', 'graduate',
        'academic', 'research', 'campus',
    ],
    'Youth and Gender Affairs': [
        'youth', 'gender', 'women', 'empowerment', 'girl child',
    ],
    'International Relations': [
        'foreign', 'diplomatic', 'embassy', 'international', 'treaty',
        'sadc', 'au', 'un', 'african union',
    ],
    'State President, Defence and Security': [
        'president', 'defence', 'security', 'military', 'army',
        'bdf', 'defense', 'national security', 'intelligence',
        'vice president', 'state president',
    ],
}


def infer_ministry(subject_text: str, current_ministry: str | None = None) -> str:
    """Infer a target ministry from subject text using keyword matching.

    If current_ministry is provided and non-empty (not 'Not specified'),
    it is returned unchanged. Otherwise, text is scanned against
    MINISTRY_KEYWORDS and the first matching ministry is returned.

    Returns 'General Parliamentary Business' when no keywords match.
    """
    if current_ministry and current_ministry.strip() and current_ministry.strip().lower() != 'not specified':
        return current_ministry.strip()

    if not subject_text:
        return 'General Parliamentary Business'

    text_lower = subject_text.lower()

    for ministry, keywords in MINISTRY_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                return ministry

    return 'General Parliamentary Business'


def seed_keywords_from_static() -> int:
    """Seed the ministry_keywords DB table from this module's static dictionary.

    Inserts all keywords from MINISTRY_KEYWORDS into the DB, creating
    ministry entries as needed. Returns total keyword associations inserted.
    """
    import sqlite3
    from backend.db.connection import get_connection

    conn = get_connection()
    try:
        cursor = conn.cursor()
        total = 0
        for ministry_name, keywords in MINISTRY_KEYWORDS.items():
            # Ensure ministry exists
            row = cursor.execute(
                "SELECT id FROM ministries WHERE canonical_name = ?",
                (ministry_name,),
            ).fetchone()
            if not row:
                cursor.execute(
                    """INSERT INTO ministries
                       (canonical_name, source_type, first_seen_date, last_seen_date)
                       VALUES (?, 'static_seed', date('now'), date('now'))""",
                    (ministry_name,),
                )
                ministry_id = cursor.lastrowid
            else:
                ministry_id = row['id']

            # Insert keywords
            for kw in keywords:
                cursor.execute(
                    """INSERT INTO ministry_keywords (ministry_id, keyword, weight, source_type)
                       VALUES (?, ?, 1.0, 'static_seed')
                       ON CONFLICT(ministry_id, keyword) DO NOTHING""",
                    (ministry_id, kw),
                )
                total += cursor.rowcount

        conn.commit()
        return total
    finally:
        conn.close()
