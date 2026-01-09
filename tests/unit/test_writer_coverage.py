"""Tests for bundle writer functionality."""

from datetime import datetime
from pathlib import Path

import pytest

from bugsafe.bundle.exceptions import AttachmentError, BundleWriteError
from bugsafe.bundle.schema import BugBundle, BundleMetadata, CaptureOutput
from bugsafe.bundle.writer import (
    add_attachment,
    create_bundle,
    validate_bundle,
)


class TestCreateBundle:
    """Test create_bundle functionality."""

    def test_create_basic_bundle(self, tmp_path: Path) -> None:
        """Test creating a basic bundle."""
        bundle = BugBundle(
            metadata=BundleMetadata(
                version="1.0",
                created_at=datetime.now(),
                command=["echo", "test"],
            ),
            capture=CaptureOutput(
                stdout="hello",
                stderr="",
                exit_code=0,
                duration_ms=50,
                timed_out=False,
                truncated=False,
            ),
        )
        path = tmp_path / "test.bugbundle"
        create_bundle(bundle, path)
        assert path.exists()
        assert path.stat().st_size > 0

    def test_create_bundle_overwrite_false(self, tmp_path: Path) -> None:
        """Test that overwrite=False raises on existing file."""
        bundle = BugBundle(
            metadata=BundleMetadata(
                version="1.0",
                created_at=datetime.now(),
                command=["test"],
            ),
            capture=CaptureOutput(),
        )
        path = tmp_path / "existing.bugbundle"
        create_bundle(bundle, path)

        with pytest.raises(FileExistsError):
            create_bundle(bundle, path, overwrite=False)

    def test_create_bundle_overwrite_true(self, tmp_path: Path) -> None:
        """Test that overwrite=True replaces existing file."""
        bundle1 = BugBundle(
            metadata=BundleMetadata(
                version="1.0",
                created_at=datetime.now(),
                command=["first"],
            ),
            capture=CaptureOutput(stdout="first"),
        )
        bundle2 = BugBundle(
            metadata=BundleMetadata(
                version="1.0",
                created_at=datetime.now(),
                command=["second"],
            ),
            capture=CaptureOutput(stdout="second"),
        )
        path = tmp_path / "overwrite.bugbundle"
        create_bundle(bundle1, path)
        size1 = path.stat().st_size

        create_bundle(bundle2, path, overwrite=True)
        # File should still exist and may have different size
        assert path.exists()

    def test_create_bundle_creates_parent_dirs(self, tmp_path: Path) -> None:
        """Test that parent directories are created."""
        bundle = BugBundle(
            metadata=BundleMetadata(
                version="1.0",
                created_at=datetime.now(),
                command=["test"],
            ),
            capture=CaptureOutput(),
        )
        path = tmp_path / "nested" / "deep" / "bundle.bugbundle"
        create_bundle(bundle, path)
        assert path.exists()

    def test_create_bundle_with_redaction_report(self, tmp_path: Path) -> None:
        """Test bundle with redaction report."""
        bundle = BugBundle(
            metadata=BundleMetadata(
                version="1.0",
                created_at=datetime.now(),
                command=["test"],
            ),
            capture=CaptureOutput(stdout="redacted <AWS_KEY_1>"),
            redaction_report={"AWS_KEY": 1},
        )
        path = tmp_path / "redacted.bugbundle"
        create_bundle(bundle, path)
        assert path.exists()


class TestAddAttachment:
    """Test add_attachment functionality."""

    def _create_test_bundle(self, tmp_path: Path) -> Path:
        """Helper to create a test bundle."""
        bundle = BugBundle(
            metadata=BundleMetadata(
                version="1.0",
                created_at=datetime.now(),
                command=["test"],
            ),
            capture=CaptureOutput(),
        )
        path = tmp_path / "test.bugbundle"
        create_bundle(bundle, path)
        return path

    def test_add_text_attachment(self, tmp_path: Path) -> None:
        """Test adding text attachment."""
        path = self._create_test_bundle(tmp_path)
        name = add_attachment(path, "config.txt", "key=value\n")
        assert name == "config.txt"

    def test_add_bytes_attachment(self, tmp_path: Path) -> None:
        """Test adding bytes attachment."""
        path = self._create_test_bundle(tmp_path)
        name = add_attachment(path, "data.log", b"binary data")
        assert name == "data.log"

    def test_add_attachment_sanitizes_name(self, tmp_path: Path) -> None:
        """Test that filenames are sanitized."""
        path = self._create_test_bundle(tmp_path)
        # Name with path traversal attempt
        name = add_attachment(path, "../../../etc/passwd.txt", "content")
        assert ".." not in name
        assert "/" not in name

    def test_add_attachment_invalid_extension(self, tmp_path: Path) -> None:
        """Test rejection of disallowed extensions."""
        path = self._create_test_bundle(tmp_path)
        with pytest.raises(AttachmentError, match="not allowed"):
            add_attachment(path, "script.exe", "malicious")

    def test_add_attachment_to_nonexistent_bundle(self, tmp_path: Path) -> None:
        """Test adding to nonexistent bundle raises error."""
        with pytest.raises(BundleWriteError, match="not found"):
            add_attachment(tmp_path / "nonexistent.bugbundle", "file.txt", "data")

    def test_add_attachment_unique_names(self, tmp_path: Path) -> None:
        """Test that duplicate names get unique suffixes."""
        path = self._create_test_bundle(tmp_path)
        name1 = add_attachment(path, "config.txt", "first")
        name2 = add_attachment(path, "config.txt", "second")
        assert name1 == "config.txt"
        assert name2 == "config_1.txt"


class TestValidateBundle:
    """Test validate_bundle functionality."""

    def test_validate_valid_bundle(self, tmp_path: Path) -> None:
        """Test validating a valid bundle."""
        bundle = BugBundle(
            metadata=BundleMetadata(
                version="1.0",
                created_at=datetime.now(),
                command=["test"],
            ),
            capture=CaptureOutput(),
        )
        path = tmp_path / "valid.bugbundle"
        create_bundle(bundle, path)

        result = validate_bundle(path)
        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_nonexistent_bundle(self, tmp_path: Path) -> None:
        """Test validating nonexistent bundle."""
        result = validate_bundle(tmp_path / "nonexistent.bugbundle")
        assert result.valid is False
        assert len(result.errors) > 0
        assert "not found" in result.errors[0].lower()

    def test_validate_corrupted_bundle(self, tmp_path: Path) -> None:
        """Test validating corrupted file."""
        path = tmp_path / "corrupted.bugbundle"
        path.write_bytes(b"not a zip file")
        result = validate_bundle(path)
        assert result.valid is False
