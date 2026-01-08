"""Integration tests for CLI commands."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from bugsafe.cli import app

runner = CliRunner()


class TestCLIHelp:
    """Tests for CLI help output."""

    def test_main_help(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "bugsafe" in result.stdout
        assert "run" in result.stdout
        assert "render" in result.stdout
        assert "inspect" in result.stdout
        assert "config" in result.stdout

    def test_version(self):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "bugsafe version" in result.stdout

    def test_run_help(self):
        result = runner.invoke(app, ["run", "--help"])
        assert result.exit_code == 0
        assert "Command to execute" in result.stdout
        assert "--timeout" in result.stdout
        assert "--output" in result.stdout

    def test_render_help(self):
        result = runner.invoke(app, ["render", "--help"])
        assert result.exit_code == 0
        assert "bugbundle" in result.stdout
        assert "--format" in result.stdout
        assert "--llm" in result.stdout

    def test_inspect_help(self):
        result = runner.invoke(app, ["inspect", "--help"])
        assert result.exit_code == 0
        assert "bugbundle" in result.stdout

    def test_config_help(self):
        result = runner.invoke(app, ["config", "--help"])
        assert result.exit_code == 0
        assert "--show" in result.stdout
        assert "--path" in result.stdout
        assert "--init" in result.stdout


class TestRunCommand:
    """Tests for run command."""

    def test_run_simple_command(self, tmp_path: Path):
        output_path = tmp_path / "test.bugbundle"
        result = runner.invoke(
            app, ["run", "echo", "hello", "-o", str(output_path)]
        )
        assert result.exit_code == 0
        assert output_path.exists()
        assert "Bundle created" in result.stdout

    def test_run_failing_command(self, tmp_path: Path):
        output_path = tmp_path / "test.bugbundle"
        result = runner.invoke(
            app, ["run", "-o", str(output_path), "--", "python", "-c", "raise ValueError('test')"]
        )
        assert result.exit_code == 0
        assert output_path.exists()
        assert "Exit code: 1" in result.stdout

    def test_run_with_timeout(self, tmp_path: Path):
        output_path = tmp_path / "test.bugbundle"
        result = runner.invoke(
            app, ["run", "echo", "test", "-o", str(output_path), "-t", "10"]
        )
        assert result.exit_code == 0
        assert output_path.exists()

    def test_run_no_redact(self, tmp_path: Path):
        output_path = tmp_path / "test.bugbundle"
        result = runner.invoke(
            app, ["run", "echo", "test@example.com", "-o", str(output_path), "--no-redact"]
        )
        assert result.exit_code == 0
        assert output_path.exists()


class TestRenderCommand:
    """Tests for render command."""

    def test_render_markdown(self, tmp_path: Path):
        bundle_path = tmp_path / "test.bugbundle"
        runner.invoke(app, ["run", "echo", "hello", "-o", str(bundle_path)])

        result = runner.invoke(app, ["render", str(bundle_path)])
        assert result.exit_code == 0
        assert "# Bug Report" in result.stdout

    def test_render_json(self, tmp_path: Path):
        bundle_path = tmp_path / "test.bugbundle"
        runner.invoke(app, ["run", "echo", "hello", "-o", str(bundle_path)])

        result = runner.invoke(app, ["render", str(bundle_path), "-f", "json"])
        assert result.exit_code == 0
        assert '"metadata"' in result.stdout

    def test_render_llm(self, tmp_path: Path):
        bundle_path = tmp_path / "test.bugbundle"
        runner.invoke(app, ["run", "echo", "hello", "-o", str(bundle_path)])

        result = runner.invoke(
            app, ["render", str(bundle_path), "-f", "json", "--llm"]
        )
        assert result.exit_code == 0
        assert "# Bug Context" in result.stdout

    def test_render_to_file(self, tmp_path: Path):
        bundle_path = tmp_path / "test.bugbundle"
        output_path = tmp_path / "output.md"
        runner.invoke(app, ["run", "echo", "hello", "-o", str(bundle_path)])

        result = runner.invoke(
            app, ["render", str(bundle_path), "-o", str(output_path)]
        )
        assert result.exit_code == 0
        assert output_path.exists()
        assert "# Bug Report" in output_path.read_text()

    def test_render_not_found(self):
        result = runner.invoke(app, ["render", "nonexistent.bugbundle"])
        assert result.exit_code == 1
        assert "not found" in result.stdout


class TestInspectCommand:
    """Tests for inspect command."""

    def test_inspect_bundle(self, tmp_path: Path):
        bundle_path = tmp_path / "test.bugbundle"
        runner.invoke(app, ["run", "echo", "hello", "-o", str(bundle_path)])

        result = runner.invoke(app, ["inspect", str(bundle_path)])
        assert result.exit_code == 0
        assert "Bundle Information" in result.stdout
        assert "Version" in result.stdout
        assert "Capture" in result.stdout

    def test_inspect_not_found(self):
        result = runner.invoke(app, ["inspect", "nonexistent.bugbundle"])
        assert result.exit_code == 1
        assert "not found" in result.stdout


class TestConfigCommand:
    """Tests for config command."""

    def test_config_show(self):
        result = runner.invoke(app, ["config", "--show"])
        assert result.exit_code == 0
        assert "Current Configuration" in result.stdout
        assert "timeout" in result.stdout

    def test_config_path(self):
        result = runner.invoke(app, ["config", "--path"])
        assert result.exit_code == 0
        assert "Config file" in result.stdout
        assert "bugsafe" in result.stdout

    def test_config_init(self, tmp_path: Path, monkeypatch):
        config_dir = tmp_path / ".config" / "bugsafe"
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / ".config"))

        result = runner.invoke(app, ["config", "--init"])
        assert result.exit_code == 0


class TestEndToEnd:
    """End-to-end integration tests."""

    def test_full_workflow(self, tmp_path: Path):
        bundle_path = tmp_path / "test.bugbundle"
        md_path = tmp_path / "report.md"

        run_result = runner.invoke(
            app, ["run", "-o", str(bundle_path), "--", "python", "-c", "print('hello')"]
        )
        assert run_result.exit_code == 0
        assert bundle_path.exists()

        inspect_result = runner.invoke(app, ["inspect", str(bundle_path)])
        assert inspect_result.exit_code == 0
        assert "Bundle Information" in inspect_result.stdout

        render_result = runner.invoke(
            app, ["render", str(bundle_path), "-o", str(md_path)]
        )
        assert render_result.exit_code == 0
        assert md_path.exists()
        assert "# Bug Report" in md_path.read_text()

    def test_error_capture_workflow(self, tmp_path: Path):
        bundle_path = tmp_path / "error.bugbundle"

        run_result = runner.invoke(
            app,
            [
                "run",
                "-o", str(bundle_path),
                "--",
                "python", "-c", "raise ValueError('test error message')",
            ],
        )
        assert run_result.exit_code == 0
        assert bundle_path.exists()
        assert "Exit code: 1" in run_result.stdout

        inspect_result = runner.invoke(app, ["inspect", str(bundle_path)])
        assert inspect_result.exit_code == 0

        render_result = runner.invoke(app, ["render", str(bundle_path)])
        assert render_result.exit_code == 0
        assert "ValueError" in render_result.stdout or "test error" in render_result.stdout
