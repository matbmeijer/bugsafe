"""Integration tests for complete bugsafe workflows."""

from pathlib import Path

from typer.testing import CliRunner

from bugsafe.cli import app

runner = CliRunner()


class TestCaptureRedactRenderWorkflow:
    """Test the complete capture -> redact -> render -> audit workflow."""

    def test_capture_redact_render_workflow(self, tmp_path: Path) -> None:
        """Test complete workflow: run -> render -> audit."""
        bundle_path = tmp_path / "test.bugbundle"

        # Run command that outputs secrets in stdout
        result = runner.invoke(
            app,
            [
                "run",
                "-o",
                str(bundle_path),
                "--",
                "python",
                "-c",
                "print('key=AKIAIOSFODNN7EXAMPLE')",
            ],
        )
        assert result.exit_code == 0
        assert bundle_path.exists()

        # Render and verify stdout is redacted (command itself may contain secret)
        result = runner.invoke(app, ["render", str(bundle_path)])
        assert result.exit_code == 0
        # The stdout section should contain the token, not the secret
        assert "<AWS_KEY_" in result.stdout
        # Redaction summary should show the redaction
        assert "Redaction Summary" in result.stdout

        # Audit checks stdout/stderr, should pass
        result = runner.invoke(app, ["audit", str(bundle_path)])
        assert result.exit_code == 0
        assert "No secrets detected" in result.stdout

    def test_workflow_with_multiple_secrets(self, tmp_path: Path) -> None:
        """Test workflow with multiple secret types."""
        bundle_path = tmp_path / "multi.bugbundle"

        # Run command that outputs multiple secrets
        script = """
import sys
print('AWS_KEY=AKIAIOSFODNN7EXAMPLE')
print('GITHUB_TOKEN=ghp_1234567890abcdefghijklmnopqrstuvwxyz')
print('API_SECRET=sk_live_abcdefghijklmnopqrstuvwxyz1234')
sys.exit(1)  # Simulate failure
"""
        result = runner.invoke(
            app,
            ["run", "-o", str(bundle_path), "--", "python", "-c", script],
        )
        assert result.exit_code == 0
        assert bundle_path.exists()

        # Verify stdout contains redaction tokens (secrets redacted)
        result = runner.invoke(app, ["render", str(bundle_path)])
        assert "<AWS_KEY_" in result.stdout
        assert "<GITHUB_TOKEN_" in result.stdout
        assert "<STRIPE_KEY_" in result.stdout
        # Redaction summary should show all 3 categories
        assert "AWS_KEY" in result.stdout
        assert "GITHUB_TOKEN" in result.stdout

    def test_workflow_no_redact_mode(self, tmp_path: Path) -> None:
        """Test workflow with --no-redact flag."""
        bundle_path = tmp_path / "noredact.bugbundle"

        result = runner.invoke(
            app,
            [
                "run",
                "-o",
                str(bundle_path),
                "--no-redact",
                "--",
                "python",
                "-c",
                "print('secret=AKIAIOSFODNN7EXAMPLE')",
            ],
        )
        assert result.exit_code == 0

        # Audit should fail (secrets NOT redacted)
        result = runner.invoke(app, ["audit", str(bundle_path)])
        assert result.exit_code == 4  # ExitCode.SECRETS_FOUND

    def test_workflow_inspect_bundle(self, tmp_path: Path) -> None:
        """Test inspect command shows bundle metadata."""
        bundle_path = tmp_path / "inspect.bugbundle"

        runner.invoke(
            app,
            ["run", "-o", str(bundle_path), "--", "echo", "hello"],
        )

        result = runner.invoke(app, ["inspect", str(bundle_path)])
        assert result.exit_code == 0
        assert "Bundle Information" in result.stdout
        assert "Version" in result.stdout

    def test_workflow_json_output(self, tmp_path: Path) -> None:
        """Test render with JSON format."""
        bundle_path = tmp_path / "json.bugbundle"

        runner.invoke(
            app,
            ["run", "-o", str(bundle_path), "--", "echo", "test"],
        )

        result = runner.invoke(app, ["render", "-f", "json", str(bundle_path)])
        assert result.exit_code == 0
        assert "{" in result.stdout  # JSON output


class TestScanWorkflow:
    """Test the scan workflow for pre-commit integration."""

    def test_scan_clean_files(self, tmp_path: Path) -> None:
        """Scan clean files passes."""
        clean_file = tmp_path / "clean.py"
        clean_file.write_text("print('hello world')\n")

        result = runner.invoke(app, ["scan", str(clean_file)])
        assert result.exit_code == 0
        assert "No secrets found" in result.stdout

    def test_scan_detects_secrets(self, tmp_path: Path) -> None:
        """Scan detects secrets and exits with code 4."""
        secret_file = tmp_path / "secret.py"
        secret_file.write_text("API_KEY = 'AKIAIOSFODNN7EXAMPLE'\n")

        result = runner.invoke(app, ["scan", str(secret_file)])
        assert result.exit_code == 4  # ExitCode.SECRETS_FOUND
        assert "potential secrets" in result.stdout.lower()

    def test_scan_multiple_files_workflow(self, tmp_path: Path) -> None:
        """Scan multiple files in pre-commit style."""
        (tmp_path / "file1.py").write_text("x = 1\n")
        (tmp_path / "file2.py").write_text("y = 2\n")
        (tmp_path / "file3.py").write_text("z = 3\n")

        result = runner.invoke(
            app,
            [
                "scan",
                str(tmp_path / "file1.py"),
                str(tmp_path / "file2.py"),
                str(tmp_path / "file3.py"),
            ],
        )
        assert result.exit_code == 0
        assert "No secrets found" in result.stdout
