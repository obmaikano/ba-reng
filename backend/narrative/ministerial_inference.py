"""Dynamic ministry inference — delegates to DBTopicClassifier for all classification."""

import sqlite3

from backend.narrative.topic_classifier import DBTopicClassifier


def dynamic_infer_ministry(
    subject_text: str,
    current_ministry: str | None = None,
    conn: sqlite3.Connection | None = None,
) -> str:
    """Infer ministry from subject text using database-driven classifier.

    All classification is done by DBTopicClassifier which queries
    ministry_keywords and parliamentary_glossary tables. No static
    dictionary lookups in the inference path.

    Accepts an optional conn parameter to reuse existing connections.
    If omitted, creates its own connection.
    """
    classifier = DBTopicClassifier(conn)
    result, _confidence, _method = classifier.classify(subject_text, current_ministry)
    return result
