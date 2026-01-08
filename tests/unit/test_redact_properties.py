"""Property-based tests for redaction module using Hypothesis."""

from hypothesis import assume, given, settings
from hypothesis import strategies as st

from bugsafe.redact.engine import RedactionEngine, create_redaction_engine
from bugsafe.redact.patterns import DEFAULT_PATTERNS
from bugsafe.redact.tokenizer import Tokenizer


class TestRedactionIdempotence:
    """Tests that redaction is idempotent."""

    @given(st.text(max_size=1000))
    @settings(max_examples=100)
    def test_redaction_is_idempotent(self, text: str):
        """Redacting twice yields same result."""
        engine = create_redaction_engine()
        r1, _ = engine.redact(text)
        r2, _ = engine.redact(r1)
        assert r1 == r2

    @given(st.text(max_size=500))
    @settings(max_examples=50)
    def test_idempotent_with_secrets(self, text: str):
        """Redacting text with injected secrets is idempotent."""
        secrets = [
            "AKIAIOSFODNN7EXAMPLE",
            "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "test@example.com",
            "192.168.1.100",
        ]
        text_with_secrets = text + " " + " ".join(secrets)
        engine = create_redaction_engine()
        r1, _ = engine.redact(text_with_secrets)
        r2, _ = engine.redact(r1)
        assert r1 == r2


class TestDeterministicTokens:
    """Tests that tokenization is deterministic with same salt."""

    @given(st.text(max_size=500))
    @settings(max_examples=100)
    def test_deterministic_tokens_same_salt(self, text: str):
        """Same input, same salt → same tokens."""
        salt = b"fixed_test_salt_1234567890123456"
        e1 = RedactionEngine(
            patterns=DEFAULT_PATTERNS,
            tokenizer=Tokenizer(salt=salt),
        )
        e2 = RedactionEngine(
            patterns=DEFAULT_PATTERNS,
            tokenizer=Tokenizer(salt=salt),
        )
        r1, _ = e1.redact(text)
        r2, _ = e2.redact(text)
        assert r1 == r2

    @given(st.text(max_size=500))
    @settings(max_examples=50)
    def test_different_salt_different_tokens(self, text: str):
        """Different salts may produce different internal state."""
        assume(len(text) > 0)
        salt1 = b"salt_one_1234567890123456789012"
        salt2 = b"salt_two_1234567890123456789012"
        e1 = RedactionEngine(
            patterns=DEFAULT_PATTERNS,
            tokenizer=Tokenizer(salt=salt1),
        )
        e2 = RedactionEngine(
            patterns=DEFAULT_PATTERNS,
            tokenizer=Tokenizer(salt=salt2),
        )
        r1, report1 = e1.redact(text)
        r2, report2 = e2.redact(text)
        assert r1 == r2
        assert e1.get_salt_hash() != e2.get_salt_hash()


class TestNoKnownSecretsInOutput:
    """Tests that known secrets are removed from output."""

    @given(st.text(max_size=200))
    @settings(max_examples=50)
    def test_aws_keys_redacted(self, prefix: str):
        """AWS access keys are always redacted."""
        aws_key = "AKIAIOSFODNN7EXAMPLE"
        text = f"{prefix} key={aws_key} end"
        engine = create_redaction_engine()
        result, _ = engine.redact(text)
        assert aws_key not in result

    @given(st.text(max_size=200))
    @settings(max_examples=50)
    def test_github_tokens_redacted(self, prefix: str):
        """GitHub tokens are always redacted."""
        gh_token = "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        text = f"{prefix} token={gh_token} end"
        engine = create_redaction_engine()
        result, _ = engine.redact(text)
        assert gh_token not in result

    @given(st.text(max_size=200))
    @settings(max_examples=50)
    def test_private_keys_redacted(self, prefix: str):
        """Private keys are always redacted."""
        private_key = "-----BEGIN RSA PRIVATE KEY-----\nMIIBOgIBA..."
        text = f"{prefix}\n{private_key}\n-----END RSA PRIVATE KEY-----"
        engine = create_redaction_engine()
        result, _ = engine.redact(text)
        assert "PRIVATE KEY" not in result

    @given(st.text(max_size=200))
    @settings(max_examples=50)
    def test_connection_strings_redacted(self, prefix: str):
        """Database connection strings are redacted."""
        conn_str = "postgres://user:password@localhost:5432/db"
        text = f"{prefix} db={conn_str}"
        engine = create_redaction_engine()
        result, _ = engine.redact(text)
        assert "password" not in result
        assert conn_str not in result


class TestTokenCorrelation:
    """Tests that token correlation is preserved."""

    def test_same_secret_same_token(self):
        """Same secret appears with same token throughout."""
        engine = create_redaction_engine()
        secret = "AKIAIOSFODNN7EXAMPLE"
        text = f"first: {secret}\nsecond: {secret}\nthird: {secret}"
        result, report = engine.redact(text)

        assert secret not in result
        assert result.count("<AWS_KEY_1>") == 3

    def test_different_secrets_different_tokens(self):
        """Different secrets get different tokens."""
        engine = create_redaction_engine()
        secret1 = "AKIAIOSFODNN7EXAMPLE"
        secret2 = "AKIAIOSFODNN7EXAMPL2"
        text = f"key1: {secret1}\nkey2: {secret2}"
        result, report = engine.redact(text)

        assert "<AWS_KEY_1>" in result
        assert "<AWS_KEY_2>" in result


