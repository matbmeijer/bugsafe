"""Configuration management for bugsafe."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


def get_config_dir() -> Path:
    """Get the configuration directory path."""
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        return Path(xdg_config) / "bugsafe"
    return Path.home() / ".config" / "bugsafe"


def get_config_file() -> Path:
    """Get the configuration file path."""
    return get_config_dir() / "config.toml"


DEFAULT_ENV_ALLOWLIST = frozenset(
    {
        "PATH",
        "VIRTUAL_ENV",
        "PYTHONPATH",
        "CONDA_DEFAULT_ENV",
        "CONDA_PREFIX",
        "SHELL",
        "TERM",
        "LANG",
        "LC_ALL",
    }
)

DEFAULT_TIMEOUT = 300
DEFAULT_OUTPUT_FORMAT = "md"
DEFAULT_MAX_OUTPUT_SIZE = 1024 * 1024  # 1 MB


@dataclass
class DefaultsConfig:
    """Default configuration values.

    Attributes:
        env_allowlist: Environment variables to include.
        timeout: Default command timeout in seconds.
        max_output_size: Maximum output size in bytes.
    """

    env_allowlist: frozenset[str] = DEFAULT_ENV_ALLOWLIST
    timeout: int = DEFAULT_TIMEOUT
    max_output_size: int = DEFAULT_MAX_OUTPUT_SIZE


@dataclass
class RedactionConfig:
    """Redaction configuration.

    Attributes:
        custom_patterns_file: Path to custom patterns YAML file.
        redact_emails: Whether to redact email addresses.
        redact_ips: Whether to redact IP addresses.
        redact_uuids: Whether to redact UUIDs.
    """

    custom_patterns_file: Path | None = None
    redact_emails: bool = True
    redact_ips: bool = True
    redact_uuids: bool = False


@dataclass
class OutputConfig:
    """Output configuration.

    Attributes:
        default_format: Default output format (md or json).
        default_output_dir: Default directory for output files.
    """

    default_format: str = DEFAULT_OUTPUT_FORMAT
    default_output_dir: Path | None = None


@dataclass
class BugsafeConfig:
    """Main configuration class.

    Attributes:
        defaults: Default settings.
        redaction: Redaction settings.
        output: Output settings.
    """

    defaults: DefaultsConfig = field(default_factory=DefaultsConfig)
    redaction: RedactionConfig = field(default_factory=RedactionConfig)
    output: OutputConfig = field(default_factory=OutputConfig)

    @classmethod
    def load(cls, path: Path | None = None) -> BugsafeConfig:
        """Load configuration from file.

        Args:
            path: Path to config file. If None, uses default location.

        Returns:
            Loaded configuration.
        """
        if path is None:
            path = get_config_file()

        if not path.exists():
            return cls()

        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)
            return cls.from_dict(data)
        except (OSError, tomllib.TOMLDecodeError):
            return cls()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BugsafeConfig:
        """Create configuration from dictionary.

        Args:
            data: Configuration dictionary.

        Returns:
            Configuration instance.
        """
        defaults_data = data.get("defaults", {})
        redaction_data = data.get("redaction", {})
        output_data = data.get("output", {})

        env_allowlist = defaults_data.get("env_allowlist")
        if env_allowlist is not None:
            env_allowlist = frozenset(env_allowlist)
        else:
            env_allowlist = DEFAULT_ENV_ALLOWLIST

        defaults = DefaultsConfig(
            env_allowlist=env_allowlist,
            timeout=defaults_data.get("timeout", DEFAULT_TIMEOUT),
            max_output_size=defaults_data.get(
                "max_output_size", DEFAULT_MAX_OUTPUT_SIZE
            ),
        )

        custom_patterns = redaction_data.get("custom_patterns")
        if custom_patterns:
            custom_patterns = Path(custom_patterns).expanduser()

        redaction = RedactionConfig(
            custom_patterns_file=custom_patterns,
            redact_emails=redaction_data.get("redact_emails", True),
            redact_ips=redaction_data.get("redact_ips", True),
            redact_uuids=redaction_data.get("redact_uuids", False),
        )

        output_dir = output_data.get("default_output_dir")
        if output_dir:
            output_dir = Path(output_dir).expanduser()

        output = OutputConfig(
            default_format=output_data.get("default_format", DEFAULT_OUTPUT_FORMAT),
            default_output_dir=output_dir,
        )

        return cls(defaults=defaults, redaction=redaction, output=output)

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary.

        Returns:
            Configuration as dictionary.
        """
        return {
            "defaults": {
                "env_allowlist": list(self.defaults.env_allowlist),
                "timeout": self.defaults.timeout,
                "max_output_size": self.defaults.max_output_size,
            },
            "redaction": {
                "custom_patterns": (
                    str(self.redaction.custom_patterns_file)
                    if self.redaction.custom_patterns_file
                    else None
                ),
                "redact_emails": self.redaction.redact_emails,
                "redact_ips": self.redaction.redact_ips,
                "redact_uuids": self.redaction.redact_uuids,
            },
            "output": {
                "default_format": self.output.default_format,
                "default_output_dir": (
                    str(self.output.default_output_dir)
                    if self.output.default_output_dir
                    else None
                ),
            },
        }


def load_config(path: Path | None = None) -> BugsafeConfig:
    """Load configuration from file.

    Args:
        path: Optional path to config file.

    Returns:
        Loaded configuration.
    """
    return BugsafeConfig.load(path)
