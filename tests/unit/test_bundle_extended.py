"""Functional tests for bundle read/write - verifies data integrity."""

import zipfile
from datetime import datetime, timezone

import pytest

from bugsafe.bundle.reader import (
    BundleCorruptError,
    BundleNotFoundError,
    BundleParseError,
    BundleSchemaError,
    read_bundle,
)
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


class TestBundleWithTraceback:
    """Functional tests for bundles containing traceback information."""

    def test_traceback_preserved_through_write_read_cycle(self, tmp_path):
        """Traceback data must survive write/read cycle intact."""
        bundle = BugBundle(
            metadata=BundleMetadata(
                created_at=datetime.now(timezone.utc),
                bugsafe_version="0.1.0",
                redaction_salt_hash="test",
            ),
            capture=CaptureOutput(
                stdout="output",
                stderr="error",
                exit_code=1,
                duration_ms=100,
                command=["python", "script.py"],
                timed_out=False,
                truncated=False,
            ),
            traceback=Traceback(
                exception_type="ValueError",
                message="test error",
                frames=[
                    Frame(
                        file="test.py",
                        line=10,
                        function="test_func",
                        code="raise ValueError('test')",
                    )
                ],
            ),
        )

        bundle_path = tmp_path / "test.bugbundle"
        create_bundle(bundle, bundle_path)
        loaded = read_bundle(bundle_path)

        assert loaded.traceback is not None, "Traceback should be preserved"
        assert loaded.traceback.exception_type == "ValueError"
        assert loaded.traceback.message == "test error"
        assert len(loaded.traceback.frames) == 1
        assert loaded.traceback.frames[0].line == 10


class TestBundleWithEnvironment:
    """Functional tests for bundles containing environment information."""

    def test_environment_preserved_through_write_read_cycle(self, tmp_path):
        """Environment data must survive write/read cycle intact."""
        bundle = BugBundle(
            metadata=BundleMetadata(
                created_at=datetime.now(timezone.utc),
                bugsafe_version="0.1.0",
                redaction_salt_hash="test",
            ),
            capture=CaptureOutput(
                stdout="output",
                stderr="",
                exit_code=0,
                duration_ms=50,
                command=["test"],
                timed_out=False,
                truncated=False,
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

        bundle_path = tmp_path / "test.bugbundle"
        create_bundle(bundle, bundle_path)
        loaded = read_bundle(bundle_path)

        assert loaded.environment is not None, "Environment should be preserved"
        assert loaded.environment.python_version == "3.10.0"
        assert loaded.environment.platform == "linux"
        assert len(loaded.environment.packages) == 1
        assert loaded.environment.packages[0].name == "pytest"


class TestBundleWithRedactionReport:
    """Functional tests for bundles containing redaction reports."""

    def test_redaction_report_preserved(self, tmp_path):
        """Redaction report counts must be preserved exactly."""
        original_report = {"API_KEY": 2, "TOKEN": 1}
        bundle = BugBundle(
            metadata=BundleMetadata(
                created_at=datetime.now(timezone.utc),
                bugsafe_version="0.1.0",
                redaction_salt_hash="test",
            ),
            capture=CaptureOutput(
                stdout="redacted output",
                stderr="",
                exit_code=0,
                duration_ms=50,
                command=["test"],
                timed_out=False,
                truncated=False,
            ),
            redaction_report=original_report,
        )

        bundle_path = tmp_path / "test.bugbundle"
        create_bundle(bundle, bundle_path)
        loaded = read_bundle(bundle_path)

        assert loaded.redaction_report == original_report, "Redaction report must match"


class TestMalformedBundles:
    """Functional tests for error handling with malformed bundles."""

    def test_missing_manifest_raises_error(self, tmp_path):
        """Bundle without manifest.json should fail with clear error."""
        bundle_path = tmp_path / "test.bugbundle"

        with zipfile.ZipFile(bundle_path, "w") as zf:
            zf.writestr("other.txt", "content")

        with pytest.raises((BundleCorruptError, BundleParseError)):
            read_bundle(bundle_path)

    def test_empty_manifest_raises_error(self, tmp_path):
        """Bundle with empty manifest should fail with clear error."""
        bundle_path = tmp_path / "test.bugbundle"

        with zipfile.ZipFile(bundle_path, "w") as zf:
            zf.writestr("manifest.json", "")

        with pytest.raises((BundleParseError, BundleSchemaError)):
            read_bundle(bundle_path)

    def test_invalid_json_raises_parse_error(self, tmp_path):
        """Bundle with invalid JSON should raise BundleParseError."""
        bundle_path = tmp_path / "test.bugbundle"

        with zipfile.ZipFile(bundle_path, "w") as zf:
            zf.writestr("manifest.json", "not valid json {{{")

        with pytest.raises(BundleParseError):
            read_bundle(bundle_path)

    def test_nonexistent_file_raises_not_found_error(self, tmp_path):
        """Reading nonexistent bundle should raise BundleNotFoundError."""
        bundle_path = tmp_path / "nonexistent.bugbundle"

        with pytest.raises(BundleNotFoundError):
            read_bundle(bundle_path)


class TestBundleRoundTrip:
    """Tests for bundle round-trip consistency."""

    def test_roundtrip_preserves_capture_fields(self, tmp_path):
        """Round-trip preserves capture output fields."""
        original = BugBundle(
            metadata=BundleMetadata(
                created_at=datetime(2026, 1, 1, 12, 0, 0),
                bugsafe_version="0.1.0",
                redaction_salt_hash="abc123",
            ),
            capture=CaptureOutput(
                stdout="test stdout",
                stderr="test stderr",
                exit_code=42,
                duration_ms=1234,
                command=["python", "-c", "print('hello')"],
                timed_out=True,
                truncated=True,
            ),
        )

        bundle_path = tmp_path / "roundtrip.bugbundle"
        create_bundle(original, bundle_path)
        loaded = read_bundle(bundle_path)

        assert loaded.capture.stdout == original.capture.stdout
        assert loaded.capture.stderr == original.capture.stderr
        assert loaded.capture.exit_code == original.capture.exit_code
        assert loaded.capture.timed_out == original.capture.timed_out
        assert loaded.capture.truncated == original.capture.truncated