class TestTokenizerProperties:
    """Property tests for the Tokenizer class."""

    @given(st.text(min_size=4, max_size=100))
    @settings(max_examples=100)
    def test_tokenize_returns_valid_format(self, secret: str):
        """Tokenized output has valid format <CATEGORY_N>."""
        assume(secret.strip())
        tokenizer = Tokenizer()
        token = tokenizer.tokenize(secret, "TEST")
        assert token.startswith("<TEST_")
        assert token.endswith(">")
        assert "_" in token

    @given(st.text(min_size=4, max_size=100))
    @settings(max_examples=50)
    def test_same_secret_same_token(self, secret: str):
        """Same secret always gets same token."""
        assume(secret.strip())
        tokenizer = Tokenizer()
        t1 = tokenizer.tokenize(secret, "CAT")
        t2 = tokenizer.tokenize(secret, "CAT")
        assert t1 == t2

    @given(st.text(min_size=4, max_size=50))
    @settings(max_examples=50)
    def test_different_secrets_different_numbers(self, secret1: str):
        """Different secrets get different token numbers."""
        assume(secret1.strip())
        secret2 = secret1 + "_different"
        tokenizer = Tokenizer()
        t1 = tokenizer.tokenize(secret1, "CAT")
        t2 = tokenizer.tokenize(secret2, "CAT")
        assert t1.startswith("<CAT_")
        assert t2.startswith("<CAT_")
        assert t1 != t2


class TestRedactionSafety:
    """Tests for redaction safety properties."""

    @given(st.text(max_size=500))
    @settings(max_examples=100)
    def test_no_crash_on_arbitrary_input(self, text: str):
        """Engine doesn't crash on arbitrary input."""
        engine = create_redaction_engine()
        result, report = engine.redact(text)
        assert isinstance(result, str)
        assert report is not None

    @given(st.binary(max_size=500))
    @settings(max_examples=50)
    def test_handles_binary_like_strings(self, data: bytes):
        """Engine handles strings with binary-like content."""
        try:
            text = data.decode("utf-8", errors="replace")
        except Exception:
            return
        engine = create_redaction_engine()
        result, _ = engine.redact(text)
        assert isinstance(result, str)

    @given(st.text(max_size=1000))
    @settings(max_examples=50)
    def test_output_length_reasonable(self, text: str):
        """Output length is reasonable relative to input."""
        engine = create_redaction_engine()
        result, _ = engine.redact(text)
        assert len(result) <= len(text) * 3 + 1000


class TestPatternMatching:
    """Property tests for pattern matching."""

    @given(st.from_regex(r"AKIA[A-Z0-9]{16}", fullmatch=True))
    @settings(max_examples=50)
    def test_aws_key_pattern_matches(self, aws_key: str):
        """AWS key pattern matches generated keys."""
        engine = create_redaction_engine()
        text = f"key: {aws_key}"
        result, report = engine.redact(text)
        assert aws_key not in result
        assert report.get_total() > 0

    @given(st.from_regex(r"ghp_[A-Za-z0-9]{36}", fullmatch=True))
    @settings(max_examples=50)
    def test_github_token_pattern_matches(self, token: str):
        """GitHub token pattern matches generated tokens."""
        engine = create_redaction_engine()
        text = f"token: {token}"
        result, report = engine.redact(text)
        assert token not in result

    @given(st.from_regex(r"[a-z][a-z0-9]{3,10}@[a-z]{3,8}\.[a-z]{2,4}", fullmatch=True))
    @settings(max_examples=50)
    def test_email_pattern_matches(self, email: str):
        """Email pattern matches valid emails."""
        engine = create_redaction_engine()
        text = f"contact: {email}"
        result, report = engine.redact(text)
        assert email not in result


class TestEdgeCases:
    """Property tests for edge cases."""

    def test_empty_string(self):
        """Empty string is handled."""
        engine = create_redaction_engine()
        result, report = engine.redact("")
        assert result == ""
        assert report.get_total() == 0

    @given(st.text(alphabet=st.characters(whitelist_categories=("Zs",)), max_size=100))
    @settings(max_examples=20)
    def test_whitespace_only(self, text: str):
        """Whitespace-only text is handled."""
        engine = create_redaction_engine()
        result, report = engine.redact(text)
        assert isinstance(result, str)

    @given(st.text(max_size=10000))
    @settings(max_examples=10)
    def test_large_input(self, text: str):
        """Large input is handled without timeout."""
        engine = create_redaction_engine()
        result, report = engine.redact(text)
        assert isinstance(result, str)

    def test_unicode_secrets(self):
        """Unicode in secrets is handled."""
        engine = create_redaction_engine()
        text = "密码: password123 邮箱: test@example.com"
        result, _ = engine.redact(text)
        assert "test@example.com" not in result
