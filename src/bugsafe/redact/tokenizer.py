"""Tokenizer - Deterministic, correlation-preserving secret replacement."""

from __future__ import annotations

import hashlib
import secrets
import unicodedata
from dataclasses import dataclass, field

MAX_SECRET_LENGTH = 1024


@dataclass
class Tokenizer:
    """Deterministic, correlation-preserving secret tokenizer.

    Ensures that the same secret always maps to the same token within
    a single redaction session, preserving correlations across different
    parts of the output.

    Attributes:
        salt: Random bytes used for the session (not stored, only hash).
        _cache: Internal cache mapping secrets to tokens.
        _counter: Sequential counter for token numbering.
    """

    salt: bytes = field(default_factory=lambda: secrets.token_bytes(32))
    _cache: dict[str, str] = field(default_factory=dict, repr=False)
    _counter: int = field(default=0, repr=False)
    _category_counters: dict[str, int] = field(default_factory=dict, repr=False)

    def tokenize(self, secret: str, category: str) -> str:
        """Replace a secret with a deterministic token.

        Args:
            secret: The secret value to tokenize.
            category: Category for the token (e.g., AWS_KEY, EMAIL).

        Returns:
            Token string in format <CATEGORY_N>.
        """
        if not secret or not secret.strip():
            return secret

        normalized = self._normalize(secret)
        if not normalized:
            return secret

        if normalized in self._cache:
            return self._cache[normalized]

        category_upper = category.upper().replace(" ", "_")
        if category_upper not in self._category_counters:
            self._category_counters[category_upper] = 0
        self._category_counters[category_upper] += 1
        count = self._category_counters[category_upper]

        token = f"<{category_upper}_{count}>"
        self._cache[normalized] = token

        if secret != normalized:
            self._cache[secret] = token

        return token

    def _normalize(self, secret: str) -> str:
        """Normalize a secret for consistent matching.

        Args:
            secret: The secret to normalize.

        Returns:
            Normalized string.
        """
        result = secret.strip()

        if len(result) > MAX_SECRET_LENGTH:
            result = result[:MAX_SECRET_LENGTH]

        result = unicodedata.normalize("NFC", result)

        return result

    def get_salt_hash(self) -> str:
        """Get SHA256 hash of the salt for bundle metadata.

        Returns:
            Hexadecimal hash string.
        """
        return hashlib.sha256(self.salt).hexdigest()

    def get_report(self) -> dict[str, int]:
        """Get count of tokens by category.

        Returns:
            Dictionary mapping category names to token counts.
        """
        return dict(self._category_counters)

    def get_total_redactions(self) -> int:
        """Get total number of unique secrets redacted.

        Returns:
            Count of unique secrets.
        """
        return len(self._cache)

    def is_token(self, text: str) -> bool:
        """Check if text is a redaction token.

        Args:
            text: Text to check.

        Returns:
            True if text matches token format.
        """
        if not text.startswith("<") or not text.endswith(">"):
            return False
        inner = text[1:-1]
        if "_" not in inner:
            return False
        parts = inner.rsplit("_", 1)
        return len(parts) == 2 and parts[1].isdigit()

    def reset(self) -> None:
        """Reset the tokenizer state for a new session."""
        self.salt = secrets.token_bytes(32)
        self._cache.clear()
        self._counter = 0
        self._category_counters.clear()
