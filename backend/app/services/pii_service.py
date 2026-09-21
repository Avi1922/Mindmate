"""Conservative local masking for obvious personally identifying information."""

import re
from dataclasses import dataclass
from typing import Match, Pattern


@dataclass(frozen=True)
class PIIMaskResult:
    anonymized_text: str
    entity_counts: dict[str, int]


class PIIService:
    """Mask common PII patterns locally before downstream model calls.

    This deliberately favors precision over aggressive masking. It is not a
    guarantee of anonymization and does not replace a privacy review.
    """

    _simple_patterns: tuple[tuple[str, Pattern[str], str], ...] = (
        (
            "EMAIL",
            re.compile(r"(?<![\w.+-])[\w.+-]+@[\w-]+(?:\.[\w-]+)+", re.IGNORECASE),
            "[EMAIL]",
        ),
        (
            "AADHAAR",
            re.compile(r"(?<!\d)\d{4}[ -]?\d{4}[ -]?\d{4}(?!\d)"),
            "[AADHAAR]",
        ),
        (
            "PHONE",
            re.compile(r"(?<!\w)(?:\+?91[ -]?)?(?:\d[ -]?){10}(?!\w)"),
            "[PHONE]",
        ),
        (
            "ADDRESS",
            re.compile(
                r"\b\d{1,5}\s+(?:[A-Za-z0-9.'-]+\s+){0,5}"
                r"(?:Road|Rd|Street|St|Lane|Ln|Avenue|Ave|Nagar|Colony|Sector)\b",
                re.IGNORECASE,
            ),
            "[ADDRESS]",
        ),
    )

    _english_name = re.compile(
        r"\b(?P<prefix>(?i:my name is|i am called|i'm called))\s+"
        r"(?P<name>[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})"
    )
    _roman_hindi_name = re.compile(
        r"\b(?P<prefix>(?i:mera naam|naam mera))\s+"
        r"(?P<name>[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})(?=\s+(?i:hai|hain)\b)"
    )
    _devanagari_name = re.compile(
        r"(?P<prefix>मेरा नाम)\s+(?P<name>[\u0900-\u097F]+(?:\s+[\u0900-\u097F]+){0,2})"
        r"(?=\s+(?:है|हैं)\b)"
    )

    def mask(self, text: str) -> PIIMaskResult:
        masked = text
        counts: dict[str, int] = {}

        for entity_type, pattern, replacement in self._simple_patterns:
            masked, count = pattern.subn(replacement, masked)
            if count:
                counts[entity_type] = counts.get(entity_type, 0) + count

        for pattern in (
            self._english_name,
            self._roman_hindi_name,
            self._devanagari_name,
        ):
            masked, count = pattern.subn(self._replace_named_person, masked)
            if count:
                counts["PERSON"] = counts.get("PERSON", 0) + count

        return PIIMaskResult(anonymized_text=masked, entity_counts=counts)

    @staticmethod
    def _replace_named_person(match: Match[str]) -> str:
        return f"{match.group('prefix')} [PERSON]"
