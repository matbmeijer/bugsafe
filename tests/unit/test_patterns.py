"""Unit tests for redact/patterns.py."""

from bugsafe.redact.patterns import (
    DEFAULT_PATTERNS,
    HIGH_PRIORITY_PATTERN_NAMES,
    PatternConfig,
    Priority,
    create_custom_pattern,
    get_pattern_by_name,
    get_patterns_by_priority,
)


class TestPattern:
    """Tests for Pattern dataclass."""

    def test_pattern_creation(self):
        pattern = create_custom_pattern(
            name="test",
            pattern=r"test\d+",
            category="TEST",
        )
        assert pattern.name == "test"
        assert pattern.category == "TEST"
        assert pattern.priority == Priority.MEDIUM

    def test_pattern_matching(self):
        pattern = create_custom_pattern(
            name="test",
            pattern=r"secret_[a-z]+",
            category="TEST",
        )
        assert pattern.regex.search("my secret_abc here")
        assert not pattern.regex.search("no match")


class TestDefaultPatterns:
    """Tests for default pattern registry."""

    def test_has_minimum_patterns(self):
        assert len(DEFAULT_PATTERNS) >= 25

    def test_all_patterns_have_required_fields(self):
        for pattern in DEFAULT_PATTERNS:
            assert pattern.name
            assert pattern.regex
            assert pattern.category
            assert pattern.priority >= 0

    def test_pattern_names_unique(self):
        names = [p.name for p in DEFAULT_PATTERNS]
        assert len(names) == len(set(names))

    def test_high_priority_patterns_exist(self):
        assert len(HIGH_PRIORITY_PATTERN_NAMES) > 0
        for name in HIGH_PRIORITY_PATTERN_NAMES:
            pattern = get_pattern_by_name(name)
            assert pattern is not None


class TestPatternMatching:
    """Tests for specific pattern matching."""

    def test_aws_access_key(self):
        pattern = get_pattern_by_name("aws_access_key")
        assert pattern is not None
        assert pattern.regex.search("AKIAIOSFODNN7EXAMPLE")
        assert not pattern.regex.search("not_a_key")

    def test_github_token(self):
        pattern = get_pattern_by_name("github_token")
        assert pattern is not None
        assert pattern.regex.search("ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        assert pattern.regex.search("gho_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        assert not pattern.regex.search("gh_short")

    def test_gitlab_token(self):
        pattern = get_pattern_by_name("gitlab_token")
        assert pattern is not None
        assert pattern.regex.search("glpat-xxxxxxxxxxxxxxxxxxxx")

    def test_slack_token(self):
        pattern = get_pattern_by_name("slack_token")
        assert pattern is not None
        assert pattern.regex.search("xoxb-1234567890-1234567890123-abcdefghij")
        assert pattern.regex.search("xoxp-1234567890-1234567890123-abcdefghij")

    def test_jwt(self):
        pattern = get_pattern_by_name("jwt")
        assert pattern is not None
        jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0In0.dGVzdHNpZ25hdHVyZQ"
        assert pattern.regex.search(jwt)

    def test_private_key_block(self):
        pattern = get_pattern_by_name("private_key_block")
        assert pattern is not None
        key = """-----BEGIN RSA PRIVATE KEY-----
MIIBogIBAAJBALRiMLAhQvbMD...
-----END RSA PRIVATE KEY-----"""
        assert pattern.regex.search(key)

    def test_connection_string_postgres(self):
        pattern = get_pattern_by_name("connection_string_postgres")
        assert pattern is not None
        assert pattern.regex.search("postgres://user:pass@host:5432/db")
        assert pattern.regex.search("postgresql://user:pass@host/db")

    def test_email(self):
        pattern = get_pattern_by_name("email")
        assert pattern is not None
        assert pattern.regex.search("test@example.com")
        assert pattern.regex.search("user.name+tag@domain.co.uk")
        assert not pattern.regex.search("not_an_email")

    def test_ip_private(self):
        pattern = get_pattern_by_name("ip_private")
        assert pattern is not None
        assert pattern.regex.search("10.0.0.1")
        assert pattern.regex.search("192.168.1.1")
        assert pattern.regex.search("172.16.0.1")
        assert not pattern.regex.search("8.8.8.8")

    def test_uuid(self):
        pattern = get_pattern_by_name("uuid")
        assert pattern is not None
        assert pattern.regex.search("550e8400-e29b-41d4-a716-446655440000")


class TestPatternConfig:
    """Tests for PatternConfig."""

    def test_default_config(self):
        config = PatternConfig()
        assert config.enabled_patterns is None
        assert len(config.disabled_patterns) == 0
        assert config.min_priority == Priority.OPTIONAL
        assert config.redact_emails is True
        assert config.redact_ips is True
        assert config.redact_uuids is False

    def test_custom_config(self):
        config = PatternConfig(
            disabled_patterns={"email", "uuid"},
            min_priority=Priority.HIGH,
            redact_emails=False,
        )
        assert "email" in config.disabled_patterns
        assert config.min_priority == Priority.HIGH


class TestGetPatternsByPriority:
    """Tests for get_patterns_by_priority function."""

    def test_filter_by_priority(self):
        patterns = get_patterns_by_priority(Priority.HIGH)
        for pattern in patterns:
            assert pattern.priority >= Priority.HIGH

    def test_sorted_by_priority(self):
        patterns = get_patterns_by_priority(Priority.OPTIONAL)
        priorities = [p.priority for p in patterns]
        assert priorities == sorted(priorities, reverse=True)

    def test_includes_critical(self):
        patterns = get_patterns_by_priority(Priority.CRITICAL)
        assert len(patterns) > 0
        for pattern in patterns:
            assert pattern.priority >= Priority.CRITICAL


class TestCaptureGroups:
    """Tests for patterns with capture groups."""

    def test_bearer_token_capture(self):
        pattern = get_pattern_by_name("bearer_token")
        assert pattern is not None
        assert pattern.capture_group == 1
        match = pattern.regex.search("Authorization: Bearer abc123def456ghi789jkl012")
        assert match is not None
        assert match.group(1) == "abc123def456ghi789jkl012"

    def test_api_key_generic_capture(self):
        pattern = get_pattern_by_name("api_key_generic")
        assert pattern is not None
        assert pattern.capture_group == 2
        match = pattern.regex.search('api_key = "sk_test_1234567890abcdef"')
        assert match is not None
        assert match.group(2) == "sk_test_1234567890abcdef"
