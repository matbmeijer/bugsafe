"""Tests for MCP server tools.

These tests verify the MCP tool functions work correctly without
requiring the mcp package to be installed.
"""

from datetime import datetime, timezone


def test_scan_secrets_detects_api_key():
    """scan_secrets detects API keys in text."""
    from bugsafe.redact.engine import create_redaction_engine

    engine = create_redaction_engine()
    text = "API_KEY=AKIAIOSFODNN7EXAMPLE"

    redacted_text, report = engine.redact(text)

    assert report.get_total() > 0
    assert "AKIAIOSFODNN7EXAMPLE" not in redacted_text


def test_scan_secrets_no_secrets():
    """scan_secrets returns empty report for clean text."""
    from bugsafe.redact.engine import create_redaction_engine

    engine = create_redaction_engine()
    text = "Hello, world!"

    _, report = engine.redact(text)

    assert report.get_total() == 0


def test_render_bundle_markdown(tmp_path):
    """render_bundle returns markdown for valid bundle."""

    from bugsafe.bundle.schema import (
        BugBundle,
        BundleMetadata,
        CaptureOutput,
    )
    from bugsafe.bundle.writer import create_bundle
    from bugsafe.render.markdown import render_markdown

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
        traceback=None,
        environment=None,
        redaction_report={},
    )

    bundle_path = tmp_path / "test.bugbundle"
    create_bundle(bundle, bundle_path)

    from bugsafe.bundle.reader import read_bundle

    loaded = read_bundle(bundle_path)
    result = render_markdown(loaded)

    assert "test output" in result or "test error" in result


def test_audit_bundle_clean(tmp_path):
    """audit_bundle passes for clean bundle."""

    from bugsafe.bundle.schema import (
        BugBundle,
        BundleMetadata,
        CaptureOutput,
    )
    from bugsafe.bundle.writer import create_bundle
    from bugsafe.redact.engine import create_redaction_engine

    bundle = BugBundle(
        metadata=BundleMetadata(
            created_at=datetime.now(timezone.utc),
            bugsafe_version="0.1.0",
            redaction_salt_hash="test",
        ),
        capture=CaptureOutput(
            stdout="clean output with no secrets",
            stderr="clean error",
            exit_code=0,
            duration_ms=50,
            command=["echo", "hello"],
            timed_out=False,
            truncated=False,
        ),
        traceback=None,
        environment=None,
        redaction_report={},
    )

    bundle_path = tmp_path / "clean.bugbundle"
    create_bundle(bundle, bundle_path)

    from bugsafe.bundle.reader import read_bundle

    loaded = read_bundle(bundle_path)
    engine = create_redaction_engine()

    combined_text = loaded.capture.stdout + "\n" + loaded.capture.stderr
    leaks = engine.verify_redaction(combined_text)

    assert len(leaks) == 0


def test_audit_bundle_with_leak(tmp_path):
    """audit_bundle detects unredacted secrets."""

    from bugsafe.bundle.schema import (
        BugBundle,
        BundleMetadata,
        CaptureOutput,
    )
    from bugsafe.bundle.writer import create_bundle
    from bugsafe.redact.engine import create_redaction_engine

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
            duration_ms=50,
            command=["test"],
            timed_out=False,
            truncated=False,
        ),
        traceback=None,
        environment=None,
        redaction_report={},
    )

    bundle_path = tmp_path / "leak.bugbundle"
    create_bundle(bundle, bundle_path)

    from bugsafe.bundle.reader import read_bundle

    loaded = read_bundle(bundle_path)
    engine = create_redaction_engine()

    combined_text = loaded.capture.stdout + "\n" + loaded.capture.stderr
    leaks = engine.verify_redaction(combined_text)

    assert len(leaks) > 0
