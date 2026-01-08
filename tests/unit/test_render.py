"""Unit tests for render module."""

from datetime import datetime

import pytest

from bugsafe.bundle.schema import (
    BugBundle,
    BundleMetadata,
    CaptureOutput,
    Environment,
    Frame,
    GitInfo,
    PackageInfo,
    Traceback,
)
from bugsafe.render.json_export import to_dict, to_json, to_llm_context
from bugsafe.render.markdown import render_markdown


@pytest.fixture
def sample_bundle() -> BugBundle:
    """Create a sample bundle for testing."""
    return BugBundle(
        metadata=BundleMetadata(
            version="1.0",
            created_at=datetime(2024, 1, 15, 10, 30, 0),
            bugsafe_version="0.1.0",
            redaction_salt_hash="abc123",
        ),
        capture=CaptureOutput(
            stdout="Hello, World!",
            stderr="Error: Something went wrong",
            exit_code=1,
            duration_ms=150,
            command=["python", "script.py", "--arg"],
        ),
        traceback=Traceback(
            exception_type="ValueError",
            message="Invalid value provided",
            frames=[
                Frame(
                    file="/home/user/project/main.py",
                    line=25,
                    function="main",
                    code="result = process(data)",
                ),
                Frame(
                    file="/home/user/project/utils.py",
                    line=10,
                    function="process",
                    code='raise ValueError("Invalid value provided")',
                ),
            ],
        ),
        environment=Environment(
            python_version="3.10.0",
            python_executable="/usr/bin/python3",
            platform="Linux-5.4.0-x86_64",
            packages=[
                PackageInfo(name="pytest", version="8.0.0"),
                PackageInfo(name="requests", version="2.31.0"),
            ],
            env_vars={"PATH": "/usr/bin", "HOME": "/home/user"},
            cwd="/home/user/project",
            git=GitInfo(
                ref="abc123def456",
                branch="main",
                dirty=False,
            ),
            virtualenv=True,
            ci_detected=False,
        ),
        redaction_report={"API_KEY": 2, "EMAIL": 1},
    )


@pytest.fixture
def minimal_bundle() -> BugBundle:
    """Create a minimal bundle for testing."""
    return BugBundle(
        capture=CaptureOutput(
            exit_code=0,
            command=["echo", "hello"],
        ),
    )


class TestRenderMarkdown:
    """Tests for Markdown rendering."""

    def test_render_basic(self, sample_bundle: BugBundle):
        result = render_markdown(sample_bundle)

        assert "# Bug Report" in result
        assert "bugsafe v0.1.0" in result
        assert "2024-01-15" in result

    def test_render_command(self, sample_bundle: BugBundle):
        result = render_markdown(sample_bundle)

        assert "## Command" in result
        assert "python script.py --arg" in result
        assert "Exit code:** 1" in result

    def test_render_traceback(self, sample_bundle: BugBundle):
        result = render_markdown(sample_bundle)

        assert "## Error" in result
        assert "ValueError" in result
        assert "Invalid value provided" in result
        assert "## Traceback" in result
        assert "main.py" in result
        assert "utils.py" in result

    def test_render_environment(self, sample_bundle: BugBundle):
        result = render_markdown(sample_bundle)

        assert "## Environment" in result
        assert "Python" in result
        assert "3.10.0" in result
        assert "Linux" in result

    def test_render_git_info(self, sample_bundle: BugBundle):
        result = render_markdown(sample_bundle)

        assert "abc123d" in result
        assert "main" in result

    def test_render_packages(self, sample_bundle: BugBundle):
        result = render_markdown(sample_bundle)

        assert "Installed Packages" in result
        assert "pytest" in result

    def test_render_redaction_summary(self, sample_bundle: BugBundle):
        result = render_markdown(sample_bundle)

        assert "## Redaction Summary" in result
        assert "API_KEY" in result
        assert "EMAIL" in result

    def test_render_minimal(self, minimal_bundle: BugBundle):
        result = render_markdown(minimal_bundle)

        assert "# Bug Report" in result
        assert "echo hello" in result
        assert "Exit code:** 0" in result

    def test_render_no_traceback(self, minimal_bundle: BugBundle):
        result = render_markdown(minimal_bundle)

        assert "## Error" not in result
        assert "## Traceback" not in result

    def test_render_stdout_truncation(self):
        bundle = BugBundle(
            capture=CaptureOutput(
                stdout="x" * 10000,
                command=["test"],
            ),
        )
        result = render_markdown(bundle)

        assert "truncated" in result
        assert len(result) < 15000

    def test_render_stderr_truncation(self):
        bundle = BugBundle(
            capture=CaptureOutput(
                stderr="x" * 10000,
                command=["test"],
            ),
        )
        result = render_markdown(bundle)

        assert "truncated" in result


