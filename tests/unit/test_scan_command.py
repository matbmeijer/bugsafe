"""Tests for bugsafe scan command."""

from tempfile import NamedTemporaryFile

from typer.testing import CliRunner

from bugsafe.cli import app

runner = CliRunner()


def test_scan_no_secrets():
    """Scan files with no secrets returns success."""
    with NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("print('hello world')\n")
        f.flush()

        result = runner.invoke(app, ["scan", f.name])

        assert result.exit_code == 0
        assert "No secrets found" in result.stdout


def test_scan_with_secrets():
    """Scan files with secrets returns failure."""
    with NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("API_KEY = 'AKIAIOSFODNN7EXAMPLE'\n")
        f.flush()

        result = runner.invoke(app, ["scan", f.name])

        assert result.exit_code == 4  # ExitCode.SECRETS_FOUND
        assert "Found" in result.stdout
        assert "secrets" in result.stdout


def test_scan_quiet_no_secrets():
    """Scan with --quiet flag produces no output on success."""
    with NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("print('hello')\n")
        f.flush()

        result = runner.invoke(app, ["scan", "--quiet", f.name])

        assert result.exit_code == 0
        assert result.stdout.strip() == ""


def test_scan_nonexistent_file():
    """Scan nonexistent file is handled gracefully."""
    result = runner.invoke(app, ["scan", "/nonexistent/file.py"])

    assert result.exit_code == 0


def test_scan_multiple_files():
    """Scan multiple files works correctly."""
    with NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f1:
        f1.write("clean = 'value'\n")
        f1.flush()
        with NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f2:
            f2.write("secret = 'ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'\n")
            f2.flush()

            result = runner.invoke(app, ["scan", f1.name, f2.name])

            assert result.exit_code == 4  # ExitCode.SECRETS_FOUND


def test_scan_github_token():
    """Scan detects GitHub token."""
    with NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("token = 'ghp_1234567890abcdefghijklmnopqrstuvwxyz'\n")
        f.flush()

        result = runner.invoke(app, ["scan", f.name])

        assert result.exit_code == 4  # ExitCode.SECRETS_FOUND
        assert "GITHUB" in result.stdout or "secrets" in result.stdout


def test_scan_aws_key():
    """Scan detects AWS access key."""
    with NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("aws_key = 'AKIAIOSFODNN7EXAMPLE'\n")
        f.flush()

        result = runner.invoke(app, ["scan", f.name])

        assert result.exit_code == 4  # ExitCode.SECRETS_FOUND
