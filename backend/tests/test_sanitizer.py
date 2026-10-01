import pytest
from backend.app.pipeline.sanitizer import DeterministicSanitizer


def test_valid_input():
    result = DeterministicSanitizer.sanitize("Bhai sleeves bohot tight hai fitting kharab hai")
    assert result.is_valid is True
    assert result.rejection_reason is None
    assert "sleeves bohot tight" in result.sanitized_text


def test_empty_string():
    result = DeterministicSanitizer.sanitize("")
    assert result.is_valid is False
    assert "Empty" in result.rejection_reason


def test_too_short():
    result = DeterministicSanitizer.sanitize("ab")
    assert result.is_valid is False
    assert "too short" in result.rejection_reason


def test_punctuation_spam():
    result = DeterministicSanitizer.sanitize("...")
    assert result.is_valid is False
    assert "punctuation" in result.rejection_reason

    result2 = DeterministicSanitizer.sanitize("?!?!?!")
    assert result2.is_valid is False


def test_repetitive_characters():
    result = DeterministicSanitizer.sanitize("aaaaaa")
    assert result.is_valid is False
    assert "repetitive" in result.rejection_reason


def test_whitespace_and_control_chars():
    result = DeterministicSanitizer.sanitize("  Color   mismatch \x00\x08 hai  ")
    assert result.is_valid is True
    assert result.sanitized_text == "Color mismatch hai"
