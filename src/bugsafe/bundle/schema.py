"""Bundle schema - Pydantic models for .bugbundle format."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from bugsafe import __version__

BUNDLE_VERSION = "1.0"


class Frame(BaseModel):
    """A single stack frame in a traceback.

    Attributes:
        file: File path where the frame originated.
        line: Line number in the file.
        function: Function name (may be None for module-level).
        code: The source code line.
        locals: Local variables in the frame.
    """

    model_config = ConfigDict(frozen=True)

    file: str
    line: int
    function: str | None = None
    code: str | None = None
    locals: dict[str, str] | None = None


class Traceback(BaseModel):
    """Structured representation of a Python traceback.

    Attributes:
        exception_type: The type of exception raised.
        message: The exception message.
        frames: List of stack frames.
        chained: Chained exceptions (cause/context).
    """

    model_config = ConfigDict(frozen=True)

    exception_type: str
    message: str
    frames: list[Frame] = Field(default_factory=list)
    chained: list[Traceback] | None = None


class CaptureOutput(BaseModel):
    """Captured command output.

    Attributes:
        stdout: Standard output (redacted).
        stderr: Standard error (redacted).
        exit_code: Process exit code.
        duration_ms: Execution duration in milliseconds.
        command: The executed command.
        timed_out: Whether the command timed out.
        truncated: Whether output was truncated.
    """

    model_config = ConfigDict(frozen=True)

    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    duration_ms: int = 0
    command: list[str] = Field(default_factory=list)
    timed_out: bool = False
    truncated: bool = False


class GitInfo(BaseModel):
    """Git repository information.

    Attributes:
        ref: Current commit SHA.
        branch: Current branch name.
        dirty: Whether there are uncommitted changes.
        remote_url: Remote origin URL (redacted).
    """

    model_config = ConfigDict(frozen=True)

    ref: str | None = None
    branch: str | None = None
    dirty: bool | None = None
    remote_url: str | None = None


class PackageInfo(BaseModel):
    """Installed package information.

    Attributes:
        name: Package name.
        version: Package version.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    version: str


class Environment(BaseModel):
    """Environment snapshot.

    Attributes:
        python_version: Full Python version string.
        python_executable: Path to Python executable.
        platform: Platform identifier string.
        packages: List of installed packages.
        env_vars: Filtered environment variables.
        cwd: Current working directory.
        git: Git repository information.
        virtualenv: Whether running in virtualenv.
        in_container: Whether running in container.
        ci_detected: Whether running in CI.
    """

    model_config = ConfigDict(frozen=True)

    python_version: str
    python_executable: str = ""
    platform: str = ""
    packages: list[PackageInfo] = Field(default_factory=list)
    env_vars: dict[str, str] = Field(default_factory=dict)
    cwd: str = ""
    git: GitInfo | None = None
    virtualenv: bool = False
    in_container: bool = False
    ci_detected: bool = False


class BundleMetadata(BaseModel):
    """Bundle metadata.

    Attributes:
        version: Bundle format version.
        created_at: Creation timestamp.
        bugsafe_version: bugsafe version used to create bundle.
        redaction_salt_hash: SHA256 hash of redaction salt.
    """

    model_config = ConfigDict(frozen=True)

    version: str = BUNDLE_VERSION
    created_at: datetime = Field(default_factory=datetime.utcnow)
    bugsafe_version: str = __version__
    redaction_salt_hash: str = ""


class BugBundle(BaseModel):
    """Complete bug bundle.

    Attributes:
        metadata: Bundle metadata.
        capture: Captured command output.
        traceback: Parsed traceback (if available).
        environment: Environment snapshot.
        redaction_report: Summary of redactions by category.
    """

    model_config = ConfigDict(frozen=True)

    metadata: BundleMetadata = Field(default_factory=BundleMetadata)
    capture: CaptureOutput = Field(default_factory=CaptureOutput)
    traceback: Traceback | None = None
    environment: Environment | None = None
    redaction_report: dict[str, int] = Field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert bundle to dictionary for JSON serialization."""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BugBundle:
        """Create bundle from dictionary."""
        return cls.model_validate(data)
