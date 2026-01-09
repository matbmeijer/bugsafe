"""Extended tests for command runner module."""

from bugsafe.capture.runner import run_command


class TestRunCommand:
    """Tests for run_command function."""

    def test_run_simple_command(self):
        """Run simple echo command."""
        result = run_command(["echo", "hello"])

        assert "hello" in result.stdout
        assert result.exit_code == 0
        assert result.timed_out is False

    def test_run_command_with_stderr(self):
        """Run command that outputs to stderr."""
        result = run_command(
            ["python", "-c", "import sys; sys.stderr.write('error\\n')"]
        )

        assert "error" in result.stderr
        assert result.exit_code == 0

    def test_run_failing_command(self):
        """Run command that fails."""
        result = run_command(["python", "-c", "raise SystemExit(42)"])

        assert result.exit_code == 42
        assert result.timed_out is False

    def test_run_command_nonexistent(self):
        """Run nonexistent command."""
        result = run_command(["nonexistent_command_xyz"])

        assert result.exit_code != 0


class TestRunCommandEdgeCases:
    """Edge case tests for run_command."""

    def test_empty_output(self):
        """Handle command with no output."""
        result = run_command(["python", "-c", "pass"])

        assert result.stdout == ""
        assert result.exit_code == 0

    def test_large_output(self):
        """Handle command with large output."""
        result = run_command(["python", "-c", "print('x' * 1000)"])

        assert len(result.stdout) >= 1000

    def test_unicode_output(self):
        """Handle unicode in command output."""
        result = run_command(["python", "-c", "print('Hello 世界 🌍')"])

        assert result.exit_code == 0

    def test_command_duration_tracked(self):
        """Duration is tracked for commands."""
        result = run_command(["python", "-c", "import time; time.sleep(0.1)"])

        assert result.duration_ms >= 50  # At least some time elapsed
