"""Behavioral tests for bundle writer."""

from pathlib import Path

import pytest

from bugsafe.bundle.exceptions import AttachmentError, BundleWriteError
from bugsafe.bundle.reader import list_attachments, read_bundle, verify_integrity
from bugsafe.bundle.schema import BugBundle, BundleMetadata, CaptureOutput, Environment
from bugsafe.bundle.writer import (
    ValidationResult,
    add_attachment,
    create_bundle,
    validate_bundle,
)


class TestCreateBundleBehavior:
    """Test create_bundle intended behavior."""

    def test_creates_readable_bundle(self, tmp_path: Path) -> None:
        """Created bundle can be read back."""
        bundle = BugBundle(
            metadata=BundleMetadata(version="1.0"),
            capture=CaptureOutput(
                stdout="Hello, World!",
                stderr="Warning: test",
                exit_code=0,
                duration_ms=1234,
            ),
        )
        path = tmp_path / "test.bugbundle"
        create_bundle(bundle, path)

        loaded = read_bundle(path)

        assert loaded.capture.stdout == "Hello, World!"
        assert loaded.capture.stderr == "Warning: test"
        assert loaded.capture.exit_code == 0

    def test_creates_valid_bundle(self, tmp_path: Path) -> None:
        """Created bundle passes integrity check."""
        bundle = BugBundle(
            metadata=BundleMetadata(version="1.0"),
            capture=CaptureOutput(stdout="test"),
        )
        path = tmp_path / "valid.bugbundle"
        create_bundle(bundle, path)

        assert verify_integrity(path) is True

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        """Parent directories are created if missing."""
        bundle = BugBundle(
            metadata=BundleMetadata(version="1.0"),
            capture=CaptureOutput(),
        )
        path = tmp_path / "nested" / "deep" / "bundle.bugbundle"
        create_bundle(bundle, path)

        assert path.exists()

    def test_overwrites_by_default(self, tmp_path: Path) -> None:
        """Existing file is overwritten by default."""
        bundle1 = BugBundle(
            metadata=BundleMetadata(version="1.0"),
            capture=CaptureOutput(stdout="first"),
        )
        bundle2 = BugBundle(
            metadata=BundleMetadata(version="1.0"),
            capture=CaptureOutput(stdout="second"),
        )
        path = tmp_path / "overwrite.bugbundle"

        create_bundle(bundle1, path)
        create_bundle(bundle2, path)

        loaded = read_bundle(path)
        assert loaded.capture.stdout == "second"

    def test_raises_when_overwrite_disabled(self, tmp_path: Path) -> None:
        """FileExistsError raised when overwrite=False."""
        bundle = BugBundle(
            metadata=BundleMetadata(version="1.0"),
            capture=CaptureOutput(),
        )
        path = tmp_path / "existing.bugbundle"

        create_bundle(bundle, path)

        with pytest.raises(FileExistsError):
            create_bundle(bundle, path, overwrite=False)

    def test_preserves_redaction_report(self, tmp_path: Path) -> None:
        """Redaction report is preserved in bundle."""
        bundle = BugBundle(
            metadata=BundleMetadata(version="1.0"),
            capture=CaptureOutput(stdout="redacted <AWS_KEY_1>"),
            redaction_report={"AWS_KEY": 1, "GITHUB_TOKEN": 2},
        )
        path = tmp_path / "redacted.bugbundle"
        create_bundle(bundle, path)

        loaded = read_bundle(path)
        assert loaded.redaction_report["AWS_KEY"] == 1
        assert loaded.redaction_report["GITHUB_TOKEN"] == 2

    def test_preserves_environment(self, tmp_path: Path) -> None:
        """Environment data is preserved."""
        bundle = BugBundle(
            metadata=BundleMetadata(version="1.0"),
            capture=CaptureOutput(),
            environment=Environment(
                python_version="3.10.0",
                platform="linux",
                cwd="/project",
            ),
        )
        path = tmp_path / "with_env.bugbundle"
        create_bundle(bundle, path)

        loaded = read_bundle(path)
        assert loaded.environment is not None
        assert loaded.environment.python_version == "3.10.0"


