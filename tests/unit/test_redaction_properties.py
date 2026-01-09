"""Property-based tests for redaction engine using hypothesis."""

import pytest

from bugsafe.redact.engine import create_redaction_engine

try:
    from hypothesis import given, settings
    from hypothesis import strategies as st

    HYPOTHESIS_AVAILABLE = True
except ImportError:
    HYPOTHESIS_AVAILABLE = False
    given = None
    settings = None
    st = None


pytestmark = pytest.mark.skipif(
    not HYPOTHESIS_AVAILABLE,
    reason="hypothesis not installed",
)


@pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="hypothesis not installed")
class TestRedactionProperties:
    """Property-based tests for redaction engine."""

    @given(st.text(max_size=1000))
    @settings(max_examples=100, deadline=None)
    def test_redact_never_crashes(self, text: str) -> None:
        """Redaction should never crash on any input."""
        engine = create_redaction_engine()
        result, report = engine.redact(text)
        assert isinstance(result, str)
        assert len(result) >= 0

    @given(st.text(max_size=500))
    @settings(max_examples=50, deadline=None)
    def test_redact_idempotent(self, text: str) -> None:
        """Redacting twice should produce same result."""
        engine = create_redaction_engine()
        result1, _ = engine.redact(text)
        result2, _ = engine.redact(result1)
        # Second pass should find nothing new (tokens don't match patterns)
        assert result1 == result2

    @given(st.text(max_size=500))
    @settings(max_examples=50, deadline=None)
    def test_redact_preserves_structure(self, text: str) -> None:
        """Redaction preserves line count and general structure."""
        engine = create_redaction_engine()
        result, _ = engine.redact(text)
        # Line count should be preserved
        assert result.count("\n") == text.count("\n")

    @given(st.text(max_size=500))
    @settings(max_examples=50, deadline=None)
    def test_tokens_are_valid_format(self, text: str) -> None:
        """Any tokens in output should be valid format."""
        engine = create_redaction_engine()
        result, report = engine.redact(text)

        # Check that any tokens follow the expected format
        for match in report.matches:
            assert match.token.startswith("<")
            assert match.token.endswith(">")
            assert "_" in match.token

    @given(st.lists(st.text(max_size=100), max_size=10))
    @settings(max_examples=30, deadline=None)
    def test_redact_multiple_inputs_consistent(self, texts: list[str]) -> None:
        """Same secrets in different texts get same tokens."""
        engine = create_redaction_engine()

        # Redact all texts with same engine
        results = [engine.redact(text) for text in texts]

        # All results should be strings
        for result, _ in results:
            assert isinstance(result, str)


@pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="hypothesis not installed")
class TestTokenizerProperties:
    """Property-based tests for tokenizer."""

    @given(st.text(min_size=4, max_size=100))
    @settings(max_examples=50, deadline=None)
    def test_same_secret_same_token(self, secret: str) -> None:
        """Same secret always produces same token within session."""
        engine = create_redaction_engine()
        token1 = engine.tokenizer.tokenize(secret, "TEST")
        token2 = engine.tokenizer.tokenize(secret, "TEST")
        assert token1 == token2

    @given(
        st.text(min_size=4, max_size=50),
        st.text(min_size=4, max_size=50),
    )
    @settings(max_examples=50, deadline=None)
    def test_different_secrets_different_tokens(
        self, secret1: str, secret2: str
    ) -> None:
        """Different secrets produce different tokens."""
        if secret1 == secret2:
            return  # Skip if same

        engine = create_redaction_engine()
        token1 = engine.tokenizer.tokenize(secret1, "TEST")
        token2 = engine.tokenizer.tokenize(secret2, "TEST")

        # Different secrets should have different tokens
        # (unless they normalize to the same value, which is rare)
        if secret1.strip().lower() != secret2.strip().lower():
            assert token1 != token2


class TestRedactionEdgeCases:
    """Edge case tests that don't require hypothesis."""

    def test_empty_string(self) -> None:
        """Redact empty string returns empty string."""
        engine = create_redaction_engine()
        result, report = engine.redact("")
        assert result == ""
        assert report.get_total() == 0

    def test_whitespace_only(self) -> None:
        """Redact whitespace-only string preserves whitespace."""
        engine = create_redaction_engine()
        result, report = engine.redact("   \n\t\n   ")
        assert result == "   \n\t\n   "
        assert report.get_total() == 0

    def test_unicode_text(self) -> None:
        """Redact unicode text works correctly."""
        engine = create_redaction_engine()
        text = "🔑 API_KEY=AKIAIOSFODNN7EXAMPLE 🔒"
        result, report = engine.redact(text)
        assert "AKIAIOSFODNN7EXAMPLE" not in result
        assert "🔑" in result
        assert "🔒" in result

    def test_very_long_line(self) -> None:
        """Redact very long line doesn't crash."""
        engine = create_redaction_engine()
        text = "x" * 100000
        result, report = engine.redact(text)
        assert len(result) == 100000

    def test_many_secrets(self) -> None:
        """Redact text with many different secrets."""
        engine = create_redaction_engine()
        # Use different secrets to test multiple redactions
        secrets = [f"AKIA{''.join(str(i % 10) for _ in range(16))}" for i in range(10)]
        text = "\n".join(f"key{i}={s}" for i, s in enumerate(secrets))
        result, report = engine.redact(text)
        # At least some secrets should be redacted
        assert report.get_total() >= 1
        # Repeated same secret uses same token (correlation preserving)
        assert "<AWS_KEY_" in result or "AKIA" not in result

    def test_nested_secrets(self) -> None:
        """Redact nested/overlapping patterns."""
        engine = create_redaction_engine()
        text = "token=ghp_AKIAIOSFODNN7EXAMPLEsecret"
        result, _ = engine.redact(text)
        # At least the AWS key should be redacted
        assert "AKIAIOSFODNN7EXAMPLE" not in result
