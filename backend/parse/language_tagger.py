"""Fast language detection for English / Setswana code-switching in Hansard transcripts."""

from lingua import Language, LanguageDetectorBuilder

_languages = [Language.ENGLISH, Language.TSWANA]
_detector = LanguageDetectorBuilder.from_languages(*_languages).build()


def detect_language(text: str) -> str:
    """Classify a speech turn as 'en' (English), 'tn' (Setswana), or 'mixed'.

    Code-switched turns where both English and Setswana confidence
    exceed 0.3 with less than 0.2 absolute difference are tagged 'mixed'.
    """
    if not text or len(text.strip()) < 10:
        return 'en'

    try:
        confidence_values = _detector.compute_language_confidence_values(text)
        scores = {val.language: val.value for val in confidence_values}

        en_score = scores.get(Language.ENGLISH, 0.0)
        tn_score = scores.get(Language.TSWANA, 0.0)

        if abs(en_score - tn_score) < 0.2 and en_score > 0.3 and tn_score > 0.3:
            return 'mixed'
        return 'tn' if tn_score > en_score else 'en'
    except Exception:
        return 'en'
