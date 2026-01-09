"""MCP server for bugsafe - Expose crash capture and secret scanning to LLMs."""

from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from mcp.server.fastmcp import FastMCP

from bugsafe import __version__

mcp = FastMCP(
    name="bugsafe",
    version=__version__,
)


@mcp.tool()
def scan_secrets(text: str) -> dict[str, Any]:
    """Scan text for secrets and return redaction report.

    Args:
        text: Text content to scan for secrets.

    Returns:
        Dictionary with redaction results including:
        - found: Boolean indicating if secrets were found
        - total: Total number of secrets detected
        - categories: Count by secret type (API_KEY, TOKEN, etc.)
        - redacted_text: Text with secrets replaced by tokens
    """
    from bugsafe.redact.engine import create_redaction_engine

    engine = create_redaction_engine()
    redacted_text, report = engine.redact(text)

    return {
        "found": report.get_total() > 0,
        "total": report.get_total(),
        "categories": report.get_summary(),
        "redacted_text": redacted_text,
    }


@mcp.tool()
def capture_crash(command: str, timeout: int = 60) -> dict[str, Any]:
    """Run a command and capture crash output with automatic secret redaction.

    Args:
        command: Shell command to execute (e.g., "python script.py").
        timeout: Maximum execution time in seconds (default: 60).

    Returns:
        Dictionary with capture results including:
        - exit_code: Process exit code
        - stdout: Redacted standard output
        - stderr: Redacted standard error
        - duration_ms: Execution time in milliseconds
        - redaction_summary: Count of secrets redacted by category
        - timed_out: Whether the command timed out
    """
    from bugsafe.capture.runner import CaptureConfig, run_command
    from bugsafe.redact.engine import create_redaction_engine

    config = CaptureConfig(timeout=timeout)
    result = run_command(command.split(), config)

    engine = create_redaction_engine()
    redacted_stdout, _ = engine.redact(result.stdout)
    redacted_stderr, _ = engine.redact(result.stderr)

    return {
        "exit_code": result.exit_code,
        "stdout": redacted_stdout,
        "stderr": redacted_stderr,
        "duration_ms": result.duration_ms,
        "redaction_summary": engine.get_redaction_summary(),
        "timed_out": result.timed_out,
    }


@mcp.tool()
def render_bundle(bundle_path: str, format: str = "markdown") -> str:
    """Render a .bugbundle file to human-readable format.

    Args:
        bundle_path: Path to the .bugbundle file.
        format: Output format - "markdown", "json", or "llm" (default: markdown).

    Returns:
        Rendered bundle content in the specified format.
    """
    from bugsafe.bundle.reader import read_bundle
    from bugsafe.render.json_export import to_json, to_llm_context
    from bugsafe.render.markdown import render_markdown

    path = Path(bundle_path)
    if not path.exists():
        return f"Error: Bundle not found at {bundle_path}"

    bundle = read_bundle(path)

    if format == "json":
        return to_json(bundle)
    elif format == "llm":
        return to_llm_context(bundle)
    else:
        return render_markdown(bundle)


@mcp.tool()
def audit_bundle(bundle_path: str) -> dict[str, Any]:
    """Verify that no secrets remain in a bundle after redaction.

    Args:
        bundle_path: Path to the .bugbundle file to audit.

    Returns:
        Dictionary with audit results:
        - passed: Boolean indicating if no secrets were found
        - leaks: List of pattern names that still matched (potential leaks)
    """
    from bugsafe.bundle.reader import read_bundle
    from bugsafe.redact.engine import create_redaction_engine

    path = Path(bundle_path)
    if not path.exists():
        return {
            "passed": False,
            "leaks": [],
            "error": f"Bundle not found: {bundle_path}",
        }

    bundle = read_bundle(path)
    engine = create_redaction_engine()

    combined_text = bundle.capture.stdout + "\n" + bundle.capture.stderr
    leaks = engine.verify_redaction(combined_text)

    return {
        "passed": len(leaks) == 0,
        "leaks": leaks,
    }


@mcp.tool()
def create_bundle(
    command: str,
    output_path: str | None = None,
    timeout: int = 300,
) -> dict[str, Any]:
    """Run a command and create a complete .bugbundle file.

    Args:
        command: Shell command to execute.
        output_path: Where to save the bundle (default: temp file).
        timeout: Maximum execution time in seconds (default: 300).

    Returns:
        Dictionary with:
        - bundle_path: Path to the created bundle
        - exit_code: Process exit code
        - redaction_summary: Count of secrets redacted
        - success: Whether bundle was created successfully
    """
    from datetime import datetime

    from bugsafe.bundle.schema import (
        BugBundle,
        BundleMetadata,
        CaptureOutput,
        Environment,
        PackageInfo,
    )
    from bugsafe.bundle.writer import create_bundle as write_bundle
    from bugsafe.capture.environment import EnvConfig, collect_environment
    from bugsafe.capture.runner import CaptureConfig, run_command
    from bugsafe.redact.engine import create_redaction_engine

    if output_path:
        bundle_file = Path(output_path)
    else:
        with NamedTemporaryFile(suffix=".bugbundle", delete=False) as f:
            bundle_file = Path(f.name)

    config = CaptureConfig(timeout=timeout)
    result = run_command(command.split(), config)

    engine = create_redaction_engine()
    redacted_stdout, _ = engine.redact(result.stdout)
    redacted_stderr, _ = engine.redact(result.stderr)

    env_snapshot = collect_environment(EnvConfig())

    capture = CaptureOutput(
        stdout=redacted_stdout,
        stderr=redacted_stderr,
        exit_code=result.exit_code,
        duration_ms=result.duration_ms,
        command=command.split(),
        timed_out=result.timed_out,
        truncated=result.truncated_stdout or result.truncated_stderr,
    )

    environment = Environment(
        python_version=env_snapshot.python_version,
        python_executable=env_snapshot.python_executable,
        platform=env_snapshot.platform,
        packages=[
            PackageInfo(name=p.name, version=p.version) for p in env_snapshot.packages
        ],
        env_vars=env_snapshot.env_vars,
        cwd=env_snapshot.cwd,
        git=None,
        virtualenv=env_snapshot.virtualenv,
        in_container=env_snapshot.in_container,
        ci_detected=env_snapshot.ci_detected,
    )

    bundle = BugBundle(
        metadata=BundleMetadata(
            created_at=datetime.utcnow(),
            bugsafe_version=__version__,
            redaction_salt_hash=engine.get_salt_hash(),
        ),
        capture=capture,
        traceback=None,
        environment=environment,
        redaction_report=engine.get_redaction_summary(),
    )

    write_bundle(bundle, bundle_file)

    return {
        "bundle_path": str(bundle_file),
        "exit_code": result.exit_code,
        "redaction_summary": engine.get_redaction_summary(),
        "success": True,
    }


def run_server() -> None:
    """Run the MCP server on stdio transport."""
    mcp.run()
