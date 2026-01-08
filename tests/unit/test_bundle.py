"""Unit tests for bundle module."""

import json
import zipfile
from datetime import datetime
from pathlib import Path

import pytest

from bugsafe.bundle.reader import (
    AttachmentNotFoundError,
    BundleCorruptError,
    BundleNotFoundError,
    BundleSchemaError,
    SecurityError,
    get_attachment,
    list_attachments,
    read_bundle,
    verify_integrity,
)
from bugsafe.bundle.schema import (
    BUNDLE_VERSION,
    BugBundle,
    BundleMetadata,
    CaptureOutput,
    Environment,
    Frame,
    GitInfo,
    PackageInfo,
    Traceback,
)
from bugsafe.bundle.writer import (
    AttachmentError,
    BundleSizeError,
    BundleWriteError,
    ValidationResult,
    add_attachment,
    create_bundle,
    validate_bundle,
)


class TestBundleSchema:
    """Tests for bundle schema models."""

    def test_frame_creation(self):
        frame = Frame(file="test.py", line=10, function="main", code="print()")
        assert frame.file == "test.py"
        assert frame.line == 10
        assert frame.function == "main"

    def test_traceback_creation(self):
        frames = [Frame(file="test.py", line=10)]
        tb = Traceback(
            exception_type="ValueError",
            message="test error",
            frames=frames,
        )
        assert tb.exception_type == "ValueError"
        assert len(tb.frames) == 1

    def test_capture_output_defaults(self):
        capture = CaptureOutput()
        assert capture.stdout == ""
        assert capture.stderr == ""
        assert capture.exit_code == 0

    def test_environment_creation(self):
        env = Environment(
            python_version="3.10.0",
            platform="Linux",
        )
        assert env.python_version == "3.10.0"

    def test_bundle_metadata_defaults(self):
        meta = BundleMetadata()
        assert meta.version == BUNDLE_VERSION
        assert isinstance(meta.created_at, datetime)

    def test_bug_bundle_creation(self):
        bundle = BugBundle(
            capture=CaptureOutput(
                stdout="output",
                stderr="error",
                exit_code=1,
                command=["python", "test.py"],
            ),
        )
        assert bundle.capture.stdout == "output"
        assert bundle.capture.exit_code == 1

    def test_bundle_to_dict(self):
        bundle = BugBundle()
        data = bundle.to_dict()
        assert "metadata" in data
        assert "capture" in data

    def test_bundle_from_dict(self):
        data = {
            "metadata": {"version": "1.0"},
            "capture": {"stdout": "test", "exit_code": 0},
        }
        bundle = BugBundle.from_dict(data)
        assert bundle.capture.stdout == "test"


class TestBundleWriter:
    """Tests for bundle writer."""

    def test_create_bundle(self, tmp_path: Path):
        bundle = BugBundle(
            capture=CaptureOutput(
                stdout="Hello, World!",
                stderr="",
                exit_code=0,
                command=["echo", "Hello"],
            ),
        )
        bundle_path = tmp_path / "test.bugbundle"
        create_bundle(bundle, bundle_path)

        assert bundle_path.exists()
        assert zipfile.is_zipfile(bundle_path)

    def test_create_bundle_contents(self, tmp_path: Path):
        bundle = BugBundle(
            capture=CaptureOutput(stdout="test output"),
        )
        bundle_path = tmp_path / "test.bugbundle"
        create_bundle(bundle, bundle_path)

        with zipfile.ZipFile(bundle_path, "r") as zf:
            assert "manifest.json" in zf.namelist()
            assert "checksum.sha256" in zf.namelist()
            assert "stdout.txt" in zf.namelist()

    def test_create_bundle_overwrite(self, tmp_path: Path):
        bundle_path = tmp_path / "test.bugbundle"
        bundle = BugBundle()

        create_bundle(bundle, bundle_path)
        create_bundle(bundle, bundle_path, overwrite=True)

        assert bundle_path.exists()

    def test_create_bundle_no_overwrite(self, tmp_path: Path):
        bundle_path = tmp_path / "test.bugbundle"
        bundle = BugBundle()

        create_bundle(bundle, bundle_path)

        with pytest.raises(FileExistsError):
            create_bundle(bundle, bundle_path, overwrite=False)

    def test_create_bundle_creates_parent_dirs(self, tmp_path: Path):
        bundle_path = tmp_path / "nested" / "dir" / "test.bugbundle"
        bundle = BugBundle()

        create_bundle(bundle, bundle_path)
        assert bundle_path.exists()

    def test_add_attachment(self, tmp_path: Path):
        bundle_path = tmp_path / "test.bugbundle"
        create_bundle(BugBundle(), bundle_path)

        final_name = add_attachment(bundle_path, "config.txt", "key=value")

        assert final_name == "config.txt"
        attachments = list_attachments(bundle_path)
        assert "config.txt" in attachments

    def test_add_attachment_unique_name(self, tmp_path: Path):
        bundle_path = tmp_path / "test.bugbundle"
        create_bundle(BugBundle(), bundle_path)

        add_attachment(bundle_path, "config.txt", "content1")
        final_name = add_attachment(bundle_path, "config.txt", "content2")

        assert final_name == "config_1.txt"

    def test_add_attachment_invalid_extension(self, tmp_path: Path):
        bundle_path = tmp_path / "test.bugbundle"
        create_bundle(BugBundle(), bundle_path)

        with pytest.raises(AttachmentError, match="Extension"):
            add_attachment(bundle_path, "file.exe", "content")

    def test_validate_bundle_valid(self, tmp_path: Path):
        bundle_path = tmp_path / "test.bugbundle"
        create_bundle(BugBundle(), bundle_path)

        result = validate_bundle(bundle_path)
        assert result.valid
        assert len(result.errors) == 0

    def test_validate_bundle_not_found(self, tmp_path: Path):
        result = validate_bundle(tmp_path / "nonexistent.bugbundle")
        assert not result.valid
        assert any("not found" in e for e in result.errors)

    def test_validate_bundle_invalid_zip(self, tmp_path: Path):
        bundle_path = tmp_path / "test.bugbundle"
        bundle_path.write_text("not a zip file")

        result = validate_bundle(bundle_path)
        assert not result.valid


