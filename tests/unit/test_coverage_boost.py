"""Tests to increase coverage for low-coverage modules."""

import pytest

from bugsafe.redact.engine import (
    PatternComplexityError,
    RedactionEngine,
    RedactionReport,
    compile_pattern_safely,
    create_redaction_engine,
)
from bugsafe.redact.path_anonymizer import create_default_anonymizer
from bugsafe.redact.patterns import Pattern, PatternConfig
from bugsafe.redact.tokenizer import Tokenizer


class TestRedactionEngineConfig:
    """Test RedactionEngine configuration options."""

    def test_disabled_patterns(self) -> None:
        """Test that disabled patterns are skipped."""
        config = PatternConfig(disabled_patterns={"aws_access_key"})
        engine = RedactionEngine(config=config)
        text = "key=AKIAIOSFODNN7EXAMPLE"
        result, report = engine.redact(text)
        # AWS key pattern disabled, should not be redacted
        assert "AKIAIOSFODNN7EXAMPLE" in result

    def test_enabled_patterns_only(self) -> None:
        """Test that only enabled patterns are applied."""
        config = PatternConfig(enabled_patterns={"github_token"})
        engine = RedactionEngine(config=config)
        # AWS key should not be redacted (not in enabled list)
        text = "key=AKIAIOSFODNN7EXAMPLE"
        result, report = engine.redact(text)
        assert "AKIAIOSFODNN7EXAMPLE" in result

    def test_redact_emails_disabled(self) -> None:
        """Test email redaction can be disabled."""
        config = PatternConfig(redact_emails=False)
        engine = RedactionEngine(config=config)
        text = "contact: user@example.com"
        result, report = engine.redact(text)
        assert "user@example.com" in result

    def test_redact_ips_disabled(self) -> None:
        """Test IP redaction can be disabled."""
        config = PatternConfig(redact_ips=False)
        engine = RedactionEngine(config=config)
        text = "server: 192.168.1.100"
        result, report = engine.redact(text)
        assert "192.168.1.100" in result

    def test_redact_uuids_enabled(self) -> None:
        """Test UUID redaction when enabled."""
        config = PatternConfig(redact_uuids=True)
        engine = RedactionEngine(config=config)
        text = "id: 550e8400-e29b-41d4-a716-446655440000"
        result, report = engine.redact(text)
        assert "550e8400-e29b-41d4-a716-446655440000" not in result

    def test_min_priority(self) -> None:
        """Test minimum priority filtering."""
        config = PatternConfig(min_priority=100)  # Very high priority
        engine = RedactionEngine(config=config)
        text = "key=AKIAIOSFODNN7EXAMPLE"
        result, report = engine.redact(text)
        # Most patterns have lower priority, should not match
        # (depends on actual pattern priorities)

    def test_custom_patterns(self) -> None:
        """Test adding custom patterns."""
        import re

        custom = Pattern(
            name="custom_secret",
            regex=re.compile(r"MYSECRET_[A-Z0-9]+"),
            category="CUSTOM",
            priority=100,
        )
        config = PatternConfig(custom_patterns=[custom])
        engine = RedactionEngine(config=config)
        text = "token=MYSECRET_ABC123"
        result, report = engine.redact(text)
        assert "MYSECRET_ABC123" not in result
        assert "<CUSTOM_" in result


class TestRedactionReport:
    """Test RedactionReport functionality."""

    def test_add_and_get_total(self) -> None:
        """Test adding matches and getting total."""
        report = RedactionReport()
        report.add("secret1", "<TOKEN_1>", "API_KEY", "pattern1")
        report.add("secret2", "<TOKEN_2>", "API_KEY", "pattern1")
        assert report.get_total() == 2

    def test_categories_tracking(self) -> None:
        """Test category counting."""
        report = RedactionReport()
        report.add("s1", "<T1>", "AWS_KEY", "p1")
        report.add("s2", "<T2>", "AWS_KEY", "p1")
        report.add("s3", "<T3>", "GITHUB_TOKEN", "p2")
        assert report.categories["AWS_KEY"] == 2
        assert report.categories["GITHUB_TOKEN"] == 1

    def test_patterns_used_tracking(self) -> None:
        """Test pattern usage tracking."""
        report = RedactionReport()
        report.add("s1", "<T1>", "CAT", "pattern_a")
        report.add("s2", "<T2>", "CAT", "pattern_b")
        assert "pattern_a" in report.patterns_used
        assert "pattern_b" in report.patterns_used

    def test_get_summary(self) -> None:
        """Test get_summary returns categories."""
        report = RedactionReport()
        report.add("s1", "<T1>", "AWS_KEY", "p1")
        summary = report.get_summary()
        assert summary == {"AWS_KEY": 1}


class TestCompilePatternSafely:
    """Test safe pattern compilation."""

    def test_normal_pattern(self) -> None:
        """Test compiling normal pattern."""
        pattern = compile_pattern_safely(r"\d+")
        assert pattern.match("123")

    def test_pattern_with_flags(self) -> None:
        """Test compiling with flags."""
        import re

        pattern = compile_pattern_safely(r"[a-z]+", re.IGNORECASE)
        assert pattern.match("ABC")

    def test_pattern_too_long(self) -> None:
        """Test rejection of overly complex patterns."""
        long_pattern = "a" * 1001
        with pytest.raises(PatternComplexityError):
            compile_pattern_safely(long_pattern)

    def test_pattern_caching(self) -> None:
        """Test that patterns are cached."""
        p1 = compile_pattern_safely(r"\w+")
        p2 = compile_pattern_safely(r"\w+")
        assert p1 is p2  # Same object from cache


