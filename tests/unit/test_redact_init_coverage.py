"""Tests for redact package exports."""

from bugsafe.redact import (
    DEFAULT_PATTERNS,
    PathAnonymizer,
    Pattern,
    PatternConfig,
    RedactionEngine,
    RedactionReport,
    Tokenizer,
    create_redaction_engine,
    get_patterns_by_priority,
)


def test_redact_package_exports_available() -> None:
    """Test all expected exports are available."""
    assert RedactionEngine is not None
    assert RedactionReport is not None
    assert create_redaction_engine is not None
    assert Tokenizer is not None
    assert PathAnonymizer is not None
    assert Pattern is not None
    assert PatternConfig is not None
    assert DEFAULT_PATTERNS is not None
    assert get_patterns_by_priority is not None


def test_default_patterns_not_empty() -> None:
    """Test DEFAULT_PATTERNS contains patterns."""
    assert len(DEFAULT_PATTERNS) > 0
    for pattern in DEFAULT_PATTERNS:
        assert isinstance(pattern, Pattern)
        assert pattern.name
        assert pattern.category


def test_get_patterns_by_priority() -> None:
    """Test getting patterns by priority."""
    high_priority = get_patterns_by_priority(min_priority=80)
    all_patterns = get_patterns_by_priority(min_priority=0)

    assert len(high_priority) > 0
    assert len(all_patterns) >= len(high_priority)

    for pattern in high_priority:
        assert pattern.priority >= 80


def test_pattern_config_defaults() -> None:
    """Test PatternConfig has sensible defaults."""
    config = PatternConfig()
    assert config.redact_emails is True
    assert config.redact_ips is True
    assert config.disabled_patterns == set()


def test_tokenizer_integration() -> None:
    """Test Tokenizer works correctly."""
    tokenizer = Tokenizer()
    token = tokenizer.tokenize("my_secret_value", "API_KEY")

    assert token.startswith("<API_KEY_")
    assert token.endswith(">")
    assert tokenizer.is_token(token)


def test_path_anonymizer_integration() -> None:
    """Test PathAnonymizer works correctly."""
    anonymizer = PathAnonymizer()
    # Should not crash on empty text
    result = anonymizer.anonymize("")
    assert result == ""


def test_redaction_engine_from_package() -> None:
    """Test creating engine from package import."""
    engine = create_redaction_engine()
    result, report = engine.redact("key=AKIAIOSFODNN7EXAMPLE")

    assert "AKIAIOSFODNN7EXAMPLE" not in result
    assert "<AWS_KEY_" in result
    assert report.get_total() >= 1
