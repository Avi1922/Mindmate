"""PII masking tests for explicitly supported patterns."""

from app.services.pii_service import PIIService


def test_masks_common_pii_without_returning_values_in_summary() -> None:
    text = (
        "My name is Rahul Sharma. Call 9876543210 or email rahul@example.com. "
        "I live at 42 MG Road."
    )

    result = PIIService().mask(text)

    assert "Rahul Sharma" not in result.anonymized_text
    assert "9876543210" not in result.anonymized_text
    assert "rahul@example.com" not in result.anonymized_text
    assert "42 MG Road" not in result.anonymized_text
    assert "[PERSON]" in result.anonymized_text
    assert "[PHONE]" in result.anonymized_text
    assert "[EMAIL]" in result.anonymized_text
    assert "[ADDRESS]" in result.anonymized_text
    assert result.entity_counts == {
        "EMAIL": 1,
        "PHONE": 1,
        "ADDRESS": 1,
        "PERSON": 1,
    }


def test_masks_hinglish_name_and_aadhaar() -> None:
    result = PIIService().mask(
        "Mera naam Priya Verma hai aur Aadhaar 1234 5678 9012 hai."
    )

    assert "Priya Verma" not in result.anonymized_text
    assert "1234 5678 9012" not in result.anonymized_text
    assert "[PERSON]" in result.anonymized_text
    assert "[AADHAAR]" in result.anonymized_text


def test_does_not_guess_unintroduced_names() -> None:
    text = "Rahul made me happy today, but I am still tired."

    result = PIIService().mask(text)

    assert result.anonymized_text == text
    assert result.entity_counts == {}
