"""Environment collector - Gather system and runtime environment information."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from importlib.metadata import distributions
from pathlib import Path
from platform import platform, uname

DEFAULT_ENV_ALLOWLIST: frozenset[str] = frozenset({
    "PATH", "PYTHONPATH", "VIRTUAL_ENV", "CONDA_DEFAULT_ENV",
    "LANG", "LC_ALL", "TZ", "TERM", "SHELL",
    "PWD", "HOME",
    "CI", "GITHUB_ACTIONS", "GITLAB_CI", "JENKINS_URL",
    "TRAVIS", "CIRCLECI", "BUILDKITE",
})

ENV_BLOCKLIST_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r".*PASSWORD.*", re.IGNORECASE),
    re.compile(r".*SECRET.*", re.IGNORECASE),
    re.compile(r".*TOKEN.*", re.IGNORECASE),
    re.compile(r".*KEY.*", re.IGNORECASE),
    re.compile(r".*CREDENTIAL.*", re.IGNORECASE),
    re.compile(r".*API.*", re.IGNORECASE),
)

ENV_BLOCKLIST: frozenset[str] = frozenset({
    "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN",
    "GITHUB_TOKEN", "GH_TOKEN", "GITLAB_TOKEN",
    "DATABASE_URL", "REDIS_URL", "MONGO_URI",
    "API_KEY", "SECRET_KEY", "PRIVATE_KEY",
})

CI_INDICATORS: tuple[str, ...] = (
    "CI", "GITHUB_ACTIONS", "GITLAB_CI", "JENKINS_URL",
    "TRAVIS", "CIRCLECI", "BUILDKITE", "AZURE_PIPELINES",
    "TEAMCITY_VERSION", "BITBUCKET_COMMIT",
)


@dataclass(frozen=True)
class EnvConfig:
    """Configuration for environment collection.

    Attributes:
        env_allowlist: Environment variables to include.
        include_git: Whether to collect git information.
        include_packages: Whether to collect installed packages.
        max_packages: Maximum number of packages to collect.
    """

    env_allowlist: frozenset[str] = DEFAULT_ENV_ALLOWLIST
    include_git: bool = True
    include_packages: bool = True
    max_packages: int = 500


@dataclass
class PlatformDetails:
    """Detailed platform information.

    Attributes:
        system: Operating system name.
        node: Network name of the machine.
        release: OS release version.
        version: OS version string.
        machine: Hardware architecture.
        processor: Processor type.
    """

    system: str
    node: str
    release: str
    version: str
    machine: str
    processor: str


@dataclass
class GitInfo:
    """Git repository information.

    Attributes:
        ref: Current commit SHA.
        branch: Current branch name.
        dirty: Whether there are uncommitted changes.
        remote_url: Remote origin URL (redacted).
    """

    ref: str | None = None
    branch: str | None = None
    dirty: bool | None = None
    remote_url: str | None = None


@dataclass
class PackageInfo:
    """Installed package information.

    Attributes:
        name: Package name.
        version: Package version.
    """

    name: str
    version: str


@dataclass
class EnvSnapshot:
    """Complete environment snapshot.

    Attributes:
        python_version: Full Python version string.
        python_executable: Path to Python executable.
        platform: Platform identifier string.
        platform_details: Detailed platform information.
        os_release: OS release information (Linux/macOS specific).
        packages: List of installed packages.
        packages_truncated: Whether package list was truncated.
        env_vars: Filtered environment variables.
        cwd: Current working directory.
        git: Git repository information.
        virtualenv: Whether running in a virtual environment.
        in_container: Whether running in a container.
        ci_detected: Whether running in CI environment.
    """

    python_version: str
    python_executable: str
    platform: str
    platform_details: PlatformDetails
    os_release: dict[str, str] = field(default_factory=dict)
    packages: list[PackageInfo] = field(default_factory=list)
    packages_truncated: bool = False
    env_vars: dict[str, str] = field(default_factory=dict)
    cwd: str = ""
    git: GitInfo | None = None
    virtualenv: bool = False
    in_container: bool = False
    ci_detected: bool = False


def _is_blocked_env_var(name: str) -> bool:
    """Check if an environment variable should be blocked."""
    if name in ENV_BLOCKLIST:
        return True
    return any(pattern.match(name) for pattern in ENV_BLOCKLIST_PATTERNS)


def _collect_env_vars(allowlist: frozenset[str]) -> dict[str, str]:
    """Collect filtered environment variables."""
    result: dict[str, str] = {}

    for name in allowlist:
        if _is_blocked_env_var(name):
            continue

        value = os.environ.get(name)
        if value is None:
            continue

        try:
            value.encode("utf-8")
            result[name] = value
        except (UnicodeEncodeError, UnicodeDecodeError):
            result[name] = "<binary>"

    return result


def _collect_platform_details() -> PlatformDetails:
    """Collect detailed platform information."""
    info = uname()
    return PlatformDetails(
        system=info.system,
        node=info.node,
        release=info.release,
        version=info.version,
        machine=info.machine,
        processor=info.processor,
    )


def _collect_os_release() -> dict[str, str]:
    """Collect OS release information."""
    result: dict[str, str] = {}

    os_release_path = Path("/etc/os-release")
    if os_release_path.exists():
        try:
            content = os_release_path.read_text(encoding="utf-8")
            for line in content.splitlines():
                if "=" in line:
                    key, _, value = line.partition("=")
                    result[key] = value.strip('"')
        except (OSError, UnicodeDecodeError):
            pass

    if sys.platform == "darwin":
        try:
            sw_vers = subprocess.run(
                ["sw_vers"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if sw_vers.returncode == 0:
                for line in sw_vers.stdout.splitlines():
                    if ":" in line:
                        key, _, value = line.partition(":")
                        result[key.strip()] = value.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass

    return result


def _collect_packages(max_packages: int) -> tuple[list[PackageInfo], bool]:
    """Collect installed package information.

    Returns:
        Tuple of (packages_list, was_truncated).
    """
    packages: list[PackageInfo] = []

    try:
        for dist in distributions():
            name = dist.metadata["Name"] if "Name" in dist.metadata else "unknown"
            version = (
                dist.metadata["Version"] if "Version" in dist.metadata else "unknown"
            )
            packages.append(PackageInfo(
                name=name or "unknown",
                version=version or "unknown",
            ))

            if len(packages) >= max_packages:
                return packages, True
    except Exception:
        pass

    packages.sort(key=lambda p: p.name.lower())
    return packages, False


def _run_git_command(args: list[str]) -> str | None:
    """Run a git command and return output, or None on failure."""
    try:
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


def _redact_git_url(url: str | None) -> str | None:
    """Redact sensitive parts of git URL."""
    if url is None:
        return None

    url = re.sub(r"://[^@]+@", "://<REDACTED>@", url)
    url = re.sub(r"git@([^:]+):", r"git@\1:<REDACTED>/", url)

    return url


def _collect_git_info() -> GitInfo | None:
    """Collect git repository information."""
    ref = _run_git_command(["rev-parse", "HEAD"])
    if ref is None:
        return None

    branch = _run_git_command(["branch", "--show-current"])

    status = _run_git_command(["status", "--porcelain"])
    dirty = bool(status) if status is not None else None

    remote_url = _run_git_command(["remote", "get-url", "origin"])
    remote_url = _redact_git_url(remote_url)

    return GitInfo(
        ref=ref,
        branch=branch or None,
        dirty=dirty,
        remote_url=remote_url,
    )


def _detect_virtualenv() -> bool:
    """Detect if running in a virtual environment."""
    return sys.prefix != sys.base_prefix


def _detect_container() -> bool:
    """Detect if running inside a container."""
    if Path("/.dockerenv").exists():
        return True

    cgroup_path = Path("/proc/1/cgroup")
    if cgroup_path.exists():
        try:
            content = cgroup_path.read_text(encoding="utf-8")
            if "docker" in content or "kubepods" in content or "containerd" in content:
                return True
        except (OSError, UnicodeDecodeError):
            pass

    return False


def _detect_ci() -> bool:
    """Detect if running in a CI environment."""
    return any(os.environ.get(indicator) for indicator in CI_INDICATORS)


def _get_cwd() -> str:
    """Get current working directory safely."""
    try:
        return os.getcwd()
    except OSError:
        return "<permission denied>"


def collect_environment(config: EnvConfig | None = None) -> EnvSnapshot:
    """Collect complete environment snapshot.

    Args:
        config: Configuration for collection. Uses defaults if None.

    Returns:
        EnvSnapshot with all collected information.
    """
    if config is None:
        config = EnvConfig()

    packages: list[PackageInfo] = []
    packages_truncated = False
    if config.include_packages:
        packages, packages_truncated = _collect_packages(config.max_packages)

    git_info: GitInfo | None = None
    if config.include_git:
        git_info = _collect_git_info()

    return EnvSnapshot(
        python_version=sys.version,
        python_executable=sys.executable,
        platform=platform(),
        platform_details=_collect_platform_details(),
        os_release=_collect_os_release(),
        packages=packages,
        packages_truncated=packages_truncated,
        env_vars=_collect_env_vars(config.env_allowlist),
        cwd=_get_cwd(),
        git=git_info,
        virtualenv=_detect_virtualenv(),
        in_container=_detect_container(),
        ci_detected=_detect_ci(),
    )
