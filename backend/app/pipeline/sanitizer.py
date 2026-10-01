import re
import unicodedata
from ..models.triage import SanitationResult


class DeterministicSanitizer:
    """
    Phase 0: Deterministic Ingestion & Sanitation (Strictly Python code)
    - Normalizes unicode and whitespace.
    - Strips non-printable control characters.
    - Filters out empty, single-character, or repetitive spam/gibberish (e.g., '...', 'asdf').
    """

    REPETITIVE_CHAR_REGEX = re.compile(r"^(.)\1{2,}$")
    PUNCTUATION_ONLY_REGEX = re.compile(r"^[\W_]+$")
    KEYBOARD_MASH_REGEX = re.compile(r"^[asdfghjklqwertyuiopzxcvbnm]{1,4}$", re.IGNORECASE)

    @classmethod
    def sanitize(cls, raw_text: str) -> SanitationResult:
        if not raw_text:
            return SanitationResult(
                is_valid=False,
                sanitized_text="",
                rejection_reason="Empty input string."
            )

        # 1. Normalize unicode (NFKC)
        normalized = unicodedata.normalize("NFKC", raw_text)

        # 2. Strip control characters except newline and tab
        cleaned_chars = [
            ch for ch in normalized
            if unicodedata.category(ch)[0] != "C" or ch in ("\n", "\t")
        ]
        cleaned_text = "".join(cleaned_chars)

        # 3. Collapse multiple whitespace and strip edges
        sanitized = re.sub(r"\s+", " ", cleaned_text).strip()

        # 4. Length check
        if len(sanitized) < 3:
            return SanitationResult(
                is_valid=False,
                sanitized_text=sanitized,
                rejection_reason="Input too short (minimum 3 characters required)."
            )

        if len(sanitized) > 2000:
            sanitized = sanitized[:2000]

        # 5. Repetitive spam checks (e.g. '...', 'aaaa', '???')
        if cls.PUNCTUATION_ONLY_REGEX.match(sanitized):
            return SanitationResult(
                is_valid=False,
                sanitized_text=sanitized,
                rejection_reason="Input contains only punctuation/symbols."
            )

        if cls.REPETITIVE_CHAR_REGEX.match(sanitized):
            return SanitationResult(
                is_valid=False,
                sanitized_text=sanitized,
                rejection_reason="Input contains repetitive characters."
            )

        # 6. Common keyboard mash patterns
        if cls.KEYBOARD_MASH_REGEX.match(sanitized.lower()) and sanitized.lower() not in {"ok", "no"}:
            return SanitationResult(
                is_valid=False,
                sanitized_text=sanitized,
                rejection_reason="Input matches low-entropy keyboard mash."
            )

        return SanitationResult(
            is_valid=True,
            sanitized_text=sanitized,
            rejection_reason=None
        )
