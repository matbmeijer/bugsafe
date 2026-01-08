"""Unit tests for capture/runner.py."""

import signal
import sys
from pathlib import Path

import pytest

from bugsafe.capture.runner import (
    CaptureConfig,
    CaptureResult,
    run_command,
)


class TestCaptureConfig:
    """Tests for CaptureConfig dataclass."""

    def test_default_values(self):
        config = CaptureConfig()
        assert config.timeout == 300
        assert config.max_output_bytes == 10_000_000
        assert config.encoding == "utf-8"
        assert config.preserve_ansi is False
        assert config.strip_cr is True

    def test_custom_values(self):
        config = CaptureConfig(timeout=60, preserve_ansi=True)
        assert config.timeout == 60
        assert config.preserve_ansi is True

    def test_frozen(self):
        config = CaptureConfig()
        with pytest.raises(AttributeError):
            config.timeout = 100


class TestRunCommand:
    """Tests for run_command function."""

    def test_simple_echo(self):
        result = run_command(["echo", "hello"])
        assert result.exit_code == 0
        assert "hello" in result.stdout
        assert result.stderr == ""
        assert result.duration_ms >= 0  # Can be 0 on fast Windows systems

    def test_command_with_stderr(self):
        result = run_command(
            [sys.executable, "-c", "import sys; sys.stderr.write('error\\n')"]
        )
        assert result.exit_code == 0
        assert "error" in result.stderr

    def test_command_exit_code(self):
        result = run_command([sys.executable, "-c", "exit(42)"])
        assert result.exit_code == 42

    def test_command_not_found(self):
        result = run_command(["nonexistent_command_xyz"])
        assert result.exit_code == -1
        assert result.error_message is not None
        assert "not found" in result.error_message.lower()

    def test_timeout(self):
        config = CaptureConfig(timeout=1)
        result = run_command(
            [sys.executable, "-c", "import time; time.sleep(10)"], config
        )
        assert result.timed_out is True
        assert result.exit_code == -2
        # Windows doesn't have SIGKILL, check for SIGTERM or None
        if sys.platform == "win32":
            assert result.signal_num is None or result.signal_num == signal.SIGTERM
        else:
            assert result.signal_num in (signal.SIGTERM, signal.SIGKILL)

    def test_large_output_truncation(self):
        config = CaptureConfig(max_output_bytes=100)
        result = run_command([sys.executable, "-c", "print('x' * 1000)"], config)
        assert result.truncated_stdout is True
        assert "TRUNCATED" in result.stdout

    def test_ansi_stripping(self):
        config = CaptureConfig(preserve_ansi=False)
        result = run_command(
            [sys.executable, "-c", r"print('\x1b[31mred\x1b[0m')"], config
        )
        assert "\x1b[" not in result.stdout
        assert "red" in result.stdout

    def test_ansi_preservation(self):
        config = CaptureConfig(preserve_ansi=True)
        result = run_command(
            [sys.executable, "-c", r"print('\x1b[31mred\x1b[0m')"], config
        )
        assert "\x1b[31m" in result.stdout

    def test_cr_normalization(self):
        config = CaptureConfig(strip_cr=True)
        result = run_command([sys.executable, "-c", r"print('line1\r\nline2')"], config)
        assert "\r\n" not in result.stdout
        # Windows may add extra newlines, just check both lines are present
        assert "line1" in result.stdout
        assert "line2" in result.stdout

    def test_working_directory(self, tmp_path: Path):
        config = CaptureConfig(cwd=tmp_path)
        result = run_command(
            [sys.executable, "-c", "import os; print(os.getcwd())"], config
        )
        assert result.exit_code == 0
        assert str(tmp_path) in result.stdout

    def test_invalid_working_directory(self):
        config = CaptureConfig(cwd=Path("/nonexistent/directory"))
        result = run_command(["echo", "test"], config)
        assert result.exit_code == -1
        assert "does not exist" in result.error_message

    def test_result_contains_command(self):
        cmd = ["echo", "test"]
        result = run_command(cmd)
        assert result.command == cmd


class TestCaptureResult:
    """Tests for CaptureResult dataclass."""

    def test_default_values(self):
        result = CaptureResult(command=["test"])
        assert result.stdout == ""
        assert result.stderr == ""
        assert result.exit_code == 0
        assert result.timed_out is False
        assert result.truncated_stdout is False

    def test_custom_values(self):
        result = CaptureResult(
            command=["test"],
            stdout="output",
            exit_code=1,
            timed_out=True,
        )
        assert result.stdout == "output"
        assert result.exit_code == 1
        assert result.timed_out is True


class TestBinaryOutput:
    """Tests for binary output handling."""

    def test_binary_output_detected(self):
        result = run_command(
            [
                sys.executable,
                "-c",
                "import sys; sys.stdout.buffer.write(bytes(range(256)))",
            ]
        )
        assert result.is_binary_stdout is True

    @pytest.mark.skipif(sys.platform == "win32", reason="Windows cp1252 encoding")
    def test_utf8_output_not_binary(self):
        result = run_command([sys.executable, "-c", "print('hello 世界')"])
        assert result.is_binary_stdout is False
        assert "世界" in result.stdout


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_command(self):
        # Behavior varies by platform - may raise or return error result
        try:
            result = run_command([])
            # If it doesn't raise, it should return an error
            assert result.exit_code != 0 or result.error_message is not None
        except (IndexError, FileNotFoundError, OSError, ValueError):
            pass  # Expected on some platforms

    def test_multiline_output(self):
        result = run_command([sys.executable, "-c", "print('line1\\nline2\\nline3')"])
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 3

    @pytest.mark.skipif(sys.platform == "win32", reason="Windows cp1252 encoding")
    def test_unicode_output(self):
        result = run_command([sys.executable, "-c", "print('emoji: 🎉 unicode: αβγ')"])
        assert "🎉" in result.stdout
        assert "αβγ" in result.stdout

    def test_quick_process(self):
        result = run_command([sys.executable, "-c", "pass"])
        assert result.exit_code == 0
        assert result.duration_ms >= 0
