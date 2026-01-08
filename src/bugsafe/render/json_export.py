"""JSON export - Generate JSON output and LLM-optimized context from bundles."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from bugsafe.bundle.schema import BugBundle

DEFAULT_MAX_TOKENS = 4000
CHARS_PER_TOKEN = 4


def _estimate_tokens(text: str) -> int:
    """Estimate token count (rough approximation)."""
    return len(text) // CHARS_PER_TOKEN


def _truncate_to_tokens(text: str, max_tokens: int) -> tuple[str, bool]:
    """Truncate text to fit within token budget.

    Returns:
        Tuple of (truncated_text, was_truncated).
    """
    max_chars = max_tokens * CHARS_PER_TOKEN
    if len(text) <= max_chars:
        return text, False

    truncated = text[:max_chars]
    last_newline = truncated.rfind("\n")
    if last_newline > max_chars // 2:
        truncated = truncated[:last_newline]

    return truncated + "\n... [truncated]", True


def to_json(bundle: BugBundle, *, indent: int = 2) -> str:
    """Export bundle as JSON string.

    Args:
        bundle: The bundle to export.
        indent: JSON indentation level.

    Returns:
        JSON string representation.
    """
    return json.dumps(
        bundle.to_dict(), indent=indent, default=str, ensure_ascii=False
    )


def to_llm_context(
    bundle: BugBundle,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> str:
    """Generate LLM-optimized context from bundle.

    Prioritizes:
    1. Error message and traceback
    2. Command and exit code
    3. Relevant environment info
    4. Truncated stdout/stderr if space allows

    Args:
        bundle: The bundle to render.
        max_tokens: Maximum token budget.

    Returns:
        LLM-optimized context string.
    """
    sections: list[str] = []
    remaining_tokens = max_tokens

    header = _build_header(bundle)
    sections.append(header)
    remaining_tokens -= _estimate_tokens(header)

    if bundle.traceback:
        error_section = _build_error_section(bundle)
        error_tokens = _estimate_tokens(error_section)
        if error_tokens <= remaining_tokens:
            sections.append(error_section)
            remaining_tokens -= error_tokens

    env_section = _build_env_section(bundle)
    env_tokens = _estimate_tokens(env_section)
    if env_tokens <= remaining_tokens:
        sections.append(env_section)
        remaining_tokens -= env_tokens

    if bundle.capture.stderr and remaining_tokens > 100:
        stderr_budget = min(remaining_tokens // 2, 1000)
        stderr_truncated, _ = _truncate_to_tokens(
            bundle.capture.stderr, stderr_budget
        )
        stderr_section = f"## stderr\n```\n{stderr_truncated}\n```"
        sections.append(stderr_section)
        remaining_tokens -= _estimate_tokens(stderr_section)

    if bundle.capture.stdout and remaining_tokens > 100:
        stdout_truncated, _ = _truncate_to_tokens(
            bundle.capture.stdout, remaining_tokens - 50
        )
        stdout_section = f"## stdout\n```\n{stdout_truncated}\n```"
        sections.append(stdout_section)

    if bundle.redaction_report:
        redaction_note = _build_redaction_note(bundle)
        sections.append(redaction_note)

    return "\n\n".join(sections)


def _build_header(bundle: BugBundle) -> str:
    """Build the header section."""
    command = " ".join(bundle.capture.command) if bundle.capture.command else "N/A"
    return f"""# Bug Context

**Command:** `{command}`
**Exit code:** {bundle.capture.exit_code}
**Duration:** {bundle.capture.duration_ms}ms"""


def _build_error_section(bundle: BugBundle) -> str:
    """Build the error/traceback section."""
    if not bundle.traceback:
        return ""

    lines = [
        "## Error",
        "",
        f"**{bundle.traceback.exception_type}:** {bundle.traceback.message}",
        "",
        "### Traceback",
        "```python",
        "Traceback (most recent call last):",
    ]

    for frame in bundle.traceback.frames[-10:]:
        location = f'  File "{frame.file}", line {frame.line}'
        if frame.function:
            location += f", in {frame.function}"
        lines.append(location)
        if frame.code:
            lines.append(f"    {frame.code}")

    lines.append(f"{bundle.traceback.exception_type}: {bundle.traceback.message}")
    lines.append("```")

    return "\n".join(lines)


def _build_env_section(bundle: BugBundle) -> str:
    """Build the environment section."""
    lines = ["## Environment"]

    if bundle.environment:
        lines.append(f"- **Python:** {bundle.environment.python_version.split()[0]}")
        lines.append(f"- **Platform:** {bundle.environment.platform}")

        if bundle.environment.git and bundle.environment.git.ref:
            ref = bundle.environment.git.ref[:7]
            dirty = " (dirty)" if bundle.environment.git.dirty else ""
            lines.append(f"- **Git:** {ref}{dirty}")

        if bundle.environment.virtualenv:
            lines.append("- **Virtualenv:** Yes")

    return "\n".join(lines)


def _build_redaction_note(bundle: BugBundle) -> str:
    """Build redaction notice."""
    total = sum(bundle.redaction_report.values())
    categories = ", ".join(sorted(bundle.redaction_report.keys()))
    return f"*Note: {total} secrets were redacted ({categories})*"


def to_dict(bundle: BugBundle) -> dict[str, Any]:
    """Convert bundle to dictionary.

    Args:
        bundle: The bundle to convert.

    Returns:
        Dictionary representation.
    """
    return bundle.to_dict()
