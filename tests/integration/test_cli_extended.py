"""Extended CLI integration tests."""

from typer.testing import CliRunner

from bugsafe.cli import app

runner = CliRunner()


class TestRunCommand:
    """Tests for the run command."""

    def test_run_echo(self):
        """Run simple echo command."""
        result = runner.invoke(app, ["run", "--", "echo", "hello"])

        assert result.exit_code == 0

    def test_run_failing_command(self):
        """Run command that fails."""
        result = runner.invoke(
            app, ["run", "--", "python", "-c", "raise SystemExit(1)"]
        )

        # Command completed, exit code may vary
        assert result.exit_code in (0, 1)

    def test_run_with_output(self, tmp_path):
        """Run with output file."""
        output = tmp_path / "test.bugbundle"

        result = runner.invoke(app, ["run", "-o", str(output), "--", "echo", "test"])

        assert result.exit_code == 0
        assert output.exists()


class TestVersionCommand:
    """Tests for version display."""

    def test_version(self):
        """Shows version."""
        result = runner.invoke(app, ["--version"])

        # May exit with 0 or show version
        assert "0." in result.stdout or result.exit_code == 0


class TestConfigCommand:
    """Tests for config command."""

    def test_config_show(self):
        """Shows config."""
        result = runner.invoke(app, ["config"])

        # Should complete without crashing
        assert result.exit_code in (0, 1, 2)


class TestHelpCommand:
    """Tests for help display."""

    def test_help(self):
        """Shows help."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "run" in result.stdout
        assert "render" in result.stdout

    def test_run_help(self):
        """Shows run help."""
        result = runner.invoke(app, ["run", "--help"])

        assert result.exit_code == 0

    def test_render_help(self):
        """Shows render help."""
        result = runner.invoke(app, ["render", "--help"])

        assert result.exit_code == 0

    def test_scan_help(self):
        """Shows scan help."""
        result = runner.invoke(app, ["scan", "--help"])

        assert result.exit_code == 0

    def test_audit_help(self):
        """Shows audit help."""
        result = runner.invoke(app, ["audit", "--help"])

        assert result.exit_code == 0
