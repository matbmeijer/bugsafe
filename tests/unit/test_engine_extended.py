"""Functional tests for RedactionReport and advanced engine behavior."""

import re

from bugsafe.redact.engine import (
    RedactionReport,
    create_redaction_engine,
)


class TestRedactionReport:
    """Functional tests for RedactionReport - tracks what was redacted."""

    def test_new_report_is_empty(self):
        """A new report should have no matches or categories."""
        report = RedactionReport()

        assert len(report.matches) == 0, "New report should have no matches"
        assert len(report.categories) == 0, "New report should have no categories"

    def test_adding_match_increments_category_count(self):
        """Adding a match should increment the category counter."""
        report = RedactionReport()

        report.add("AKIAIOSFODNN7EXAMPLE", "<API_KEY_1>", "api_key", "aws_access_key")

        assert len(report.matches) == 1, "Should have exactly one match"
        assert report.categories["api_key"] == 1, "Category count should be 1"
        assert "aws_access_key" in report.patterns_used, "Pattern should be tracked"

    def test_multiple_matches_same_category(self):
        """Multiple matches in same category should sum correctly."""
        report = RedactionReport()

        report.add("secret1", "<TOKEN_1>", "api_key", "pattern1")
        report.add("secret2", "<TOKEN_2>", "api_key", "pattern2")
        report.add("secret3", "<TOKEN_3>", "password", "pattern3")

        assert report.categories["api_key"] == 2, "api_key should have 2 matches"
        assert report.categories["password"] == 1, "password should have 1 match"
        assert len(report.matches) == 3, "Total matches should be 3"


class TestTokenCorrelation:
    """Functional tests for token correlation - same secret = same token."""

    def test_identical_secrets_produce_identical_tokens(self):
        """The same secret appearing multiple times must get the same token."""
        engine = create_redaction_engine()
        secret = "AKIAIOSFODNN7EXAMPLE"
        text = f"First: {secret}\nSecond: {secret}\nThird: {secret}"

        result, _ = engine.redact(text)

        # Extract tokens
        tokens = re.findall(r"<[A-Z_]+_\d+>", result)
        unique_tokens = set(tokens)

        assert len(tokens) == 3, "Should have 3 token occurrences"
        assert len(unique_tokens) == 1, "All tokens should be identical"

    def test_different_secrets_produce_different_tokens(self):
        """Different secrets must get different tokens for traceability."""
        engine = create_redaction_engine()
        text = "Key1: AKIAIOSFODNN7EXAMPLE\nKey2: AKIAIOSFODNN7ANOTHER"

        result, _ = engine.redact(text)

        tokens = re.findall(r"<[A-Z_]+_\d+>", result)
        unique_tokens = set(tokens)

        assert len(tokens) == 2, "Should have 2 token occurrences"
        assert len(unique_tokens) == 2, "Tokens should be different"


class TestTextStructurePreservation:
    """Functional tests ensuring redaction preserves text formatting."""

    def test_line_count_preserved(self):
        """Number of lines should be unchanged after redaction."""
        engine = create_redaction_engine()
        text = "Line 1\nLine 2 has AKIAIOSFODNN7EXAMPLE\nLine 3\nLine 4"

        result, _ = engine.redact(text)

        assert result.count("\n") == 3, "Should preserve 3 newlines"

    def test_empty_lines_preserved(self):
        """Empty lines in input should be preserved."""
        engine = create_redaction_engine()
        text = "Before\n\nAfter secret AKIAIOSFODNN7EXAMPLE"

        result, _ = engine.redact(text)

        assert "\n\n" in result, "Empty line should be preserved"

    def test_indentation_preserved(self):
        """Leading whitespace should be preserved."""
        engine = create_redaction_engine()
        text = "    indented: AKIAIOSFODNN7EXAMPLE"

        result, _ = engine.redact(text)

        assert result.startswith("    "), "Indentation should be preserved"


class TestVerifyRedaction:
    """Functional tests for verify_redaction - leak detection."""

    def test_redacted_output_passes_verification(self):
        """Output from redact() should always pass verify_redaction()."""
        engine = create_redaction_engine()
        original = "AWS Key: AKIAIOSFODNN7EXAMPLE and password: secret123"

        redacted, _ = engine.redact(original)
        leaks = engine.verify_redaction(redacted)

        assert len(leaks) == 0, "Redacted output must pass verification"

    def test_unredacted_secret_fails_verification(self):
        """Text with unredacted secrets should fail verification."""
        engine = create_redaction_engine()
        text_with_secret = "Leaked: AKIAIOSFODNN7EXAMPLE"

        leaks = engine.verify_redaction(text_with_secret)

        assert len(leaks) > 0, "Unredacted secret should be detected"


class TestSaltConsistency:
    """Functional tests for salt behavior."""

    def test_salt_hash_stable_within_engine(self):
        """Salt hash should not change during engine lifetime."""
        engine = create_redaction_engine()

        hash1 = engine.get_salt_hash()
        # Perform some operations
        engine.redact("AKIAIOSFODNN7EXAMPLE")
        hash2 = engine.get_salt_hash()

        assert hash1 == hash2, "Salt hash must remain stable"

    def test_salt_hash_is_not_empty(self):
        """Salt hash should be a non-empty string."""
        engine = create_redaction_engine()

        salt_hash = engine.get_salt_hash()

        assert isinstance(salt_hash, str), "Salt hash should be string"
        assert len(salt_hash) > 0, "Salt hash should not be empty"