class TestJsonExport:
    """Tests for JSON export."""

    def test_to_json_basic(self, sample_bundle: BugBundle):
        result = to_json(sample_bundle)

        assert isinstance(result, str)
        import json

        data = json.loads(result)
        assert "metadata" in data
        assert "capture" in data

    def test_to_json_roundtrip(self, sample_bundle: BugBundle):
        json_str = to_json(sample_bundle)
        import json

        data = json.loads(json_str)

        assert data["capture"]["exit_code"] == 1
        assert data["capture"]["command"] == ["python", "script.py", "--arg"]

    def test_to_json_indent(self, minimal_bundle: BugBundle):
        result_2 = to_json(minimal_bundle, indent=2)
        result_4 = to_json(minimal_bundle, indent=4)

        assert result_4.count(" ") > result_2.count(" ")

    def test_to_dict(self, sample_bundle: BugBundle):
        result = to_dict(sample_bundle)

        assert isinstance(result, dict)
        assert result["capture"]["exit_code"] == 1


class TestLLMContext:
    """Tests for LLM context generation."""

    def test_llm_context_basic(self, sample_bundle: BugBundle):
        result = to_llm_context(sample_bundle)

        assert "# Bug Context" in result
        assert "python script.py --arg" in result
        assert "Exit code:** 1" in result

    def test_llm_context_includes_error(self, sample_bundle: BugBundle):
        result = to_llm_context(sample_bundle)

        assert "## Error" in result
        assert "ValueError" in result
        assert "Invalid value provided" in result

    def test_llm_context_includes_traceback(self, sample_bundle: BugBundle):
        result = to_llm_context(sample_bundle)

        assert "Traceback" in result
        assert "main.py" in result

    def test_llm_context_includes_environment(self, sample_bundle: BugBundle):
        result = to_llm_context(sample_bundle)

        assert "## Environment" in result
        assert "Python" in result

    def test_llm_context_token_limit(self, sample_bundle: BugBundle):
        result = to_llm_context(sample_bundle, max_tokens=500)

        assert len(result) < 500 * 4 + 500

    def test_llm_context_redaction_note(self, sample_bundle: BugBundle):
        result = to_llm_context(sample_bundle)

        assert "secrets were redacted" in result
        assert "API_KEY" in result

    def test_llm_context_no_traceback(self, minimal_bundle: BugBundle):
        result = to_llm_context(minimal_bundle)

        assert "# Bug Context" in result
        assert "## Error" not in result

    def test_llm_context_truncates_long_output(self):
        bundle = BugBundle(
            capture=CaptureOutput(
                stdout="x" * 50000,
                stderr="y" * 50000,
                command=["test"],
            ),
        )
        result = to_llm_context(bundle, max_tokens=1000)

        assert "truncated" in result
        assert len(result) < 10000


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_bundle(self):
        bundle = BugBundle()
        md = render_markdown(bundle)
        json_str = to_json(bundle)
        llm = to_llm_context(bundle)

        assert "# Bug Report" in md
        assert isinstance(json_str, str)
        assert "# Bug Context" in llm

    def test_unicode_content(self):
        bundle = BugBundle(
            capture=CaptureOutput(
                stdout="Hello 世界 🎉",
                stderr="エラー",
                command=["echo", "こんにちは"],
            ),
        )

        md = render_markdown(bundle)
        assert "世界" in md
        assert "🎉" in md

        json_str = to_json(bundle)
        assert "世界" in json_str

    def test_special_characters(self):
        bundle = BugBundle(
            capture=CaptureOutput(
                stdout="Line with | pipe and `backticks`",
                command=["test"],
            ),
        )

        md = render_markdown(bundle)
        assert "pipe" in md

    def test_very_long_traceback(self):
        frames = [
            Frame(file=f"file{i}.py", line=i, function=f"func{i}") for i in range(100)
        ]
        bundle = BugBundle(
            traceback=Traceback(
                exception_type="RecursionError",
                message="maximum recursion depth exceeded",
                frames=frames,
            ),
            capture=CaptureOutput(command=["test"]),
        )

        llm = to_llm_context(bundle, max_tokens=2000)
        assert "RecursionError" in llm

    def test_no_environment(self):
        bundle = BugBundle(
            capture=CaptureOutput(command=["test"]),
            environment=None,
        )

        md = render_markdown(bundle)
        assert "## Environment" not in md

    def test_git_dirty(self):
        bundle = BugBundle(
            capture=CaptureOutput(command=["test"]),
            environment=Environment(
                python_version="3.10.0",
                git=GitInfo(ref="abc123", dirty=True),
            ),
        )

        md = render_markdown(bundle)
        assert "dirty" in md
