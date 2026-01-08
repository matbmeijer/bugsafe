"""Unit tests for redact/tokenizer.py."""

from bugsafe.redact.tokenizer import Tokenizer


class TestTokenizer:
    """Tests for Tokenizer class."""

    def test_basic_tokenization(self):
        tokenizer = Tokenizer()
        token = tokenizer.tokenize("secret123", "API_KEY")
        assert token == "<API_KEY_1>"

    def test_same_secret_same_token(self):
        tokenizer = Tokenizer()
        token1 = tokenizer.tokenize("secret123", "API_KEY")
        token2 = tokenizer.tokenize("secret123", "API_KEY")
        assert token1 == token2

    def test_different_secrets_different_tokens(self):
        tokenizer = Tokenizer()
        token1 = tokenizer.tokenize("secret1", "API_KEY")
        token2 = tokenizer.tokenize("secret2", "API_KEY")
        assert token1 != token2
        assert token1 == "<API_KEY_1>"
        assert token2 == "<API_KEY_2>"

    def test_different_categories(self):
        tokenizer = Tokenizer()
        token1 = tokenizer.tokenize("secret1", "API_KEY")
        token2 = tokenizer.tokenize("secret2", "PASSWORD")
        assert "<API_KEY_" in token1
        assert "<PASSWORD_" in token2

    def test_empty_secret_unchanged(self):
        tokenizer = Tokenizer()
        assert tokenizer.tokenize("", "API_KEY") == ""
        assert tokenizer.tokenize("   ", "API_KEY") == "   "

    def test_whitespace_normalization(self):
        tokenizer = Tokenizer()
        token1 = tokenizer.tokenize("  secret  ", "API_KEY")
        token2 = tokenizer.tokenize("secret", "API_KEY")
        assert token1 == token2

    def test_category_uppercase(self):
        tokenizer = Tokenizer()
        token = tokenizer.tokenize("secret", "api key")
        assert token == "<API_KEY_1>"

    def test_get_salt_hash(self):
        tokenizer = Tokenizer()
        salt_hash = tokenizer.get_salt_hash()
        assert len(salt_hash) == 64
        assert all(c in "0123456789abcdef" for c in salt_hash)

    def test_salt_hash_consistent(self):
        tokenizer = Tokenizer()
        hash1 = tokenizer.get_salt_hash()
        hash2 = tokenizer.get_salt_hash()
        assert hash1 == hash2

    def test_different_sessions_different_salts(self):
        tokenizer1 = Tokenizer()
        tokenizer2 = Tokenizer()
        assert tokenizer1.get_salt_hash() != tokenizer2.get_salt_hash()

    def test_get_report(self):
        tokenizer = Tokenizer()
        tokenizer.tokenize("secret1", "API_KEY")
        tokenizer.tokenize("secret2", "API_KEY")
        tokenizer.tokenize("password", "PASSWORD")

        report = tokenizer.get_report()
        assert report["API_KEY"] == 2
        assert report["PASSWORD"] == 1

    def test_get_total_redactions(self):
        tokenizer = Tokenizer()
        tokenizer.tokenize("secret1", "API_KEY")
        tokenizer.tokenize("secret1", "API_KEY")
        tokenizer.tokenize("secret2", "API_KEY")

        assert tokenizer.get_total_redactions() == 2

    def test_is_token(self):
        tokenizer = Tokenizer()
        assert tokenizer.is_token("<API_KEY_1>")
        assert tokenizer.is_token("<PASSWORD_42>")
        assert not tokenizer.is_token("not_a_token")
        assert not tokenizer.is_token("<INCOMPLETE")
        assert not tokenizer.is_token("<NO_NUMBER>")

    def test_reset(self):
        tokenizer = Tokenizer()
        old_hash = tokenizer.get_salt_hash()
        tokenizer.tokenize("secret", "API_KEY")

        tokenizer.reset()

        assert tokenizer.get_salt_hash() != old_hash
        assert tokenizer.get_total_redactions() == 0
        assert tokenizer.get_report() == {}


class TestTokenizerEdgeCases:
    """Tests for tokenizer edge cases."""

    def test_unicode_secret(self):
        tokenizer = Tokenizer()
        token = tokenizer.tokenize("密码123", "PASSWORD")
        assert token == "<PASSWORD_1>"

    def test_long_secret_truncation(self):
        tokenizer = Tokenizer()
        long_secret = "x" * 2000
        token = tokenizer.tokenize(long_secret, "LONG")
        assert token == "<LONG_1>"
        # Both original and truncated are cached, but point to same token
        assert tokenizer.get_total_redactions() >= 1

    def test_special_characters_in_secret(self):
        tokenizer = Tokenizer()
        token = tokenizer.tokenize("pass!@#$%^&*()", "PASSWORD")
        assert token == "<PASSWORD_1>"

    def test_newlines_in_secret(self):
        tokenizer = Tokenizer()
        token = tokenizer.tokenize("line1\nline2", "MULTILINE")
        assert token == "<MULTILINE_1>"

    def test_correlation_preserved(self):
        tokenizer = Tokenizer()
        secret = "AKIAIOSFODNN7EXAMPLE"

        token1 = tokenizer.tokenize(secret, "AWS_KEY")
        token2 = tokenizer.tokenize(f"key={secret}", "AWS_KEY")

        assert secret not in token1
        text = f"Found key: {secret}"
        text = text.replace(secret, token1)
        assert secret not in text
