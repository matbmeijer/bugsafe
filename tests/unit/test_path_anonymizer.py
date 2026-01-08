"""Unit tests for redact/path_anonymizer.py."""

import sys
from pathlib import Path

from bugsafe.redact.path_anonymizer import (
    PathAnonymizer,
    create_default_anonymizer,
)


class TestPathAnonymizer:
    """Tests for PathAnonymizer class."""

    def test_anonymize_home_directory(self):
        anonymizer = PathAnonymizer(home_dir="/Users/alice")
        result = anonymizer.anonymize("/Users/alice/project/file.py")
        assert result == "~/project/file.py"

    def test_anonymize_home_linux(self):
        anonymizer = PathAnonymizer(home_dir="/home/alice")
        result = anonymizer.anonymize("/home/alice/project/file.py")
        assert result == "~/project/file.py"

    def test_anonymize_username_in_path(self):
        anonymizer = PathAnonymizer(
            home_dir="/other/path",
            username="alice",
        )
        result = anonymizer.anonymize("/home/alice/project/file.py")
        assert "<USER>" in result
        assert "alice" not in result

    def test_anonymize_project_root(self):
        if sys.platform == "win32":
            anonymizer = PathAnonymizer(
                project_root=Path("C:/Users/alice/myproject"),
                home_dir="C:/Users/alice",
            )
            result = anonymizer.anonymize("C:/Users/alice/myproject/src/main.py")
        else:
            anonymizer = PathAnonymizer(
                project_root=Path("/Users/alice/myproject"),
                home_dir="/Users/alice",
            )
            result = anonymizer.anonymize("/Users/alice/myproject/src/main.py")
        assert result == "<PROJECT>/src/main.py"

    def test_anonymize_temp_macos(self):
        anonymizer = PathAnonymizer()
        result = anonymizer.anonymize("/var/folders/abc/xyz/T/pytest-123/test.py")
        assert "<TMPDIR>" in result

    def test_anonymize_temp_linux(self):
        anonymizer = PathAnonymizer()
        result = anonymizer.anonymize("/tmp/pytest-of-alice/test.py")
        assert "<TMPDIR>" in result

    def test_anonymize_site_packages(self):
        anonymizer = PathAnonymizer()
        result = anonymizer.anonymize(
            "/usr/lib/python3.10/site-packages/requests/api.py"
        )
        assert "<SITE_PACKAGES>" in result

    def test_anonymize_venv(self):
        anonymizer = PathAnonymizer()
        result = anonymizer.anonymize(
            "/project/.venv/lib/python3.10/site-packages/pkg/mod.py"
        )
        assert "<VENV>" in result

    def test_empty_text(self):
        anonymizer = PathAnonymizer()
        assert anonymizer.anonymize("") == ""
        assert anonymizer.anonymize(None) is None

    def test_no_paths(self):
        anonymizer = PathAnonymizer()
        text = "Just some regular text without paths"
        assert anonymizer.anonymize(text) == text

    def test_multiple_paths(self):
        anonymizer = PathAnonymizer(
            home_dir="/home/alice",
            username="alice",
        )
        text = (
            "File /home/alice/project/main.py line 10\n"
            "File /home/alice/project/utils.py line 20"
        )
        result = anonymizer.anonymize(text)
        assert "alice" not in result
        assert result.count("~") == 2

    def test_disable_home_anonymization(self):
        anonymizer = PathAnonymizer(
            home_dir="/home/alice",
            anonymize_home=False,
        )
        result = anonymizer.anonymize("/home/alice/file.py")
        assert "/home/alice" in result or "<USER>" in result

    def test_disable_username_anonymization(self):
        anonymizer = PathAnonymizer(
            home_dir="/other",
            username="alice",
            anonymize_username=False,
        )
        result = anonymizer.anonymize("/home/alice/file.py")
        assert "alice" in result

    def test_disable_temp_anonymization(self):
        anonymizer = PathAnonymizer(anonymize_temp=False)
        result = anonymizer.anonymize("/tmp/test123/file.py")
        assert "<TMPDIR>" not in result


class TestPathAnonymizerPath:
    """Tests for anonymize_path method."""

    def test_anonymize_path_string(self):
        anonymizer = PathAnonymizer(home_dir="/home/alice")
        result = anonymizer.anonymize_path("/home/alice/file.py")
        assert result == "~/file.py"

    def test_anonymize_path_object(self):
        anonymizer = PathAnonymizer(home_dir="/home/alice")
        result = anonymizer.anonymize_path(Path("/home/alice/file.py"))
        # Windows uses backslash in Path, normalize for comparison
        assert result.replace("\\", "/") == "~/file.py"


class TestCreateDefaultAnonymizer:
    """Tests for create_default_anonymizer function."""

    def test_creates_anonymizer(self):
        anonymizer = create_default_anonymizer()
        assert isinstance(anonymizer, PathAnonymizer)

    def test_with_project_root(self):
        anonymizer = create_default_anonymizer(project_root=Path("/my/project"))
        assert anonymizer.project_root == Path("/my/project")


class TestPathAnonymizerEdgeCases:
    """Tests for edge cases."""

    def test_relative_path_unchanged(self):
        anonymizer = PathAnonymizer()
        result = anonymizer.anonymize("./relative/path.py")
        assert result == "./relative/path.py"

    def test_url_with_path(self):
        anonymizer = PathAnonymizer(home_dir="/home/alice")
        text = "file:///home/alice/document.txt"
        result = anonymizer.anonymize(text)
        assert "alice" not in result or "<USER>" in result

    def test_traceback_format(self):
        anonymizer = PathAnonymizer(home_dir="/home/alice")
        text = '  File "/home/alice/project/main.py", line 10, in main'
        result = anonymizer.anonymize(text)
        assert "alice" not in result
        assert "line 10" in result

    def test_json_escaped_paths(self):
        anonymizer = PathAnonymizer(home_dir="/home/alice")
        text = r'{"path": "/home/alice/file.py"}'
        result = anonymizer.anonymize(text)
        assert "alice" not in result

    def test_mixed_separators(self):
        anonymizer = PathAnonymizer(
            home_dir="/home/alice",
            username="alice",
        )
        text = "/home/alice\\mixed/path"
        result = anonymizer.anonymize(text)
        assert "alice" not in result
