# api/app/validators.py
import re

MIN_WORDS = 300
_WORD_RE = re.compile(r"\b[\wÀ-ÿ'-]+\b", re.UNICODE)

def count_words(text: str) -> int:
    return len(_WORD_RE.findall(text))

def ensure_min_words(text: str, min_words: int = MIN_WORDS) -> str:
    if count_words(text) < min_words:
        raise ValueError(f"Texto com {count_words(text)} palavras; mínimo é {min_words}.")
    return text
