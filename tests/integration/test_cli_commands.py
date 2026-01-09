"""Integration tests for CLI commands."""

from datetime import datetime, timezone

from typer.testing import CliRunner

from bugsafe.cli import app

runner = CliRunner()


class TestScanCommand:
    """Tests for the scan command."""

    def test_scan_clean_file(self, tmp_path):
        """Scan reports no secrets in clean file."""
        clean_file = tmp_path / "clean.py"
        clean_file.write_text("print('hello world')")

        result = runner.invoke(app, ["scan", str(clean_file)])

        assert result.exit_code == 0
        assert "No secrets found" in result.stdout

    def test_scan_file_with_secrets(self, tmp_path):
        """Scan detects secrets in file."""
        secret_file = tmp_path / "secret.py"
        secret_file.write_text("API_KEY = 'AKIAIOSFODNN7EXAMPLE'")

        result = runner.invoke(app, ["scan", str(secret_file)])

        assert result.exit_code == 4  # ExitCode.SECRETS_FOUND
        assert "potential secrets" in result.stdout.lower()

    def test_scan_quiet_clean(self, tmp_path):
        """Scan quiet mode produces no output for clean file."""
        clean_file = tmp_path / "clean.py"
        clean_file.write_text("print('hello world')")

        result = runner.invoke(app, ["scan", "--quiet", str(clean_file)])

        assert result.exit_code == 0
        assert result.stdout.strip() == ""

    def test_scan_nonexistent_file(self, tmp_path):
        """Scan handles nonexistent file gracefully."""
        result = runner.invoke(app, ["scan", str(tmp_path / "nonexistent.py")])

        assert result.exit_code == 0

    def test_scan_multiple_files(self, tmp_path):
        """Scan handles multiple files."""
        file1 = tmp_path / "file1.py"
        file2 = tmp_path / "file2.py"
        file1.write_text("x = 1")
        file2.write_text("y = 2")

        result = runner.invoke(app, ["scan", str(file1), str(file2)])

        assert result.exit_code == 0


class TestAuditCommand:
    """Tests for the audit command."""

    def test_audit_clean_bundle(self, tmp_path):
        """Audit passes for clean bundle."""

        from bugsafe.bundle.schema import BugBundle, BundleMetadata, CaptureOutput
        from bugsafe.bundle.writer import create_bundle

        bundle = BugBundle(
            metadata=BundleMetadata(
                created_at=datetime.now(timezone.utc),
                bugsafe_version="0.1.0",
                redaction_salt_hash="test",
            ),
            capture=CaptureOutput(
                stdout="clean output",
                stderr="clean error",
                exit_code=0,
                duration_ms=100,
                command=["test"],
                timed_out=False,
                truncated=False,
            ),
        )

        bundle_path = tmp_path / "clean.bugbundle"
        create_bundle(bundle, bundle_path)

        result = runner.invoke(app, ["audit", str(bundle_path)])

        assert result.exit_code == 0
        assert "No secrets detected" in result.stdout

    def test_audit_bundle_with_leak(self, tmp_path):
        """Audit fails for bundle with unredacted secrets."""

        from bugsafe.bundle.schema import BugBundle, BundleMetadata, CaptureOutput
        from bugsafe.bundle.writer import create_bundle

        bundle = BugBundle(
            metadata=BundleMetadata(
                created_at=datetime.now(timezone.utc),
                bugsafe_version="0.1.0",
                redaction_salt_hash="test",
            ),
            capture=CaptureOutput(
                stdout="AWS key: AKIAIOSFODNN7EXAMPLE",
                stderr="",
                exit_code=0,
                duration_ms=100,
                command=["test"],
                timed_out=False,
                truncated=False,
            ),
        )

        bundle_path = tmp_path / "leak.bugbundle"
        create_bundle(bundle, bundle_path)

        result = runner.invoke(app, ["audit", str(bundle_path)])

        assert result.exit_code == 4  # ExitCode.SECRETS_FOUND

    def test_audit_nonexistent_bundle(self, tmp_path):
        """Audit handles nonexistent bundle."""
        result = runner.invoke(app, ["audit", str(tmp_path / "nonexistent.bugbundle")])

        assert result.exit_code == 2  # ExitCode.BUNDLE_NOT_FOUND
        assert "not found" in result.stdout.lower()


