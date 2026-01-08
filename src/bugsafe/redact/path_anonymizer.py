"""Path anonymizer - Cross-platform path anonymization."""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

TEMP_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"/var/folders/[^/]+/[^/]+/[^/]+"),
    re.compile(r"/tmp/pytest-of-[^/]+"),  # nosec B108 - pattern for detection
    re.compile(r"/tmp/[^/\s]+"),  # nosec B108 - pattern for detection
    re.compile(r"/private/var/folders/[^/]+/[^/]+/[^/]+"),
    re.compile(r"C:\\Users\\[^\\]+\\AppData\\Local\\Temp\\[^\\]+", re.IGNORECASE),  # nosec B108 - pattern for detection
    re.compile(r"C:\\Windows\\Temp\\[^\\]+", re.IGNORECASE),  # nosec B108 - pattern for detection
    re.compile(r"/run/user/\d+/[^/]+"),
)

SITE_PACKAGES_PATTERN = re.compile(r"[/\\](?:site-packages|dist-packages)[/\\]")

VENV_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"[/\\]\.venv[/\\]lib[/\\]python\d+\.\d+[/\\]"),
    re.compile(r"[/\\]venv[/\\]lib[/\\]python\d+\.\d+[/\\]"),
    re.compile(r"[/\\]\.virtualenvs[/\\][^/\\]+[/\\]lib[/\\]python\d+\.\d+[/\\]"),
    re.compile(r"[/\\]envs[/\\][^/\\]+[/\\]lib[/\\]python\d+\.\d+[/\\]"),
)


def _get_username() -> str:
    """Get current username safely."""
    return os.getenv("USER") or os.getenv("USERNAME") or "user"


def _get_home() -> str:
    """Get home directory safely."""
    try:
        return str(Path.home())
    except (RuntimeError, OSError):
        return ""


@dataclass
class PathAnonymizer:
    """Cross-platform path anonymizer.

    Transforms paths to remove sensitive information like usernames
    and absolute paths while preserving the structure needed for debugging.

    Attributes:
        project_root: Optional project root to replace with <PROJECT>.
        username: Username to anonymize.
        home_dir: Home directory path.
        anonymize_home: Whether to replace home dir with ~.
        anonymize_username: Whether to replace username with <USER>.
        anonymize_temp: Whether to replace temp dirs with <TMPDIR>.
        anonymize_site_packages: Whether to replace site-packages path.
        anonymize_venv: Whether to replace virtualenv paths.
    """

    project_root: Path | None = None
    username: str = field(default_factory=_get_username)
    home_dir: str = field(default_factory=_get_home)
    anonymize_home: bool = True
    anonymize_username: bool = True
    anonymize_temp: bool = True
    anonymize_site_packages: bool = True
    anonymize_venv: bool = True

    def anonymize(self, text: str) -> str:
        """Anonymize paths in text.

        Order matters: most specific replacements first.

        Args:
            text: Text containing paths to anonymize.

        Returns:
            Text with anonymized paths.
        """
        if not text:
            return text

        result = text

        if self.project_root:
            project_str = str(self.project_root)
            result = result.replace(project_str, "<PROJECT>")
            if sys.platform == "win32":
                result = result.replace(project_str.replace("/", "\\"), "<PROJECT>")

        if self.anonymize_venv:
            result = self._anonymize_venv(result)

        if self.anonymize_site_packages:
            result = self._anonymize_site_packages(result)

        if self.anonymize_temp:
            result = self._anonymize_temp(result)

        if self.anonymize_home and self.home_dir:
            result = self._anonymize_home(result)

        if self.anonymize_username and self.username:
            result = self._anonymize_username(result)

        return result

    def _anonymize_home(self, text: str) -> str:
        """Replace home directory with ~."""
        result = text.replace(self.home_dir, "~")

        if sys.platform == "win32":
            result = result.replace(self.home_dir.replace("/", "\\"), "~")

        return result

    def _anonymize_username(self, text: str) -> str:
        """Replace username in paths with <USER>."""
        username_escaped = re.escape(self.username)

        patterns = [
            (rf"(?<=/home/){username_escaped}(?=/|$)", "<USER>"),
            (rf"(?<=/Users/){username_escaped}(?=/|$)", "<USER>"),
            (rf"(?<=\\Users\\){username_escaped}(?=\\|$)", "<USER>"),
            (r"(?<=/run/user/)\d+(?=/|$)", "<UID>"),
        ]

        result = text
        for pattern, replacement in patterns:
            result = re.sub(pattern, replacement, result)

        return result

    def _anonymize_temp(self, text: str) -> str:
        """Replace temp directories with <TMPDIR>."""
        result = text
        for pattern in TEMP_PATTERNS:
            result = pattern.sub("<TMPDIR>", result)
        return result

    def _anonymize_site_packages(self, text: str) -> str:
        """Mark site-packages paths."""

        def replace_site_packages(match: re.Match[str]) -> str:
            sep = match.group(0)[0]
            return f"{sep}<SITE_PACKAGES>{sep}"

        return SITE_PACKAGES_PATTERN.sub(replace_site_packages, text)

    def _anonymize_venv(self, text: str) -> str:
        """Replace virtualenv paths with <VENV>."""
        result = text
        for pattern in VENV_PATTERNS:
            result = pattern.sub("/<VENV>/", result)
        return result

    def anonymize_path(self, path: str | Path) -> str:
        """Anonymize a single path.

        Args:
            path: Path to anonymize.

        Returns:
            Anonymized path string.
        """
        return self.anonymize(str(path))


def create_default_anonymizer(project_root: Path | None = None) -> PathAnonymizer:
    """Create a path anonymizer with default settings.

    Args:
        project_root: Optional project root directory.

    Returns:
        Configured PathAnonymizer.
    """
    return PathAnonymizer(project_root=project_root)
