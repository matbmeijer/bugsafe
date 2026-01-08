"""Process runner - Execute commands and capture output streams."""

from __future__ import annotations

import base64
import os
import re
import signal
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

# ANSI escape code pattern
ANSI_PATTERN = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]|\x1b\][^\x07]*\x07")


class CaptureError(Exception):
    """Base exception for capture errors."""


class WorkingDirectoryError(CaptureError):
    """Raised when working directory is invalid."""


class CommandNotFoundError(CaptureError):
    """Raised when command is not found."""


@dataclass(frozen=True)
class CaptureConfig:
    """Configuration for command capture.

    Attributes:
        timeout: Maximum execution time in seconds.
        max_output_bytes: Maximum bytes per stream (stdout/stderr).
        max_total_bytes: Maximum total bytes for bundle.
        encoding: Text encoding for output.
        encoding_errors: How to handle encoding errors.
        preserve_ansi: Whether to preserve ANSI escape codes.
        strip_cr: Whether to normalize \\r\\n to \\n.
        cwd: Working directory for command execution.
        env_passthrough: Environment variables to pass through.
    """

    timeout: int = 300
    max_output_bytes: int = 10_000_000
    max_total_bytes: int = 25_000_000
    encoding: str = "utf-8"
    encoding_errors: str = "replace"
    preserve_ansi: bool = False
    strip_cr: bool = True
    cwd: Path | None = None
    env_passthrough: frozenset[str] = field(default_factory=frozenset)


@dataclass
class CaptureResult:
    """Result of command capture.

    Attributes:
        command: The executed command.
        stdout: Captured standard output.
        stderr: Captured standard error.
        exit_code: Process exit code (-1 for errors, -2 for timeout).
        duration_ms: Execution duration in milliseconds.
        signal_num: Signal number if process was killed.
        timed_out: Whether the process timed out.
        truncated_stdout: Whether stdout was truncated.
        truncated_stderr: Whether stderr was truncated.
        encoding_errors_count: Number of encoding errors encountered.
        is_binary_stdout: Whether stdout is binary (base64 encoded).
        is_binary_stderr: Whether stderr is binary (base64 encoded).
        error_message: Error message if command failed to start.
    """

    command: list[str]
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    duration_ms: int = 0
    signal_num: int | None = None
    timed_out: bool = False
    truncated_stdout: bool = False
    truncated_stderr: bool = False
    encoding_errors_count: int = 0
    is_binary_stdout: bool = False
    is_binary_stderr: bool = False
    error_message: str | None = None


def _strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    return ANSI_PATTERN.sub("", text)


def _decode_output(
    data: bytes,
    config: CaptureConfig,
) -> tuple[str, bool, int]:
    """Decode bytes to string, handling binary data.

    Returns:
        Tuple of (decoded_string, is_binary, encoding_error_count).
    """
    if not data:
        return "", False, 0

    try:
        text = data.decode(config.encoding, errors="strict")
        return text, False, 0
    except UnicodeDecodeError:
        pass

    try:
        text = data.decode(config.encoding, errors=config.encoding_errors)
        error_count = text.count("\ufffd")
        if error_count > len(data) * 0.1:
            return base64.b64encode(data).decode("ascii"), True, 0
        return text, False, error_count
    except (UnicodeDecodeError, LookupError):
        return base64.b64encode(data).decode("ascii"), True, 0


def _truncate_output(
    data: bytes,
    max_bytes: int,
) -> tuple[bytes, bool]:
    """Truncate output if it exceeds max bytes.

    Returns:
        Tuple of (data, was_truncated).
    """
    if len(data) <= max_bytes:
        return data, False

    truncated_bytes = len(data) - max_bytes
    marker = f"\n[TRUNCATED: {truncated_bytes} bytes omitted]\n".encode()
    return data[:max_bytes] + marker, True


def _normalize_output(text: str, config: CaptureConfig) -> str:
    """Normalize output text based on configuration."""
    if config.strip_cr:
        text = text.replace("\r\n", "\n").replace("\r", "\n")

    if not config.preserve_ansi:
        text = _strip_ansi(text)

    return text