class TestRenderCommand:
    """Tests for the render command."""

    def test_render_markdown(self, tmp_path):
        """Render outputs markdown by default."""

        from bugsafe.bundle.schema import BugBundle, BundleMetadata, CaptureOutput
        from bugsafe.bundle.writer import create_bundle

        bundle = BugBundle(
            metadata=BundleMetadata(
                created_at=datetime.now(timezone.utc),
                bugsafe_version="0.1.0",
                redaction_salt_hash="test",
            ),
            capture=CaptureOutput(
                stdout="test output",
                stderr="test error",
                exit_code=1,
                duration_ms=100,
                command=["test"],
                timed_out=False,
                truncated=False,
            ),
        )

        bundle_path = tmp_path / "test.bugbundle"
        create_bundle(bundle, bundle_path)

        result = runner.invoke(app, ["render", str(bundle_path)])

        assert result.exit_code == 0

    def test_render_json(self, tmp_path):
        """Render outputs JSON when requested."""

        from bugsafe.bundle.schema import BugBundle, BundleMetadata, CaptureOutput
        from bugsafe.bundle.writer import create_bundle

        bundle = BugBundle(
            metadata=BundleMetadata(
                created_at=datetime.now(timezone.utc),
                bugsafe_version="0.1.0",
                redaction_salt_hash="test",
            ),
            capture=CaptureOutput(
                stdout="test output",
                stderr="",
                exit_code=0,
                duration_ms=100,
                command=["test"],
                timed_out=False,
                truncated=False,
            ),
        )

        bundle_path = tmp_path / "test.bugbundle"
        create_bundle(bundle, bundle_path)

        result = runner.invoke(app, ["render", "--format", "json", str(bundle_path)])

        assert result.exit_code == 0

    def test_render_llm(self, tmp_path):
        """Render outputs LLM format when requested."""

        from bugsafe.bundle.schema import BugBundle, BundleMetadata, CaptureOutput
        from bugsafe.bundle.writer import create_bundle

        bundle = BugBundle(
            metadata=BundleMetadata(
                created_at=datetime.now(timezone.utc),
                bugsafe_version="0.1.0",
                redaction_salt_hash="test",
            ),
            capture=CaptureOutput(
                stdout="test output",
                stderr="",
                exit_code=0,
                duration_ms=100,
                command=["test"],
                timed_out=False,
                truncated=False,
            ),
        )

        bundle_path = tmp_path / "test.bugbundle"
        create_bundle(bundle, bundle_path)

        result = runner.invoke(app, ["render", "--llm", str(bundle_path)])

        assert result.exit_code == 0

    def test_render_nonexistent_bundle(self, tmp_path):
        """Render handles nonexistent bundle."""
        result = runner.invoke(app, ["render", str(tmp_path / "nonexistent.bugbundle")])

        assert result.exit_code == 2  # ExitCode.BUNDLE_NOT_FOUND


class TestInspectCommand:
    """Tests for the inspect command."""

    def test_inspect_bundle(self, tmp_path):
        """Inspect shows bundle metadata."""

        from bugsafe.bundle.schema import BugBundle, BundleMetadata, CaptureOutput
        from bugsafe.bundle.writer import create_bundle

        bundle = BugBundle(
            metadata=BundleMetadata(
                created_at=datetime.now(timezone.utc),
                bugsafe_version="0.1.0",
                redaction_salt_hash="test",
            ),
            capture=CaptureOutput(
                stdout="test",
                stderr="",
                exit_code=0,
                duration_ms=100,
                command=["test"],
                timed_out=False,
                truncated=False,
            ),
        )

        bundle_path = tmp_path / "test.bugbundle"
        create_bundle(bundle, bundle_path)

        result = runner.invoke(app, ["inspect", str(bundle_path)])

        assert result.exit_code == 0


class TestMcpCommand:
    """Tests for the mcp command."""

    def test_mcp_import_error(self, monkeypatch):
        """MCP command fails gracefully when mcp not installed."""
        import sys

        original_modules = sys.modules.copy()

        def mock_import(name, *args, **kwargs):
            if "mcp" in name:
                raise ImportError("No module named 'mcp'")
            return original_modules.get(name)

        monkeypatch.setattr("builtins.__import__", mock_import)

        result = runner.invoke(app, ["mcp"])

        assert result.exit_code == 1