class TestAddAttachmentBehavior:
    """Test add_attachment intended behavior."""

    def _create_bundle(self, tmp_path: Path) -> Path:
        """Helper to create a test bundle."""
        bundle = BugBundle(
            metadata=BundleMetadata(version="1.0"),
            capture=CaptureOutput(),
        )
        path = tmp_path / "test.bugbundle"
        create_bundle(bundle, path)
        return path

    def test_adds_text_attachment(self, tmp_path: Path) -> None:
        """Text attachment is added and readable."""
        path = self._create_bundle(tmp_path)

        name = add_attachment(path, "config.txt", "key=value")

        assert name == "config.txt"
        attachments = list_attachments(path)
        assert "config.txt" in attachments

    def test_adds_bytes_attachment(self, tmp_path: Path) -> None:
        """Binary attachment is added."""
        path = self._create_bundle(tmp_path)

        name = add_attachment(path, "data.log", b"binary\x00data")

        assert name == "data.log"

    def test_sanitizes_dangerous_filenames(self, tmp_path: Path) -> None:
        """Dangerous filenames are sanitized."""
        path = self._create_bundle(tmp_path)

        # Path traversal attempt
        name = add_attachment(path, "../../../etc/passwd.txt", "content")

        assert ".." not in name
        assert "/" not in name
        assert name.endswith(".txt")

    def test_sanitizes_url_encoded_names(self, tmp_path: Path) -> None:
        """URL-encoded filenames are sanitized."""
        path = self._create_bundle(tmp_path)

        name = add_attachment(path, "..%2F..%2Fetc%2Fpasswd.txt", "content")

        assert ".." not in name
        assert "%" not in name

    def test_generates_unique_names(self, tmp_path: Path) -> None:
        """Duplicate names get unique suffixes."""
        path = self._create_bundle(tmp_path)

        name1 = add_attachment(path, "file.txt", "first")
        name2 = add_attachment(path, "file.txt", "second")
        name3 = add_attachment(path, "file.txt", "third")

        assert name1 == "file.txt"
        assert name2 == "file_1.txt"
        assert name3 == "file_2.txt"

    def test_rejects_disallowed_extensions(self, tmp_path: Path) -> None:
        """Disallowed file extensions are rejected."""
        path = self._create_bundle(tmp_path)

        with pytest.raises(AttachmentError, match="not allowed"):
            add_attachment(path, "script.exe", "malicious")

        with pytest.raises(AttachmentError, match="not allowed"):
            add_attachment(path, "binary.dll", "malicious")

    def test_allows_safe_extensions(self, tmp_path: Path) -> None:
        """Safe extensions are allowed."""
        path = self._create_bundle(tmp_path)

        # All these should work
        add_attachment(path, "config.txt", "text")
        add_attachment(path, "data.json", '{"key": "value"}')
        add_attachment(path, "settings.yaml", "key: value")
        add_attachment(path, "readme.md", "# README")

        attachments = list_attachments(path)
        assert len(attachments) == 4

    def test_raises_for_nonexistent_bundle(self, tmp_path: Path) -> None:
        """Adding to nonexistent bundle raises error."""
        with pytest.raises(BundleWriteError, match="not found"):
            add_attachment(
                tmp_path / "nonexistent.bugbundle",
                "file.txt",
                "content",
            )


class TestValidateBundleBehavior:
    """Test validate_bundle intended behavior."""

    def test_valid_bundle_passes(self, tmp_path: Path) -> None:
        """Valid bundle passes validation."""
        bundle = BugBundle(
            metadata=BundleMetadata(version="1.0"),
            capture=CaptureOutput(stdout="test"),
        )
        path = tmp_path / "valid.bugbundle"
        create_bundle(bundle, path)

        result = validate_bundle(path)

        assert result.valid is True
        assert len(result.errors) == 0

    def test_nonexistent_bundle_fails(self, tmp_path: Path) -> None:
        """Nonexistent bundle fails validation."""
        result = validate_bundle(tmp_path / "nonexistent.bugbundle")

        assert result.valid is False
        assert len(result.errors) > 0
        assert any("not found" in e.lower() for e in result.errors)

    def test_corrupt_bundle_fails(self, tmp_path: Path) -> None:
        """Corrupt bundle fails validation."""
        path = tmp_path / "corrupt.bugbundle"
        path.write_bytes(b"not a zip")

        result = validate_bundle(path)

        assert result.valid is False

    def test_returns_validation_result(self, tmp_path: Path) -> None:
        """Returns proper ValidationResult object."""
        bundle = BugBundle(
            metadata=BundleMetadata(version="1.0"),
            capture=CaptureOutput(),
        )
        path = tmp_path / "test.bugbundle"
        create_bundle(bundle, path)

        result = validate_bundle(path)

        assert isinstance(result, ValidationResult)
        assert isinstance(result.valid, bool)
        assert isinstance(result.errors, list)
        assert isinstance(result.warnings, list)


class TestBundleSizeLimits:
    """Test bundle size limit enforcement."""

    def test_normal_bundle_succeeds(self, tmp_path: Path) -> None:
        """Bundle under size limit succeeds."""
        bundle = BugBundle(
            metadata=BundleMetadata(version="1.0"),
            capture=CaptureOutput(stdout="x" * 1000),  # 1KB
        )
        path = tmp_path / "small.bugbundle"

        create_bundle(bundle, path)

        assert path.exists()


class TestFilenameSanitization:
    """Test filename sanitization edge cases."""

    def test_no_extension_rejected(self, tmp_path: Path) -> None:
        """Files without allowed extension are rejected."""
        bundle = BugBundle(
            metadata=BundleMetadata(version="1.0"),
            capture=CaptureOutput(),
        )
        path = tmp_path / "test.bugbundle"
        create_bundle(bundle, path)

        # Files without proper extension should be rejected
        with pytest.raises(AttachmentError, match="not allowed"):
            add_attachment(path, "noextension", "content")

    def test_special_chars_removed(self, tmp_path: Path) -> None:
        """Special characters are removed from filenames."""
        bundle = BugBundle(
            metadata=BundleMetadata(version="1.0"),
            capture=CaptureOutput(),
        )
        path = tmp_path / "test.bugbundle"
        create_bundle(bundle, path)

        name = add_attachment(path, 'file<>:"\\|?*.txt', "content")

        # Should not contain any of the special chars
        for char in '<>:"\\|?*':
            assert char not in name
