"""Functional tests for bundle writer - verifies correct serialization."""

from datetime import datetime, timezone

from bugsafe.bundle.reader import read_bundle
from bugsafe.bundle.schema import (
    BugBundle,
    BundleMetadata,
    CaptureOutput,
    Environment,
    Frame,
    PackageInfo,
    Traceback,
)
from bugsafe.bundle.writer import create_bundle


class TestBundleCreation:
    """Functional tests for basic bundle creation."""

    def test_creates_valid_bundle_file(self, tmp_path):
        """create_bundle should produce a readable bundle file."""
        bundle = BugBundle(
            metadata=BundleMetadata(
                created_at=datetime.now(timezone.utc),
                bugsafe_version="0.1.0",
                redaction_salt_hash="test",
            ),
            capture=CaptureOutput(
                stdout="output text",
                stderr="error text",
                exit_code=0,
                command=["python", "script.py"],
            ),
        )

        path = tmp_path / "test.bugbundle"
        create_bundle(bundle, path)

        assert path.exists(), "Bundle file should be created"
        loaded = read_bundle(path)
        assert loaded.capture.stdout == "output text", "Content should be readable"


class TestLargeContent:
    """Functional tests for handling large content."""

    def test_large_output_preserved_exactly(self, tmp_path):
        """Large stdout/stderr must be preserved without truncation."""
        large_content = "x" * 10000
        bundle = BugBundle(
            metadata=BundleMetadata(
                created_at=datetime.now(timezone.utc),
                bugsafe_version="0.1.0",
                redaction_salt_hash="test",
            ),
            capture=CaptureOutput(
                stdout=large_content,
                stderr=large_content,
                exit_code=0,
                command=["test"],
            ),
        )

        path = tmp_path / "test.bugbundle"
        create_bundle(bundle, path)
        loaded = read_bundle(path)

        assert len(loaded.capture.stdout) == 10000, "Large content must be preserved"
        assert loaded.capture.stdout == large_content, "Content must match exactly"


class TestUnicodeContent:
    """Functional tests for unicode handling."""

    def test_unicode_characters_preserved(self, tmp_path):
        """Unicode characters must survive write/read cycle."""
        unicode_text = "Hello 世界 🌍 émojis"
        bundle = BugBundle(
            metadata=BundleMetadata(
                created_at=datetime.now(timezone.utc),
                bugsafe_version="0.1.0",
                redaction_salt_hash="test",
            ),
            capture=CaptureOutput(
                stdout=unicode_text,
                stderr="エラー",
                exit_code=0,
                command=["test"],
            ),
        )

        path = tmp_path / "test.bugbundle"
        create_bundle(bundle, path)
        loaded = read_bundle(path)

        assert "世界" in loaded.capture.stdout, "Chinese characters must be preserved"
        assert "🌍" in loaded.capture.stdout, "Emoji must be preserved"
        assert "エラー" in loaded.capture.stderr, (
            "Japanese characters must be preserved"
        )


class TestOptionalFields:
    """Functional tests for optional bundle fields."""

    def test_traceback_field_preserved(self, tmp_path):
        """Optional traceback field must be correctly serialized."""
        bundle = BugBundle(
            metadata=BundleMetadata(
                created_at=datetime.now(timezone.utc),
                bugsafe_version="0.1.0",
                redaction_salt_hash="test",
            ),
            capture=CaptureOutput(
                stdout="",
                stderr="error",
                exit_code=1,
                command=["test"],
            ),
            traceback=Traceback(
                exception_type="ValueError",
                message="test error",
                frames=[Frame(file="test.py", line=10, function="test")],
            ),
        )

        path = tmp_path / "test.bugbundle"
        create_bundle(bundle, path)
        loaded = read_bundle(path)

        assert loaded.traceback is not None, "Traceback should be preserved"
        assert loaded.traceback.exception_type == "ValueError"

    def test_environment_field_preserved(self, tmp_path):
        """Optional environment field must be correctly serialized."""
        bundle = BugBundle(
            metadata=BundleMetadata(
                created_at=datetime.now(timezone.utc),
                bugsafe_version="0.1.0",
                redaction_salt_hash="test",
            ),
            capture=CaptureOutput(
                stdout="",
                stderr="",
                exit_code=0,
                command=["test"],
            ),
            environment=Environment(
                python_version="3.10.0",
                python_executable="/usr/bin/python",
                platform="linux",
                packages=[PackageInfo(name="pytest", version="8.0.0")],
                env_vars={"PATH": "/usr/bin"},
                cwd="/home/user",
            ),
        )

        path = tmp_path / "test.bugbundle"
        create_bundle(bundle, path)
        loaded = read_bundle(path)

        assert loaded.environment is not None, "Environment should be preserved"
        assert loaded.environment.python_version == "3.10.0"
        assert loaded.environment.packages[0].name == "pytest"

    def test_redaction_report_preserved(self, tmp_path):
        """Redaction report counts must be exactly preserved."""
        expected_report = {"API_KEY": 3, "PASSWORD": 1}
        bundle = BugBundle(
            metadata=BundleMetadata(
                created_at=datetime.now(timezone.utc),
                bugsafe_version="0.1.0",
                redaction_salt_hash="test",
            ),
            capture=CaptureOutput(
                stdout="redacted",
                stderr="",
                exit_code=0,
                command=["test"],
            ),
            redaction_report=expected_report,
        )

        path = tmp_path / "test.bugbundle"
        create_bundle(bundle, path)
        loaded = read_bundle(path)

        assert loaded.redaction_report == expected_report, "Report counts must match"