class TestBundleReader:
    """Tests for bundle reader."""

    def test_read_bundle(self, tmp_path: Path):
        original = BugBundle(
            capture=CaptureOutput(
                stdout="test output",
                stderr="test error",
                exit_code=42,
                command=["test", "cmd"],
            ),
        )
        bundle_path = tmp_path / "test.bugbundle"
        create_bundle(original, bundle_path)

        loaded = read_bundle(bundle_path)
        assert loaded.capture.stdout == "test output"
        assert loaded.capture.exit_code == 42

    def test_read_bundle_not_found(self, tmp_path: Path):
        with pytest.raises(BundleNotFoundError):
            read_bundle(tmp_path / "nonexistent.bugbundle")

    def test_read_bundle_invalid_zip(self, tmp_path: Path):
        bundle_path = tmp_path / "test.bugbundle"
        bundle_path.write_text("not a zip")

        with pytest.raises(BundleCorruptError):
            read_bundle(bundle_path)

    def test_read_bundle_missing_manifest(self, tmp_path: Path):
        bundle_path = tmp_path / "test.bugbundle"
        with zipfile.ZipFile(bundle_path, "w") as zf:
            zf.writestr("other.txt", "content")

        with pytest.raises(BundleCorruptError, match="manifest"):
            read_bundle(bundle_path)

    def test_read_bundle_invalid_json(self, tmp_path: Path):
        bundle_path = tmp_path / "test.bugbundle"
        with zipfile.ZipFile(bundle_path, "w") as zf:
            zf.writestr("manifest.json", "not valid json")

        with pytest.raises(Exception):
            read_bundle(bundle_path)

    def test_read_bundle_path_traversal(self, tmp_path: Path):
        bundle_path = tmp_path / "test.bugbundle"
        with zipfile.ZipFile(bundle_path, "w") as zf:
            zf.writestr("../evil.txt", "malicious")
            zf.writestr("manifest.json", "{}")

        with pytest.raises(SecurityError):
            read_bundle(bundle_path)

    def test_list_attachments(self, tmp_path: Path):
        bundle_path = tmp_path / "test.bugbundle"
        create_bundle(BugBundle(), bundle_path)
        add_attachment(bundle_path, "file1.txt", "content1")
        add_attachment(bundle_path, "file2.txt", "content2")

        attachments = list_attachments(bundle_path)
        assert len(attachments) == 2
        assert "file1.txt" in attachments
        assert "file2.txt" in attachments

    def test_list_attachments_empty(self, tmp_path: Path):
        bundle_path = tmp_path / "test.bugbundle"
        create_bundle(BugBundle(), bundle_path)

        attachments = list_attachments(bundle_path)
        assert attachments == []

    def test_get_attachment(self, tmp_path: Path):
        bundle_path = tmp_path / "test.bugbundle"
        create_bundle(BugBundle(), bundle_path)
        add_attachment(bundle_path, "config.txt", "key=value")

        content = get_attachment(bundle_path, "config.txt")
        assert content == "key=value"

    def test_get_attachment_not_found(self, tmp_path: Path):
        bundle_path = tmp_path / "test.bugbundle"
        create_bundle(BugBundle(), bundle_path)

        with pytest.raises(AttachmentNotFoundError):
            get_attachment(bundle_path, "nonexistent.txt")

    def test_verify_integrity_valid(self, tmp_path: Path):
        bundle_path = tmp_path / "test.bugbundle"
        create_bundle(BugBundle(), bundle_path)

        assert verify_integrity(bundle_path) is True

    def test_verify_integrity_corrupted(self, tmp_path: Path):
        bundle_path = tmp_path / "test.bugbundle"
        create_bundle(BugBundle(), bundle_path)

        with zipfile.ZipFile(bundle_path, "a") as zf:
            zf.writestr("manifest.json", '{"corrupted": true}')

        assert verify_integrity(bundle_path) is False


