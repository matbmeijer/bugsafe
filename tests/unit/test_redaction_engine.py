"""Unit tests for redact/engine.py."""

from pathlib import Path

import pytest

from bugsafe.redact.engine import (
    RedactionEngine,
    RedactionReport,
    create_redaction_engine,
)
from bugsafe.redact.patterns import PatternConfig, Priority
from bugsafe.redact.tokenizer import Tokenizer


class TestRedactionReport:
    """Tests for RedactionReport class."""

    def test_empty_report(self):
        report = RedactionReport()
        assert report.get_total() == 0
        assert report.get_summary() == {}

    def test_add_match(self):
        report = RedactionReport()
        report.add(
            original="secret123",
            token="<API_KEY_1>",
            category="API_KEY",
            pattern_name="test_pattern",
        )
        assert report.get_total() == 1
        assert report.get_summary() == {"API_KEY": 1}

    def test_multiple_matches(self):
        report = RedactionReport()
        report.add("s1", "<API_KEY_1>", "API_KEY", "p1")
        report.add("s2", "<API_KEY_2>", "API_KEY", "p1")
        report.add("s3", "<PASSWORD_1>", "PASSWORD", "p2")
        
        assert report.get_total() == 3
        assert report.get_summary() == {"API_KEY": 2, "PASSWORD": 1}

    def test_merge_reports(self):
        report1 = RedactionReport()
        report1.add("s1", "<A_1>", "A", "p1")
        
        report2 = RedactionReport()
        report2.add("s2", "<B_1>", "B", "p2")
        
        report1.merge(report2)
        assert report1.get_total() == 2
        assert "A" in report1.get_summary()
        assert "B" in report1.get_summary()


class TestRedactionEngine:
    """Tests for RedactionEngine class."""

    def test_basic_redaction(self):
        engine = create_redaction_engine()
        text = "My API key is AKIAIOSFODNN7EXAMPLE"
        result, report = engine.redact(text)
        
        assert "AKIAIOSFODNN7EXAMPLE" not in result
        assert "<AWS_KEY_" in result
        assert report.get_total() > 0

    def test_github_token_redaction(self):
        engine = create_redaction_engine()
        text = "token: ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        result, report = engine.redact(text)
        
        assert "ghp_" not in result
        assert "<GITHUB_TOKEN_" in result

    def test_jwt_redaction(self):
        engine = create_redaction_engine()
        jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0In0.dGVzdHNpZ25hdHVyZQ"
        text = f"Authorization: Bearer {jwt}"
        result, report = engine.redact(text)
        
        assert jwt not in result

    def test_email_redaction(self):
        engine = create_redaction_engine()
        text = "Contact: user@example.com"
        result, report = engine.redact(text)
        
        assert "user@example.com" not in result
        assert "<EMAIL_" in result

    def test_email_redaction_disabled(self):
        config = PatternConfig(redact_emails=False)
        engine = create_redaction_engine(config=config)
        text = "Contact: user@example.com"
        result, report = engine.redact(text)
        
        assert "user@example.com" in result

    def test_correlation_preserved(self):
        engine = create_redaction_engine()
        secret = "AKIAIOSFODNN7EXAMPLE"
        text = f"Key1: {secret}\nKey2: {secret}"
        result, report = engine.redact(text)
        
        lines = result.split("\n")
        token1 = lines[0].split(": ")[1]
        token2 = lines[1].split(": ")[1]
        assert token1 == token2

    def test_empty_text(self):
        engine = create_redaction_engine()
        result, report = engine.redact("")
        assert result == ""
        assert report.get_total() == 0

    def test_no_secrets(self):
        engine = create_redaction_engine()
        text = "Just regular text without secrets"
        result, report = engine.redact(text)
        assert result == text
        assert report.get_total() == 0

    def test_path_anonymization(self):
        engine = RedactionEngine()
        engine.path_anonymizer.home_dir = "/home/testuser"
        text = "File: /home/testuser/project/main.py"
        result, report = engine.redact(text)
        
        assert "/home/testuser" not in result

    def test_multiple_patterns(self):
        engine = create_redaction_engine()
        text = (
            "AWS: AKIAIOSFODNN7EXAMPLE\n"
            "GitHub: ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx\n"
            "Email: test@example.com"
        )
        result, report = engine.redact(text)
        
        assert "AKIA" not in result
        assert "ghp_" not in result
        assert "@example.com" not in result

    def test_private_key_redaction(self):
        engine = create_redaction_engine()
        key = """-----BEGIN RSA PRIVATE KEY-----
MIIBogIBAAJBALRiMLAhQvbMD...
-----END RSA PRIVATE KEY-----"""
        text = f"Key:\n{key}"
        result, report = engine.redact(text)
        
        assert "PRIVATE KEY" not in result
        assert "<PRIVATE_KEY_" in result

    def test_connection_string_redaction(self):
        engine = create_redaction_engine()
        text = "DATABASE_URL=postgres://user:pass@host:5432/db"
        result, report = engine.redact(text)
        
        assert "postgres://" not in result
        assert "<CONNECTION_STRING_" in result


class TestRedactionEngineConfig:
    """Tests for RedactionEngine with configuration."""

    def test_disabled_patterns(self):
        config = PatternConfig(disabled_patterns={"email"})
        engine = create_redaction_engine(config=config)
        text = "Email: test@example.com"
        result, report = engine.redact(text)
        
        assert "test@example.com" in result

    def test_min_priority(self):
        config = PatternConfig(min_priority=Priority.CRITICAL)
        engine = create_redaction_engine(config=config)
        
        text = "IP: 192.168.1.1"
        result, report = engine.redact(text)
        assert "192.168.1.1" in result

    def test_uuid_disabled_by_default(self):
        engine = create_redaction_engine()
        text = "ID: 550e8400-e29b-41d4-a716-446655440000"
        result, report = engine.redact(text)
        
        assert "550e8400" in result

    def test_uuid_enabled(self):
        config = PatternConfig(redact_uuids=True)
        engine = create_redaction_engine(config=config)
        text = "ID: 550e8400-e29b-41d4-a716-446655440000"
        result, report = engine.redact(text)
        
        assert "550e8400" not in result


class TestRedactionEngineVerification:
    """Tests for redaction verification."""

    def test_verify_clean_text(self):
        engine = create_redaction_engine()
        text = "No secrets here, just <API_KEY_1>"
        leaks = engine.verify_redaction(text)
        assert len(leaks) == 0

    def test_verify_leaked_secret(self):
        engine = create_redaction_engine()
        text = "Leaked: AKIAIOSFODNN7EXAMPLE"
        leaks = engine.verify_redaction(text)
        assert "aws_access_key" in leaks

    def test_get_salt_hash(self):
        engine = create_redaction_engine()
        hash1 = engine.get_salt_hash()
        assert len(hash1) == 64

    def test_get_redaction_summary(self):
        engine = create_redaction_engine()
        engine.redact("Key: AKIAIOSFODNN7EXAMPLE")
        summary = engine.get_redaction_summary()
        assert "AWS_KEY" in summary


class TestCreateRedactionEngine:
    """Tests for create_redaction_engine function."""

    def test_default_engine(self):
        engine = create_redaction_engine()
        assert engine is not None
        assert engine.tokenizer is not None
        assert engine.path_anonymizer is not None

    def test_with_project_root(self):
        engine = create_redaction_engine(project_root=Path("/my/project"))
        assert engine.path_anonymizer.project_root == Path("/my/project")

    def test_with_config(self):
        config = PatternConfig(redact_emails=False)
        engine = create_redaction_engine(config=config)
        assert engine.config.redact_emails is False