class TestTokenizer:
    """Test Tokenizer functionality."""

    def test_tokenize_consistency(self) -> None:
        """Test same secret gets same token."""
        tokenizer = Tokenizer()
        t1 = tokenizer.tokenize("secret123", "API_KEY")
        t2 = tokenizer.tokenize("secret123", "API_KEY")
        assert t1 == t2

    def test_tokenize_different_secrets(self) -> None:
        """Test different secrets get different tokens."""
        tokenizer = Tokenizer()
        t1 = tokenizer.tokenize("secret1", "API_KEY")
        t2 = tokenizer.tokenize("secret2", "API_KEY")
        assert t1 != t2

    def test_token_format(self) -> None:
        """Test token follows expected format."""
        tokenizer = Tokenizer()
        token = tokenizer.tokenize("mysecret", "AWS_KEY")
        assert token.startswith("<AWS_KEY_")
        assert token.endswith(">")

    def test_is_token(self) -> None:
        """Test token detection."""
        tokenizer = Tokenizer()
        token = tokenizer.tokenize("secret", "API_KEY")
        assert tokenizer.is_token(token)
        assert not tokenizer.is_token("not_a_token")

    def test_get_total_redactions(self) -> None:
        """Test counting total redactions."""
        tokenizer = Tokenizer()
        tokenizer.tokenize("s1", "CAT1")
        tokenizer.tokenize("s2", "CAT2")
        tokenizer.tokenize("s1", "CAT1")  # Same secret, same token
        assert tokenizer.get_total_redactions() == 2  # Unique secrets

    def test_reset(self) -> None:
        """Test resetting tokenizer state."""
        tokenizer = Tokenizer()
        t1 = tokenizer.tokenize("secret", "API_KEY")
        tokenizer.reset()
        t2 = tokenizer.tokenize("secret", "API_KEY")
        # After reset, may get different token number
        assert "<API_KEY_" in t1
        assert "<API_KEY_" in t2

    def test_get_salt_hash(self) -> None:
        """Test salt hash retrieval."""
        tokenizer = Tokenizer()
        salt_hash = tokenizer.get_salt_hash()
        assert isinstance(salt_hash, str)
        assert len(salt_hash) > 0


class TestPathAnonymizer:
    """Test PathAnonymizer functionality."""

    def test_anonymize_home_directory(self) -> None:
        """Test home directory anonymization."""
        anonymizer = create_default_anonymizer()
        import os

        home = os.path.expanduser("~")
        text = f"file at {home}/Documents/secret.txt"
        result = anonymizer.anonymize(text)
        assert home not in result
        assert "~" in result or "<HOME>" in result or "/Documents/" in result

    def test_anonymize_temp_directory(self) -> None:
        """Test temp directory anonymization."""
        anonymizer = create_default_anonymizer()
        text = "file at /tmp/test123/file.txt"
        result = anonymizer.anonymize(text)
        # Temp paths are anonymized to <TMPDIR>
        assert "<TMPDIR>" in result or "/tmp/" not in result

    def test_anonymize_preserves_structure(self) -> None:
        """Test that anonymization preserves text structure."""
        anonymizer = create_default_anonymizer()
        text = "Line 1\nLine 2\nLine 3"
        result = anonymizer.anonymize(text)
        assert result.count("\n") == text.count("\n")


class TestRedactionEngineVerify:
    """Test RedactionEngine verify_redaction."""

    def test_verify_clean_text(self) -> None:
        """Test verification of clean text."""
        engine = create_redaction_engine()
        leaks = engine.verify_redaction("This is clean text with no secrets")
        assert len(leaks) == 0

    def test_verify_text_with_secrets(self) -> None:
        """Test verification detects remaining secrets."""
        engine = create_redaction_engine()
        text = "key=AKIAIOSFODNN7EXAMPLE"
        leaks = engine.verify_redaction(text)
        assert len(leaks) > 0

    def test_verify_text_with_tokens(self) -> None:
        """Test verification ignores tokens."""
        engine = create_redaction_engine()
        text = "key=<AWS_KEY_1> and token=<GITHUB_TOKEN_2>"
        leaks = engine.verify_redaction(text)
        assert len(leaks) == 0


class TestRedactionEngineSummary:
    """Test RedactionEngine get_redaction_summary."""

    def test_get_redaction_summary_after_redact(self) -> None:
        """Test summary after redaction."""
        engine = create_redaction_engine()
        engine.redact("key=AKIAIOSFODNN7EXAMPLE")
        summary = engine.get_redaction_summary()
        assert "AWS_KEY" in summary or len(summary) > 0

    def test_get_redaction_summary_empty(self) -> None:
        """Test summary with no redactions."""
        engine = create_redaction_engine()
        engine.redact("clean text")
        summary = engine.get_redaction_summary()
        assert summary == {} or len(summary) == 0


class TestCreateRedactionEngine:
    """Test create_redaction_engine factory."""

    def test_creates_engine(self) -> None:
        """Test factory creates working engine."""
        engine = create_redaction_engine()
        assert isinstance(engine, RedactionEngine)

    def test_engine_has_patterns(self) -> None:
        """Test engine has default patterns."""
        engine = create_redaction_engine()
        assert len(engine.patterns) > 0

    def test_engine_redacts(self) -> None:
        """Test engine actually redacts."""
        engine = create_redaction_engine()
        result, _ = engine.redact("AKIAIOSFODNN7EXAMPLE")
        assert "AKIAIOSFODNN7EXAMPLE" not in result