class TestRoundTrip:
    """Tests for round-trip serialization."""

    def test_simple_roundtrip(self, tmp_path: Path):
        original = BugBundle(
            capture=CaptureOutput(
                stdout="Hello",
                stderr="Error",
                exit_code=1,
                duration_ms=100,
                command=["python", "-c", "print()"],
            ),
            redaction_report={"API_KEY": 2, "EMAIL": 1},
        )

        bundle_path = tmp_path / "test.bugbundle"
        create_bundle(original, bundle_path)
        loaded = read_bundle(bundle_path)

        assert loaded.capture.stdout == original.capture.stdout
        assert loaded.capture.stderr == original.capture.stderr
        assert loaded.capture.exit_code == original.capture.exit_code
        assert loaded.redaction_report == original.redaction_report

    def test_roundtrip_with_traceback(self, tmp_path: Path):
        original = BugBundle(
            traceback=Traceback(
                exception_type="ValueError",
                message="test error",
                frames=[
                    Frame(file="test.py", line=10, function="main"),
                    Frame(file="test.py", line=5, function="helper"),
                ],
            ),
        )

        bundle_path = tmp_path / "test.bugbundle"
        create_bundle(original, bundle_path)
        loaded = read_bundle(bundle_path)

        assert loaded.traceback is not None
        assert loaded.traceback.exception_type == "ValueError"
        assert len(loaded.traceback.frames) == 2

    def test_roundtrip_with_environment(self, tmp_path: Path):
        original = BugBundle(
            environment=Environment(
                python_version="3.10.0",
                platform="Linux-5.4.0",
                packages=[
                    PackageInfo(name="pytest", version="8.0.0"),
                ],
                env_vars={"PATH": "/usr/bin"},
                git=GitInfo(ref="abc123", branch="main", dirty=False),
            ),
        )

        bundle_path = tmp_path / "test.bugbundle"
        create_bundle(original, bundle_path)
        loaded = read_bundle(bundle_path)

        assert loaded.environment is not None
        assert loaded.environment.python_version == "3.10.0"
        assert len(loaded.environment.packages) == 1
        assert loaded.environment.git is not None
        assert loaded.environment.git.ref == "abc123"

    def test_roundtrip_with_attachments(self, tmp_path: Path):
        bundle_path = tmp_path / "test.bugbundle"
        create_bundle(BugBundle(), bundle_path)

        add_attachment(bundle_path, "config.yaml", "key: value")
        add_attachment(bundle_path, "requirements.txt", "pytest>=8.0")

        attachments = list_attachments(bundle_path)
        assert len(attachments) == 2

        config = get_attachment(bundle_path, "config.yaml")
        assert config == "key: value"


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_bundle(self, tmp_path: Path):
        bundle_path = tmp_path / "test.bugbundle"
        create_bundle(BugBundle(), bundle_path)
        loaded = read_bundle(bundle_path)

        assert loaded.capture.stdout == ""
        assert loaded.traceback is None

    def test_unicode_content(self, tmp_path: Path):
        original = BugBundle(
            capture=CaptureOutput(
                stdout="Hello 世界 🎉",
                stderr="エラー",
            ),
        )

        bundle_path = tmp_path / "test.bugbundle"
        create_bundle(original, bundle_path)
        loaded = read_bundle(bundle_path)

        assert "世界" in loaded.capture.stdout
        assert "🎉" in loaded.capture.stdout
        assert "エラー" in loaded.capture.stderr

    def test_large_output(self, tmp_path: Path):
        large_content = "x" * 100000
        original = BugBundle(
            capture=CaptureOutput(stdout=large_content),
        )

        bundle_path = tmp_path / "test.bugbundle"
        create_bundle(original, bundle_path)
        loaded = read_bundle(bundle_path)

        assert len(loaded.capture.stdout) == 100000

    def test_special_characters_in_attachment_name(self, tmp_path: Path):
        bundle_path = tmp_path / "test.bugbundle"
        create_bundle(BugBundle(), bundle_path)

        final_name = add_attachment(
            bundle_path, "file with spaces.txt", "content"
        )
        assert " " not in final_name

    def test_path_traversal_in_attachment(self, tmp_path: Path):
        bundle_path = tmp_path / "test.bugbundle"
        create_bundle(BugBundle(), bundle_path)

        with pytest.raises(SecurityError):
            get_attachment(bundle_path, "../etc/passwd")