def _terminate_process(
    proc: subprocess.Popen[bytes], grace_period: float = 5.0
) -> int | None:
    """Terminate process gracefully, then forcefully if needed.

    Returns:
        Signal number used to terminate (None on Windows after kill).
    """
    proc.terminate()
    try:
        proc.wait(timeout=grace_period)
        return signal.SIGTERM
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
        # SIGKILL doesn't exist on Windows
        return getattr(signal, "SIGKILL", None)


def run_command(
    cmd: Sequence[str],
    config: CaptureConfig | None = None,
) -> CaptureResult:
    """Execute a command and capture its output.

    Args:
        cmd: Command and arguments to execute.
        config: Capture configuration options.

    Returns:
        CaptureResult with captured output and metadata.

    Raises:
        KeyboardInterrupt: If interrupted by user (after cleanup).
    """
    if config is None:
        config = CaptureConfig()

    command_list = list(cmd)
    result = CaptureResult(command=command_list)

    if config.cwd is not None and not config.cwd.is_dir():
        result.exit_code = -1
        result.error_message = f"Working directory does not exist: {config.cwd}"
        return result

    cwd = str(config.cwd) if config.cwd else None
    env = _build_environment(config.env_passthrough) if config.env_passthrough else None

    start_time = time.monotonic()
    proc: subprocess.Popen[bytes] | None = None
    stdout_data = b""
    stderr_data = b""
    keyboard_interrupt = False

    try:
        proc = subprocess.Popen(
            command_list,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            cwd=cwd,
            env=env,
        )

        try:
            stdout_data, stderr_data = proc.communicate(timeout=config.timeout)
        except subprocess.TimeoutExpired:
            result.signal_num = _terminate_process(proc)
            stdout_data, stderr_data = proc.communicate()
            result.timed_out = True
            result.exit_code = -2

    except FileNotFoundError:
        result.exit_code = -1
        result.error_message = f"Command not found: {command_list[0]}"
        result.stderr = result.error_message

    except PermissionError:
        result.exit_code = -1
        result.error_message = f"Permission denied: {command_list[0]}"
        result.stderr = result.error_message

    except KeyboardInterrupt:
        keyboard_interrupt = True
        if proc is not None and proc.poll() is None:
            _terminate_process(proc, grace_period=1.0)
            try:
                stdout_data, stderr_data = proc.communicate(timeout=1.0)
            except subprocess.TimeoutExpired:
                pass
        result.exit_code = -128 - signal.SIGINT

    except OSError as e:
        result.exit_code = -1
        result.error_message = f"OS error: {e}"
        result.stderr = result.error_message

    finally:
        result.duration_ms = int((time.monotonic() - start_time) * 1000)

    if proc is not None and result.exit_code == 0:
        if proc.returncode is not None:
            if proc.returncode < 0:
                result.signal_num = -proc.returncode
            result.exit_code = proc.returncode

    stdout_data, result.truncated_stdout = _truncate_output(
        stdout_data, config.max_output_bytes
    )
    stderr_data, result.truncated_stderr = _truncate_output(
        stderr_data, config.max_output_bytes
    )

    stdout_text, result.is_binary_stdout, stdout_errors = _decode_output(
        stdout_data, config
    )
    stderr_text, result.is_binary_stderr, stderr_errors = _decode_output(
        stderr_data, config
    )
    result.encoding_errors_count = stdout_errors + stderr_errors

    if not result.is_binary_stdout:
        result.stdout = _normalize_output(stdout_text, config)
    else:
        result.stdout = stdout_text

    if not result.is_binary_stderr:
        result.stderr = _normalize_output(stderr_text, config)
    else:
        result.stderr = stderr_text

    if keyboard_interrupt:
        raise KeyboardInterrupt

    return result


def _build_environment(passthrough: frozenset[str]) -> dict[str, str]:
    """Build environment dict with only specified variables."""
    current_env = os.environ.copy()
    return {k: v for k, v in current_env.items() if k in passthrough}
