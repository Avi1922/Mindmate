"""Lightweight English, Hindi, and Hinglish detection."""

import re
from dataclasses import dataclass

from langdetect import DetectorFactory, LangDetectException, detect_langs

from app.models.analysis import SupportedLanguage

DetectorFactory.seed = 0

DEVANAGARI_PATTERN = re.compile(r"[\u0900-\u097F]")
LATIN_PATTERN = re.compile(r"[A-Za-z]")
TOKEN_PATTERN = re.compile(r"[A-Za-z']+")

ROMAN_HINDI_TOKENS = {
    "aaj",
    "abhi",
    "acha",
    "accha",
    "bahut",
    "bura",
    "din",
    "dukhi",
    "hai",
    "hain",
    "ho",
    "kharab",
    "khush",
    "kyun",
    "lag",
    "mera",
    "meri",
    "mujhe",
    "naam",
    "nahi",
    "raha",
    "rahi",
    "tha",
    "thi",
    "yaar",
    "zindagi",
}


@dataclass(frozen=True)
class LanguageDetection:
    language: SupportedLanguage
    confidence: float


class LanguageService:
    """Detect language locally so raw text is not sent to another service."""

    def detect(self, text: str) -> LanguageDetection:
        has_devanagari = DEVANAGARI_PATTERN.search(text) is not None
        has_latin = LATIN_PATTERN.search(text) is not None

        if has_devanagari:
            language: SupportedLanguage = "hinglish" if has_latin else "hi"
            return LanguageDetection(language=language, confidence=0.99)

        tokens = [token.lower() for token in TOKEN_PATTERN.findall(text)]
        roman_hindi_count = sum(token in ROMAN_HINDI_TOKENS for token in tokens)
        if roman_hindi_count >= 2:
            confidence = min(0.98, 0.72 + roman_hindi_count * 0.04)
            return LanguageDetection(language="hinglish", confidence=confidence)

        if len(text.strip()) < 3:
            return LanguageDetection(language="unknown", confidence=0.0)

        try:
            candidates = detect_langs(text)
        except LangDetectException:
            return LanguageDetection(language="unknown", confidence=0.0)

        if not candidates:
            return LanguageDetection(language="unknown", confidence=0.0)

        candidate = candidates[0]
        mapped: SupportedLanguage
        if candidate.lang == "en":
            mapped = "en"
        elif candidate.lang == "hi":
            mapped = "hi"
        else:
            mapped = "other"

        return LanguageDetection(
            language=mapped,
            confidence=round(float(candidate.prob), 4),
        )
